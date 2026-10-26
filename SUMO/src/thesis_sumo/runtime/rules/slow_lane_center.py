"""`slow_lane_center` (PLAN 4.5, I_slow, optional): slow riders of the rule's vTypes keep `lat_offset` m from their
lane centre (posLat, positive to the left; 0 = centre) on the inbound lanes of the junction.

- When |posLat - lat_offset| > `TOLERANCE_M` the rule sends `changeSublane(lat_offset - posLat)` ("forces a lateral
  change by the given amount ... but conform to safety-constraints as configured by laneChangeMode",
  TraCI/Change_Vehicle_State); no mode is changed. The vType's latAlignment is not touched (a type setter would give
  the vehicle a `typeid@vehid` copy, see `base`).
- `executed` = |posLat - lat_offset| <= `TOLERANCE_M` within `SETTLE_S` while on the same lane;
  `lateral_target_not_reached` otherwise, `lane_changed` if it left the lane first. After an outcome the vehicle is
  left alone for `COOLDOWN_S` (no command every step).
"""

from __future__ import annotations

from thesis_sumo.runtime.rules.base import Intervention, Rule
from thesis_sumo.runtime.state import Step

TOLERANCE_M = 0.2   # half the experiment's lateral resolution (0.4 m)
SETTLE_S = 3.0
COOLDOWN_S = 2.0


class SlowLaneCenter(Rule):
    rule_type = "slow_lane_center"

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._quiet_until: dict[str, float] = {}

    def on_step(self, s: Step) -> list[Intervention]:
        out = self.left_zone(s)
        target = self.p["lat_offset"]
        for vid in sorted(self.active):
            a, v = self.active[vid], s.vehicles[vid]
            if v.lane != a.data["lane"]:
                out.append(self.finish(vid, s.t, False, "lane_changed"))
            elif abs(v.lat - target) <= TOLERANCE_M:
                out.append(self.finish(vid, s.t, True, ""))
            elif s.t >= a.t0 + SETTLE_S - 1e-9:
                out.append(self.finish(vid, s.t, False, "lateral_target_not_reached"))
            else:
                continue
            self._quiet_until[vid] = s.t + COOLDOWN_S
        for lanes in self.info.lanes.values():
            for lane in lanes:
                for vid in s.by_lane.get(lane, ()):
                    v = s.vehicles[vid]
                    if (abs(v.lat - target) <= TOLERANCE_M or s.t < self._quiet_until.get(vid, -1.0)
                            or not self.applies(s, vid)):
                        continue
                    a = self.start(vid, "center_in_lane", s.t, lane=lane)
                    try:
                        self.b.vehicle.changeSublane(vid, target - v.lat)
                    except self.b.TraCIException as e:
                        out.append(self.failed_command(a, s.t, e))
        return out
