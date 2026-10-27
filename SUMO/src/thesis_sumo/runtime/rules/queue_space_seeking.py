"""`queue_space_seeking` (PLAN 4.5; behaviours 5 S_cheat, 6 right-lane blocking, 7 sidewalk; `opposite` deferred, R38).

Trigger and draw
- A vehicle of the rule's vTypes is a candidate while it is on its approach upstream of the bollard edge (on an
  approach without segments: on the inbound edge) and not on a sidewalk. Its movement = the link from the stop-line
  edge to its next route edge; its queue = the longest queue (`Step.queue_length`, chained across the segments) of
  the lanes whose markings (site `lane_movements`) permit that movement; its wait = time halted on the approach
  inside the controller radius.
- Green check (PLAN 4.5 "đèn sắp xanh", Viktor 2026-10-27; `t_g_s` > 0): when its approach's next green is at most
  `t_g_s` away, each halted candidate not yet drawn checks once per red whether it expects to clear the stop line in
  that green: needed = (vehicles ahead of it on the approach's signalled lanes) x (the approach's discharge headway in
  its previous green, measured live: (last - first) / (n - 1) over the stop-line crossings from the signalled lanes
  while green), estimate = needed x exp(N(0, `est_noise`)) (multiplicative lognormal error, median unbiased), against
  the duration of the coming green from the running TLS program. Signalled lanes = stop-line lanes with an open link
  whose state changes between phases (not the continuous right turn, not the closed lane-0 straight). Estimate >
  green: the vehicle draws (trigger `green`); no headway yet (first green): no check. Viktor framed it around
  wrong-way riding, which stays deferred (R38): the draw is over the options that exist (wrong_lane, right_lane,
  sidewalk).
- The first step where queue >= `q` (or wait >= `t_w`, if given, or the green check fails), the vehicle draws once
  (one `rng.random()`):
  option o with probability `option_probabilities` = p_o of the options that exist for it, the p_* of the absent ones
  redistributed proportionally (PLAN 4.5 "dồn hành vi"); none with the rest. No option with p > 0 exists: no seeking.
  An option exists (static, from the net, as the validator sees it):
  - `wrong_lane`: some lane permitting the movement has an adjacent lane whose markings do not, with a connection to
    the next edge allowing the vClass (`wrong_lane.dodge_targets`, R27);
  - `right_lane`: movement straight, lane 0's markings do not permit it, the bollard edge forbids lane 0 -> 1 for the
    vClass (`lane.getChangePermissions`) and the upstream lane 0 allows it;
  - `sidewalk`: the approach has a sidewalk lane that allows the vClass and links to the next edge.

Execution (one intervention per vehicle; no speed or lane-change mode is changed: the default lane-change mode 1621
lets a TraCI request win; Phase 3A: no lock is needed, violators do not enter lane 0 or the sidewalk by themselves)
- `right_lane` (Phase 3A recipe): `changeLane(0, HOLD_S)`; `executed` once the vehicle is in lane 0 (speed capped at
  `v_creep` from then); the request ends with `changeLane(<lane>, 0)` `merge_zone_m` before the bollard edge (or when
  the vehicle reaches it) and SL2015 merges it back (never a request to lane 1: gridlock in 3A);
  `lane_change_not_done` if it never got to lane 0. Not sent (`past_merge_zone`) within `merge_zone_m`. The
  intervention window (R10/R30) closes when the vehicle is back in a through lane (lane index >= 1) after the release,
  not at the junction exit: the rule's effect is the ride in lane 0 and the merge; a later collision in the junction
  is the ordinary straight movement. (Sidewalk and wrong_lane keep the R30 window up to the junction exit: riders
  enter the junction from the sidewalk links, with priority, or from the wrong lane, so the junction traversal is part
  of the intervention.)
- `sidewalk` (Phase 3B, topology c), only while on the segment upstream of the sidewalk start (else
  `past_sidewalk_start`): `changeLane(0, HOLD_S)`; once the rider is in lane 0 of that segment it is centred
  (`changeSublane`) until its body fits the sidewalk width (|posLat| <= (sidewalk width - vehicle width) / 2), then
  `setRoute(<up>, <sidewalk>, <next edge>, ...)` and the hold is ended at once (`changeLane(0, 0)`). Rerouting a rider that is not yet in lane 0 can leave it stopped at
  the end of its lane, blocking it, when the queue fills lane 1 (checked on the toy net of tests/test_runtime.py); a
  rider that leaves the segment without reaching lane 0 keeps its road route (`lane_change_not_done`). `executed` once
  on the sidewalk lane (speed capped at `v_creep`); the cap is lifted at its stop-line crossing.
- `wrong_lane`: `changeLane(j, HOLD_S)` to the usable wrong adjacent lane with the shortest queue (`no_wrong_lane_here`
  if the vehicle's lane has none); `executed` once on lane j within `LANE_CHANGE_TIMEOUT_S` (speed capped at
  `v_creep`), `lane_change_not_done` otherwise; the request and cap end at the stop-line crossing.

Log (`interventions.csv`): action = the option (the `space` of PLAN 5.1 space_seeking_events), detail =
`approach=..;trigger=queue|wait|green;queue_m=..;wait_s=..` (+ `;needed_s=..;est_s=..;green_s=..` for green) at the
draw; one row per executed / not executed decision.
"""

