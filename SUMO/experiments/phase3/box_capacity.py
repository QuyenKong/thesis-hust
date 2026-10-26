"""PLAN Phase 3: how many motorcycles can SUMO (sublane, SL2015) hold waiting inside the junction on the
illegal left of LVL_W (TLS link 16 on the proxy net)?

    .venv/Scripts/python experiments/phase3/box_capacity.py [--scenarios sat target sat_tight target_modopp sat_mg18]
        [--seeds 1 2 3 4 5] [--end 900] [--net scenario/net/site.proxy.net.xml] [--tag native] [--nproc 4]
        [--reanalyse] [--no-figures]

Scenarios (`SCENARIOS`; demand written per seed, Poisson arrivals, rng seeded with (scenario index, seed)):

- `sat`: 1500 moto_violator/h on the illegal left (about 50 per 120 s cycle, far more than the box holds);
- `target`: 225 moto_violator/h = 7.5 box entrants per cycle, the M7 entrant mean of data/proxy/targets.yaml;
- `sat_tight`: as `sat`, moto_violator with minGap 1.0 m and minGapLat 0.3 m (sensitivity of the capacity to the
  two vType parameters that bound it; every other attribute = B0);
- `target_modopp`: as `target`, with a moderate opposing LVL_E through of 1300 moto/h + 200 car/h, near the
  PROXY_D1-D3 LVL_E through volume (1204-1498 moto/h, 157-221 car/h in turn_counts.csv): early leavers through
  gaps;
- `sat_mg18`: as `sat`, moto_violator minGap 1.8 m (minGapLat B0): checks the predicted capacity of 10.

Opposing LVL_E through: dense (4000 moto/h + 700 car/h) unless stated; HDT_N / HDT_S through 1200 moto/h +
250 car/h each so the next phase start meets the box waiters. No other movements. New scenarios are appended
to `SCENARIOS`, so the rng streams (and routes) of the earlier ones stay unchanged.

Each run goes through `thesis_sumo.sim.runner.run` (manifest.json, observed-schema tables incl. box_queue.csv)
into `experiments/runs/phase3/<tag>/<spec>__PHASE3_<scenario>/seed_XX/`. A TraCI observer (no intervention)
logs every step: each vehicle on the box lanes (`outputs.junction_geometry(net).box_lanes`: lane, pos, posLat,
speed, waiting time), the target TLS state on change, halting vehicles on LVL_W lane 2, starting teleports and
colliding vehicles (`box_steps.csv`, `tls_steps.csv`, `events.csv`); the per-cycle table is `cycles.csv` and the
waiter positions at each opposing green end `waiters.csv`.

Summary per seed -> experiments/phase3/results_<tag>.csv; figures -> docs/research/figures/phase3_*_<tag>.png.
"""

from __future__ import annotations

import argparse
import json
import multiprocessing
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
import sumolib
import yaml
from lxml import etree

from thesis_sumo.config import REPO_ROOT, load_site
from thesis_sumo.demand.build_demand import movement_table
from thesis_sumo.net.build_net import approach_edges, target_tls, write_xml
from thesis_sumo.sim.outputs import HALT_SPEED_MPS, junction_geometry, read_loop_crossings
from thesis_sumo.sim.runner import COMPILED_DIR, MANIFEST_NAME, RUNS_DIR, RunInputs, run

SITE = REPO_ROOT / "config" / "site.proxy.yaml"
NET = REPO_ROOT / "scenario" / "net" / "site.proxy.net.xml"
TARGETS = REPO_ROOT / "data" / "proxy" / "targets.yaml"
OUT_ROOT = RUNS_DIR / "phase3"
RESULTS_DIR = REPO_ROOT / "experiments" / "phase3"
FIG_DIR = REPO_ROOT / "docs" / "research" / "figures"
VIOLATOR_APPROACH, OPPOSING, CROSSING = "LVL_W", "LVL_E", ("HDT_N", "HDT_S")
VIOLATOR_VTYPE = "moto_violator_B0"
OPPOSING_VPH = {"moto": 4000.0, "car": 700.0}        # dense: no usable gap during the green
OPPOSING_MODERATE_VPH = {"moto": 1300.0, "car": 200.0}  # near the PROXY_D1-D3 LVL_E through volume


@dataclass(frozen=True)
class Scenario:
    violator_vph: float
    overrides: dict  # moto_violator vType attribute -> value (names: sumo.dlr.de/docs/Definition_of_Vehicles,
                     # _Vehicle_Types,_and_Routes.html: minGap default 2.5 m; minGapLat default 0.6 m, SL2015)
    opposing_vph: dict


