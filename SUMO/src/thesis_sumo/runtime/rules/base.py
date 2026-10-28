"""Shared machinery of the TraCI rules: the intervention record, the command wrapper and the `Rule` base class.

Every command goes through `Commands`, which

- allows one intervention per vehicle at a time (`busy`): a vehicle under one rule is skipped by the others, so
  modes and speed overrides never stack;
- keeps the intervals during which a vehicle was under intervention (`intervened(vid, t)`, the runner's collision
  hook, ruling R10). Ruling R30: a window opens with the command and stays open after the overrides are undone
  until the vehicle is first seen on a non-internal lane after the stop line (`update_windows`: a lane that is
  neither internal nor an inbound lane of the junction), or leaves the zone; so a red runner that collides inside
  the junction after its stop-line crossing is still "intervened";
- changes the speed mode only by clearing named bits of the vehicle's current mode, checks the change with
  `getSpeedMode`, and on restore sets the recorded original mode and checks it again (`ModeNotRestoredError` when
  SUMO reports another mode: a bug, never silently tolerated).

speedMode bits (sumo.dlr.de/docs/TraCI/Change_Vehicle_State.html#speed_mode_0xb3): bit0 safe speed, bit1 max
accel, bit2 max decel, bit3 right of way at intersections (approaching foes), bit4 brake hard to avoid passing a
red light, bit5 disregard right of way within intersections, bit6 disregard speed limit. Default 31.
Experiment (SUMO 1.27.0, single-lane signalised cross, a motorcycle halted 1.0 m before a red stop line,
`setSpeed(3)`, then the mode): 31 and 23 (bit3 cleared) stay at the line; 15 (bit4 cleared), 7 and 0 cross. With a
crossing foe stream (one car every 0.7 s on the green road) 15 still waits (bit3 kept: it yields to the foes) while
7 and 0 drive into the stream. So passing a red light needs exactly bit4 cleared (`RED_LIGHT_BIT`), and every
other safety bit stays as it is.

`setSpeed(v)` / `setSpeed(-1)` and `changeLane` / `changeSublane` act through the vehicle's influencer and keep its
vType. Type setters (e.g. `setLateralAlignment`, `setMinGap`) are never used: they give the vehicle a copy of its
type named `typeid@vehid` (same docs page), which would break vType matching and the fcd `type` column.

Intervention log row (`interventions.csv`): `t` = time the command was issued, `veh_id`, `rule` (rule_type),
`action`, `executed` (SUMO's observed response, defined per rule), `reason` (why not executed, or "" when
executed), `t_end` = time the outcome was decided, `detail` = rule-specific context at the decision ("" if none;
queue_space_seeking: `approach=..;queue_m=..;wait_s=..`, the inputs of the later space_seeking_events table).
"""

from __future__ import annotations

import random
from collections import Counter
from dataclasses import dataclass, field

from thesis_sumo.runtime.state import JunctionInfo, Step

RED_LIGHT_BIT = 1 << 4
LOG_COLUMNS = ("t", "veh_id", "rule", "action", "executed", "reason", "t_end", "detail")


class ModeNotRestoredError(RuntimeError):
    """SUMO reports another speed mode than the one the controller set."""


@dataclass(frozen=True)
class Intervention:
    t: float
    veh_id: str
    rule: str
    action: str
    executed: bool
    reason: str
    t_end: float
    detail: str = ""

    def row(self) -> tuple:
        return (f"{self.t:.2f}", self.veh_id, self.rule, self.action, str(self.executed), self.reason,
                f"{self.t_end:.2f}", self.detail)


@dataclass
class Active:
    """One running intervention of a rule on one vehicle."""

    vid: str
    action: str
    t0: float
    orig_speed_mode: int | None = None   # set when the speed mode was changed
    speed_set: bool = False              # setSpeed override active
    data: dict = field(default_factory=dict)