from __future__ import annotations

import math

from thesis_sumo.runtime.rules.base import Intervention, Rule
from thesis_sumo.runtime.state import HALT_SPEED_MPS, Step, allowed_classes
from thesis_sumo.runtime.wrong_lane import MOVEMENT_OF_DIR, dodge_targets

OPTIONS = ("wrong_lane", "right_lane", "sidewalk")
HOLD_S = 600.0  # changeLane duration of the held requests; always ended explicitly (Phase 3A)
LANE_CHANGE_TIMEOUT_S = 5.0


def option_probabilities(p: dict[str, float], available) -> dict[str, float]:
    """PLAN 4.5: the total seeking probability sum(p) is kept and shared among the available options in proportion
    to their p; all zero when no available option has p > 0."""
    total = sum(p[o] for o in OPTIONS)
    kept = sum(p[o] for o in OPTIONS if o in available)
    return {o: p[o] * total / kept if o in available and kept > 0 else 0.0 for o in OPTIONS}


class QueueSpaceSeeking(Rule):
    rule_type = "queue_space_seeking"

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        if not self.info.lane_movements:
            raise ValueError("queue_space_seeking needs the site's lane_movements (JunctionInfo need_lane_movements)")
        self.probs = {o: self.p[f"p_{o}"] for o in OPTIONS}
        if sum(self.probs.values()) > 1 + 1e-9:
            raise ValueError(f"queue_space_seeking: p_wrong_lane + p_right_lane + p_sidewalk = "
                             f"{sum(self.probs.values())} > 1")
        self.decided: set[str] = set()
        self.wait: dict[str, float] = {}
        self._t: float | None = None
        self._next: dict[str, str | None] = {}
        self._vclass: dict[str, str] = {}
        self._avail: dict[tuple, frozenset] = {}
        self.lane_index = {ln: k for chains in self.info.chains.values() for k, ch in enumerate(chains) for ln in ch}
        self.sidewalk_lanes = frozenset(self.info.sidewalk.values())
        # green check: signalled stop-line lanes, live discharge headway, one check per vehicle and red
        self.signalled: dict[str, set[int]] = {a: set() for a in self.info.lanes}
        if self.p["t_g_s"] > 0:
            for i, conns in enumerate(self.b.trafficlight.getControlledLinks(self.info.tls_id)):
                for in_lane, out_lane, _via in conns:
                    app = self.info.lane_approach.get(in_lane)
                    if app is None or in_lane not in self.info.lanes[app]:
                        continue
                    (lk,) = [x for x in self.info.links[in_lane] if x.to_lane == out_lane]
                    if lk.allowed != frozenset() and len({st[i] for _, st in self.info.phases}) > 1:
                        self.signalled[app].add(self.info.lanes[app].index(in_lane))
        self.headway: dict[str, float] = {}
        self._green_cross: dict[str, list[float]] = {a: [] for a in self.info.lanes}
        self._stop_lane: dict[str, str] = {}
        self._checked: dict[str, int] = {}
        self._merging: set[str] = set()
        self._sw_width: dict[str, float] = {}
        self._veh_width: dict[str, float] = {}  # released right_lane vehicles whose window closes once back in lane >= 1

    # ------------------------------------------------------------ helpers
    def _vc(self, vtype: str) -> str:
        if vtype not in self._vclass:
            self._vclass[vtype] = self.b.vehicletype.getVehicleClass(vtype)
        return self._vclass[vtype]

    def _next_edge(self, vid: str, app: str) -> str | None:
        if vid not in self._next:
            route = list(self.b.vehicle.getRoute(vid))
            edge = self.info.approach_edge[app]
            i = route.index(edge) if edge in route else -1
            self._next[vid] = route[i + 1] if 0 <= i < len(route) - 1 else None
        return self._next[vid]

    def _movement(self, app: str, nxt: str) -> str | None:
        return next((MOVEMENT_OF_DIR[lk.direction] for ln in self.info.lanes[app] for lk in self.info.links[ln]
                     if lk.to_edge == nxt), None)

    def _in_zone(self, lane: str, app: str) -> bool:
        return lane not in self.sidewalk_lanes and (len(self.info.segments[app]) == 1
                                                    or lane not in self.info.lanes[app])

    def available(self, app: str, vclass: str, nxt: str, mv: str) -> frozenset:
        key = (app, vclass, nxt)
        if key not in self._avail:
            info, marks, out = self.info, self.info.lane_movements[app], set()
            links = info.lane_links(app)
            if any(mv in marks[i] and dodge_targets(links, marks, i, nxt, vclass)[1] for i in range(len(marks))):
                out.add("wrong_lane")
            lane0 = info.lanes[app][0]
            if (mv == "s" and mv not in marks[0] and len(info.segments[app]) > 1
                    and vclass not in self.b.lane.getChangePermissions(lane0, 1)
                    and _allows(allowed_classes(self.b, info.chains[app][0][-1]), vclass)):
                out.add("right_lane")
            sw = info.sidewalk.get(app)
            if sw and _allows(allowed_classes(self.b, sw), vclass) and any(lk.to_edge == nxt for lk in info.links[sw]):
                out.add("sidewalk")
            self._avail[key] = frozenset(out)
        return self._avail[key]

    def _cancel(self, vid: str, lane: str) -> None:
        """End a held lane request (duration 0 on the vehicle's current lane index)."""
        try:
            self.b.vehicle.changeLane(vid, self.lane_index.get(lane, 0), 0.0)
        except self.b.TraCIException:
            pass

    def _end(self, vid: str, t: float, reason: str, lane: str | None = None) -> list[Intervention]:
        """End an intervention: a logged (executed) one only lifts its overrides; otherwise logged as not executed."""
        a = self.active[vid]
        if a.data["opt"] == "right_lane":
            self._merging.add(vid)
        if a.data["opt"] != "sidewalk" and lane is not None:
            self._cancel(vid, lane)
        if a.data["logged"]:
            self.release(vid, t)
            return []
        return [self.finish(vid, t, False, reason)]

    def _executed(self, vid: str, t: float) -> Intervention:
        a = self.active[vid]
        a.data["logged"] = True
        try:
            self.b.vehicle.setSpeed(vid, self.p["v_creep"])
            a.speed_set = True
        except self.b.TraCIException:
            pass
        return Intervention(a.t0, vid, self.rule_type, a.action, True, "", t, a.data["detail"])

    # ------------------------------------------------------------ hooks
    def close(self, t: float) -> list[Intervention]:
        return [r for vid in sorted(self.active) for r in self._end(vid, t, "run_ended")]

    def on_step(self, s: Step) -> list[Intervention]:
        dt = 0.0 if self._t is None else s.t - self._t
        self._t = s.t
        out = self._progress(s)
        self._close_merged(s)
        if self.p["t_g_s"] > 0:
            self._measure_headways(s)
        wait = {}
        for vid in sorted(s.vehicles):
            v = s.vehicles[vid]
            app = self.info.approach_lanes.get(v.lane)
            if app is None or v.vtype not in self.vtypes:
                continue
            wait[vid] = self.wait.get(vid, 0.0) + (dt if v.speed < HALT_SPEED_MPS else 0.0)
            if vid in self.decided or not self._in_zone(v.lane, app) or not self.applies(s, vid):
                continue
            nxt = self._next_edge(vid, app)
            mv = None if nxt is None else self._movement(app, nxt)
            if mv is None:
                self.decided.add(vid)
                self.counters["no_route_movement"] += 1
                continue
            marks = self.info.lane_movements[app]
            q = max((s.queue_length(self.info.chains[app][k]) for k in range(len(marks)) if mv in marks[k]),
                    default=0.0)
            t_w = self.p.get("t_w")
            extra = ""
            if q >= self.p["q"]:
                trigger = "queue"
            elif t_w is not None and wait[vid] >= t_w:
                trigger = "wait"
            else:
                extra = self._green_check(s, vid, app)
                if not extra:
                    continue
                trigger = "green"
            self.decided.add(vid)
            probs = option_probabilities(self.probs, self.available(app, self._vc(v.vtype), nxt, mv))
            u = self.rng.random()
            self.counters["draws"] += 1
            choice, acc = None, 0.0
            for o in OPTIONS:
                acc += probs[o]
                if u < acc:
                    choice = o
                    break
            if choice is None:
                self.counters["no_seek" if any(probs.values()) or not any(self.probs.values()) else "no_option"] += 1
                continue
            self.counters[f"drawn_{choice}"] += 1
            detail = f"approach={app};trigger={trigger};queue_m={q:.1f};wait_s={wait[vid]:.1f}{extra}"
            out += getattr(self, f"_start_{choice}")(s, vid, app, nxt, detail)
        self.wait = wait
        return out

    # ------------------------------------------------------------ green check
    def _measure_headways(self, s: Step) -> None:
        for vid, app, st in s.crossings:
            lane = self._stop_lane.get(vid)
            if st == "G" and lane is not None and self.info.lanes[app].index(lane) in self.signalled[app]:
                self._green_cross[app].append(s.t)
        for app, (prev, _new) in s.changed.items():
            if prev == "G":  # the green ended: its headway is the estimate for the next one
                ts = self._green_cross[app]
                if len(ts) >= 2:
                    self.headway[app] = (ts[-1] - ts[0]) / (len(ts) - 1)
                self._green_cross[app] = []
        self._stop_lane = {vid: v.lane for vid, v in s.vehicles.items()
                           if v.lane in self.info.lane_approach and v.lane not in self.sidewalk_lanes}

    def _coming_green_s(self, s: Step, app: str) -> float:
        phases, n = self.info.phases, len(self.info.phases)
        k = next(j for j in range(s.phase + 1, s.phase + n + 1)
                 if self.info.group_state(phases[j % n][1], app) == "G")
        dur = 0.0
        for j in range(k, k + n):
            if self.info.group_state(phases[j % n][1], app) != "G":
                break
            dur += phases[j % n][0]
        return dur

    def _green_check(self, s: Step, vid: str, app: str) -> str:
        """'' when the check does not fire, else the detail suffix (the vehicle expects to miss the coming green)."""
        ttg = s.time_to_green(app)
        if not (self.p["t_g_s"] > 0 and 0 < ttg <= self.p["t_g_s"]) or s.vehicles[vid].speed >= HALT_SPEED_MPS \
                or self._checked.get(vid) == s.red_id[app]:
            return ""
        self._checked[vid] = s.red_id[app]
        h = self.headway.get(app)
        if h is None:
            self.counters["green_check_no_headway"] += 1
            return ""
        d = s.dist(vid)
        ahead = sum(1 for o, v in s.vehicles.items() if o != vid and self.info.approach_lanes.get(v.lane) == app
                    and v.lane not in self.sidewalk_lanes and self.lane_index.get(v.lane) in self.signalled[app]
                    and 0 <= s.dist(o) < d)
        needed = ahead * h
        est = needed * math.exp(self.rng.gauss(0.0, self.p["est_noise"])) if self.p["est_noise"] > 0 else needed
        green = self._coming_green_s(s, app)
        if est <= green:
            self.counters["green_check_pass"] += 1
            return ""
        return f";needed_s={needed:.1f};est_s={est:.1f};green_s={green:.1f}"

    # ------------------------------------------------------------ options
    def _start_right_lane(self, s: Step, vid: str, app: str, nxt: str, detail: str) -> list[Intervention]:
        if s.dist(vid) - self.info.lane_length[self.info.lanes[app][0]] <= self.p["merge_zone_m"]:
            return [self.record(vid, "right_lane", s.t, False, "past_merge_zone", detail)]
        a = self.start(vid, "right_lane", s.t, app=app, opt="right_lane", logged=False, detail=detail)
        try:
            self.b.vehicle.changeLane(vid, 0, HOLD_S)
        except self.b.TraCIException as e:
            return [self.failed_command(a, s.t, e)]
        return []

    def _start_sidewalk(self, s: Step, vid: str, app: str, nxt: str, detail: str) -> list[Intervention]:
        up = self.info.segments[app][-1]
        if s.vehicles[vid].lane.rsplit("_", 1)[0] != up:
            return [self.record(vid, "sidewalk", s.t, False, "past_sidewalk_start", detail)]
        a = self.start(vid, "sidewalk", s.t, app=app, opt="sidewalk", logged=False, detail=detail, nxt=nxt,
                       routed=False)
        try:
            self.b.vehicle.changeLane(vid, 0, HOLD_S)
        except self.b.TraCIException as e:
            return [self.failed_command(a, s.t, e)]
        return self._reroute(a, s.vehicles[vid], s.t)

    def _reroute(self, a, v, t: float) -> list[Intervention]:
        """Sidewalk: once in lane 0 upstream of the sidewalk start and laterally inside the sidewalk's width, send the
        rider over the sidewalk. A rider entering the (narrower) connector at the edge of the 3.5 m lane overlaps the
        neighbouring road connector and waits behind its queue (proxy run: 300 s at posLat 1.5 on a 3.0 m connector),
        so it is first centred with changeSublane."""
        app = a.data["app"]
        up = self.info.segments[app][-1]
        lane = v.lane
        if a.data["routed"] or lane != f"{up}_0":
            return []
        sw = self.info.sidewalk[app]
        if sw not in self._sw_width:
            self._sw_width[sw] = self.b.lane.getWidth(sw)
        if v.vtype not in self._veh_width:
            self._veh_width[v.vtype] = self.b.vehicletype.getWidth(v.vtype)
        if abs(v.lat) > (self._sw_width[sw] - self._veh_width[v.vtype]) / 2:
            try:
                self.b.vehicle.changeSublane(a.vid, -v.lat)
            except self.b.TraCIException as e:
                return [self.failed_command(a, t, e)]
            return []
        route = list(self.b.vehicle.getRoute(a.vid))
        try:
            self.b.vehicle.setRoute(a.vid, [up, self.info.sidewalk[app].rsplit("_", 1)[0]]
                                    + route[route.index(a.data["nxt"]):])
        except self.b.TraCIException as e:
            return [self.failed_command(a, t, e)]
        a.data["routed"] = True
        # end the lane-0 hold now: the route keeps the rider in lane 0, while a held request would keep its lateral
        # position in the 3.5 m lane on the narrower sidewalk connector until HOLD_S expires (blocking lane 0)
        self._cancel(a.vid, lane)
        return []

    def _start_wrong_lane(self, s: Step, vid: str, app: str, nxt: str, detail: str) -> list[Intervention]:
        i = self.lane_index[s.vehicles[vid].lane]
        targets = dodge_targets(self.info.lane_links(app), self.info.lane_movements[app], i, nxt,
                                self._vc(s.vehicles[vid].vtype))[1]
        if not targets:
            return [self.record(vid, "wrong_lane", s.t, False, "no_wrong_lane_here", detail)]
        j = min(targets, key=lambda k: (s.queue_length(self.info.chains[app][k]), k))
        a = self.start(vid, "wrong_lane", s.t, app=app, opt="wrong_lane", logged=False, detail=detail, target=j)
        try:
            self.b.vehicle.changeLane(vid, j, HOLD_S)
        except self.b.TraCIException as e:
            return [self.failed_command(a, s.t, e)]
        return []

    def _close_merged(self, s: Step) -> None:
        for vid in sorted(self._merging):
            v = s.vehicles.get(vid)
            if v is None or self.info.approach_lanes.get(v.lane) is None:  # gone, or past: the R30 rule closes it
                self._merging.discard(vid)
            elif self.lane_index.get(v.lane, 0) >= 1:
                self.cmd.close_window(vid, s.t)
                self._merging.discard(vid)

    def _progress(self, s: Step) -> list[Intervention]:
        out = [r for vid in sorted(self.active) if vid not in s.vehicles for r in self._end(vid, s.t, "left_zone")]
        crossed = {vid for vid, _a, _st in s.crossings}
        for vid in sorted(self.active):
            a, v = self.active[vid], s.vehicles[vid]
            app, opt, lane = a.data["app"], a.data["opt"], v.lane
            on_app = self.info.approach_lanes.get(lane) == app
            if opt == "right_lane":
                if not a.data["logged"] and on_app and self.lane_index.get(lane) == 0 and lane not in \
                        self.info.lanes[app]:
                    out.append(self._executed(vid, s.t))
                d = s.dist(vid) - self.info.lane_length[self.info.lanes[app][0]]
                if not on_app or lane in self.info.lanes[app] or d <= self.p["merge_zone_m"]:
                    out += self._end(vid, s.t, "lane_change_not_done", lane)
            elif opt == "sidewalk":
                up = self.info.segments[app][-1]
                if not a.data["logged"] and lane == self.info.sidewalk[app]:
                    self._cancel(vid, lane)
                    out.append(self._executed(vid, s.t))
                elif a.data["logged"]:
                    if vid in crossed or lane != self.info.sidewalk[app]:
                        out += self._end(vid, s.t, "")
                elif lane.rsplit("_", 1)[0] == up:
                    out += self._reroute(a, v, s.t)
                elif not lane.startswith(":"):  # on a normal lane past the upstream segment, not the sidewalk
                    self._cancel(vid, lane)
                    out += self._end(vid, s.t, "not_on_sidewalk" if a.data["routed"] else "lane_change_not_done")
            else:  # wrong_lane
                if not a.data["logged"] and on_app and self.lane_index.get(lane) == a.data["target"]:
                    out.append(self._executed(vid, s.t))
                if vid in crossed or not on_app:
                    out += self._end(vid, s.t, "lane_change_not_done", lane)
                elif not a.data["logged"] and s.t >= a.t0 + LANE_CHANGE_TIMEOUT_S - 1e-9:
                    out += self._end(vid, s.t, "lane_change_not_done", lane)
        return out


def _allows(allowed: frozenset[str] | None, vclass: str) -> bool:
    return allowed is None or vclass in allowed
