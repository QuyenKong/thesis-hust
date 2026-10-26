"""`wrong_lane_dodge` (PLAN 4.5, S_cheat): on red, a vehicle of the rule's vTypes queued on a lane whose queue is
at least `q_min` m moves to an adjacent lane whose markings do not permit its movement (a wrong lane, the M8
definition: site `approaches[].lane_movements`), to advance there at no more than `v_creep`.

- Queue = `Step.queue_length` (halting vehicles chained by JAM_GAP_M from the stop line). Candidates: rule vehicles on
  that lane with the front within queue + JAM_GAP_M of the stop line; one try per vehicle and red phase.
- Movement = the link from the inbound edge to the vehicle's next route edge; wrong and usable lanes come from
  `thesis_sumo.runtime.wrong_lane.dodge_targets` (shared with the validator, ruling R27).
- Target = an adjacent wrong lane with a shorter queue (shortest first) that has a connection to the vehicle's next
  edge allowing its vClass. A wrong lane without one cannot be driven on for this route (the vehicle would be stuck
  at its end): the try
  is logged `executed False`, reason `no_connection`, and no command is sent. No wrong adjacent lane / none with a
  shorter queue: nothing to dodge into, counted only (`counters`).
- Command: `changeLane(index, duration = remaining red)` + `setSpeed(v_creep)`. The default laneChangeMode (strategic
  changes only "if not in conflict with a TraCI request") lets the request win; no mode is changed.
- `executed` = the vehicle is on the target lane within `LANE_CHANGE_TIMEOUT_S` (and before the red ends);
  `lane_change_not_done` otherwise. The row is written at that outcome; the speed cap stays until the red ends or
  the vehicle crosses the stop line (the vehicle stays "under intervention" until then).
"""

from __future__ import annotations

from thesis_sumo.runtime.rules.base import Intervention, Rule
from thesis_sumo.runtime.state import JAM_GAP_M, Step
from thesis_sumo.runtime.wrong_lane import dodge_targets

LANE_CHANGE_TIMEOUT_S = 5.0


class WrongLaneDodge(Rule):
    rule_type = "wrong_lane_dodge"

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        if not self.info.lane_movements:
            raise ValueError("wrong_lane_dodge needs the site's lane_movements (JunctionInfo need_lane_movements)")
        self._tried: dict[str, tuple[int, set]] = {}
        self._next_edge: dict[str, str] = {}
        self._vclasses: dict[str, str] = {}

    def _next(self, vid: str, edge: str) -> str | None:
        if vid not in self._next_edge:
            route = self.b.vehicle.getRoute(vid)
            i = list(route).index(edge) if edge in route else -1
            self._next_edge[vid] = route[i + 1] if 0 <= i < len(route) - 1 else None
        return self._next_edge[vid]

    def _end(self, vid: str, t: float, reason: str) -> list[Intervention]:
        """End an intervention: a logged (executed) lane change only lifts its speed cap; otherwise it is logged
        as not executed."""
        if self.active[vid].data["logged"]:
            self.release(vid, t)
            return []
        return [self.finish(vid, t, False, reason)]

    def close(self, t: float) -> list[Intervention]:
        return [r for vid in sorted(self.active) for r in self._end(vid, t, "run_ended")]

    def on_step(self, s: Step) -> list[Intervention]:
        out = [r for vid in sorted(self.active) if vid not in s.vehicles for r in self._end(vid, s.t, "left_zone")]
        crossed = {vid for vid, _a, _st in s.crossings}
        for vid in sorted(self.active):
            a = self.active[vid]
            v = s.vehicles[vid]
            ended = s.groups[a.data["app"]] != "r" or vid in crossed
            if not a.data["logged"]:
                if v.lane == a.data["target"]:
                    a.data["logged"] = True
                    out.append(Intervention(a.t0, vid, self.rule_type, a.action, True, "", s.t))
                elif ended or s.t >= a.t0 + LANE_CHANGE_TIMEOUT_S - 1e-9:
                    out.append(self.finish(vid, s.t, False, "lane_change_not_done"))
                    continue
            if ended:
                self.release(vid, s.t)  # speed cap lifted; the row was written at the lane change
        for app, lanes in self.info.lanes.items():
            if s.groups[app] != "r":
                continue
            rid, tried = self._tried.get(app, (None, set()))
            if rid != s.red_id[app]:
                tried = set()
                self._tried[app] = (s.red_id[app], tried)
            queues = {ln: s.queue_length(ln) for ln in lanes}
            for idx, lane in enumerate(lanes):
                q = queues[lane]
                if q < self.p["q_min"]:
                    continue
                for vid in s.by_lane.get(lane, ()):
                    if s.dist(vid) > q + JAM_GAP_M:
                        break
                    if vid in tried or not self.applies(s, vid):
                        continue
                    tried.add(vid)
                    out += self._dodge(s, vid, app, idx, lanes, queues)
        return out

    def _vclass(self, vtype: str) -> str:
        if vtype not in self._vclasses:
            self._vclasses[vtype] = self.b.vehicletype.getVehicleClass(vtype)
        return self._vclasses[vtype]

    def _dodge(self, s: Step, vid: str, app: str, idx: int, lanes: list[str], queues: dict) -> list[Intervention]:
        lane = lanes[idx]
        nxt = self._next(vid, self.info.approach_edge[app])
        if nxt is None:
            self.counters["no_route_movement"] += 1
            return []
        vclass = self._vclass(s.vehicles[vid].vtype)
        wrong, usable = dodge_targets(self.info.lane_links(app), self.info.lane_movements[app], idx, nxt, vclass)
        if not wrong:
            self.counters["no_wrong_lane"] += 1
            return []
        shorter = sorted((queues[lanes[j]], j) for j in wrong if queues[lanes[j]] < queues[lane])
        if not shorter:
            self.counters["no_shorter_wrong_lane"] += 1
            return []
        usable = [j for _q, j in shorter if j in usable]
        if not usable:
            return [self.record(vid, f"change_lane_to_{shorter[0][1]}", s.t, False, "no_connection")]
        j = usable[0]
        a = self.start(vid, f"change_lane_to_{j}", s.t, app=app, target=lanes[j], logged=False)
        try:
            self.b.vehicle.changeLane(vid, j, max(s.time_to_green(app), 1.0))
            self.b.vehicle.setSpeed(vid, self.p["v_creep"])
            a.speed_set = True
        except self.b.TraCIException as e:
            return [self.failed_command(a, s.t, e)]
        return []