class Commands:
    def __init__(self, backend, inbound_lanes=frozenset()):
        self.b = backend
        self.inbound = frozenset(inbound_lanes)
        self.owner: dict[str, str] = {}
        self._intervals: dict[str, list[list]] = {}
        self._closing: set[str] = set()  # intervention over, window open until past the junction (R30)

    def busy(self, vid: str) -> bool:
        return vid in self.owner

    def begin(self, vid: str, rule: str, t: float) -> None:
        if vid in self.owner:
            raise RuntimeError(f"vehicle {vid} is already under {self.owner[vid]}")
        self.owner[vid] = rule
        if vid in self._closing:  # a new intervention before the last window closed: close it now
            self._close(vid, t)
        self._intervals.setdefault(vid, []).append([t, None])

    def end(self, vid: str, t: float) -> None:
        """The intervention is over (overrides undone); its window closes in `update_windows` (R30)."""
        self.owner.pop(vid, None)
        self._closing.add(vid)

    def close_window(self, vid: str, t: float) -> None:
        """Close the window of an ended intervention early, when a rule knows its effect is over before the vehicle
        is past the junction (queue_space_seeking right_lane: merged back into a through lane)."""
        if vid in self._closing and vid not in self.owner:
            self._close(vid, t)

    def _close(self, vid: str, t: float) -> None:
        self._closing.discard(vid)
        iv = self._intervals.get(vid)
        if iv and iv[-1][1] is None:
            iv[-1][1] = t

    def update_windows(self, s: "Step") -> None:
        """Close the windows of vehicles that are past the junction (first non-internal, non-inbound lane) or no
        longer in the zone."""
        for vid in sorted(self._closing):
            v = s.vehicles.get(vid)
            if v is None or (not v.lane.startswith(":") and v.lane not in self.inbound):
                self._close(vid, s.t)

    def intervened(self, vid: str, t: float) -> bool:
        return any(t0 <= t and (t1 is None or t <= t1) for t0, t1 in self._intervals.get(vid, ()))

    def clear_speed_bits(self, vid: str, bits: int) -> int:
        """Clear `bits` of the vehicle's speed mode; return the original mode."""
        orig = self.b.vehicle.getSpeedMode(vid)
        new = orig & ~bits
        self.b.vehicle.setSpeedMode(vid, new)
        got = self.b.vehicle.getSpeedMode(vid)
        if got != new:
            raise ModeNotRestoredError(f"{vid}: speed mode {new} set, SUMO reports {got}")
        return orig

    def restore_speed_mode(self, vid: str, orig: int) -> None:
        self.b.vehicle.setSpeedMode(vid, orig)
        got = self.b.vehicle.getSpeedMode(vid)
        if got != orig:
            raise ModeNotRestoredError(f"{vid}: speed mode {orig} restored, SUMO reports {got}")