# order matters: the index seeds each scenario's demand rng, append new scenarios at the end
SCENARIOS = {
    "sat": Scenario(1500.0, {}, OPPOSING_VPH),
    "target": Scenario(225.0, {}, OPPOSING_VPH),
    "sat_tight": Scenario(1500.0, {"minGap": "1.0", "minGapLat": "0.3"}, OPPOSING_VPH),
    "target_modopp": Scenario(225.0, {}, OPPOSING_MODERATE_VPH),
    "sat_mg18": Scenario(1500.0, {"minGap": "1.8"}, OPPOSING_VPH),
}
LATERAL_FIGURE_SCENARIOS = ("sat", "sat_mg18", "sat_tight")  # <= 3 series (dataviz all-pairs cap)
CROSSING_VPH = {"moto": 1200.0, "car": 250.0}
SIDE_BY_SIDE_LONG_M = 2.2   # two waiters are abreast when their fronts are closer than a moto length ...
ROW_LAT_M = 0.9             # ... and their centres are at least a moto width apart laterally
GAPS_JSON = "violator_gaps.json"  # violator minGap / minGapLat as loaded by SUMO, per run dir
CYCLE_S = 120.0             # a box residence longer than one signal cycle = stuck (deadlock check)


# ---------------------------------------------------------------- demand and vTypes


def write_routes(path: Path, scenario: str, seed: int, end_s: float, net_path: Path) -> Path:
    """Poisson arrivals for every stream of the scenario, sorted by departure."""
    routes = {v: k for k, v in movement_table(sumolib.net.readNet(str(net_path))).items()}  # (app, mv) -> (from, to)
    rng = np.random.default_rng([list(SCENARIOS).index(scenario), seed])
    sc = SCENARIOS[scenario]
    streams = [(VIOLATOR_APPROACH, "illegal_l", "moto_violator", sc.violator_vph)]
    streams += [(OPPOSING, "s", vt, q) for vt, q in sc.opposing_vph.items()]
    streams += [(a, "s", vt, q) for a in CROSSING for vt, q in CROSSING_VPH.items()]
    vehicles = []
    for app, mv, vtype, vph in streams:
        t = rng.exponential(3600 / vph)
        while t < end_s:
            vehicles.append((round(t, 2), f"{app}_{mv}_{vtype}_{len(vehicles)}", vtype, routes[(app, mv)]))
            t += rng.exponential(3600 / vph)
    root = etree.Element("routes")
    root.append(etree.Comment(f" experiments/phase3/box_capacity.py: scenario {scenario}, seed {seed} "))
    for depart, vid, vtype, (frm, to) in sorted(vehicles):
        v = etree.SubElement(root, "vehicle", id=vid, depart=f"{depart:.2f}", type=vtype,
                             departLane="best", departSpeed="max")
        etree.SubElement(v, "route", edges=f"{frm} {to}")
    write_xml(root, path)
    return path


def spec_dir_for(scenario: str, root: Path) -> tuple[str, Path]:
    """(spec id, dir with vtypes.add.xml): B0 itself, or a copy of B0 with the scenario's violator overrides."""
    overrides = SCENARIOS[scenario].overrides
    if not overrides:
        return "B0", COMPILED_DIR / "B0"
    tree = etree.parse(str(COMPILED_DIR / "B0" / "vtypes.add.xml"))
    (vt,) = [e for e in tree.getroot().iter("vType") if e.get("id") == VIOLATOR_VTYPE]
    for k, v in overrides.items():
        vt.set(k, v)
    spec_id = f"P3_{scenario}"
    out = root / "specs" / spec_id / "vtypes.add.xml"
    tree.getroot().insert(0, etree.Comment(f" B0 with {VIOLATOR_VTYPE} overrides {overrides} (Phase 3 sensitivity) "))
    write_xml(tree.getroot(), out)
    return spec_id, out.parent


# ---------------------------------------------------------------- per-step TraCI observer


