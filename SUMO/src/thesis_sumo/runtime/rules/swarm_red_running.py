"""`swarm_red_running` (PLAN 4.5): a vehicle of the rule's vTypes that reaches the stop line on red runs it with
probability p = min(p_max, p0 + k * n), n = vehicles (any type) that crossed the same approach's stop line on red
within the last `dt` s (window (t - dt, t]).

- Arrival at the stop line = the vehicle is in the front row (front within `state.FRONT_ROW_M` of the stop line)
  while its own signal is red: the TLS link it takes (`Rule.link_of`; the approach group if its lane has no link to
  its next edge), so a LVL left-turner in its left arrow is not on red (protected left, 2026-10-28) and one waiting
  during the LVL straight green is (yellow is SUMO's own jmDriveAfterYellowTime business).
- The decision is drawn once per vehicle and red phase of its signal, at its first front-row step on red (Task 7
  note: drawing every step would make p a per-step hazard and overshoot the red-running share).
- A red violation (for n) = a stop-line crossing (inbound lane -> internal lane) while the crossing vehicle's own link
  is red, whoever caused it (this rule, early_start, SUMO's jmDriveAfterRedTime).
- Command and `executed`: as `early_start` (speedMode bit4 cleared, no speed cap; undone at the outcome).

Clear junction (owner decision D1, 2026-11-04). A vehicle that waits for its green is kept out of the intersection by
the red light until the crossing streams are gone; a runner (bit4 cleared) is not, and SUMO lets it in while vehicles
of another stream are still in its path (seen on the proxy net, below). The rule therefore applies SUMO's two entry
rules (sumo.dlr.de/docs/Simulation/Intersections.html) itself before it sends the command:

- junction blocking (the "no-block-heuristic"): the exit lane of its link (`Link.to_lane`, the lane after the internal
  lane(s)) has room for it, i.e. the rear of the last vehicle on that lane is at least the runner's length + minGap
  (SUMO's brutto length, `getLengthWithGap`) from the lane start;
- "not permitted to enter the intersection if it is blocked by vehicles already on the intersection": no vehicle at
  all on an internal lane in conflict with its link (`lane.getInternalFoes` of each internal lane of the link), and
  no vehicle halting (speed < `state.HALT_SPEED_MPS`) on an internal lane of its own link (a moving leader there is
  no block: swarm runners follow each other). Foes still before their stop line are SUMO's business: bit3 (right of
  way) stays set.

REF_n29s5 B1, PROXY_D1 seed 4 (t = 287 s) and PROXY_D2 seed 1 (t = 1029 s): the lock starts when a runner enters
while halted vehicles of another stream stand in its path (HMG stragglers on the LVL_W straight's path; LVL_E
left-turners on the NT straight's path) and each side then waits for the other. In these and in PROXY_D2 seed 4
the exit lanes of the vehicles frozen in the junction were empty: the exit check alone would not have fired. Counting
only halted foes left locks (with this run's PROXY_D1 seed 3, t = 1017 s: the runner entered while the foes were
moving, one of them then stopped in its path, the runner crawled 7 m in 20 s inside the junction and was caught by
the next phase's stream). Hence any vehicle on a conflicting internal lane blocks.

The decision stays drawn at arrival, with the p of that moment, so the drawn red-running share does not depend on the
junction state. A runner that finds the junction blocked is held (no command yet) and starts its pass at the first
step the junction is clear while its signal is still red; it is logged at its outcome: if the pass starts, as any
pass (`t` = command time, `detail` = `held_s=<seconds held>`); if its signal leaves red first, not executed with reason
`junction_blocked`; if it crossed anyway (SUMO's own red running), another rule took it, or it left, not executed with
`crossed_while_held`, `taken_by_other_rule`, `left_zone`. No parameter: both checks are SUMO's own rules. A runner
whose lane has no link to its next edge (its signal is the approach group's) has no path to check and starts at once.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from thesis_sumo.runtime.rules.base import Intervention, Rule, settle_red_passes, start_red_pass
from thesis_sumo.runtime.state import HALT_SPEED_MPS, Link, Step


@dataclass(frozen=True)
class _Path:
    """Internal lanes of a link (its chain, entry first), the internal lanes in conflict with them, its exit lane."""

    chain: tuple[str, ...]
    foes: frozenset[str]
    exit_lane: str


@dataclass(frozen=True)
class _Held:
    t_draw: float
    app: str
    link: int | None
    red_id: int
    path: _Path


class SwarmRedRunning(Rule):
    rule_type = "swarm_red_running"

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._violations = {app: deque() for app in self.info.lanes}
        self._drawn: dict[tuple[str, int | None], tuple[int, set]] = {}  # (approach, own link) -> (red id, drawn)
        self.draw_log: list[tuple[float, str, int, float, bool]] = []  # (t, vehicle, n, p, runs) per draw
        self._held: dict[str, _Held] = {}
        self._paths: dict[str, _Path] = {}       # via lane -> path
        self._min_gap: dict[str, float] = {}     # vType -> minGap

    def n_recent(self, app: str, t: float) -> int:
        q = self._violations[app]
        while q and q[0] <= t - self.p["dt"]:
            q.popleft()
        return len(q)

    def path(self, lk: Link) -> _Path:
        if lk.via not in self._paths:
            chain = [lk.via]
            while True:
                nxt = [x[4] for x in self.b.lane.getLinks(chain[-1]) if x[4]]
                if not nxt:
                    break
                chain.append(nxt[0])
            foes = {f for ln in chain for f in self.b.lane.getInternalFoes(ln)} - set(chain)
            self._paths[lk.via] = _Path(tuple(chain), frozenset(foes), lk.to_lane)
        return self._paths[lk.via]

    def blocked(self, s: Step, vid: str, path: _Path) -> bool:
        """The junction is blocked for `vid` (module doc): any vehicle on a conflicting internal lane, a halted vehicle
        on its link's internal lanes, or no room for it on its exit lane."""
        if any(s.by_lane.get(ln) for ln in path.foes):
            return True
        if any(s.vehicles[o].speed < HALT_SPEED_MPS for ln in path.chain for o in s.by_lane.get(ln, ())):
            return True
        on_exit = s.by_lane.get(path.exit_lane)
        if not on_exit:
            return False
        last = s.vehicles[on_exit[-1]]
        vtype = s.vehicles[vid].vtype
        if vtype not in self._min_gap:
            self._min_gap[vtype] = self.b.vehicletype.getMinGap(vtype)
        need = self.info.vtype_length[vtype] + self._min_gap[vtype]
        return last.pos - self.info.vtype_length[last.vtype] < need

    def _start(self, s: Step, vid: str, app: str, link: int | None, t_draw: float) -> Intervention | None:
        rec = start_red_pass(self, s, vid, app, "run_red", link=link)
        if rec is None and t_draw < s.t:
            self.active[vid].data["detail"] = f"held_s={s.t - t_draw:.1f}"
        return rec

    def _drop(self, vid: str, t: float, reason: str) -> Intervention:
        h = self._held.pop(vid)
        return Intervention(h.t_draw, vid, self.rule_type, "run_red", False, reason, t)

    def _release_held(self, s: Step) -> list[Intervention]:
        out = []
        crossed = {vid for vid, _app, _st in s.crossings}
        for vid in sorted(self._held):
            h = self._held[vid]
            if vid not in s.vehicles:
                out.append(self._drop(vid, s.t, "left_zone"))
            elif vid in crossed or s.vehicles[vid].lane not in self.info.lane_approach:
                out.append(self._drop(vid, s.t, "crossed_while_held"))
            elif s.signal(h.app, h.link) != "r" or s.red_id_of(h.app, h.link) != h.red_id:
                out.append(self._drop(vid, s.t, "junction_blocked"))
            elif self.cmd.busy(vid):
                out.append(self._drop(vid, s.t, "taken_by_other_rule"))
            elif not self.blocked(s, vid, h.path):
                del self._held[vid]
                rec = self._start(s, vid, h.app, h.link, h.t_draw)
                if rec is not None:
                    out.append(rec)
        return out

    def on_step(self, s: Step) -> list[Intervention]:
        for _vid, app, state in s.crossings:
            if state == "r":
                self._violations[app].append(s.t)
        out = settle_red_passes(self, s)
        out += self._release_held(s)
        for app in self.info.lanes:
            n = self.n_recent(app, s.t)
            for vid in s.front_row(app):
                if not self.applies(s, vid) or vid in self._held:
                    continue
                lk = self.link_to(s, vid)
                link = None if lk is None else self.info.link_of_internal[lk.via]
                if s.signal(app, link) != "r":
                    continue
                rid, drawn = self._drawn.get((app, link), (None, set()))
                if rid != s.red_id_of(app, link):
                    drawn = set()
                    self._drawn[(app, link)] = (s.red_id_of(app, link), drawn)
                if vid in drawn:
                    continue
                drawn.add(vid)
                p = min(self.p["p_max"], self.p["p0"] + self.p["k"] * n)
                self.counters["draws"] += 1
                runs = self.rng.random() < p
                self.draw_log.append((s.t, vid, n, p, runs))
                if not runs:
                    continue
                self.counters["decided_run"] += 1
                path = None if lk is None else self.path(lk)
                if path is not None and self.blocked(s, vid, path):
                    self.counters["held"] += 1
                    self._held[vid] = _Held(s.t, app, link, s.red_id_of(app, link), path)
                    continue
                rec = self._start(s, vid, app, link, s.t)
                if rec is not None:
                    out.append(rec)
        return out

    def close(self, t: float) -> list[Intervention]:
        return super().close(t) + [self._drop(vid, t, "run_ended") for vid in sorted(self._held)]
