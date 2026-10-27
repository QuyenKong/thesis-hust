"""SUMO run output -> PLAN 5.1 observed-data tables (+ the tier-1 `traversals` extension): `to_observed_schema`.

The simulation side writes the same tables the video pipeline will, so one set of metric functions runs
on both. Every derivation is fixed here; the proxy-data generator (Task 6) and the metrics (Task 10) rely
on exactly these definitions. Shared conventions (time base, approach groups, G/y/r, cycles, green onset,
the binding box_queue definition) are in `thesis_sumo.schema_observed`.

Inputs read from `run_dir` (all written by `thesis_sumo.sim.runner`): `run.sumocfg` (net and route file
paths), `manifest.json` (`config.sim` begin/end/fcd radius, `config.observation.queue_range_m`),
`vtypes.json` (vType id -> vClass/length, queried from SUMO at run start), `tls_states.xml`,
`detectors.xml`, `fcd.xml.gz`. Each file is read as `.xml` or `.xml.gz`, whichever exists.

Definitions (R = `observation.queue_range_m` from experiment.yaml, a modelling choice)
-----------
- **Stop line** of an approach = end of each lane of its inbound edge (where `in__<lane>` loops sit,
  `sumocfg.ENTRY_OFFSET_M` before it). `dist_m` / `long_m_from_stopline` = distance of the vehicle's
  front bumper (fcd `pos`) upstream of the stop line; negative once past it (on the approach's internal
  lanes: minus the distance travelled along the internal-lane chain of its link). An approach split by the site
  patches (bollard edge, sidewalk start: `build_net.approach_segments`) is one approach: the lanes of its upstream
  segments and of the short internal lanes between them count with the length of everything downstream added.
- **Sidewalk** (`build_net.sidewalk_edges`, Phase 3B): its lane belongs to its approach (stop-line crossings, turn
  counts, traversals, lateral snapshots with a negative lateral position: the sidewalk centre lies half its width
  right of the roadway edge) but is no part of the road queue (`queue_snapshots` leave it out). Its movement is read
  from the route file, which keeps the road route (the sidewalk is a TraCI reroute).
- **Lateral position** `lat_m` / `lane_or_lat_m` / `lat_m_at_stopline` = distance of the vehicle centre from
  the right edge of the approach's roadway (lane 0's right border), positive to the left: widths of the
  lanes right of the vehicle's lane + half its lane width + fcd `posLat` (lateral offset from the lane
  centre, positive to the left, FCDOutput docs: speedLat "negative if the vehicle moves to the right").
  On internal lanes the lane centre used is that of the link's from-lane (approximation).
- **signal_events**: one row at the first tlsStates record and one per change of an approach group's
  state; group state = normalised state of the approach's straight links (`signal_events`).
- **stopline_crossings**: the first `enter` event per vehicle on any `in__` loop; `t` = SUMO's
  interpolated crossing time; lateral position from the vehicle's last fcd row on an inbound lane (one
  step before the crossing at most; NaN if it has none); `signal_state_at_t` = the approach group's state
  at `t`.
- **turn_counts**: stop-line crossings binned by crossing time into `INTERVAL_S` bins from the sim begin,
  movement from the vehicle's route (`build_demand.movement_table`); the full grid of
  (bin, approach, movement, vclass) is written with zeros (no `car` x `illegal_l`); the last bin is partial
  when the run does not end on a bin boundary.
- **queue_snapshots**: at each green onset of an approach, from the fcd frame at that time
  (`queue_at`): halting vehicles (speed < `HALT_SPEED_MPS`) on the inbound edge with the front within R of
  the stop line; walking upstream from the stop line, a vehicle joins the queue if its front is within
  `JAM_GAP_M` of the queue tail (the stop line for the first one); the tail is the farthest rear bumper so
  far. `queue_length_m` = min(tail, R): **a queue reaching R is censored and reported as exactly R**
  (`queue_length_m >= R` <=> censored; M5's `share_censored`). `area_m2` = `queue_length_m` x roadway width.
- **lateral_snapshots**: at each green onset of an approach, every halting vehicle of that approach with
  the front within R upstream of the stop line, or anywhere past it on the approach's internal lanes
  (stop-line overshoot, red runners, box waiters).
- **box_queue**: see `schema_observed` (binding). Box = the internal-lane chain of the approach's
  `illegal_l` link(s) (proxy net: TLS link 16, `:<junction>_16_0` + `_28_0`); exits = first fcd row off the
  box lanes. A vehicle that **disappears while in the box** (absent from the next fcd step before the
  record ends: collision teleport, removal) has no box exit: it still counts in `n_waiting_in_box` when it
  was halting at `t`, but it is left out of `t_clear_start` / `t_clear_end` and does not make `t_clear_end`
  NaN; NaN `t_clear_end` with a value in `t_clear_start` therefore always means "still in the box when the
  record ends".
- **F2 tables** (`queue_timeseries`, `space_seeking_events`, `right_turn_delay`; definitions in `schema_observed`),
  from the fcd frames on the `QUEUE_TS_STEP_S` grid from the sim begin (the video sampling grid), never from the
  TraCI log (`interventions.csv`), so the same rule works on video: queue = `queue_at` on each frame; lane 0's band
  = [0, width of the stop-line edge's lane 0); a vehicle's movement = its route (as turn_counts; the sidewalk is a
  TraCI reroute and the route file keeps the road route). `wrong_lane` lane markings = the movements of the stop-line
  lane's connections open to `passenger` or `motorcycle` (`Geometry.lane_marks`; the proxy net is built so that they
  equal the site's `lane_movements`, which M8 reads), the lane from `lane_or_lat_m` as in M8.
- **traversals** (one row per stop-line crossing, same `track_id`): `movement` as in turn_counts;
  `exit_approach` = approach id of the arm the vehicle leaves by (outbound edge -> arm with the nearest
  bearing from the junction centre); `t_range_entry` = time the front crosses R upstream of the stop line,
  interpolated between the two fcd rows around it (NaN if first seen inside R); `t_stopline` = the
  crossing `t`; `t_exit` = first `enter` on an `out__` loop (NaN if not exited before the record ends).
"""