class Rule:
    """Base class: `on_step(step)` returns the interventions whose outcome was decided in this step."""

    rule_type: str = ""

    def __init__(self, params: dict, vtype_ids: list[str], info: JunctionInfo, cmd: Commands, rng: random.Random):
        self.p = dict(params)
        self.vtypes = frozenset(vtype_ids)
        self.info, self.cmd, self.b, self.rng = info, cmd, cmd.b, rng
        self.active: dict[str, Active] = {}
        self.counters: Counter = Counter()
        self._route_next: dict[str, str | None] = {}

    # ------------------------------------------------------------ hooks
    def on_step(self, s: Step) -> list[Intervention]:
        raise NotImplementedError

    def close(self, t: float) -> list[Intervention]:
        """End of the run: interventions still running are logged as not executed (`run_ended`)."""
        return [self.finish(vid, t, False, "run_ended") for vid in sorted(self.active)]

    # ------------------------------------------------------------ helpers
    def applies(self, s: Step, vid: str) -> bool:
        return s.vehicles[vid].vtype in self.vtypes and not self.cmd.busy(vid)

    def link_of(self, s: Step, vid: str) -> int | None:
        """TLS link index of the connection `vid` takes from its stop-line lane to its route's next edge (its own
        signal, `Step.signal`); None when that lane has no link to the edge: the approach group's signal applies."""
        lane = s.vehicles[vid].lane
        if vid not in self._route_next:  # one getRoute per vehicle; the edge after the approach never changes
            route, edge = list(self.b.vehicle.getRoute(vid)), lane.rsplit("_", 1)[0]
            i = route.index(edge) if edge in route else -1
            self._route_next[vid] = route[i + 1] if 0 <= i < len(route) - 1 else None
        nxt = self._route_next[vid]
        return next((self.info.link_of_internal[lk.via] for lk in self.info.links.get(lane, ())
                     if lk.to_edge == nxt and lk.via in self.info.link_of_internal), None)

    def start(self, vid: str, action: str, t: float, **data) -> Active:
        self.cmd.begin(vid, self.rule_type, t)
        a = Active(vid, action, t, data=data)
        self.active[vid] = a
        return a

    def release(self, vid: str, t: float) -> bool:
        """Undo the overrides of an active intervention and end it; False when the vehicle has left the
        simulation (nothing to restore)."""
        a = self.active.pop(vid)
        alive = True
        try:
            if a.speed_set:
                self.b.vehicle.setSpeed(vid, -1)
            if a.orig_speed_mode is not None:
                self.cmd.restore_speed_mode(vid, a.orig_speed_mode)
        except self.b.TraCIException:
            alive = False
        self.cmd.end(vid, t)
        return alive

    def finish(self, vid: str, t: float, executed: bool, reason: str) -> Intervention:
        """`release` the intervention and return its record."""
        a = self.active[vid]
        if not self.release(vid, t) and not executed and reason == "left_zone":
            reason = "vehicle_gone"
        return Intervention(a.t0, vid, self.rule_type, a.action, executed, "" if executed else reason, t,
                            a.data.get("detail", ""))

    def record(self, vid: str, action: str, t: float, executed: bool, reason: str, detail: str = "") -> Intervention:
        """A command decided in the same step (e.g. refused before it was sent): no override, no interval."""
        return Intervention(t, vid, self.rule_type, action, executed, "" if executed else reason, t, detail)

    def failed_command(self, a: Active, t: float, err: Exception) -> Intervention:
        return self.finish(a.vid, t, False, f"command_error: {err}")

    def left_zone(self, s: Step) -> list[Intervention]:
        return [self.finish(vid, s.t, False, "left_zone") for vid in sorted(self.active) if vid not in s.vehicles]


def start_red_pass(rule: Rule, s: Step, vid: str, app: str, action: str, v_max: float | None = None,
                   link: int | None = None) -> Intervention | None:
    """Let `vid` pass the red stop line of `app` (red = its own TLS link `link`, `Rule.link_of`): clear speedMode bit4
    (and cap the speed with setSpeed(v_max)). Returns a record only when SUMO refused the command (TraCIException)."""
    a = rule.start(vid, action, s.t, app=app, link=link)
    try:
        a.orig_speed_mode = rule.cmd.clear_speed_bits(vid, RED_LIGHT_BIT)
        if v_max is not None:
            rule.b.vehicle.setSpeed(vid, v_max)
            a.speed_set = True
    except rule.b.TraCIException as e:
        return rule.failed_command(a, s.t, e)
    return None


def settle_red_passes(rule: Rule, s: Step) -> list[Intervention]:
    """Outcome of the running red passes: executed when the vehicle crossed the stop line while its own link was
    red (SUMO moved it onto an internal lane); not executed when the red ended first or the vehicle left the zone.
    The overrides are undone at the outcome."""
    out = rule.left_zone(s)
    crossed = {vid: st for vid, _app, st in s.crossings}
    for vid in sorted(rule.active):
        a = rule.active[vid]
        if vid in crossed:
            out.append(rule.finish(vid, s.t, crossed[vid] == "r", "crossed_after_red"))
        elif s.signal(a.data["app"], a.data["link"]) != "r":
            out.append(rule.finish(vid, s.t, False, "red_ended_before_crossing"))
    return out
