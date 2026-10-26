"""`swarm_red_running` (PLAN 4.5): a vehicle of the rule's vTypes that reaches the stop line on red runs it with
probability p = min(p_max, p0 + k * n), n = vehicles (any type) that crossed the same approach's stop line on red
within the last `dt` s (window (t - dt, t]).

- Arrival at the stop line = the vehicle is in the front row (front within `state.FRONT_ROW_M` of the stop line)
  while its approach group is red (yellow is SUMO's own jmDriveAfterYellowTime business).
- The decision is drawn once per vehicle and red phase, at its first front-row step on red (Task 7 note: drawing
  every step would make p a per-step hazard and overshoot the red-running share).
- A red violation (for n) = a stop-line crossing (inbound lane -> internal lane) while the group is red, whoever
  caused it (this rule, early_start, SUMO's jmDriveAfterRedTime).
- Command and `executed`: as `early_start` (speedMode bit4 cleared, no speed cap; undone at the outcome).
"""

from __future__ import annotations

from collections import deque

from thesis_sumo.runtime.rules.base import Intervention, Rule, settle_red_passes, start_red_pass
from thesis_sumo.runtime.state import Step


class SwarmRedRunning(Rule):
    rule_type = "swarm_red_running"

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._violations = {app: deque() for app in self.info.lanes}
        self._drawn: dict[str, tuple[int, set]] = {}
        self.draw_log: list[tuple[float, str, int, float, bool]] = []  # (t, vehicle, n, p, runs) per draw

    def n_recent(self, app: str, t: float) -> int:
        q = self._violations[app]
        while q and q[0] <= t - self.p["dt"]:
            q.popleft()
        return len(q)

    def on_step(self, s: Step) -> list[Intervention]:
        for _vid, app, state in s.crossings:
            if state == "r":
                self._violations[app].append(s.t)
        out = settle_red_passes(self, s)
        for app in self.info.lanes:
            n = self.n_recent(app, s.t)
            if s.groups[app] != "r":
                continue
            rid, drawn = self._drawn.get(app, (None, set()))
            if rid != s.red_id[app]:
                drawn = set()
                self._drawn[app] = (s.red_id[app], drawn)
            for vid in s.front_row(app):
                if vid in drawn or not self.applies(s, vid):
                    continue
                drawn.add(vid)
                p = min(self.p["p_max"], self.p["p0"] + self.p["k"] * n)
                self.counters["draws"] += 1
                runs = self.rng.random() < p
                self.draw_log.append((s.t, vid, n, p, runs))
                if runs:
                    self.counters["decided_run"] += 1
                    rec = start_red_pass(self, s, vid, app, "run_red")
                    if rec is not None:
                        out.append(rec)
        return out
