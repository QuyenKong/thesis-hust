"""`uturn_bypass` (Viktor 2026-10-30, field): a vehicle that stands behind a standing U-turner in the same stop-line
lane while its own signal is green does not wait: most motorcycles squeeze past it (beside it in the lane, or into the
adjacent lane), cars rarely do. One rule entry per archetype group, so motorcycles and cars carry their own `p`.

- Blocker: a vehicle on a stop-line lane of an approach, speed < `HALT_SPEED_MPS`, whose route takes a U-turn link
  (direction `t`) from that lane. Any reason for its stop counts (waiting for a gap in the opposing stream on a
  permissive green, or for its own arrow).
- Follower: a vehicle of the rule's vTypes in the same lane, behind the blocker with a gap (blocker rear to follower
  front) of at most `BLOCK_GAP_M`, standing, overlapping the blocker laterally, not a U-turner itself, whose own link
  (`Rule.link_of`) is green (`G`/`g`). Once it has stood so for `t_wait` s, one draw with probability `p` per
  (follower, blocker) pair.
- On success: `squeeze` when the lane has a free lateral gap beside the blocker (among the vehicles whose length
  overlaps the blocker's, the blocker included) that fits the follower with `MIN_GAP_LAT_M` on both sides:
  `changeSublane(target - posLat)` to the nearest such gap (TraCI/Change_Vehicle_State: lateral change "conform to
  safety-constraints as configured by laneChangeMode"); otherwise `change_lane` to an adjacent stop-line lane that has
  a link to the follower's next edge open to its vClass: `changeLane(j, HOLD_S)`, ended with `changeLane(j, 0)` at
  the outcome.
- Weaving: during the intervention the follower's laneChangeMode bits 9-8 are 01 ("avoid immediate collisions when
  following a TraCI request") instead of the default 10 ("respect the speed / brake gaps of others",
  TraCI/Change_Vehicle_State), and its SL2015 `lcPushy` is 1 ("willingness to encroach laterally on other drivers",
  per vehicle through `setParameter("laneChangeModel.lcPushy")`, which keeps the vType), so it may squeeze through
  gaps narrower than its normal lateral safety margin; both are restored at the outcome. The speed mode is not
  changed. `lcPushyGap` is not used: set to 0.1 through setParameter it reads back as -0.1 (SUMO 1.27, not understood).
- `executed` once the follower is ahead of the blocker (smaller distance to the stop line), has crossed the stop line,
  or (change_lane) is in lane j; `not_passed` after `SETTLE_S`; `left_zone` if it leaves the radius first. Vehicle
  widths come from the vTypes (`vehicletype.getWidth`, cached per type).
"""

from __future__ import annotations

from thesis_sumo.runtime.rules.base import Intervention, Rule
from thesis_sumo.runtime.state import HALT_SPEED_MPS, Step

BLOCK_GAP_M = 10.0     # = the queue jam gap (JAM_GAP_M) upper end: a vehicle further back is not held by the blocker
MIN_GAP_LAT_M = 0.1    # lateral clearance of a squeezing rider: Saval et al. 2023 Sec 4 (0.7 m width + 0.1 m spacing)
PUSHY = "laneChangeModel.lcPushy"  # SL2015 "willingness to encroach laterally on other drivers" [0, 1]
SETTLE_S = 6.0
HOLD_S = 6.0
LC_TRACI_BITS = 0b11 << 8          # laneChangeMode bits 9-8
LC_AVOID_COLLISIONS_ONLY = 0b01 << 8


