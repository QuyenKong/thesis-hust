"""PLAN Phase 3A: behaviour 6 "chan lan re phai lien tuc" on a toy approach (not the main net).

    .venv/bin/python experiments/phase3a/right_lane_blocking.py [--seeds 1 2 3] [--end 900] [--nproc 8]
        [--only probe|main|merge]

Toy (built here, in experiments/phase3a/net/): one 3-lane approach (3.5 m lanes) W -> C, a TLS cross point C,
exits outE (2 lanes, straight) and outS (1 lane, right). Lane 0 = continuous right-turn lane (right link always
'g', i.e. never signal-stopped; nothing conflicts with it in the toy), lanes 1-2 straight with a fixed 120 s cycle
64 G / 4 y / 52 r. The approach is split: `up` (400 m) + `bol` (the bollard stretch, L m). On `bol`,
lane 0 changeLeft="emergency" and lane 1 changeRight="emergency" (only class emergency, absent here, may cross
the separator; netconvert silently drops changeLeft="ignoring", so "emergency" is used, see report).
Net variant `lock` additionally sets `up` lane 1 changeRight="custom1 custom2 emergency": compliant classes
cannot change from lane 1 into lane 0 upstream, violators can. Variant `open`: no restriction upstream.

ALL numbers below (lengths, flows, shares, trigger threshold, cycle) are EXPERIMENTAL SETTINGS, not field values.

Scenarios (each x demand {heavy, light} x L {30, 60} x seeds; arrivals identical across scenarios for one
(demand, seed); a straight vehicle is a violator iff its uniform draw < share):
- noviol: lock net, violator share 0 (reference for right-turn delay);
- open:   open net, share 0.2, no TraCI (native SL2015);
- lock:   lock net, share 0.2, no TraCI (native SL2015, compliant held out by the net);
- trig:   lock net, share 0.2, TraCI: violators get LOCK_MODE at departure; while the straight queue >= Q_TRIGGER_M
          each violator on up lanes 1-2 within queue+TRIGGER_AHEAD_M of the stop line draws once; with probability
          P_RELEASE it is released: mode 1621 + changeLane(0, HOLD_S) (held in lane 0), and MERGE_ZONE_M before the
          bollard start the request ends (MERGE "expire": changeLane(0, 0)) so SL2015's strategic model merges it;
          a released vehicle that never reached lane 0 by the merge zone has its request dropped ("giveup");
- trigp1: as trig with P_RELEASE = 1 (every eligible violator);
- trigshort: as trig but changeLane(0, CHANGE_DUR_S) only (no hold; SL2015 decides when to go back);
- probe_<mode>: lock net, heavy, L=60, share 0.2, violators get <mode> for their whole trip (finds the minimal
          lane-change-mode bits that keep them out of lane 0);
- --only merge: trigp1 heavy L=60 with MERGE "request1" (changeLane(1, HOLD_S) at the merge zone) vs "expire".
Vehicle types are read from rules/compiled/B0/vtypes.add.xml (SL2015, SUMO defaults; violators custom1/custom2).
Results -> experiments/phase3a/results[_merge].csv (one row per run), lc_events*.csv, interventions*.csv;
per-run SUMO output (routes, tripinfo, log) in experiments/phase3a/runs/<run>/.
"""

from __future__ import annotations

import argparse
import multiprocessing
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd
import sumolib

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
VTYPES = REPO / "rules" / "compiled" / "B0" / "vtypes.add.xml"
STEP = 0.1
UP_LEN = 400.0
CYCLE = [(64, "gGG"), (4, "gyy"), (52, "grr")]
DEMAND = {  # veh/h: (straight moto, straight car, right moto, right car)
    "heavy": (4000.0, 650.0, 300.0, 60.0),
    "light": (700.0, 120.0, 300.0, 60.0),
}
SHARE = 0.2
HALT = 0.1               # m/s, = SUMO halting threshold
Q_TRIGGER_M = 50.0       # straight queue that releases violators (experimental)
TRIGGER_AHEAD_M = 60.0   # release violators up to this far behind the queue tail
CHANGE_DUR_S = 3.0
HOLD_S = 600.0           # "until further notice" for the trig hold request
MERGE_ZONE_M = 15.0      # trig: stop holding a violator in lane 0 this far before the bollard start
MERGE = "expire"         # trig merge action, chosen by experiment (see report; alternative "request1")
P_RELEASE = 0.3          # probability that an eligible violator takes the right lane (trig, trigshort)
DEFAULT_MODE = 1621
LOCK_MODE = 1541         # set from the probe result (see report): 1621 minus speedGain (16) minus keepRight (64)
PROBE_MODES = (1621, 1605, 1541, 517)
NEAR_BOLLARD_M = 20.0    # a straight vehicle halting on up_0 within this of the bollard start = blocker
TYPES = {"m": "moto_B0", "c": "car_B0", "vm": "moto_violator_B0", "vc": "car_violator_B0"}