@dataclass
class BoxLogger:
    """Per-step observer (no intervention): box occupancy, link states, upstream queue, teleports, collisions."""

    backend: object
    tls_id: str
    box_lanes: list[str]
    upstream_lane: str
    box: list = field(default_factory=list)
    tls: list = field(default_factory=list)
    events: list = field(default_factory=list)
    violator_gap_lat: dict = field(default_factory=dict)
    _last_state: str | None = None

    def on_step(self, t: float) -> None:
        b = self.backend
        t = round(t, 2)
        if not self.violator_gap_lat:  # check the vType attributes SUMO actually loaded
            self.violator_gap_lat = {"minGap": b.vehicletype.getMinGap(VIOLATOR_VTYPE),
                                     "minGapLat": b.vehicletype.getMinGapLat(VIOLATOR_VTYPE)}
        for lane in self.box_lanes:
            for v in b.lane.getLastStepVehicleIDs(lane):
                self.box.append((t, v, lane, b.vehicle.getLanePosition(v), b.vehicle.getLateralLanePosition(v),
                                 b.vehicle.getSpeed(v), b.vehicle.getWaitingTime(v)))
        state = b.trafficlight.getRedYellowGreenState(self.tls_id)
        if state != self._last_state:
            self.tls.append((t, state))
            self._last_state = state
        self.events.append((t, "upstream_halting", b.lane.getLastStepHaltingNumber(self.upstream_lane), ""))
        for v in b.simulation.getStartingTeleportIDList():
            self.events.append((t, "teleport", 1, v))
        for v in b.simulation.getCollidingVehiclesIDList():
            self.events.append((t, "colliding", 1, v))

    def write(self, run_dir: Path) -> None:
        pd.DataFrame(self.box, columns=["t", "veh", "lane", "pos", "posLat", "speed", "waiting"]).to_csv(
            run_dir / "box_steps.csv", index=False, lineterminator="\n")
        pd.DataFrame(self.tls, columns=["t", "state"]).to_csv(run_dir / "tls_steps.csv", index=False,
                                                              lineterminator="\n")
        pd.DataFrame(self.events, columns=["t", "kind", "value", "veh"]).to_csv(
            run_dir / "events.csv", index=False, lineterminator="\n")
        (run_dir / GAPS_JSON).write_text(json.dumps(self.violator_gap_lat), encoding="utf-8")


def loaded_violator_gaps(net_path: Path, spec_dir: Path) -> dict:
    """minGap / minGapLat of the violator vType as SUMO loads them from `spec_dir` (libsumo, no step simulated);
    used by --reanalyse for runs that have no GAPS_JSON."""
    import libsumo
    libsumo.start([sumolib.checkBinary("sumo"), "-n", str(net_path), "-a", str(spec_dir / "vtypes.add.xml"),
                   "--no-step-log", "true"])
    try:
        return {"minGap": libsumo.vehicletype.getMinGap(VIOLATOR_VTYPE),
                "minGapLat": libsumo.vehicletype.getMinGapLat(VIOLATOR_VTYPE)}
    finally:
        libsumo.close()


# ---------------------------------------------------------------- analysis


@dataclass
class Links:
    opposing_s: int     # a straight link of the opposing approach (LVL_E)
    crossing_s: int     # a straight link of a crossing approach (HDT_S)


def link_indices(net_path: Path) -> Links:
    net = sumolib.net.readNet(str(net_path), withPrograms=True)
    geo = junction_geometry(net_path)
    first = {}
    for in_lane, out_lane, idx in sorted(target_tls(net).getConnections(), key=lambda c: c[2]):
        first.setdefault(geo.movements[(in_lane.getEdge().getID(), out_lane.getEdge().getID())], idx)
    return Links(first[(OPPOSING, "s")], first[(CROSSING[1], "s")])


def box_lane_chain(net_path: Path) -> list[str]:
    geo = junction_geometry(net_path)
    lanes = [ln for ln, a in geo.box_lanes.items() if a == VIOLATOR_APPROACH]
    return sorted(lanes, key=lambda ln: geo.internal[ln][1])  # by offset past the stop line


def blocked_crossing_lanes(net_path: Path, lanes: list[str]) -> list[str]:
    """Inbound crossing-approach lanes whose internal lane passes over the waiting point (centre line within
    half its width): the lanes a waiter physically sits on at the crossing road's green onset."""
    net = sumolib.net.readNet(str(net_path), withInternal=True)
    point = net.getLane(lanes[0]).getShape()[-1]
    out = []
    for e in sorted(approach_edges(net)[a] for a in CROSSING):
        for lane in net.getEdge(e).getLanes():
            for c in lane.getOutgoing():
                via = net.getLane(c.getViaLaneID())
                if sumolib.geomhelper.distancePointToPolygon(point, via.getShape()) <= via.getWidth() / 2:
                    out.append(lane.getID())
    return sorted(set(out))