from __future__ import annotations

import gzip
import json
import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
import sumolib
from lxml import etree

from thesis_sumo.demand.build_demand import movement_table
from thesis_sumo.net.apply_patches import movement_of
from thesis_sumo.net.build_net import approach_edges, approach_segments, sidewalk_edges, target_node, target_tls
from thesis_sumo.schema_observed import (
    INTERVAL_S,
    QUEUE_TS_STEP_S,
    TABLES,
    VCLASSES,
    cycle_id_at,
    green_onsets,
    normalise_state,
    queue_at_times,
)

OBSERVED_DIR = "observed_schema"
VTYPES_JSON = "vtypes.json"
HALT_SPEED_MPS = 5 / 3.6  # E2 detector default speedThreshold (sumo.dlr.de/docs/Simulation/Output/Lanearea_Detectors_(E2).html)
JAM_GAP_M = 10.0          # E2 detector default jamThreshold, same page
TIME_DECIMALS = 2         # fcd / tlsStates times are written with 2 decimals
VCLASS_OF_SUMO = {"passenger": "car", "motorcycle": "moto", "custom1": "moto", "custom2": "car"}
MAX_EXIT_BEARING_DIFF_DEG = 45.0  # an outbound edge belongs to the arm whose inbound edge has the nearest bearing


def _open(path: Path):
    """Open `path` for reading, falling back to its `.gz` / plain twin when only that one exists."""
    path = Path(path)
    if not path.is_file():
        twin = path.with_suffix("") if path.suffix == ".gz" else path.with_name(path.name + ".gz")
        if twin.is_file():
            path = twin
    return gzip.open(path, "rb") if path.suffix == ".gz" else path.open("rb")


def _rt(t) -> float:
    return round(float(t), TIME_DECIMALS)


# ---------------------------------------------------------------- junction geometry


@dataclass
class Geometry:
    """What the conversion needs to know about the target junction of the net."""

    inbound: dict[str, str]                      # approach -> inbound edge id
    lane_info: dict[str, tuple[str, float, float]]  # approach lane -> (approach, distance from its start to the stop
    # line, lat of lane centre): the stop-line lanes, the upstream segments and the sidewalk
    internal: dict[str, tuple[str, float, float]]   # internal lane -> (approach, offset past stop line, lat)
    road_width: dict[str, float]                 # approach -> roadway width at the stop line
    group_links: dict[str, list[int]]            # approach group -> TLS link indices (straight links)
    box_lanes: dict[str, str] = field(default_factory=dict)  # internal lane of an illegal_l link -> approach
    opposing: dict[str, str] = field(default_factory=dict)   # approach -> opposing approach
    movements: dict[tuple[str, str], tuple[str, str]] = field(default_factory=dict)
    exit_approach: dict[str, str] = field(default_factory=dict)  # outbound edge -> approach id of its arm
    stopline_from_centre: dict[str, float] = field(default_factory=dict)
    sidewalk_lanes: frozenset = frozenset()
    lane_bounds: dict[str, np.ndarray] = field(default_factory=dict)  # approach -> cumulative stop-line lane widths
    lane_marks: dict[str, list[set]] = field(default_factory=dict)    # approach -> movements per stop-line lane

    def opposing_of(self, approach: str) -> str:
        try:
            return self.opposing[approach]
        except KeyError:
            raise ValueError(f"approach {approach!r} has no opposing approach: the opposing approach is the only "
                             f"other approach with the same road prefix ('<ROAD>_<side>', e.g. LVL_W <-> LVL_E); "
                             f"approaches are {sorted(self.inbound)}") from None