class UturnBypass(Rule):
    rule_type = "uturn_bypass"

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._since: dict[tuple[str, str], float] = {}   # (follower, blocker) -> first time seen held
        self._drawn: set[tuple[str, str]] = set()
        self._width: dict[str, float] = {}
        self._lane_width: dict[str, float] = {}

    def _w(self, vtype: str) -> float:
        if vtype not in self._width:
            self._width[vtype] = self.b.vehicletype.getWidth(vtype)
        return self._width[vtype]

    def _lw(self, lane: str) -> float:
        if lane not in self._lane_width:
            self._lane_width[lane] = self.b.lane.getWidth(lane)
        return self._lane_width[lane]

    def _link(self, s: Step, vid: str):
        lane = s.vehicles[vid].lane
        self.link_of(s, vid)  # fills the route's next edge
        nxt = self._route_next[vid]
        return next((lk for lk in self.info.links.get(lane, ()) if lk.to_edge == nxt), None)

    def on_step(self, s: Step) -> list[Intervention]:
        out = self.left_zone(s)
        for vid in sorted(self.active):
            a, v = self.active[vid], s.vehicles[vid]
            blocker = s.vehicles.get(a.data["blocker"])
            if v.lane.startswith(":") or (blocker is not None and v.lane == blocker.lane
                                          and s.dist(vid) < s.dist(a.data["blocker"])):
                done, reason = True, ""
            elif a.action == "change_lane" and v.lane == a.data["target"]:
                done, reason = True, ""
            elif s.t >= a.t0 + SETTLE_S - 1e-9:
                done, reason = False, "not_passed"
            else:
                continue
            try:
                if a.action == "change_lane":
                    self.b.vehicle.changeLane(vid, a.data["index"], 0)
                if "lc_mode" in a.data:
                    self.b.vehicle.setLaneChangeMode(vid, a.data["lc_mode"])
                if "pushy" in a.data:
                    self.b.vehicle.setParameter(vid, PUSHY, a.data["pushy"])
            except self.b.TraCIException:
                pass
            out.append(self.finish(vid, s.t, done, reason))
        held = set()
        for app, lanes in self.info.lanes.items():
            for lane in lanes:
                ids = s.by_lane.get(lane, ())
                for k, bid in enumerate(ids):
                    b = s.vehicles[bid]
                    if b.speed >= HALT_SPEED_MPS:
                        continue
                    lk = self._link(s, bid)
                    if lk is None or lk.direction != "t":
                        continue
                    b_rear = s.dist(bid) + self.info.vtype_length[b.vtype]
                    bw = self._w(b.vtype)
                    for fid in ids[k + 1:]:
                        f = s.vehicles[fid]
                        if s.dist(fid) - b_rear > BLOCK_GAP_M:
                            break
                        if (f.speed >= HALT_SPEED_MPS or not self.applies(s, fid)
                                or abs(f.lat - b.lat) >= (bw + self._w(f.vtype)) / 2):
                            continue
                        flk = self._link(s, fid)
                        if flk is None or flk.direction == "t":
                            continue
                        link = self.link_of(s, fid)
                        if link is None or s.signal(app, link) != "G":
                            continue
                        key = (fid, bid)
                        held.add(key)
                        t0 = self._since.setdefault(key, s.t)
                        if key in self._drawn or s.t - t0 < self.p["t_wait"] - 1e-9:
                            continue
                        self._drawn.add(key)
                        if self.rng.random() >= self.p["p"]:
                            continue
                        rec = self._bypass(s, app, lane, fid, bid, bw)
                        if rec is not None:
                            out.append(rec)
        self._since = {k: t for k, t in self._since.items() if k in held}
        return out

    def _free_lat(self, s: Step, lane: str, fid: str, bid: str) -> float | None:
        """Centre of the free lateral gap of `lane` nearest to the follower that fits it with `MIN_GAP_LAT_M` on both
        sides, beside the blocker (the vehicles whose length overlaps the blocker's, the blocker included); None
        when there is none."""
        f = s.vehicles[fid]
        half, fw = self._lw(lane) / 2, self._w(f.vtype)
        lo_d, hi_d = s.dist(bid), s.dist(bid) + self.info.vtype_length[s.vehicles[bid].vtype]
        spans = sorted((v.lat - self._w(v.vtype) / 2 - MIN_GAP_LAT_M, v.lat + self._w(v.vtype) / 2 + MIN_GAP_LAT_M)
                       for vid, v in ((i, s.vehicles[i]) for i in s.by_lane.get(lane, ()) if i != fid)
                       if s.dist(vid) <= hi_d and s.dist(vid) + self.info.vtype_length[v.vtype] >= lo_d)
        gaps, edge = [], -half
        for a, b in spans:
            if a - edge >= fw:
                gaps.append((edge, a))
            edge = max(edge, b)
        if half - edge >= fw:
            gaps.append((edge, half))
        if not gaps:
            return None
        centre = [min(max(f.lat, a + fw / 2), b - fw / 2) for a, b in gaps]
        return min(centre, key=lambda c: abs(c - f.lat))

    def _weave(self, a, fid: str) -> None:
        a.data["lc_mode"] = mode = self.b.vehicle.getLaneChangeMode(fid)
        a.data["pushy"] = self.b.vehicle.getParameter(fid, PUSHY)
        self.b.vehicle.setLaneChangeMode(fid, (mode & ~LC_TRACI_BITS) | LC_AVOID_COLLISIONS_ONLY)
        self.b.vehicle.setParameter(fid, PUSHY, "1")

    def _bypass(self, s: Step, app: str, lane: str, fid: str, bid: str, bw: float) -> Intervention | None:
        f = s.vehicles[fid]
        target = self._free_lat(s, lane, fid, bid)
        if target is not None:
            a = self.start(fid, "squeeze", s.t, blocker=bid, detail=f"approach={app};blocker={bid}")
            try:
                self._weave(a, fid)
                self.b.vehicle.changeSublane(fid, target - f.lat)
            except self.b.TraCIException as e:
                return self.failed_command(a, s.t, e)
            return None
        lanes = self.info.lanes[app]
        i, nxt = lanes.index(lane), self._route_next[fid]
        vclass = self.b.vehicletype.getVehicleClass(f.vtype)
        for j in sorted((i - 1, i + 1), key=lambda j: s.queue_length(lanes[j]) if 0 <= j < len(lanes) else 0.0):
            if not 0 <= j < len(lanes):
                continue
            if any(lk.to_edge == nxt and (lk.allowed is None or vclass in lk.allowed) for lk in self.info.links[lanes[j]]):
                a = self.start(fid, "change_lane", s.t, blocker=bid, target=lanes[j], index=j,
                               detail=f"approach={app};blocker={bid}")
                try:
                    self._weave(a, fid)
                    self.b.vehicle.changeLane(fid, j, HOLD_S)
                except self.b.TraCIException as e:
                    return self.failed_command(a, s.t, e)
                return None
        return self.record(fid, "change_lane", s.t, False, "no_room_no_lane", f"approach={app};blocker={bid}")