def bin_(name: str) -> str:
    return sumolib.checkBinary(name)


def build_net(L: float, variant: str) -> Path:
    d = HERE / "net"
    d.mkdir(exist_ok=True)
    tag = f"L{int(L)}_{variant}"
    off = 7.5  # netconvert cuts this much of `bol` for junction C (checked below)
    (d / f"{tag}.nod.xml").write_text(
        '<nodes>\n'
        f' <node id="W" x="{-(UP_LEN + L + off)}" y="0"/>\n'
        f' <node id="B" x="{-(L + off)}" y="0" type="priority"/>\n'
        ' <node id="C" x="0" y="0" type="traffic_light"/>\n'
        ' <node id="E" x="300" y="0"/>\n <node id="S" x="0" y="-300"/>\n</nodes>\n')
    up_lane1 = '<lane index="1" changeRight="custom1 custom2 emergency"/>' if variant == "lock" else ""
    (d / f"{tag}.edg.xml").write_text(
        '<edges>\n'
        f' <edge id="up" from="W" to="B" numLanes="3" speed="13.89" width="3.5">{up_lane1}</edge>\n'
        ' <edge id="bol" from="B" to="C" numLanes="3" speed="13.89" width="3.5">\n'
        '  <lane index="0" changeLeft="emergency"/>\n  <lane index="1" changeRight="emergency"/>\n </edge>\n'
        ' <edge id="outE" from="C" to="E" numLanes="2" speed="13.89" width="3.5"/>\n'
        ' <edge id="outS" from="C" to="S" numLanes="1" speed="13.89" width="3.5"/>\n</edges>\n')
    (d / f"{tag}.con.xml").write_text(
        '<connections>\n'
        + "".join(f' <connection from="up" to="bol" fromLane="{i}" toLane="{i}"/>\n' for i in range(3))
        + ' <connection from="bol" to="outS" fromLane="0" toLane="0"/>\n'
          ' <connection from="bol" to="outE" fromLane="1" toLane="0"/>\n'
          ' <connection from="bol" to="outE" fromLane="2" toLane="1"/>\n</connections>\n')
    (d / f"{tag}.tll.xml").write_text(
        '<tlLogics>\n <tlLogic id="C" type="static" programID="0" offset="0">\n'
        + "".join(f'  <phase duration="{t}" state="{s}"/>\n' for t, s in CYCLE) + ' </tlLogic>\n</tlLogics>\n')
    net = d / f"{tag}.net.xml"
    subprocess.run([bin_("netconvert"), "-n", str(d / f"{tag}.nod.xml"), "-e", str(d / f"{tag}.edg.xml"),
                    "-x", str(d / f"{tag}.con.xml"), "-i", str(d / f"{tag}.tll.xml"), "--no-turnarounds",
                    "-o", str(net)], check=True, capture_output=True)
    n = sumolib.net.readNet(str(net))
    assert abs(n.getEdge("bol").getLength() - L) < 0.5, n.getEdge("bol").getLength()
    lanes = ET.parse(net).getroot().iter("lane")
    attrs = {la.get("id"): (la.get("changeLeft"), la.get("changeRight")) for la in lanes}
    assert attrs["bol_0"][0] == "emergency" and attrs["bol_1"][1] == "emergency", attrs
    assert (attrs["up_1"][1] is not None) == (variant == "lock"), attrs
    return net


