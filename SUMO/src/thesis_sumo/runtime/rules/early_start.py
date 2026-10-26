"""`early_start` (PLAN 4.5): in the last `t_before_green` s of red, a halting front-row vehicle of the rule's
vTypes creeps over the stop line with probability `p` at no more than `v_max`.

- Remaining red = time until the approach group's next green under the running program
  (`JunctionInfo.time_to_green`: next switch of the TLS + durations of the following phases).
- Front row = front within `state.FRONT_ROW_M` of the stop line; halting = speed < `state.HALT_SPEED_MPS`.
- `p` is drawn once per vehicle and red phase (the first step it is a halting front-row vehicle inside the window).
- Command: speedMode bit4 cleared (the only bit that lets a vehicle pass a red light, see `base`; right of way
  towards foes, safe speed, accel/decel limits stay) + `setSpeed(v_max)`. Both are undone at the outcome.
- `executed` = the vehicle crossed the stop line before its approach left red; `red_ended_before_crossing` when
  SUMO kept it behind the line (e.g. it yields to crossing foes) until green.
"""

from __future__ import annotations

from thesis_sumo.runtime.rules.base import Intervention, Rule, settle_red_passes, start_red_pass
from thesis_sumo.runtime.state import HALT_SPEED_MPS, Step


class EarlyStart(Rule):
    rule_type = "early_start"

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._drawn: dict[str, tuple[int, set]] = {}

    def on_step(self, s: Step) -> list[Intervention]:
        out = settle_red_passes(self, s)
        for app in self.info.lanes:
            if s.groups[app] != "r" or not 0.0 < s.time_to_green(app) <= self.p["t_before_green"]:
                continue
            rid, drawn = self._drawn.get(app, (None, set()))
            if rid != s.red_id[app]:
                drawn = set()
                self._drawn[app] = (s.red_id[app], drawn)
            for vid in s.front_row(app):
                if vid in drawn or not self.applies(s, vid) or s.vehicles[vid].speed >= HALT_SPEED_MPS:
                    continue
                drawn.add(vid)
                self.counters["draws"] += 1
                if self.rng.random() < self.p["p"]:
                    rec = start_red_pass(self, s, vid, app, "creep_over_stop_line", v_max=self.p["v_max"])
                    if rec is not None:
                        out.append(rec)
        return out
