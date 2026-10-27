"""What the TraCI rules see (PLAN 4.5): the target junction, read once at start, and one snapshot per step.

`JunctionInfo.build(backend, site)` reads the junction through TraCI and the site file only (no net file), so the
controller works on any net whose site file names the inbound edges (`approaches[].edge`):

- target traffic light = the one controlling the inbound edges; junction = `edge.getToJunction` of them;
- approach group links = the TLS link indices of an approach's straight (`s`) links, as
  `thesis_sumo.sim.outputs.junction_geometry` (the signal state of an approach is the state of these links,
  `schema_observed.normalise_state`);
- stop line of an inbound lane = its end; `dist` = lane length - lanePosition (front bumper);
- segments of an approach (site patches, `thesis_sumo.net.apply_patches`): the inbound edge plus its straight
  upstream continuation (`<edge>.mid`, `<edge>.up`), found by walking `junction.getIncomingEdges` upstream; `chains`
  = per lane index the lanes from the stop line upstream incl. the short internal lanes of the split nodes, each with
  `lane_offset` (distance from its end to the stop line), so `dist` and the queue continue across the split;
  `lanes` / `lane_approach` stay the stop-line lanes (+ sidewalk lanes, see below) so that stop-line crossings
  keep their meaning; `approach_lanes` = every lane of an approach (the intervention windows, R30);
- sidewalk of an approach (Phase 3B topology c): an inbound edge of the junction that is no site approach edge and
  starts at a segment node; its lane is in `lane_approach` (a rider crossing its stop line is a crossing) but not in
  `lanes` or the signal group;
- box of an illegal-left approach (site `illegal_left.approaches`, its left links): the internal-lane chain of the
  left link (as `outputs.junction_geometry.box_lanes`); `hold_lanes` = the chain lanes before the last one, i.e. the
  lanes that end at the internal junction where the left-turners wait (proxy net: `:<junction>_16_0`). A vehicle on
  the last chain lane has passed the waiting point and is inside the crossing stream: it is never held;
- opposing approach = the other approach of the same road (`<ROAD>_<side>`), as `outputs.Geometry.opposing_of`;
  crossing approaches = the remaining ones.

`Step` is built every step from one junction context subscription (lane, lanePosition, speed, type, posLat of every
vehicle within the radius) and the TLS subscription (state, phase, next switch). Stop-line crossings are found by
comparing each vehicle's lane with its lane of the previous step (inbound lane -> internal lane; a teleport is
none). `Step.t` = `simulation.getTime()` after the step, with the TLS state SUMO reports then: a switch scheduled at
T is seen from T + step length (checked on the tiny cross: green at 45.0 in the program, reported at 45.1).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import traci.constants as tc

from thesis_sumo.config import Site
from thesis_sumo.runtime.wrong_lane import LaneLink
from thesis_sumo.schema_observed import normalise_state

FRONT_ROW_M = 2.5  # front within this distance of the stop line = front row. A second-row vehicle stands at least
# length + minGap behind the line: >= 2.2 + 0.5 m for motorcycles (minGap lower bound, rules/bounds/param_bounds.yaml)
HALT_SPEED_MPS = 5 / 3.6  # halting, as thesis_sumo.sim.outputs.HALT_SPEED_MPS (E2 detector speedThreshold)
JAM_GAP_M = 10.0          # queue chaining gap, as thesis_sumo.sim.outputs.JAM_GAP_M
VEH_VARS = (tc.VAR_LANE_ID, tc.VAR_LANEPOSITION, tc.VAR_SPEED, tc.VAR_TYPE, tc.VAR_LANEPOSITION_LAT)
TLS_VARS = (tc.TL_RED_YELLOW_GREEN_STATE, tc.TL_CURRENT_PHASE, tc.TL_NEXT_SWITCH)


def allowed_classes(backend, lane: str) -> frozenset[str] | None:
    """vClasses allowed on `lane`; None = no restriction. SUMO 1.27 `lane.getAllowed` lists the classes, and is empty
    for a lane nobody may use (the closed lane-0 straight, `disallow="all"`, R37), so an empty list counts as
    unrestricted only when `getDisallowed` is empty too."""
    allowed = frozenset(backend.lane.getAllowed(lane))
    return allowed if allowed or backend.lane.getDisallowed(lane) else None


@dataclass(frozen=True)
class Link:
    to_lane: str
    to_edge: str
    via: str
    direction: str
    allowed: frozenset[str] | None  # vClasses of the via lane (the connection's permissions); None = unrestricted


@dataclass
class JunctionInfo:
    tls_id: str
    junction_id: str
    approach_edge: dict[str, str]                 # approach -> inbound edge
    lanes: dict[str, list[str]]                   # approach -> inbound lane ids by index (0 = rightmost)
    lane_approach: dict[str, str]                 # inbound lane -> approach
    lane_length: dict[str, float]                 # inbound + box lanes -> length
    links: dict[str, list[Link]]                  # inbound lane -> its links
    group_links: dict[str, list[int]]             # approach -> straight TLS link indices
    phases: list[tuple[float, str]]               # (duration, state) of the running program
    opposing: dict[str, str] = field(default_factory=dict)
    box_lanes: dict[str, list[str]] = field(default_factory=dict)   # illegal-left approach -> internal chain
    hold_lanes: dict[str, list[str]] = field(default_factory=dict)  # illegal-left approach -> chain before waiting point
    lane_movements: dict[str, list[list[str]]] = field(default_factory=dict)  # approach -> per lane index
    vtype_length: dict[str, float] = field(default_factory=dict)  # vType id -> length (filled by StepReader)
    segments: dict[str, list[str]] = field(default_factory=dict)  # approach -> edges, stop line first
    chains: dict[str, list[list[str]]] = field(default_factory=dict)  # approach -> per lane index, stop line first
    lane_offset: dict[str, float] = field(default_factory=dict)  # approach lane -> distance of its end to the stop line
    sidewalk: dict[str, str] = field(default_factory=dict)  # approach -> sidewalk lane
    approach_lanes: dict[str, str] = field(default_factory=dict)  # every lane of an approach (all segments) -> approach

    @classmethod
    def build(cls, backend, site: Site, *, need_lane_movements: bool = False,
              need_box: bool = False) -> "JunctionInfo":
        approach_edge = {}
        for i, app in enumerate(site["approaches"]):
            approach_edge[site.require(f"approaches.{i}.id")] = str(site.require(f"approaches.{i}.edge"))
        lanes, lane_approach, lane_length, links = {}, {}, {}, {}
        junctions = set()
        for app, edge in approach_edge.items():
            n = backend.edge.getLaneNumber(edge)
            lanes[app] = [f"{edge}_{k}" for k in range(n)]
            junctions.add(backend.edge.getToJunction(edge))
            for lane in lanes[app]:
                lane_approach[lane] = app
                lane_length[lane] = backend.lane.getLength(lane)
                links[lane] = [Link(lk[0], backend.lane.getEdgeID(lk[0]), lk[4], lk[6],
                                    allowed_classes(backend, lk[4]) if lk[4] else None)
                               for lk in backend.lane.getLinks(lane)]
        if len(junctions) != 1:
            raise ValueError(f"site approaches end at {len(junctions)} junctions {sorted(junctions)}, expected 1")
        tls_id = cls._tls_of(backend, set(lane_approach))
        group_links = {a: [] for a in approach_edge}
        for idx, conns in enumerate(backend.trafficlight.getControlledLinks(tls_id)):
            for in_lane, out_lane, _via in conns:
                if in_lane in lane_approach:  # road stop-line lanes only (sidewalks are added below)
                    if any(lk.to_lane == out_lane and lk.direction == "s" for lk in links[in_lane]):
                        group_links[lane_approach[in_lane]].append(idx)
        missing = [a for a, v in group_links.items() if not v]
        if missing:
            raise ValueError(f"approaches {missing} have no straight TLS link to define their signal group")
        program = backend.trafficlight.getProgram(tls_id)
        (logic,) = [lg for lg in backend.trafficlight.getAllProgramLogics(tls_id) if lg.programID == program]
        info = cls(tls_id, junctions.pop(), approach_edge, lanes, lane_approach, lane_length, links,
                   {a: sorted(v) for a, v in group_links.items()}, [(float(p.duration), p.state) for p in logic.phases])
        for app in approach_edge:
            same = [o for o in approach_edge if o != app and o.split("_")[0] == app.split("_")[0]]
            if len(same) == 1:
                info.opposing[app] = same[0]
        info._build_segments(backend)
        if need_lane_movements:
            for i, a in enumerate(site["approaches"]):
                mv = site.require(f"approaches.{i}.lane_movements")
                if len(mv) != len(lanes[a["id"]]):
                    raise ValueError(f"approaches.{i}.lane_movements has {len(mv)} lanes, the net has "
                                     f"{len(lanes[a['id']])} on {approach_edge[a['id']]}")
                info.lane_movements[a["id"]] = [list(x) for x in mv]
        if need_box:
            info._build_box(backend, site)
        return info

    def _build_segments(self, backend) -> None:
        for app, edge in self.approach_edge.items():
            segs = [edge]
            while True:
                ups = [e for e in backend.junction.getIncomingEdges(backend.edge.getFromJunction(segs[-1]))
                       if not e.startswith(":") and e not in segs
                       and any(backend.lane.getEdgeID(lk[0]) == segs[-1] and lk[6] == "s"
                               for lk in backend.lane.getLinks(f"{e}_0"))]
                if len(ups) > 1:
                    raise ValueError(f"approach {app}: edge {segs[-1]} has several upstream continuations {ups}")
                if not ups:
                    break
                segs.append(ups[0])
            self.segments[app] = segs
            self.chains[app] = []
            for k, lane in enumerate(self.lanes[app]):
                chain, offset = [lane], 0.0
                self.lane_offset[lane] = 0.0
                for up in segs[1:]:
                    up_lane = f"{up}_{k}"
                    (via,) = [lk[4] for lk in backend.lane.getLinks(up_lane) if lk[0] == chain[-1]] or [""]
                    for ln in ([via] if via else []) + [up_lane]:
                        offset += self.lane_length[chain[-1]]
                        self.lane_length[ln] = backend.lane.getLength(ln)
                        self.lane_offset[ln] = offset
                        chain.append(ln)
                self.chains[app].append(chain)
                for ln in chain:
                    self.approach_lanes[ln] = app
        starts = {backend.edge.getFromJunction(s): a for a, segs in self.segments.items() for s in segs}
        for e in backend.junction.getIncomingEdges(self.junction_id):
            if e.startswith(":") or e in self.approach_edge.values():
                continue
            if backend.edge.getFromJunction(e) not in starts:
                raise ValueError(f"inbound edge {e} is neither a site approach nor a sidewalk of one")
            app, lane = starts[backend.edge.getFromJunction(e)], f"{e}_0"
            self.sidewalk[app] = lane
            self.lane_approach[lane] = self.approach_lanes[lane] = app
            self.lane_length[lane] = backend.lane.getLength(lane)
            self.lane_offset[lane] = 0.0
            self.links[lane] = [Link(lk[0], backend.lane.getEdgeID(lk[0]), lk[4], lk[6],
                                     allowed_classes(backend, lk[4]) if lk[4] else None)
                                for lk in backend.lane.getLinks(lane)]

    @staticmethod
    def _tls_of(backend, inbound: set[str]) -> str:
        found = [t for t in backend.trafficlight.getIDList() if inbound & set(backend.trafficlight.getControlledLanes(t))]
        if len(found) != 1:
            raise ValueError(f"expected one traffic light controlling the site approaches, found {found}")
        return found[0]

    def _build_box(self, backend, site: Site) -> None:
        for app in site.require("illegal_left.approaches"):
            if app not in self.lanes:
                raise ValueError(f"illegal_left.approaches names {app!r}, not an approach {sorted(self.lanes)}")
            chains = []
            for lane in self.lanes[app]:
                for lk in self.links[lane]:
                    if lk.direction == "l" and lk.via:
                        chain = [lk.via]
                        while True:
                            nxt = [x[4] for x in backend.lane.getLinks(chain[-1]) if x[4]]
                            if not nxt:
                                break
                            chain.append(nxt[0])
                        chains.append(chain)
            if len(chains) != 1:
                raise ValueError(f"approach {app}: expected one left link for the illegal left, found {len(chains)}")
            (chain,) = chains
            self.box_lanes[app] = chain
            self.hold_lanes[app] = chain[:-1]
            for lane in chain:
                self.lane_length[lane] = backend.lane.getLength(lane)
            if not self.hold_lanes[app]:
                raise ValueError(f"approach {app}: the left link {chain} has no internal waiting point")

    def crossing_of(self, app: str) -> list[str]:
        return [a for a in self.lanes if a != app and a != self.opposing.get(app)]

    def group_state(self, tls_state: str, app: str) -> str:
        states = {normalise_state(tls_state[i]) for i in self.group_links[app]}
        if len(states) != 1:
            raise ValueError(f"straight links {self.group_links[app]} of {app} disagree in {tls_state!r}")
        return states.pop()

    def time_to_green(self, app: str, phase: int, next_switch: float, t: float) -> float:
        """Seconds until the approach group next turns G under the running static program (0 when G now)."""
        if self.group_state(self.phases[phase][1], app) == "G":
            return 0.0
        wait = max(next_switch - t, 0.0)
        for k in range(1, len(self.phases) + 1):
            dur, state = self.phases[(phase + k) % len(self.phases)]
            if self.group_state(state, app) == "G":
                return wait
            wait += dur
        return float("inf")

    def lane_links(self, app: str) -> list[list[LaneLink]]:
        """The approach's connections per lane index, as `wrong_lane` takes them."""
        return [[LaneLink(lk.to_edge, lk.direction, lk.allowed) for lk in self.links[ln]] for ln in self.lanes[app]]