def _via_chain(net, via_id: str) -> list:
    chain = [net.getLane(via_id)]
    while True:
        nxt = [c.getViaLaneID() for c in chain[-1].getOutgoing() if c.getViaLaneID()]
        if not nxt:
            return chain
        chain.append(net.getLane(nxt[0]))


def _bearing(frm, to) -> float:
    return math.degrees(math.atan2(to[0] - frm[0], to[1] - frm[1])) % 360


def _exit_arms(net, node, inbound: dict[str, str]) -> dict[str, str]:
    """Outbound edge -> approach id of the same arm (nearest bearing of the edge's far node from the centre)."""
    centre = node.getCoord()
    arm = {a: _bearing(centre, net.getEdge(e).getFromNode().getCoord()) for a, e in inbound.items()}
    out = {}
    for edge in node.getOutgoing():
        if edge.isSpecial():
            continue
        b = _bearing(centre, edge.getToNode().getCoord())
        diff = {a: abs((b - ab + 180) % 360 - 180) for a, ab in arm.items()}
        best = min(diff, key=diff.get)
        if diff[best] > MAX_EXIT_BEARING_DIFF_DEG:
            raise ValueError(f"outbound edge {edge.getID()} matches no approach arm (nearest {best}, {diff[best]:.0f} deg)")
        out[edge.getID()] = best
    if len(set(out.values())) != len(out):
        raise ValueError(f"outbound edges do not map one-to-one onto approach arms: {out}")
    return out


def junction_geometry(net_path: Path) -> Geometry:
    net = sumolib.net.readNet(str(net_path), withInternal=True)
    tls = target_tls(net)
    node = target_node(tls)
    centre = node.getCoord()
    inbound = approach_edges(net)
    approach_of = {e: a for a, e in inbound.items()}
    movements = movement_table(net)
    lane_info, road_width, stop_dist = {}, {}, {}
    for app, edge_id in inbound.items():
        offset, segs = 0.0, approach_segments(net, edge_id)
        for k, seg in enumerate(segs):
            right = 0.0
            for lane in sorted(seg.getLanes(), key=lambda ln: ln.getIndex()):
                lane_info[lane.getID()] = (app, offset + lane.getLength(), right + lane.getWidth() / 2)
                right += lane.getWidth()
                if k == 0:
                    stop_dist[app] = max(stop_dist.get(app, 0.0), math.dist(centre, lane.getShape()[-1]))
                    road_width[app] = right
            offset += seg.getLanes()[0].getLength()
            if k + 1 < len(segs):  # internal lanes of the split node upstream of `seg`
                for c in segs[k + 1].getOutgoing()[seg]:
                    if c.getViaLaneID():
                        via = net.getLane(c.getViaLaneID())
                        lane_info[via.getID()] = (app, offset + via.getLength(), lane_info[c.getToLane().getID()][2])
                offset += max((net.getLane(c.getViaLaneID()).getLength() for c in segs[k + 1].getOutgoing()[seg]
                               if c.getViaLaneID()), default=0.0)
    sidewalks = sidewalk_edges(net)
    for sw, app in sidewalks.items():
        for lane in net.getEdge(sw).getLanes():
            lane_info[lane.getID()] = (app, lane.getLength(), -lane.getWidth() / 2)
    approach_of.update(sidewalks)
    internal, box_lanes, group_links = {}, {}, {a: [] for a in inbound}
    for in_lane, out_lane, idx in tls.getConnections():
        (conn,) = [c for c in in_lane.getOutgoing() if c.getToLane() == out_lane]
        app = approach_of[in_lane.getEdge().getID()]
        if in_lane.getEdge().getID() in sidewalks:
            mv = {"t": "u"}.get(movement_of(conn.getDirection()), movement_of(conn.getDirection()))
        else:
            _, mv = movements[(in_lane.getEdge().getID(), out_lane.getEdge().getID())]
            if conn.getDirection() == "s":  # the signal group is the road's straight links
                group_links[app].append(idx)
        offset = 0.0
        for lane in _via_chain(net, conn.getViaLaneID()):
            prev = internal.setdefault(lane.getID(), (app, offset, lane_info[in_lane.getID()][2]))
            if prev[0] != app:
                raise ValueError(f"internal lane {lane.getID()} is used by approaches {prev[0]} and {app}")
            if mv == "illegal_l":
                box_lanes[lane.getID()] = app
            offset += lane.getLength()
    missing = [a for a, links in group_links.items() if not links]
    if missing:
        raise ValueError(f"approaches {missing} have no straight link to define their signal group")
    lane_bounds, lane_marks = {}, {}
    for app, edge_id in inbound.items():
        lanes = sorted(net.getEdge(edge_id).getLanes(), key=lambda ln: ln.getIndex())
        lane_bounds[app] = np.cumsum([ln.getWidth() for ln in lanes])
        lane_marks[app] = [{movements[(edge_id, c.getToLane().getEdge().getID())][1] for c in ln.getOutgoing()
                            if c.allows("passenger") or c.allows("motorcycle")} for ln in lanes]
    opposing = {}
    for app in inbound:
        same_road = [o for o in inbound if o != app and o.split("_")[0] == app.split("_")[0]]
        if len(same_road) == 1:
            opposing[app] = same_road[0]
    return Geometry(inbound, lane_info, internal, road_width, {a: sorted(v) for a, v in group_links.items()},
                    box_lanes, opposing, movements, _exit_arms(net, node, inbound), stop_dist,
                    frozenset(ln.getID() for sw in sidewalks for ln in net.getEdge(sw).getLanes()),
                    lane_bounds, lane_marks)


