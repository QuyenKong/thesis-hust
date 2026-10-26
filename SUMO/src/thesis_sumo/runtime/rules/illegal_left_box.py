"""`illegal_left_box` (PLAN 4.5, rulings R14/R15/R25): delays the release of the illegal left-turners waiting inside
the junction box by `release_lag_s`. It only HOLDS vehicles (`setSpeed(0)`, undone with `setSpeed(-1)`); it never
sends a vehicle into a foe, changes no speed-mode bit and touches no other vehicle, so SUMO's native foe checks
decide every departure.

Per illegal-left approach A (site `illegal_left.approaches`), with O = its opposing approach:

- Native release: after O's green ends (G -> y), the first step at which a rule vehicle in the front of a hold lane
  (front within `state.FRONT_ROW_M` of the waiting point) starts moving (speed < `RELEASE_SPEED_MPS` at the
  previous step, on the hold lanes, and >= now) is SUMO's native release time t_nat (Phase 3: ~4.7 s after the
  opposing green end).
- `release_lag_s` > 0: every rule vehicle on the hold lanes is held from t_nat to t_nat + release_lag_s
  (`hold_release_lag`), so the release comes release_lag_s after the native one; vehicles entering the hold lanes in
  that window are held too. 0 = no hold (native).
- Hold lanes = the box lanes before the internal-junction waiting point (`JunctionInfo.hold_lanes`); a vehicle past it
  is never held. A vehicle that cannot stop before the waiting point (speed^2 / (2 decel) > distance left) is not
  held and logged `cannot_stop`.
- The waiting point is NOT outside the crossing stream: on the proxy net the hold lane `:<junction>_16_0` crosses
  the three HDT_N through internal lanes and the waiting point is 0.03 m from the lane-2 centreline (ruling R25).
  SUMO registers a vehicle's link approach before a TraCI speed override acts, so a held waiter still announces
  that it will pass and crossing vehicles yield to it: a hold that reaches into the crossing green delays the
  crossing start (experiment: tiny cross, a 2 s N-S stream, waiters held through the crossing green: N-S passages
  35 -> 18, waits up to 34 s). This is the intended "late box release delays the crossing road" effect of the lag
  (at most 4 s); letting the crossing vehicles ignore held waiters (junction-model ignore-ids parameter) was tried and
  rejected (junction collisions, R25), and holding waiters through the whole crossing green
  (`max_clear_into_cross_green_s`) was dropped with it.
- `executed` = the vehicle was still on the hold lanes when its hold ended (SUMO kept it there); `not_held` when it
  left them during the hold.
"""

from __future__ import annotations

from thesis_sumo.runtime.rules.base import Intervention, Rule
from thesis_sumo.runtime.state import FRONT_ROW_M, Step

RELEASE_SPEED_MPS = 0.1  # "starts moving": one 0.1 s step at the lowest accel bound (0.5 m/s^2) gives 0.05 m/s,
# so detection takes one to two steps
ACTION = "hold_release_lag"


class IllegalLeftBox(Rule):
    rule_type = "illegal_left_box"

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        if not self.info.hold_lanes:
            raise ValueError("illegal_left_box needs the site's illegal_left.approaches box (JunctionInfo need_box)")
        self._cycle: dict[str, dict | None] = {app: None for app in self.info.hold_lanes}
        self._prev_speed: dict[str, float] = {}
        self._decel: dict[str, float] = {}
        self._refused: set = set()

    def _update_cycle(self, s: Step, app: str) -> dict | None:
        opp = self.info.opposing.get(app)
        if opp is None:
            raise ValueError(f"illegal-left approach {app} has no opposing approach")
        old, new = s.changed.get(opp, (None, None))
        if old == "G" and new != "G":
            self._cycle[app] = {"t_e": s.t, "t_nat": None}
        cyc = self._cycle[app]
        if cyc is not None and cyc["t_nat"] is None:
            for lane in self.info.hold_lanes[app]:
                for vid in s.by_lane.get(lane, ()):
                    v = s.vehicles[vid]
                    if v.vtype not in self.vtypes or self.info.lane_length[lane] - v.pos > FRONT_ROW_M:
                        continue
                    if vid in self._prev_speed and self._prev_speed[vid] < RELEASE_SPEED_MPS <= v.speed:
                        cyc["t_nat"] = s.t
                        self.counters["native_releases"] += 1
        return cyc

    def on_step(self, s: Step) -> list[Intervention]:
        out = self.left_zone(s)
        lag = self.p["release_lag_s"]
        for app, hold in self.info.hold_lanes.items():
            cyc = self._update_cycle(s, app)
            holding = (cyc is not None and cyc["t_nat"] is not None and lag > 0
                       and s.t < cyc["t_nat"] + lag - 1e-9)
            for vid in sorted(v for v, a in self.active.items() if a.data["app"] == app):
                if s.vehicles[vid].lane not in hold:
                    out.append(self.finish(vid, s.t, False, "not_held"))
                elif not holding:
                    out.append(self.finish(vid, s.t, True, ""))
            if cyc is not None and cyc["t_nat"] is not None and not holding:
                self._cycle[app] = None  # this cycle's release is done
            if not holding:
                continue
            for lane in hold:
                for vid in s.by_lane.get(lane, ()):
                    if vid in self.active or (vid, cyc["t_e"]) in self._refused or not self.applies(s, vid):
                        continue
                    out += self._hold(s, vid, lane, app, cyc["t_e"])
        self._prev_speed = {vid: s.vehicles[vid].speed for lane in
                            (ln for h in self.info.hold_lanes.values() for ln in h) for vid in s.by_lane.get(lane, ())}
        return out

    def _hold(self, s: Step, vid: str, lane: str, app: str, cycle_key: float) -> list[Intervention]:
        v = s.vehicles[vid]
        if v.vtype not in self._decel:
            self._decel[v.vtype] = self.b.vehicletype.getDecel(v.vtype)
        if v.speed ** 2 / (2 * self._decel[v.vtype]) > self.info.lane_length[lane] - v.pos:
            self._refused.add((vid, cycle_key))
            return [self.record(vid, ACTION, s.t, False, "cannot_stop")]
        a = self.start(vid, ACTION, s.t, app=app)
        try:
            self.b.vehicle.setSpeed(vid, 0.0)
            a.speed_set = True
        except self.b.TraCIException as e:
            return [self.failed_command(a, s.t, e)]
        return []