def transitions(tls: pd.DataFrame, link: int, frm: str, to: str) -> np.ndarray:
    s = tls["state"].str[link]
    prev = s.shift()
    return tls.loc[prev.isin(list(frm)) & s.isin(list(to)), "t"].to_numpy(dtype=float)


def opposing_green(tls: pd.DataFrame, link: int) -> tuple[np.ndarray, np.ndarray]:
    """(starts, ends) of the opposing through green; a green at the first record starts there."""
    on, off = transitions(tls, link, "yr", "G"), transitions(tls, link, "G", "y")
    if tls["state"].iloc[0][link] == "G":
        on = np.r_[tls["t"].iloc[0], on]
    return on, off


def n_abreast(w: pd.DataFrame) -> int:
    """Waiters with a neighbour abreast (fronts within SIDE_BY_SIDE_LONG_M, centres >= ROW_LAT_M apart)."""
    rows = w[["s", "posLat"]].to_numpy()
    n = 0
    for i, (s, lat) in enumerate(rows):
        o = np.delete(rows, i, axis=0)
        n += bool(len(o) and ((np.abs(o[:, 0] - s) < SIDE_BY_SIDE_LONG_M) & (np.abs(o[:, 1] - lat) >= ROW_LAT_M)).any())
    return n


def ssm_violator_conflicts(path: Path, approach_of_veh) -> pd.DataFrame:
    """PET records of SSM conflicts between an illegal-left vehicle and another vehicle (foe approach, PET s)."""
    rows = []
    if not path.exists():   # R22: SSM is off by default, so no ssm.xml (PET columns stay empty)
        return pd.DataFrame(rows, columns=["foe_approach", "pet_s", "t"])
    for c in etree.parse(str(path)).getroot().iter("conflict"):
        ids = (c.get("ego"), c.get("foe"))
        viol = [v for v in ids if "illegal_l" in v]
        other = [v for v in ids if "illegal_l" not in v]
        pet = c.find("PET")
        if len(viol) == 1 and pet is not None and float(pet.get("value")) >= 0:
            rows.append((approach_of_veh(other[0]), float(pet.get("value")), float(pet.get("time"))))
    return pd.DataFrame(rows, columns=["foe_approach", "pet_s", "t"]).drop_duplicates()