# ---------------------------------------------------------------- readers


def read_tls_states(path: Path) -> pd.DataFrame:
    """All `<tlsState>` records: t, state (SUMO state string, one char per link index)."""
    rows = []
    with _open(path) as f:
        for _, el in etree.iterparse(f, tag="tlsState"):
            rows.append((_rt(el.get("time")), el.get("state")))
            el.clear()
    return pd.DataFrame(rows, columns=["t", "state"])


def read_loop_crossings(path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """First `enter` event per vehicle on the `in__<lane>` loops (t, lane, track_id, type) and on the
    `out__<lane>` loops (track_id, t)."""
    entries, exits, seen_in, seen_out = [], [], set(), set()
    with _open(path) as f:
        for _, el in etree.iterparse(f, tag="instantOut"):
            det, vid = el.get("id"), el.get("vehID")
            if el.get("state") == "enter":
                if det.startswith("in__") and vid not in seen_in:
                    seen_in.add(vid)
                    entries.append((float(el.get("time")), det[len("in__"):], vid, el.get("type")))
                elif det.startswith("out__") and vid not in seen_out:
                    seen_out.add(vid)
                    exits.append((vid, float(el.get("time"))))
            el.clear()
    return (pd.DataFrame(entries, columns=["t", "lane", "track_id", "type"]),
            pd.DataFrame(exits, columns=["track_id", "t"]))


def read_route_edges(path: Path) -> dict[str, tuple[str, ...]]:
    """vehicle id -> route edges (nested `<route edges>` or a `route=` reference to a named route)."""
    named, out = {}, {}
    with _open(path) as f:
        for _, el in etree.iterparse(f, tag=("route", "vehicle")):
            if el.tag == "route" and el.get("id") is not None and el.getparent().tag != "vehicle":
                named[el.get("id")] = tuple(el.get("edges").split())
            elif el.tag == "vehicle":
                child = el.find("route")
                out[el.get("id")] = tuple(child.get("edges").split()) if child is not None else named[el.get("route")]
                el.clear()
    return out


@dataclass
class FcdScan:
    frames: pd.DataFrame       # rows at the requested times on inbound/internal lanes of the junction
    last_inbound: dict         # vehicle -> (lane, posLat) of its last row on an inbound lane
    range_entry: dict          # vehicle -> time its front crossed R upstream of the stop line (NaN: first seen inside)
    box_rows: pd.DataFrame     # t, track_id, speed, approach for rows on box lanes
    box_exits: pd.DataFrame    # track_id, t, kind: "exit" (first row off the box lanes) | "removed" (vanished)


def scan_fcd(path: Path, geo: Geometry, frame_times: set[float], range_m: float) -> FcdScan:
    """One streaming pass over the fcd output keeping only what the tables need."""
    frames, box_rows, exits = [], [], []
    last_inbound, range_entry, prev_dist, in_box = {}, {}, {}, {}
    present: set[str] = set()
    with _open(path) as f:
        t = None
        for ev, el in etree.iterparse(f, events=("start", "end"), tag=("timestep", "vehicle")):
            if el.tag == "timestep":
                if ev == "start":
                    t, present = _rt(el.get("time")), set()
                else:
                    for vid in [v for v, inside in in_box.items() if inside and v not in present]:
                        exits.append((vid, t, "removed"))  # on the box lanes last step, gone now
                        in_box[vid] = False
                    el.clear()
                continue
            if ev != "end":
                continue
            vid, lane = el.get("id"), el.get("lane")
            present.add(vid)
            if lane in geo.lane_info:
                last_inbound[vid] = (lane, float(el.get("posLat")))
                d = geo.lane_info[lane][1] - float(el.get("pos"))
                if vid not in range_entry and d <= range_m:
                    p = prev_dist.get(vid)
                    range_entry[vid] = np.nan if p is None else p[0] + (p[1] - range_m) / (p[1] - d) * (t - p[0])
                prev_dist[vid] = (t, d)
            if t in frame_times and (lane in geo.lane_info or lane in geo.internal):
                frames.append((t, vid, el.get("type"), lane, float(el.get("pos")), float(el.get("posLat")),
                               float(el.get("speed"))))
            if lane in geo.box_lanes:
                box_rows.append((t, vid, float(el.get("speed")), geo.box_lanes[lane]))
                in_box[vid] = True
            elif in_box.get(vid):
                exits.append((vid, t, "exit"))
                in_box[vid] = False
    # vehicles still on the box lanes at the last step have neither an exit nor a removal
    return FcdScan(pd.DataFrame(frames, columns=["t", "track_id", "type", "lane", "pos", "posLat", "speed"]),
                   last_inbound, range_entry,
                   pd.DataFrame(box_rows, columns=["t", "track_id", "speed", "approach"]),
                   pd.DataFrame(exits, columns=["track_id", "t", "kind"]))


# ---------------------------------------------------------------- derivations


def signal_events(tls_states: pd.DataFrame, group_links: dict[str, list[int]]) -> pd.DataFrame:
    """signal_events rows: the first record and every change of each group's state (schema G/y/r)."""
    rows, last = [], {}
    for t, state in tls_states.itertuples(index=False):
        for group, links in group_links.items():
            states = {normalise_state(state[i]) for i in links}
            if len(states) != 1:
                raise ValueError(f"t={t}: links {links} of signal group {group} disagree ({state!r})")
            (s,) = states
            if last.get(group) != s:
                rows.append((t, group, s))
                last[group] = s
    ev = pd.DataFrame(rows, columns=TABLES["signal_events"])
    return ev.sort_values(["t", "approach_group"], kind="stable").reset_index(drop=True)


def state_at(signal_events_df: pd.DataFrame, group: str, t) -> np.ndarray:
    """State of `group` at each time in `t` (last event at or before t)."""
    ev = signal_events_df[signal_events_df["approach_group"] == group].sort_values("t", kind="stable")
    idx = np.searchsorted(ev["t"].to_numpy(dtype=float), np.asarray(t, dtype=float), side="right") - 1
    if (idx < 0).any():
        raise ValueError(f"times before the first signal record of {group}")
    return ev["state"].to_numpy()[idx]


def opposing_green_ends(signal_events_df: pd.DataFrame, group: str) -> np.ndarray:
    """Times at which `group` leaves G (G -> y or r)."""
    ev = signal_events_df[signal_events_df["approach_group"] == group].sort_values("t", kind="stable")
    prev = ev["state"].shift()
    return ev.loc[(prev == "G") & (ev["state"] != "G"), "t"].to_numpy(dtype=float)


def check_shared_green(signal_events_df: pd.DataFrame, a: str, b: str) -> None:
    """Raise unless groups `a` and `b` are green together at some time (the illegal left of `a` waits in the
    box during its own through green, which must also be the opposing through green of `b`)."""
    times = signal_events_df["t"].unique()
    if not ((state_at(signal_events_df, a, times) == "G") & (state_at(signal_events_df, b, times) == "G")).any():
        raise ValueError(f"illegal-left approach {a} and its opposing approach {b} never share a green phase; "
                         f"the box_queue definition (wait during the opposing through green) does not apply")


def queue_at(frame: pd.DataFrame, range_m: float) -> tuple[float, int, int]:
    """(queue_length_m, n_car, n_moto) from one approach's vehicles at one time; length capped at `range_m`.

    `frame` columns: vclass, dist_m (front bumper upstream of the stop line, 0 <= dist_m <= range_m),
    length, speed.
    """
    tail, n = 0.0, {"car": 0, "moto": 0}
    for row in frame[frame["speed"] < HALT_SPEED_MPS].sort_values("dist_m", kind="stable").itertuples():
        if row.dist_m > tail + JAM_GAP_M:
            break
        tail = max(tail, row.dist_m + row.length)
        n[row.vclass] += 1
    return min(tail, range_m), n["car"], n["moto"]


def box_queue_rows(approach: str, opposing_ends, onsets, box_rows: pd.DataFrame, box_exits: pd.DataFrame) -> pd.DataFrame:
    """box_queue rows for one illegal-left approach (definition in `schema_observed`, removal rule in the
    module docstring). `box_rows` (t, track_id, speed) and `box_exits` (track_id, t, kind) belong to that
    approach's box."""
    entered = box_rows.groupby("track_id")["t"].min()
    entry_cycle = pd.Series(cycle_id_at(onsets, entered.to_numpy()), index=entered.index)
    outcome = {}  # vehicle -> (kind, t) of its first exit/removal after entering; absent: still in the box
    for v, t0 in entered.items():
        after = box_exits[(box_exits["track_id"] == v) & (box_exits["t"] > t0)].sort_values("t", kind="stable")
        if len(after):
            outcome[v] = (after.iloc[0]["kind"], float(after.iloc[0]["t"]))
    halting = box_rows[box_rows["speed"] < HALT_SPEED_MPS]
    rows = []
    for t_e in opposing_ends:
        k = int(cycle_id_at(onsets, [t_e])[0])
        n_waiting = halting.loc[halting["t"] == t_e, "track_id"].nunique()
        entrants = entry_cycle.index[entry_cycle == k]
        exits = [outcome[v][1] for v in entrants if v in outcome and outcome[v][0] == "exit"]
        still_in = any(v not in outcome for v in entrants)
        start = min(exits) if exits else np.nan
        end = np.nan if still_in or not exits else max(exits)
        rows.append((k, float(t_e), approach, n_waiting, start, end))
    return pd.DataFrame(rows, columns=TABLES["box_queue"])


def _vtype_info(run_dir: Path) -> dict[str, dict]:
    info = json.loads((run_dir / VTYPES_JSON).read_text(encoding="utf-8"))
    for d in info.values():
        d["schema_vclass"] = VCLASS_OF_SUMO.get(d["vclass"])
    return info


def _schema_vclass(types: pd.Series, info: dict) -> pd.Series:
    out = types.map(lambda t: info.get(t, {}).get("schema_vclass"))
    bad = sorted(set(types[out.isna()]))
    if bad:
        raise ValueError(f"vehicle types {bad} have no schema vclass (known SUMO classes {sorted(VCLASS_OF_SUMO)})")
    return out


def _sumocfg_inputs(run_dir: Path) -> tuple[Path, Path]:
    opts = {el.tag: el.get("value") for sec in etree.parse(str(run_dir / "run.sumocfg")).getroot()
            for el in sec if isinstance(el.tag, str)}
    return Path(opts["net-file"]), Path(opts["route-files"])


def queue_range_m(config: dict) -> float:
    """`observation.queue_range_m` of an experiment config; raises when it is missing or null."""
    value = (config.get("observation") or {}).get("queue_range_m")
    if value is None:
        raise ValueError("experiment config observation.queue_range_m is missing or null; it sets the observed "
                         "upstream range of queues, lateral snapshots and traversals")
    return float(value)


# ---------------------------------------------------------------- main entry


def to_observed_schema(run_dir: Path) -> dict[str, pd.DataFrame]:
    """Write the `schema_observed.TABLES` CSVs into `run_dir/observed_schema/`; return them by table name."""
    run_dir = Path(run_dir)
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    sim = manifest["config"]["sim"]
    range_m = queue_range_m(manifest["config"])
    net_path, routes_path = _sumocfg_inputs(run_dir)
    geo = junction_geometry(net_path)
    too_far = {a: round(d, 1) for a, d in geo.stopline_from_centre.items() if d + range_m > sim["fcd_radius_m"]}
    if too_far:
        raise ValueError(f"stop line + observation.queue_range_m ({range_m} m) leaves the fcd zone "
                         f"(sim.fcd_radius_m {sim['fcd_radius_m']} m) for approaches (stop line distance) {too_far}")
    vinfo = _vtype_info(run_dir)

    ev = signal_events(read_tls_states(run_dir / "tls_states.xml"), geo.group_links)
    onsets = {a: green_onsets(ev, a) for a in geo.inbound}
    illegal = sorted(set(geo.box_lanes.values()))
    opp_ends = {}
    for a in illegal:
        check_shared_green(ev, a, geo.opposing_of(a))
        opp_ends[a] = opposing_green_ends(ev, geo.opposing_of(a))
    grid = [_rt(t) for t in np.arange(float(sim["begin_s"]), float(sim["end_s"]) - 1e-9, QUEUE_TS_STEP_S)]
    frame_times = {_rt(t) for v in list(onsets.values()) + list(opp_ends.values()) for t in v} | set(grid)
    scan = scan_fcd(run_dir / "fcd.xml.gz", geo, frame_times, range_m)
    entries, exits = read_loop_crossings(run_dir / "detectors.xml")
    routes = read_route_edges(routes_path)

    cr = _crossings(entries, geo, ev, scan, vinfo)
    moves = [_route_movement(r, routes, geo) for r in cr.itertuples()]
    cr["movement"] = [m for m, _ in moves]
    cr["exit_edge"] = [e for _, e in moves]
    tables = {"signal_events": ev, "stopline_crossings": cr,
              "turn_counts": _turn_counts(cr, geo, sim["begin_s"], sim["end_s"]),
              "traversals": _traversals(cr, exits, scan, geo)}
    frames = _annotate(scan.frames, geo, vinfo)
    tables["queue_snapshots"], tables["lateral_snapshots"] = _snapshots(geo, onsets, frames, range_m)
    tables.update(_f2_tables(geo, frames, grid, cr, routes, onsets, scan.range_entry, range_m))
    box = [box_queue_rows(a, opp_ends[a], onsets[a], scan.box_rows[scan.box_rows["approach"] == a],
                          scan.box_exits) for a in illegal]
    tables["box_queue"] = (pd.concat(box, ignore_index=True) if box
                           else pd.DataFrame(columns=TABLES["box_queue"]))
    out_dir = run_dir / OBSERVED_DIR
    out_dir.mkdir(exist_ok=True)
    for name, cols in TABLES.items():
        tables[name] = tables[name][cols].reset_index(drop=True)
        tables[name].to_csv(out_dir / f"{name}.csv", index=False, lineterminator="\n")
    return tables


def _crossings(cr: pd.DataFrame, geo: Geometry, ev: pd.DataFrame, scan: FcdScan, vinfo: dict) -> pd.DataFrame:
    cr = cr.copy()
    unknown = sorted(set(cr["lane"]) - set(geo.lane_info))
    if unknown:
        raise ValueError(f"entry loops on lanes {unknown} that are no approach lanes")
    cr["approach"] = cr["lane"].map(lambda ln: geo.lane_info[ln][0])

    def lat(vid):
        if vid not in scan.last_inbound:
            return np.nan
        lane, pos_lat = scan.last_inbound[vid]
        return geo.lane_info[lane][2] + pos_lat

    cr["lane_or_lat_m"] = cr["track_id"].map(lat).astype(float)
    cr["vclass"] = _schema_vclass(cr["type"], vinfo)
    cr["signal_state_at_t"] = ""
    for app, idx in cr.groupby("approach").groups.items():
        cr.loc[idx, "signal_state_at_t"] = state_at(ev, app, cr.loc[idx, "t"])
    return cr.sort_values(["t", "track_id"], kind="stable").reset_index(drop=True)


def _route_movement(row, routes: dict, geo: Geometry) -> tuple[str, str]:
    """(movement, outbound edge) of a crossing vehicle from its route."""
    edges = routes.get(row.track_id)
    if edges is None:
        raise ValueError(f"vehicle {row.track_id!r} crossed a stop line but is not in the route file")
    frm = geo.inbound[row.approach]
    if frm not in edges[:-1]:
        raise ValueError(f"vehicle {row.track_id!r} crossed the {row.approach} stop line but its route {edges} "
                         f"does not continue from {frm}")
    to = edges[edges.index(frm) + 1]
    return geo.movements[(frm, to)][1], to


def _turn_counts(cr: pd.DataFrame, geo: Geometry, begin: float, end: float) -> pd.DataFrame:
    cr = cr.assign(interval_start=(np.floor(cr["t"] / INTERVAL_S) * INTERVAL_S).astype(int))
    counts = cr.groupby(["interval_start", "approach", "movement", "vclass"]).size()
    starts = range(int(begin // INTERVAL_S) * INTERVAL_S, int(math.ceil(end)), INTERVAL_S)
    grid = [(s, app, mv, vc) for s in starts for (app, mv) in geo.movements.values() for vc in VCLASSES
            if not (mv == "illegal_l" and vc == "car")]
    rows = [(s, s + INTERVAL_S, app, mv, vc, int(counts.get((s, app, mv, vc), 0))) for s, app, mv, vc in grid]
    lost = len(cr) - sum(r[-1] for r in rows)
    if lost:
        raise ValueError(f"{lost} stop-line crossings fall outside the turn-count grid")
    return pd.DataFrame(rows, columns=TABLES["turn_counts"])


def _traversals(cr: pd.DataFrame, exits: pd.DataFrame, scan: FcdScan, geo: Geometry) -> pd.DataFrame:
    t_exit = exits.groupby("track_id")["t"].min()
    return pd.DataFrame({
        "track_id": cr["track_id"], "vclass": cr["vclass"], "approach": cr["approach"],
        "movement": cr["movement"], "exit_approach": cr["exit_edge"].map(geo.exit_approach),
        "lat_m_at_stopline": cr["lane_or_lat_m"],
        "t_range_entry": cr["track_id"].map(lambda v: scan.range_entry.get(v, np.nan)).astype(float),
        "t_stopline": cr["t"], "t_exit": cr["track_id"].map(t_exit).astype(float),
    }, columns=TABLES["traversals"])


def _annotate(frames: pd.DataFrame, geo: Geometry, vinfo: dict) -> pd.DataFrame:
    """fcd frame rows + approach, dist_m (front upstream of the stop line), lat_m, vclass, length."""
    fr = frames.copy()
    on_inbound = fr["lane"].isin(geo.lane_info).to_numpy()
    lane = fr["lane"].map(lambda ln: geo.lane_info.get(ln) or geo.internal[ln])  # (approach, length|offset, lat)
    fr["approach"] = lane.map(lambda x: x[0])
    ref = lane.map(lambda x: x[1]).astype(float)
    # inbound: lane length - front position; internal: minus (offset of the lane in its chain + position)
    fr["dist_m"] = np.where(on_inbound, ref - fr["pos"], -(ref + fr["pos"]))
    fr["lat_m"] = lane.map(lambda x: x[2]).astype(float) + fr["posLat"]
    fr["vclass"] = _schema_vclass(fr["type"], vinfo)
    fr["length"] = fr["type"].map(lambda t: vinfo[t]["length"])
    return fr


def _snapshots(geo: Geometry, onsets: dict, fr: pd.DataFrame, range_m: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    q_rows, lat_rows = [], []
    for app, times in onsets.items():
        for k, t0 in enumerate(times):
            at = fr[(fr["t"] == _rt(t0)) & (fr["approach"] == app)]
            upstream = at[(at["dist_m"] >= 0) & (at["dist_m"] <= range_m) & ~at["lane"].isin(geo.sidewalk_lanes)]
            length, n_car, n_moto = queue_at(upstream, range_m)
            q_rows.append((k, float(t0), app, length, n_car, n_moto, length * geo.road_width[app]))
            halted = at[(at["speed"] < HALT_SPEED_MPS) & (at["dist_m"] <= range_m)]
            lat_rows += [(k, app, r.track_id, r.vclass, r.lat_m, r.dist_m)
                         for r in halted.sort_values("dist_m", kind="stable").itertuples()]
    return (pd.DataFrame(q_rows, columns=TABLES["queue_snapshots"]),
            pd.DataFrame(lat_rows, columns=TABLES["lateral_snapshots"]))


def _f2_tables(geo: Geometry, fr: pd.DataFrame, grid: list[float], cr: pd.DataFrame, routes: dict, onsets: dict,
               range_entry: dict, range_m: float) -> dict[str, pd.DataFrame]:
    """queue_timeseries, space_seeking_events, right_turn_delay (schema_observed; module docstring) from the annotated
    frames on `grid` and the stop-line crossings `cr` (with movement)."""
    g = fr[fr["t"].isin(set(grid)) & (fr["dist_m"] >= 0) & (fr["dist_m"] <= range_m)]
    on_sw = g["lane"].isin(geo.sidewalk_lanes)
    by = dict(iter(g[~on_sw].groupby(["t", "approach"])))
    empty = g.iloc[:0]
    qts = pd.DataFrame([(t, a, *queue_at(by.get((t, a), empty), range_m)) for t in grid for a in sorted(geo.inbound)],
                       columns=TABLES["queue_timeseries"])

    moves: dict[str, str | None] = {}

    def movement(vid: str, app: str) -> str | None:
        if vid not in moves:
            edges, frm = routes.get(vid, ()), geo.inbound[app]
            moves[vid] = geo.movements[(frm, edges[edges.index(frm) + 1])][1] if frm in edges[:-1] else None
        return moves[vid]

    g = g.assign(movement=[movement(v, a) for v, a in zip(g["track_id"], g["approach"])])
    w0 = g["approach"].map(lambda a: geo.lane_bounds[a][0])
    lane0 = g[~on_sw & (g["lat_m"] >= 0) & (g["lat_m"] < w0)]
    ev = []
    for space, sub in (("right_lane", lane0[lane0["movement"] == "s"]), ("sidewalk", g[on_sw])):
        first = sub.sort_values("t", kind="stable").drop_duplicates("track_id")
        ev += [(r.t, r.approach, r.track_id, r.vclass, space) for r in first.itertuples()]
    turning = cr[cr["movement"].isin(("r", "l", "u")) & ~cr["lane"].isin(geo.sidewalk_lanes) & cr["lane_or_lat_m"].notna()]
    for r in turning.itertuples():
        bounds = geo.lane_bounds[r.approach]
        lane = min(int(np.searchsorted(bounds, r.lane_or_lat_m, side="right")), len(bounds) - 1)
        if r.movement not in geo.lane_marks[r.approach][lane]:
            t0 = range_entry.get(r.track_id, np.nan)
            ev.append((r.t if np.isnan(t0) else _rt(t0), r.approach, r.track_id, r.vclass, "wrong_lane"))
    ev = pd.DataFrame(ev, columns=["t", "approach", "track_id", "vclass", "space"])
    ev["cycle_id"], ev["queue_length_m_at_t"] = -1, np.nan
    for a, idx in ev.groupby("approach").groups.items():
        ev.loc[idx, "cycle_id"] = cycle_id_at(onsets[a], ev.loc[idx, "t"])
        ev.loc[idx, "queue_length_m_at_t"] = queue_at_times(qts, a, ev.loc[idx, "t"])
    ev = ev.sort_values(["t", "approach", "track_id", "space"], kind="stable")[TABLES["space_seeking_events"]]

    blocked = set()  # right-turners in lane 0 with a straight vehicle in lane 0 ahead of them at a grid time
    for _, grp in lane0.groupby(["t", "approach"]):
        s = grp.loc[grp["movement"] == "s", "dist_m"]
        if len(s):
            blocked |= set(grp.loc[(grp["movement"] == "r") & (grp["dist_m"] > s.min()), "track_id"])
    rt = cr[(cr["movement"] == "r") & ~cr["lane"].isin(geo.sidewalk_lanes)]
    rtd = pd.DataFrame({"track_id": rt["track_id"], "approach": rt["approach"], "vclass": rt["vclass"],
                        "t_enter": rt["track_id"].map(lambda v: range_entry.get(v, np.nan)).astype(float),
                        "t_exit": rt["t"], "blocked": rt["track_id"].isin(blocked)}, columns=TABLES["right_turn_delay"])
    return {"queue_timeseries": qts, "space_seeking_events": ev.reset_index(drop=True),
            "right_turn_delay": rtd.reset_index(drop=True)}