@dataclass(frozen=True)
class Veh:
    lane: str
    pos: float
    speed: float
    vtype: str
    lat: float


@dataclass
class Step:
    t: float
    tls_state: str
    phase: int
    next_switch: float
    groups: dict[str, str]                         # approach -> G | y | r
    changed: dict[str, tuple[str | None, str]]     # approach -> (previous, new) group state, this step only
    vehicles: dict[str, Veh]                       # vehicles within the radius (sorted by id)
    by_lane: dict[str, list[str]]                  # lane -> vehicle ids, front first
    crossings: list[tuple[str, str, str]]          # (vehicle, approach, group state) that crossed a stop line now
    red_id: dict[str, int]                         # approach -> number of red onsets so far (id of the red phase)
    info: JunctionInfo

    def dist(self, vid: str) -> float:
        """Front bumper upstream of the stop line, across the segments of a split approach."""
        v = self.vehicles[vid]
        return self.info.lane_offset.get(v.lane, 0.0) + self.info.lane_length[v.lane] - v.pos

    def front_row(self, app: str) -> list[str]:
        """Vehicles on the approach's inbound lanes whose front is within FRONT_ROW_M of the stop line."""
        out = []
        for lane in self.info.lanes[app]:
            for vid in self.by_lane.get(lane, ()):
                if self.dist(vid) > FRONT_ROW_M:
                    break
                out.append(vid)
        return sorted(out)

    def queue_length(self, lanes) -> float:
        """Queue from the stop line along `lanes` (an inbound lane, or a `JunctionInfo.chains` lane list, stop line
        first): halting vehicles chained by JAM_GAP_M (outputs.queue_at, without the range cap); the tail is the
        farthest rear bumper (vType length)."""
        tail = 0.0
        for lane in [lanes] if isinstance(lanes, str) else lanes:
            for vid in self.by_lane.get(lane, ()):
                v = self.vehicles[vid]
                if v.speed >= HALT_SPEED_MPS:
                    continue
                d = self.dist(vid)
                if d > tail + JAM_GAP_M:
                    return tail
                tail = max(tail, d + self.info.vtype_length[v.vtype])
        return tail

    def time_to_green(self, app: str) -> float:
        return self.info.time_to_green(app, self.phase, self.next_switch, self.t)