def analyse(run_dir: Path, net_path: Path, lanes: list[str]) -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    """(seed summary, per-cycle table, waiter positions at the opposing green ends)."""
    links = link_indices(net_path)
    net = sumolib.net.readNet(str(net_path), withInternal=True)
    offset, acc = {}, 0.0
    for lane in lanes:
        offset[lane] = acc
        acc += net.getLane(lane).getLength()
    wait_point = net.getLane(lanes[0]).getLength()  # end of the first box lane = the internal junction
    box = pd.read_csv(run_dir / "box_steps.csv")
    tls = pd.read_csv(run_dir / "tls_steps.csv", dtype={"state": str})
    ev = pd.read_csv(run_dir / "events.csv")
    box["s"] = box["lane"].map(offset) + box["pos"]          # front: distance along the box chain from the stop line
    box["halting"] = box["speed"] < HALT_SPEED_MPS
    opp_on, opp_off = opposing_green(tls, links.opposing_s)
    cross_on = transitions(tls, links.crossing_s, "yr", "G")
    in_green = np.zeros(len(box), dtype=bool)
    for a in opp_on:
        b = opp_off[opp_off > a].min() if (opp_off > a).any() else np.inf
        in_green |= ((box["t"] >= a) & (box["t"] < b)).to_numpy()
    g = box[in_green].groupby("t").agg(n_halt=("halting", "sum"), n_first=("lane", lambda x: (x == lanes[0]).sum()))
    per_t = box.groupby("t")["veh"].nunique()
    first_t, last_t = box.groupby("veh")["t"].min(), box.groupby("veh")["t"].max()
    upstream = ev[ev["kind"] == "upstream_halting"].set_index("t")["value"]
    sim_end = float(upstream.index.max())
    cr = pd.read_csv(run_dir / "observed_schema" / "stopline_crossings.csv")
    cr_cross = np.sort(cr.loc[cr["approach"].isin(CROSSING), "t"].to_numpy(dtype=float))
    entries, _ = read_loop_crossings(run_dir / "detectors.xml")
    blocked = blocked_crossing_lanes(net_path, lanes)
    cr_blocked = np.sort(entries.loc[entries["lane"].isin(blocked), "t"].to_numpy(dtype=float))
    cycles, waiters = [], []
    for k, te in enumerate(opp_off):
        at = box[(box["t"] == round(te, 2)) & box["halting"]]
        vs = list(at["veh"])
        exits = last_t[vs] + 0.1  # first step off the box lanes
        done = exits[last_t[vs] < sim_end]
        on = cross_on[cross_on > te].min() if (cross_on > te).any() else np.nan
        start = opp_on[opp_on < te].max() if (opp_on < te).any() else -np.inf
        early = int(((first_t >= start) & (first_t < te) & (last_t + 0.1 < te)).sum())
        after = cr_cross[cr_cross >= on] if not np.isnan(on) else np.array([])
        after_b = cr_blocked[cr_blocked >= on] if not np.isnan(on) else np.array([])
        cycles.append({
            "cycle": k, "t_opp_green_end": te, "n_waiting": len(vs),
            "n_waiting_before_wait_point": int((at["s"] <= wait_point).sum()),
            "n_abreast": n_abreast(at),
            "lat_span_m": float(at["posLat"].max() - at["posLat"].min()) if len(at) else 0.0,
            "leader_gap_to_wait_point_m": float(wait_point - at["s"].max()) if len(at) else np.nan,
            "upstream_halting_lane2": int(upstream.get(round(te, 2), 0)),
            "n_early_leavers": early,
            "first_exit_after_end_s": float(done.min() - te) if len(done) else np.nan,
            "last_exit_after_end_s": float(done.max() - te) if len(vs) and len(done) == len(vs) else np.nan,
            "crossing_onset_after_end_s": float(on - te) if not np.isnan(on) else np.nan,
            "n_in_box_at_crossing_onset": int(sum(1 for v in vs if not np.isnan(on) and last_t[v] + 0.1 > on)),
            "crossing_first_crossing_delay_s": float(after.min() - on) if len(after) else np.nan,
            "blocked_lane_first_crossing_delay_s": float(after_b.min() - on) if len(after_b) else np.nan,
        })
        waiters += [(k, r.veh, r.lane, r.s, r.posLat) for r in at.itertuples()]
    cyc = pd.DataFrame(cycles)
    residence = (last_t - first_t)[last_t < sim_end]
    approach_of = lambda v: v.split("_")[0] + "_" + v.split("_")[1]
    ssm = ssm_violator_conflicts(run_dir / "ssm.xml", approach_of)
    log = (run_dir / "sumo.log").read_text(encoding="utf-8", errors="replace")
    ssm_overlap = len({tuple(sorted(m)) for m in re.findall(r"vehicle '([^']*illegal_l[^']*)' detected collision with "
                                                             r"vehicle '([^']*)'", log)})
    opp_pet = ssm.loc[ssm["foe_approach"] == OPPOSING, "pet_s"]
    cross_pet = ssm.loc[ssm["foe_approach"].isin(CROSSING), "pet_s"]
    summary = {
        "max_halting_in_box_opp_green": int(g["n_halt"].max()) if len(g) else 0,
        "max_before_wait_point_opp_green": int(g["n_first"].max()) if len(g) else 0,
        "max_on_box_lanes": int(per_t.max()) if len(per_t) else 0,
        "n_cycles": len(cyc),
        "mean_waiting_at_end": float(cyc["n_waiting"].mean()),
        "max_waiting_at_end": int(cyc["n_waiting"].max()),
        "max_abreast": int(cyc["n_abreast"].max()),
        "max_lat_span_m": float(cyc["lat_span_m"].max()),
        "max_leader_gap_to_wait_point_m": float(cyc["leader_gap_to_wait_point_m"].max()),
        "mean_early_leavers": float(cyc["n_early_leavers"].mean()),
        "mean_first_exit_s": float(cyc["first_exit_after_end_s"].mean()),
        "mean_last_exit_s": float(cyc["last_exit_after_end_s"].mean()),
        "max_last_exit_s": float(cyc["last_exit_after_end_s"].max()),
        "cycles_not_clear_at_crossing_onset": int((cyc["n_in_box_at_crossing_onset"] > 0).sum()),
        "mean_in_box_at_crossing_onset": float(cyc["n_in_box_at_crossing_onset"].mean()),
        "mean_crossing_first_delay_s": float(cyc["crossing_first_crossing_delay_s"].mean()),
        "blocked_crossing_lanes": " ".join(blocked),
        "mean_blocked_lane_first_delay_s": float(cyc["blocked_lane_first_crossing_delay_s"].mean()),
        "max_box_residence_s": float(residence.max()) if len(residence) else np.nan,
        "n_stuck_over_cycle": int((residence > CYCLE_S).sum() + ((last_t >= sim_end) & (sim_end - first_t > CYCLE_S)).sum()),
        "n_teleports_step_log": int((ev["kind"] == "teleport").sum()),
        "n_pet_vs_opposing": len(opp_pet), "min_pet_vs_opposing_s": float(opp_pet.min()) if len(opp_pet) else np.nan,
        "n_pet_vs_crossing": len(cross_pet),
        "median_pet_vs_crossing_s": float(cross_pet.median()) if len(cross_pet) else np.nan,
        "n_ssm_overlap_pairs_violator": ssm_overlap,
    }
    return summary, cyc, pd.DataFrame(waiters, columns=["cycle", "veh", "lane", "s", "posLat"])


