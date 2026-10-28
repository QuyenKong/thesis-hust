"""`early_start` (PLAN 4.5): in the last `t_before_green` s of red, a halting front-row vehicle of the rule's
vTypes creeps over the stop line with probability `p` at no more than `v_max`.

- Red and remaining red are those of the vehicle's own signal, the TLS link it takes (`Rule.link_of`; the approach
  group if its lane has no link to its next edge): time until that link's next green under the running program
  (`JunctionInfo.time_to_green`: next switch of the TLS + durations of the following phases). A LVL left-turner
  waits for the left arrow, not for the LVL straight green (protected left, 2026-10-28).
- Front row = front within `state.FRONT_ROW_M` of the stop line; halting = speed < `state.HALT_SPEED_MPS`.
- `p` is drawn once per vehicle and red phase of its signal (the first step it is a halting front-row vehicle inside
  the window).
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
        self._drawn: dict[tuple[str, int | None], tuple[int, set]] = {}  # (approach, own link) -> (red id, drawn)

    def on_step(self, s: Step) -> list[Intervention]:
        out = settle_red_passes(self, s)
        for app in self.info.lanes:
            for vid in s.front_row(app):
                if not self.applies(s, vid) or s.vehicles[vid].speed >= HALT_SPEED_MPS:
                    continue
                link = self.link_of(s, vid)
                if s.signal(app, link) != "r" or not 0.0 < s.time_to_green(app, link) <= self.p["t_before_green"]:
                    continue
                rid, drawn = self._drawn.get((app, link), (None, set()))
                if rid != s.red_id_of(app, link):
                    drawn = set()
                    self._drawn[(app, link)] = (s.red_id_of(app, link), drawn)
                if vid in drawn:
                    continue
                drawn.add(vid)
                self.counters["draws"] += 1
                if self.rng.random() < self.p["p"]:
                    rec = start_red_pass(self, s, vid, app, "creep_over_stop_line", v_max=self.p["v_max"], link=link)
                    if rec is not None:
                        out.append(rec)
        return out