class StepReader:
    """Subscribes once and turns the subscription results into a `Step` every simulation step."""

    def __init__(self, backend, info: JunctionInfo, radius_m: float):
        self.b, self.info = backend, info
        backend.junction.subscribeContext(info.junction_id, tc.CMD_GET_VEHICLE_VARIABLE, float(radius_m), list(VEH_VARS))
        backend.trafficlight.subscribe(info.tls_id, list(TLS_VARS))
        self._prev_lane: dict[str, str] = {}
        self._prev_groups: dict[str, str] = {}
        self._red_id = {a: 0 for a in info.lanes}

    def read(self) -> Step:
        b, info = self.b, self.info
        t = round(b.simulation.getTime(), 6)
        tl = b.trafficlight.getSubscriptionResults(info.tls_id)
        state = tl[tc.TL_RED_YELLOW_GREEN_STATE]
        groups = {a: info.group_state(state, a) for a in info.lanes}
        changed = {a: (self._prev_groups.get(a), s) for a, s in groups.items() if self._prev_groups.get(a) != s}
        self._prev_groups = groups
        for a, (_, new) in changed.items():
            if new == "r":
                self._red_id[a] += 1
        res = b.junction.getContextSubscriptionResults(info.junction_id) or {}
        vehicles, by_lane, crossings, lanes_now = {}, {}, [], {}
        for vid in sorted(res):
            d = res[vid]
            v = Veh(d[tc.VAR_LANE_ID], d[tc.VAR_LANEPOSITION], d[tc.VAR_SPEED], d[tc.VAR_TYPE],
                    d[tc.VAR_LANEPOSITION_LAT])
            vehicles[vid] = v
            if v.vtype not in info.vtype_length:
                info.vtype_length[v.vtype] = b.vehicletype.getLength(v.vtype)
            lanes_now[vid] = v.lane
            by_lane.setdefault(v.lane, []).append(vid)
            prev = self._prev_lane.get(vid)
            # an internal lane is required: a teleport off an inbound lane lands on a normal edge (often the
            # outbound one, in the same step) and is no stop-line crossing (tests/test_runtime.py)
            if prev is not None and prev in info.lane_approach and v.lane.startswith(":"):
                app = info.lane_approach[prev]
                crossings.append((vid, app, groups[app]))
        for ids in by_lane.values():
            ids.sort(key=lambda i: -vehicles[i].pos)
        self._prev_lane = lanes_now
        return Step(t, state, int(tl[tc.TL_CURRENT_PHASE]), float(tl[tc.TL_NEXT_SWITCH]), groups, changed,
                    vehicles, by_lane, crossings, dict(self._red_id), info)