# ---------------------------------------------------------------- one run


def run_one(scenario: str, seed: int, end_s: float, net_path: Path, tag: str, reanalyse: bool = False) -> dict:
    """Simulate one scenario x seed and summarise it; with `reanalyse`, only re-read the finished run (violator
    minGap / minGapLat from its GAPS_JSON, or queried from SUMO for runs written before that file existed)."""
    root = OUT_ROOT / tag
    spec_id, spec_dir = spec_dir_for(scenario, root)
    if reanalyse:
        run_dir = root / f"{spec_id}__PHASE3_{scenario}" / f"seed_{seed:02d}"
        gaps_file = run_dir / GAPS_JSON
        gaps = (json.loads(gaps_file.read_text(encoding="utf-8")) if gaps_file.is_file()
                else loaded_violator_gaps(net_path, spec_dir))
        return _summarise(scenario, seed, run_dir, net_path, gaps)
    routes = write_routes(root / "routes" / f"{scenario}_seed{seed:02d}.rou.xml", scenario, seed, end_s, net_path)
    day = f"PHASE3_{scenario}"
    inputs = RunInputs(spec_id, day, load_site(SITE), net_path, routes, spec_dir)
    lanes = box_lane_chain(net_path)
    upstream = f"{approach_edges(sumolib.net.readNet(str(net_path)))[VIOLATOR_APPROACH]}_2"
    tls_id = target_tls(sumolib.net.readNet(str(net_path), withPrograms=True)).getID()
    holder: list[BoxLogger] = []

    def factory(backend, _inputs, _run_dir):
        holder.append(BoxLogger(backend, tls_id, lanes, upstream))
        return holder[0]

    res = run(spec_id, day, seed, sim_end_s=end_s, runs_root=root, inputs=inputs, controller_factory=factory)
    holder[0].write(res.run_dir)
    return _summarise(scenario, seed, res.run_dir, net_path, holder[0].violator_gap_lat)


def _summarise(scenario: str, seed: int, run_dir: Path, net_path: Path, gaps: dict) -> dict:
    summary, cyc, waiters = analyse(run_dir, net_path, box_lane_chain(net_path))
    cyc.to_csv(run_dir / "cycles.csv", index=False, lineterminator="\n")
    waiters.to_csv(run_dir / "waiters.csv", index=False, lineterminator="\n")
    bq = pd.read_csv(run_dir / "observed_schema" / "box_queue.csv")
    m = json.loads((run_dir / MANIFEST_NAME).read_text(encoding="utf-8"))
    return {"scenario": scenario, "seed": seed, **summary,
            "violator_minGap": gaps["minGap"], "violator_minGapLat": gaps["minGapLat"],
            "schema_mean_n_waiting_in_box": float(bq["n_waiting_in_box"].mean()) if len(bq) else np.nan,
            "schema_max_n_waiting_in_box": int(bq["n_waiting_in_box"].max()) if len(bq) else 0,
            "manifest_teleports": m["n_teleports"], "manifest_teleports_noncollision": m["n_teleports_noncollision"],
            "manifest_collisions": m["n_collisions"], "insertion_backlog_end": m["insertion_backlog"],
            "run_dir": run_dir.relative_to(REPO_ROOT).as_posix()}