def write_routes(path: Path, demand: str, seed: int, end: float, share: float) -> None:
    rng = np.random.default_rng([list(DEMAND).index(demand), seed])
    qsm, qsc, qrm, qrc = DEMAND[demand]
    veh = []
    for kind, vph, route in (("m", qsm, "S"), ("c", qsc, "S"), ("m", qrm, "R"), ("c", qrc, "R")):
        t = rng.exponential(3600 / vph)
        while t < end:
            u = rng.uniform()  # drawn for every vehicle so arrivals stay identical across shares
            k = ("v" + kind) if (route == "S" and u < share) else kind
            veh.append((round(t, 1), k, route))
            t += rng.exponential(3600 / vph)
    lines = ['<routes>', ' <route id="S" edges="up bol outE"/>', ' <route id="R" edges="up bol outS"/>']
    for i, (t, k, r) in enumerate(sorted(veh)):
        lines.append(f' <vehicle id="{r}_{k}_{i}" type="{TYPES[k]}" route="{r}" depart="{t:.1f}" '
                     'departLane="best" departSpeed="max"/>')
    path.write_text("\n".join(lines + ["</routes>\n"]))


def is_violator(vid: str) -> bool:
    return vid.split("_")[1] in ("vm", "vc")


def run_one(job: dict) -> dict:
    import libsumo as ts
    sc, demand, L, seed, end = job["scenario"], job["demand"], job["L"], job["seed"], job["end"]
    variant = "open" if sc == "open" else "lock"
    share = 0.0 if sc == "noviol" else SHARE
    merge = job.get("merge", MERGE)
    name = f"{sc}_{demand}_L{int(L)}_s{seed}" + ("" if merge == MERGE else f"_{merge}")
    rd = HERE / "runs" / name
    rd.mkdir(parents=True, exist_ok=True)
    net = HERE / "net" / f"L{int(L)}_{variant}.net.xml"
    write_routes(rd / "routes.rou.xml", demand, seed, end, share)
    ts.start([bin_("sumo"), "-n", str(net), "-a", str(VTYPES), "-r", str(rd / "routes.rou.xml"),
              "--step-length", str(STEP), "--lateral-resolution", "0.4", "--collision.check-junctions", "true",
              "--seed", str(seed), "--end", str(end), "--tripinfo-output", str(rd / "tripinfo.xml"),
              "--no-step-log", "true", "--no-warnings", "false", "--log", str(rd / "sumo.log")])
    probe_mode = int(sc.split("_")[1]) if sc.startswith("probe_") else None
    last = {}              # vid -> (edge, lane index)
    lc, inter = [], []
    triggered, holding, decided = set(), set(), set()
    rng = np.random.default_rng([seed, 7])
    blk_s = rt_blocked_s = 0.0
    blockers, straight_on_bol0, depart_lane0_straight = set(), set(), 0
    n_tele = n_col_lane = n_col_junc = 0
    qmax = 0.0
    bol_len = UP_LEN_eff = None
    t = 0.0
    while t < end - 1e-6:
        ts.simulationStep()
        t = ts.simulation.getTime()
        if bol_len is None:
            bol_len, UP_LEN_eff = ts.lane.getLength("bol_1"), ts.lane.getLength("up_1")
        for v in ts.simulation.getDepartedIDList():
            if v.startswith("S_") and ts.vehicle.getLaneIndex(v) == 0:
                depart_lane0_straight += 1
            if is_violator(v) and (probe_mode is not None or sc.startswith("trig")):
                ts.vehicle.setLaneChangeMode(v, probe_mode if probe_mode is not None else LOCK_MODE)
        n_tele += len(ts.simulation.getStartingTeleportIDList())
        for c in ts.simulation.getCollisions():
            if c.lane.startswith(":"):
                n_col_junc += 1
            else:
                n_col_lane += 1
        # straight queue: farthest halting vehicle on lanes 1-2, distance to the stop line
        q = 0.0
        for lane, base in (("bol_1", 0.0), ("bol_2", 0.0), ("up_1", bol_len), ("up_2", bol_len)):
            ln = bol_len if lane.startswith("bol") else UP_LEN_eff
            for v in ts.lane.getLastStepVehicleIDs(lane):
                if ts.vehicle.getSpeed(v) < HALT:
                    q = max(q, base + ln - ts.vehicle.getLanePosition(v))
        qmax = max(qmax, q)
        # lane-change events on up / bol
        for edge in ("up", "bol"):
            for v in ts.edge.getLastStepVehicleIDs(edge):
                li = ts.vehicle.getLaneIndex(v)
                prev = last.get(v)
                if prev is not None and prev[0] == edge and prev[1] != li:
                    lc.append((t, v, v.split("_")[1], v[0], edge, prev[1], li, round(q, 1),
                               round(ts.vehicle.getLanePosition(v), 1), v in triggered))
                last[v] = (edge, li)
        # blocking on up_0
        up0 = [(v, ts.vehicle.getLanePosition(v), ts.vehicle.getSpeed(v)) for v in ts.lane.getLastStepVehicleIDs("up_0")]
        halted_straight = [p for v, p, s in up0 if v.startswith("S_") and s < HALT]
        for v, p, s in up0:
            if v.startswith("S_") and s < HALT:
                blk_s += STEP
                if p > UP_LEN_eff - NEAR_BOLLARD_M:
                    blockers.add(v)
        if halted_straight:
            front = max(halted_straight)
            rt_blocked_s += STEP * sum(1 for v, p, s in up0 if v.startswith("R_") and s < HALT and p < front)
        for v in ts.lane.getLastStepVehicleIDs("bol_0"):
            if v.startswith("S_"):
                straight_on_bol0.add(v)
        # TraCI trigger (trig: hold in lane 0 until the merge zone; trigshort: 3 s request, then native)
        if sc.startswith("trig") and q >= Q_TRIGGER_M:
            for lane, base in (("up_1", bol_len), ("up_2", bol_len)):
                for v in ts.lane.getLastStepVehicleIDs(lane):
                    if is_violator(v) and v not in decided:
                        dist = base + UP_LEN_eff - ts.vehicle.getLanePosition(v)
                        if dist <= q + TRIGGER_AHEAD_M:
                            decided.add(v)  # one draw per violator
                            if rng.uniform() >= (1.0 if sc == "trigp1" else P_RELEASE):
                                continue
                            ts.vehicle.setLaneChangeMode(v, DEFAULT_MODE)
                            ts.vehicle.changeLane(v, 0, CHANGE_DUR_S if sc == "trigshort" else HOLD_S)
                            triggered.add(v)
                            if sc != "trigshort":
                                holding.add(v)
                            inter.append((t, v, "release", ts.vehicle.getLaneIndex(v), round(q, 1), round(dist, 1)))
        alive = set(ts.vehicle.getIDList()) if holding else set()
        for v in list(holding):
            if v not in alive:
                holding.discard(v)
            elif ts.vehicle.getRoadID(v) != "up" or (ts.vehicle.getLaneIndex(v) != 0 and ts.vehicle.getLanePosition(v)
                                                     >= UP_LEN_eff - MERGE_ZONE_M):
                # never reached lane 0 before the merge zone: drop the hold request (a lane-0 request left active
                # past `up` kept the vehicle stuck on the junction lane until a jam teleport)
                ts.vehicle.changeLane(v, ts.vehicle.getLaneIndex(v), 0.0)
                holding.discard(v)
                inter.append((t, v, "giveup", ts.vehicle.getLaneIndex(v), round(q, 1), 0.0))
            elif ts.vehicle.getLaneIndex(v) == 0 and ts.vehicle.getLanePosition(v) >= UP_LEN_eff - MERGE_ZONE_M:
                if merge == "request1":
                    ts.vehicle.changeLane(v, 1, HOLD_S)
                else:  # "expire": end the TraCI request, the strategic model takes over
                    ts.vehicle.changeLane(v, 0, 0.0)
                holding.discard(v)
                inter.append((t, v, "merge", 0, round(q, 1), round(UP_LEN_eff - ts.vehicle.getLanePosition(v), 1)))
    pending = len(ts.simulation.getPendingVehicles())
    ts.close()

    lcdf = pd.DataFrame(lc, columns=["t", "veh", "kind", "route", "edge", "from", "to", "queue_m", "pos",
                                     "triggered"])
    lcdf.insert(0, "run", name)
    idf = pd.DataFrame(inter, columns=["t", "veh", "action", "lane", "queue_m", "dist_m"])
    idf.insert(0, "run", name)
    # did each triggered violator reach up_0 after the trigger?
    if len(idf):
        reached = set(lcdf[(lcdf.edge == "up") & (lcdf.to == 0) & lcdf.triggered].veh)
        idf["reached_lane0"] = idf.veh.isin(reached) & (idf.action == "release")
    trips = pd.DataFrame([dict(e.attrib) for e in ET.parse(rd / "tripinfo.xml").getroot().iter("tripinfo")])
    trips["depart"] = trips.depart.astype(float)
    trips["timeLoss"] = trips.timeLoss.astype(float)
    win = trips[(trips.depart >= 60) & (trips.depart <= end - 180)]
    rt = win[win.id.str.startswith("R_")].timeLoss
    st = win[win.id.str.startswith("S_")].timeLoss
    into0 = lcdf[(lcdf.edge == "up") & (lcdf.to == 0) & (lcdf.route == "S")]
    n_straight = {k: sum(1 for i in trips.id if i.startswith(f"S_{k}_")) for k in ("m", "c", "vm", "vc")}
    row = dict(run=name, scenario=sc, demand=demand, L=L, seed=seed, end=end, merge=merge,
               queue_max_m=round(qmax, 1),
               n_straight_m=n_straight["m"], n_straight_c=n_straight["c"],
               n_straight_vm=n_straight["vm"], n_straight_vc=n_straight["vc"],
               depart_lane0_straight=depart_lane0_straight)
    for k in ("m", "c", "vm", "vc"):
        sub = into0[into0.kind == k]
        row[f"into0_{k}_veh"] = sub.veh.nunique()
        row[f"into0_{k}_qge{int(Q_TRIGGER_M)}"] = sub[sub.queue_m >= Q_TRIGGER_M].veh.nunique()
    row.update(straight_halt_up0_vs=round(blk_s, 1), blockers_near_bollard=len(blockers),
               blockers_compliant=sum(1 for v in blockers if not is_violator(v)),
               rt_halted_behind_blocker_vs=round(rt_blocked_s, 1),
               straight_on_bol0=len(straight_on_bol0),
               bol_lane_changes=int((lcdf.edge == "bol").sum()),
               rt_n=len(rt), rt_timeloss_mean=round(rt.mean(), 2), rt_timeloss_p90=round(rt.quantile(.9), 2),
               st_timeloss_mean=round(st.mean(), 2),
               teleports=n_tele, collisions_lane=n_col_lane, collisions_junction=n_col_junc,
               pending_at_end=pending, n_triggered=len(triggered),
               trig_reached_lane0=int(idf.reached_lane0.sum()) if len(idf) else 0,
               n_giveup=int((idf.action == "giveup").sum()) if len(idf) else 0)
    return dict(row=row, lc=lcdf, inter=idf)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3])
    ap.add_argument("--end", type=float, default=900.0)
    ap.add_argument("--nproc", type=int, default=8)
    ap.add_argument("--only", choices=["probe", "main", "merge"], default=None)
    a = ap.parse_args(argv)
    for L in (30.0, 60.0):
        for variant in ("open", "lock"):
            build_net(L, variant)
    jobs = []
    if a.only == "merge":  # merge action at the end of the hold: TraCI request to lane 1 vs. let the request expire
        jobs += [dict(scenario="trigp1", demand="heavy", L=60.0, seed=s, end=a.end, merge=m)
                 for m in ("request1", "expire") for s in a.seeds]
    if a.only in (None, "probe"):
        jobs += [dict(scenario=f"probe_{m}", demand="heavy", L=60.0, seed=s, end=a.end)
                 for m in PROBE_MODES for s in a.seeds]
    if a.only in (None, "main"):
        jobs += [dict(scenario=sc, demand=d, L=L, seed=s, end=a.end)
                 for sc in ("noviol", "open", "lock", "trig", "trigp1", "trigshort") for d in DEMAND for L in (30.0, 60.0)
                 for s in a.seeds]
    with multiprocessing.get_context("spawn").Pool(a.nproc, maxtasksperchild=1) as pool:
        out = pool.map(run_one, jobs)
    tag = "" if a.only is None else f"_{a.only}"
    pd.DataFrame([o["row"] for o in out]).to_csv(HERE / f"results{tag}.csv", index=False, lineterminator="\n")
    pd.concat([o["lc"] for o in out]).to_csv(HERE / f"lc_events{tag}.csv", index=False, lineterminator="\n")
    inter = [o["inter"] for o in out if len(o["inter"])]
    if inter:
        pd.concat(inter).to_csv(HERE / f"interventions{tag}.csv", index=False, lineterminator="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