def collisions_with_violators(rows: pd.DataFrame) -> int:
    n = 0
    for r in rows["run_dir"]:
        root = etree.parse(str(REPO_ROOT / r / "collisions.xml")).getroot()
        n += sum(1 for c in root.iter("collision") if "illegal_l" in c.get("collider") + c.get("victim"))
    return n


# ---------------------------------------------------------------- target


def target_stats(path: Path = TARGETS, n: int = 200_000) -> dict:
    """M7 target: box entrants ~ NB(mean n_waiting / (1 - early_leave_share), var/mean), waiting = entrants
    thinned by (1 - early_leave_share) (the generator's family); tails by simulation (fixed rng)."""
    m7 = _m7(path)
    mean_w, early, vm = (m7[k]["value"] for k in ("n_waiting_in_box", "early_leave_share", "entrants_var_to_mean"))
    mean_e = mean_w / (1 - early)
    rng = np.random.default_rng(0)
    entrants = rng.negative_binomial(mean_e / (vm - 1), 1 / vm, n)
    waiting = rng.binomial(entrants, 1 - early)
    q = lambda x, p: float(np.percentile(x, p))
    return {"waiting_mean": mean_w, "waiting_p90": q(waiting, 90), "waiting_p95": q(waiting, 95),
            "entrants_mean": mean_e, "entrants_p90": q(entrants, 90)}


def _m7(path: Path) -> dict:
    stack = [yaml.safe_load(path.read_text(encoding="utf-8"))]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            if "M7_illegal_left" in node:
                return node["M7_illegal_left"]
            stack += list(node.values())
    raise KeyError(f"{path}: no M7_illegal_left section")


# ---------------------------------------------------------------- figures

SERIES = ("#2a78d6", "#eb6834", "#1baf7a")  # dataviz reference palette, categorical slots 1-3 (light)
INK, MUTED, GRID, SHADE = "#0b0b0b", "#52514e", "#e4e3df", "#eeeeec"


def _style(ax):
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(MUTED)
    ax.tick_params(colors=MUTED, labelsize=8)


def _net_of(run_dir: Path) -> Path:
    opts = {el.tag: el.get("value") for sec in etree.parse(str(run_dir / "run.sumocfg")).getroot()
            for el in sec if isinstance(el.tag, str)}
    return Path(opts["net-file"])


def figure_occupancy(rows: pd.DataFrame, tgt: dict, out: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    scen = list(rows["scenario"].unique())
    fig, axes = plt.subplots(len(scen), 1, figsize=(8, 2.1 * len(scen)), sharex=True, sharey=True)
    axes = np.atleast_1d(axes)
    for ax, sc in zip(axes, scen):
        first = rows[rows["scenario"] == sc].iloc[0]
        rd = REPO_ROOT / first["run_dir"]
        box = pd.read_csv(rd / "box_steps.csv")
        tls = pd.read_csv(rd / "tls_steps.csv", dtype={"state": str})
        on, off = opposing_green(tls, link_indices(_net_of(rd)).opposing_s)
        for a in on:
            ax.axvspan(a, off[off > a].min() if (off > a).any() else box["t"].max(), color=SHADE, linewidth=0)
        box["halt"] = box["speed"] < HALT_SPEED_MPS
        ts = box.groupby("t").agg(n=("veh", "nunique"), h=("halt", "sum"))
        ts = ts.reindex(np.round(np.arange(0, box["t"].max() + 0.05, 0.1), 2), fill_value=0)
        ax.plot(ts.index, ts["n"], color=SERIES[0], linewidth=1.2, label="on box lanes")
        ax.plot(ts.index, ts["h"], color=SERIES[1], linewidth=1.2, label="halting on box lanes")
        for y, name, ls in ((tgt["waiting_mean"], "target mean", "--"), (tgt["waiting_p90"], "target p90", ":")):
            ax.axhline(y, color=MUTED, linewidth=1, linestyle=ls)
            ax.text(ts.index.max(), y, f" {name}", va="center", fontsize=7, color=MUTED)
        opp = sum(SCENARIOS[sc].opposing_vph.values())
        ax.set_title(f"{sc}: {SCENARIOS[sc].violator_vph:.0f} violators/h, opposing {opp:.0f} veh/h, seed "
                     f"{first['seed']}  (grey: opposing LVL_E through green)", fontsize=9, color=INK, loc="left")
        ax.set_ylabel("vehicles", fontsize=8, color=MUTED)
        _style(ax)
    axes[0].legend(fontsize=7, frameon=False, loc="upper left", ncol=2)
    axes[-1].set_xlabel("simulation time (s)", fontsize=8, color=MUTED)
    fig.tight_layout()
    fig.savefig(out, dpi=100)
    plt.close(fig)


def figure_lateral(rows: pd.DataFrame, out: Path, net_path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    lane = sumolib.net.readNet(str(net_path), withInternal=True).getLane(box_lane_chain(net_path)[0])
    fig, ax = plt.subplots(figsize=(8, 2.8))
    for i, sc in enumerate(s for s in LATERAL_FIGURE_SCENARIOS if s in set(rows["scenario"])):
        w = pd.concat([pd.read_csv(REPO_ROOT / r / "waiters.csv") for r in rows[rows["scenario"] == sc]["run_dir"]])
        ax.scatter(w["s"], w["posLat"], s=22, color=SERIES[i % len(SERIES)], alpha=0.55, edgecolors="white",
                   linewidths=0.5, label=f"{sc} ({len(w)} waiter snapshots)")
    half = lane.getWidth() / 2
    for y in (-half, half):
        ax.axhline(y, color=MUTED, linewidth=0.8)
    ax.axvline(lane.getLength(), color=INK, linewidth=1, linestyle="--")
    ax.text(lane.getLength(), half + 0.12, "waiting point (internal junction) ", fontsize=7, color=INK, ha="right")
    ax.set_xlabel("front position past the LVL_W stop line along the left-turn path (m)", fontsize=8, color=MUTED)
    ax.set_ylabel("posLat (m)", fontsize=8, color=MUTED)
    ax.set_ylim(-half - 0.4, half + 1.2)
    ax.set_title("Halting illegal lefts at each opposing green end, all seeds (lines: edges of the 3.2 m "
                 "internal lane)", fontsize=9, color=INK, loc="left")
    ax.legend(fontsize=7, frameon=False, loc="upper left", ncol=3)
    _style(ax)
    fig.tight_layout()
    fig.savefig(out, dpi=100)
    plt.close(fig)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--scenarios", nargs="+", default=list(SCENARIOS), choices=list(SCENARIOS))
    ap.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3, 4, 5])
    ap.add_argument("--end", type=float, default=900.0)
    ap.add_argument("--net", type=Path, default=NET)
    ap.add_argument("--tag", default="native", help="output sub-directory and results file suffix")
    ap.add_argument("--nproc", type=int, default=1, help="parallel runs (one SUMO per spawned process)")
    ap.add_argument("--reanalyse", action="store_true", help="re-read finished runs of --tag, no simulation")
    ap.add_argument("--no-figures", action="store_true")
    args = ap.parse_args(argv)
    net = args.net.resolve()
    jobs = [(sc, s, args.end, net, args.tag, args.reanalyse) for sc in args.scenarios for s in args.seeds]
    if args.nproc > 1 and not args.reanalyse:
        with multiprocessing.get_context("spawn").Pool(args.nproc, maxtasksperchild=1) as pool:
            rows = pd.DataFrame(pool.starmap(run_one, jobs))
    else:
        rows = pd.DataFrame([run_one(*j) for j in jobs])
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"results_{args.tag}.csv"
    if out.is_file():  # keep the rows of scenario x seed pairs not run this time
        old = pd.read_csv(out)
        old = old[~old.set_index(["scenario", "seed"]).index.isin(rows.set_index(["scenario", "seed"]).index)]
        rows = pd.concat([old, rows], ignore_index=True)
    order = {sc: i for i, sc in enumerate(SCENARIOS)}
    rows = rows.sort_values(["scenario", "seed"], key=lambda c: c.map(order) if c.name == "scenario" else c,
                            kind="stable").reset_index(drop=True)
    rows.to_csv(out, index=False, lineterminator="\n", float_format="%.2f")
    tgt = target_stats()
    pd.set_option("display.width", 300)
    pd.set_option("display.max_columns", 100)
    print(rows.drop(columns=["run_dir"]).T.to_string())
    print("collisions involving an illegal-left vehicle:", collisions_with_violators(rows))
    print("target:", tgt)
    if not args.no_figures:
        FIG_DIR.mkdir(parents=True, exist_ok=True)
        figure_occupancy(rows, tgt, FIG_DIR / f"phase3_box_occupancy_{args.tag}.png")
        figure_lateral(rows, FIG_DIR / f"phase3_box_lateral_{args.tag}.png", net)
    return 0


if __name__ == "__main__":
    sys.exit(main())
