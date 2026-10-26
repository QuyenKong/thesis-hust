"""PLAN Phase 3C: can SUMO 1.27.0 reproduce "ride on the opposite lane alongside a standing red queue and cut back
in before the hard median"? Toy scenario only (never the site net).

    .venv/bin/python experiments/phase3c/wrong_way.py [--seeds 1 2 3] [--end 600] [--nproc 6]

Toy net (built by netconvert from plain XML written here into experiments/phase3c/toy/<net>/):

    A ---- up (400 m, opposite lanes are <neigh>) ---- B -- med (M m, no <neigh> = hard median) -- J(TLS) -- out --> E
    A <--- up_r --------------------------------------- B <- med_r -------------------------------- J <-- out_r -- E
                                                                                                    N/S cross street

M = MEDIAN_M (an experimental setting, not a field value). Lane width 3.2 m (setting). Signal 120 s: WE/EW green
42 s + yellow 3 s, NS green 72 s + yellow 3 s, so the direction of interest (WE) has a ~78 s red queue.
Demand per lane of WE: 200 car/h + 400 moto/h + 150 custom1/h; opposing EW through 150 car + 300 moto per lane,
plus N->W right 200/h and S->W left 100/h (keeps the opposite lane busy during the WE red); NS through 300/h each.
Poisson arrivals (period=exp), randomness only from --seed.

Nets: `n1` (1 lane per direction, opposite neighbours), `n2` (2 lanes per direction, innermost lanes neighbours;
docs: only emergency vehicles overtake via the opposite lane from a multi-lane edge), `v1` (1 lane + a virtual
left lane on `up` allowed for custom1 only, merging into med_0 at B, no <neigh>).

Cases (CASES): lane-change model x net x sublane (--lateral-resolution 0.4) or not; all runs
--collision.check-junctions (R28), step 0.1 s. Observer (no intervention) logs every opposite-lane episode (vehicle
whose current edge is not on its route: up_r or med_r) and every custom1 use of the virtual lane up_1.
Gain = depart rank - stop-line crossing rank within the WE stream (positive = overtook).

Custom1 (`viol`) variants: default LC attributes, lcOpposite=100, lcSpeedGain=100, or both ("eager"); car and
moto keep the defaults. LC2013 with --lateral-resolution is refused by SUMO; that is recorded as an `error` row.

Part 4 (always run): TraCI-commanded move to the opposite lane: a standing custom1 in the leftmost lane of the red
queue gets vehicle.changeLane(id, numLanes, 20) (index one past the leftmost forward lane) or
changeSublane(id, 3.2); logs whether it reaches up_r, where it comes back, and its collisions within 60 s.

Outputs: experiments/phase3c/results.csv (one row per run), episodes.csv (one row per opposite / virtual episode),
traci_cmd.csv; raw SUMO output in experiments/phase3c/out/ (git-ignored). Runs take ~20 s on 8 processes.
"""
from __future__ import annotations

import argparse
import csv
import subprocess
from multiprocessing import Pool
from pathlib import Path

import sumolib

HERE = Path(__file__).resolve().parent
TOY = HERE / "toy"
MEDIAN_M = 30.0
UP_LEN = 400.0  # shortcut: n1/n2 lane length; v1 lanes are 396 m (merge junction shape), so v1 positions are off by 4 m
LANE_W = 3.2
STEP = 0.1
HALT = 5 / 3.6
NETS = ("n1", "n2", "v1")
# (case id, net, laneChangeModel, sublane, custom1 extra vType attributes)
CASES = [
    ("LC2013_n1_nosub", "n1", "LC2013", False, ""),
    ("LC2013_n1_sub", "n1", "LC2013", True, ""),
    ("SL2015_n1_nosub", "n1", "SL2015", False, ""),
    ("SL2015_n1_sub", "n1", "SL2015", True, ""),
    ("LC2013_n1_nosub_eager", "n1", "LC2013", False, 'lcOpposite="100" lcSpeedGain="100"'),
    ("SL2015_n1_sub_eager", "n1", "SL2015", True, 'lcOpposite="100" lcSpeedGain="100"'),
    ("LC2013_n1_nosub_opp100", "n1", "LC2013", False, 'lcOpposite="100"'),
    ("SL2015_n1_sub_opp100", "n1", "SL2015", True, 'lcOpposite="100"'),
    ("SL2015_n1_sub_sg100", "n1", "SL2015", True, 'lcSpeedGain="100"'),
    ("SL2015_n1_nosub_eager", "n1", "SL2015", False, 'lcOpposite="100" lcSpeedGain="100"'),
    ("LC2013_n2_nosub_eager", "n2", "LC2013", False, 'lcOpposite="100" lcSpeedGain="100"'),
    ("SL2015_n2_sub_eager", "n2", "SL2015", True, 'lcOpposite="100" lcSpeedGain="100"'),
    ("LC2013_n2_nosub", "n2", "LC2013", False, ""),
    ("SL2015_n2_sub", "n2", "SL2015", True, ""),
    ("SL2015_v1_nosub", "v1", "SL2015", False, ""),
    ("SL2015_v1_sub", "v1", "SL2015", True, ""),
]
MOTO = ('guiShape="motorcycle" length="2.2" width="0.9" height="1.5" minGap="2.5" accel="6" decel="10" '
        'emergencyDecel="10" maxSpeed="55.55555555555556" speedDev="0.1"')  # B0 moto_violator copy


def build_net(net: str) -> Path:
    d = TOY / net
    d.mkdir(parents=True, exist_ok=True)
    lanes = 2 if net == "n2" else 1
    up_lanes = lanes + 1 if net == "v1" else lanes
    (d / "toy.nod.xml").write_text(f"""<nodes>
  <node id="A" x="{-MEDIAN_M - UP_LEN}" y="0" type="priority"/>
  <node id="B" x="{-MEDIAN_M}" y="0" type="priority"/>
  <node id="J" x="0" y="0" type="traffic_light"/>
  <node id="E" x="200" y="0" type="priority"/>
  <node id="N" x="0" y="200" type="priority"/>
  <node id="S" x="0" y="-200" type="priority"/>
</nodes>
""")
    neigh = net in ("n1", "n2")
    up_extra = ""
    if net == "v1":  # virtual contraflow lane: leftmost lane of `up`, custom1 only
        up_extra = f'\n    <lane index="{lanes}" allow="custom1"/>'
    e = lambda i, f, t, n=lanes, body="": (  # noqa: E731
        f'  <edge id="{i}" from="{f}" to="{t}" numLanes="{n}" speed="13.89" width="{LANE_W}">{body}\n  </edge>\n')
    edges = "<edges>\n"
    edges += e("up", "A", "B", up_lanes, up_extra + (f'\n    <neigh lane="up_r_{lanes - 1}"/>' if neigh else ""))
    edges += e("up_r", "B", "A", lanes, f'\n    <neigh lane="up_{lanes - 1}"/>' if neigh else "")
    for i, f, t in [("med", "B", "J"), ("med_r", "J", "B"), ("out", "J", "E"), ("out_r", "E", "J"),
                    ("n_in", "N", "J"), ("n_out", "J", "N"), ("s_in", "S", "J"), ("s_out", "J", "S")]:
        edges += e(i, f, t)
    (d / "toy.edg.xml").write_text(edges + "</edges>\n")
    con = "<connections>\n"
    for i in range(lanes):
        con += f'  <connection from="up" to="med" fromLane="{i}" toLane="{i}"/>\n'
    if net == "v1":
        con += f'  <connection from="up" to="med" fromLane="{lanes}" toLane="{lanes - 1}"/>\n'
    (d / "toy.con.xml").write_text(con + "</connections>\n")
    out = d / "toy.net.xml"
    subprocess.run([sumolib.checkBinary("netconvert"), "-n", d / "toy.nod.xml", "-e", d / "toy.edg.xml",
                    "-x", d / "toy.con.xml", "-o", out, "--no-turnarounds", "true", "--offset.disable-normalization",
                    "true", "--opposites.guess.fix-lengths", "true", "--no-warnings", "false"], check=True,
                   capture_output=True)
    # signal program: phase 0 for links coming from med / out_r, phase 2 for n_in / s_in
    n = sumolib.net.readNet(str(out))
    tls = n.getTLS("J")
    links = {}  # link index -> (incoming edge, direction); straight = G, turns = g (permissive)
    for c in tls.getConnections():
        d_ = next(x.getDirection() for x in c[0].getOutgoing() if x.getToLane() == c[1])
        links[c[2]] = (c[0].getEdge().getID(), d_)
    def st(group, green):
        return "".join((("G" if d_ == "s" else "g") if green else "y") if e_ in group else "r"
                       for e_, d_ in (links[i] for i in sorted(links)))
    we, ns = {"med", "out_r"}, {"n_in", "s_in"}
    phases = [(42, st(we, True)), (3, st(we, False)), (72, st(ns, True)), (3, st(ns, False))]
    (d / "tls.add.xml").write_text('<additional>\n  <tlLogic id="J" type="static" programID="p3c" offset="0">\n'
                                   + "".join(f'    <phase duration="{du}" state="{s}"/>\n' for du, s in phases)
                                   + "  </tlLogic>\n</additional>\n")
    return out


def write_routes(path: Path, net: str, lcm: str, viol_extra: str) -> None:
    lanes = 2 if net == "n2" else 1
    f = []
    def flow(i, typ, rate, route):
        f.append(f'  <flow id="{i}" type="{typ}" route="{route}" begin="0" end="7200" period="exp({rate / 3600})" '
                 f'departLane="best" departSpeed="max"/>')
    for typ, r in [("car", 200), ("moto", 400), ("viol", 150)]:
        flow(f"we_{typ}", typ, r * lanes, "we")
    for typ, r in [("car", 150), ("moto", 300)]:
        flow(f"ew_{typ}", typ, r * lanes, "ew")
    flow("nw_moto", "moto", 200, "nw")
    flow("sw_moto", "moto", 100, "sw")
    flow("ns_moto", "moto", 300, "ns")
    flow("sn_moto", "moto", 300, "sn")
    path.write_text(f"""<routes>
  <vType id="car" vClass="passenger" laneChangeModel="{lcm}"/>
  <vType id="moto" vClass="motorcycle" laneChangeModel="{lcm}"/>
  <vType id="viol" vClass="custom1" laneChangeModel="{lcm}" {MOTO} {viol_extra}/>
  <route id="we" edges="up med out"/>
  <route id="ew" edges="out_r med_r up_r"/>
  <route id="nw" edges="n_in med_r up_r"/>
  <route id="sw" edges="s_in med_r up_r"/>
  <route id="ns" edges="n_in s_out"/>
  <route id="sn" edges="s_in n_out"/>
""" + "\n".join(f) + "\n</routes>\n")


def sumo_cmd(net: str, routes: Path, seed: int, end: float, sub: bool, out: Path) -> list[str]:
    d = TOY / net
    cmd = ["sumo", "-n", str(d / "toy.net.xml"), "-r", str(routes), "-a", str(d / "tls.add.xml"),
           "--seed", str(seed), "--end", str(end), "--step-length", str(STEP), "--collision.check-junctions", "true",
           "--collision-output", str(out / "collisions.xml"),
           "--tripinfo-output", str(out / "tripinfo.xml"), "--no-step-log", "true", "--duration-log.disable", "true",
           "--log", str(out / "sumo.log")]
    return cmd + (["--lateral-resolution", "0.4"] if sub else [])


def fwd_pos(road: str, pos: float) -> float | None:
    """Position along the WE direction (0 = start of up); None off the WE corridor."""
    if road == "up":
        return pos
    if road == "up_r":
        return UP_LEN - pos
    if road == "med":
        return UP_LEN + pos
    if road == "med_r":
        return UP_LEN + MEDIAN_M - pos
    return None


def run_case(args):
    """Wrapper: a SUMO error (e.g. LC2013 refused under sublane) becomes a result row, not a crash."""
    case, net, lcm, sub, extra, seed, end = args
    try:
        return _run_case(args)
    except Exception as ex:  # noqa: BLE001 - libsumo errors are not picklable, keep the text
        import libsumo as tc
        try:
            tc.close()
        except Exception:  # noqa: BLE001
            pass
        return dict(case=case, net=net, lcm=lcm, sublane=sub, viol_extra=extra, seed=seed, end_s=end,
                    error=str(ex)), []


def _run_case(args):
    case, net, lcm, sub, extra, seed, end = args
    import libsumo as tc
    out = HERE / "out" / case / f"seed_{seed:02d}"
    out.mkdir(parents=True, exist_ok=True)
    routes = out / "toy.rou.xml"
    write_routes(routes, net, lcm, extra)
    tc.start(sumo_cmd(net, routes, seed, end, sub, out))
    depart_rank, cross_rank, vtype = {}, {}, {}
    episodes, open_ep = [], {}
    n_tel = 0
    coll_lane = coll_junc = coll_opp = coll_frontal = 0
    while tc.simulation.getTime() < end:
        tc.simulationStep()
        t = tc.simulation.getTime()
        for v in tc.simulation.getDepartedIDList():
            if v.startswith("we_"):
                depart_rank[v] = len(depart_rank)
                vtype[v] = tc.vehicle.getTypeID(v)
        n_tel += tc.simulation.getStartingTeleportNumber()
        for c in tc.simulation.getCollisions():
            if c.lane.startswith(":"):
                coll_junc += 1
            else:
                coll_lane += 1
            coll_frontal += c.type == "frontal"
            if c.lane.startswith(("up_r", "med_r")) and (c.collider.startswith("we_") or c.victim.startswith("we_")):
                coll_opp += 1
        halted = {}
        state = {}
        for v in tc.vehicle.getIDList():
            if not v.startswith("we_"):
                continue
            road = tc.vehicle.getRoadID(v)
            if v not in cross_rank and (road == "out" or road.startswith(":J")):
                cross_rank[v] = len(cross_rank)
            lane = tc.vehicle.getLaneID(v)
            fp = fwd_pos(road, tc.vehicle.getLanePosition(v))
            spd = tc.vehicle.getSpeed(v)
            state[v] = (road, lane, fp, spd)
            if fp is not None and road in ("up", "med") and spd < HALT:
                halted[v] = fp
        for v, (road, lane, fp, spd) in state.items():
            kind = "opposite" if road in ("up_r", "med_r") else ("virtual" if lane == "up_1" and net == "v1" else None)
            if kind and v not in open_ep:
                open_ep[v] = dict(case=case, seed=seed, veh=v, type=vtype[v], kind=kind, t_start=round(t, 1),
                                  fp_start=round(fp, 1), halted_ahead_start=sum(h > fp for h in halted.values()),
                                  halted_total_start=len(halted), we_state=tc.trafficlight.getRedYellowGreenState("J"),
                                  min_speed=spd)
            elif kind:
                open_ep[v]["min_speed"] = min(open_ep[v]["min_speed"], spd)
            elif v in open_ep:
                ep = open_ep.pop(v)
                ep.update(t_end=round(t, 1), fp_end=round(fp, 1) if fp is not None else "", back_on=lane,
                          dist_from_median_end=round(UP_LEN - fp, 1) if fp is not None and road == "up" else "")
                episodes.append(ep)
        for v in tc.simulation.getArrivedIDList():
            if v in open_ep:
                ep = open_ep.pop(v)
                ep.update(t_end=round(t, 1), back_on="ARRIVED_OR_TELEPORTED")
                episodes.append(ep)
    for ep in open_ep.values():
        ep.update(t_end="", back_on="STILL_ON_AT_END")
        episodes.append(ep)
    pending = len(tc.simulation.getPendingVehicles())
    tc.close()
    # gain per vehicle that crossed the stop line
    gain = {v: depart_rank[v] - cross_rank[v] for v in cross_rank if v in depart_rank}
    users = {ep["veh"] for ep in episodes}
    for ep in episodes:
        ep["rank_gain"] = gain.get(ep["veh"], "")
    def mean(xs):
        return round(sum(xs) / len(xs), 2) if xs else ""
    tt = travel_times(out / "tripinfo.xml")
    log = (out / "sumo.log").read_text()
    viol = [v for v in depart_rank if vtype[v] == "viol"]
    row = dict(case=case, net=net, lcm=lcm, sublane=sub, viol_extra=extra, seed=seed, end_s=end,
               we_departed=len(depart_rank), we_crossed=len(cross_rank), pending_insert=pending,
               n_opp_episodes=sum(e["kind"] == "opposite" for e in episodes),
               n_opp_vehicles=len({e["veh"] for e in episodes if e["kind"] == "opposite"}),
               **{f"n_opp_{t_}": sum(1 for e in episodes if e["kind"] == "opposite" and e["type"] == t_)
                  for t_ in ("car", "moto", "viol")},
               n_opp_while_queue=sum(e["kind"] == "opposite" and e["halted_ahead_start"] >= 3 for e in episodes),
               n_virtual_episodes=sum(e["kind"] == "virtual" for e in episodes),
               viol_users=len(users & set(viol)), viol_total=len(viol),
               gain_users=mean([gain[v] for v in users if v in gain]),
               gain_viol_nonusers=mean([gain[v] for v in viol if v in gain and v not in users]),
               tt_viol_users=mean([tt[v] for v in users if v in tt]),
               tt_viol_nonusers=mean([tt[v] for v in viol if v in tt and v not in users]),
               tt_car=mean([tt[v] for v in depart_rank if vtype[v] == "car" and v in tt]),
               teleports=n_tel, coll_lane=coll_lane, coll_junction=coll_junc, coll_opp_lane=coll_opp,
               coll_frontal=coll_frontal, warn_unexpected_end_opposite=log.count("Unexpected end of opposite lane"),
               warn_emergency_braking=log.count("performs emergency braking"))
    return row, episodes


def travel_times(path: Path) -> dict[str, float]:
    return {t.id: float(t.duration) for t in sumolib.xml.parse(str(path), "tripinfo") if t.id.startswith("we_")}


def traci_cmd(seed: int, end: float) -> list[dict]:
    """Part 4: command a standing custom1 in the leftmost lane of the red queue onto the opposite lane."""
    import libsumo as tc
    rows = []
    for net, lcm, sub in [("n1", "LC2013", False), ("n1", "SL2015", False), ("n1", "SL2015", True),
                          ("n2", "SL2015", True)]:
        lanes = 2 if net == "n2" else 1
        for method in ("changeLane", "changeSublane"):
            case = f"traci_{method}_{lcm}_{net}_{'sub' if sub else 'nosub'}"
            out = HERE / "out" / case / f"seed_{seed:02d}"
            out.mkdir(parents=True, exist_ok=True)
            routes = out / "toy.rou.xml"
            write_routes(routes, net, lcm, "")
            tc.start(sumo_cmd(net, routes, seed, end, sub, out))
            target, err, reached, t_cmd, t_reach = None, "", False, "", ""
            t_back, back_fp, coll, fp_reach = "", "", [], ""
            while tc.simulation.getTime() < end:
                tc.simulationStep()
                if target is None:
                    for v in tc.vehicle.getIDList():
                        if (v.startswith("we_viol") and tc.vehicle.getLaneID(v) == f"up_{lanes - 1}"
                                and tc.vehicle.getSpeed(v) < 0.1
                                and tc.vehicle.getLanePosition(v) < UP_LEN - 20):
                            target, t_cmd = v, tc.simulation.getTime()
                            try:
                                if method == "changeLane":
                                    tc.vehicle.changeLane(v, lanes, 20.0)  # one past the leftmost lane
                                else:
                                    tc.vehicle.changeSublane(v, LANE_W)
                            except Exception as ex:  # noqa: BLE001 - record the SUMO error text
                                err = str(ex)
                            break
                    if tc.simulation.getTime() > end - 1:
                        break
                else:
                    coll += [f"{c.type}:{c.collider}>{c.victim}@{c.lane}" for c in tc.simulation.getCollisions()
                             if target in (c.collider, c.victim)]
                    if target not in tc.vehicle.getIDList() or tc.simulation.getTime() - t_cmd > 60:
                        break
                    road = tc.vehicle.getRoadID(target)
                    if not reached and road in ("up_r", "med_r"):
                        reached, t_reach = True, tc.simulation.getTime()
                        fp_reach = round(fwd_pos(road, tc.vehicle.getLanePosition(target)), 1)
                    elif reached and not t_back and road not in ("up_r", "med_r"):
                        t_back = tc.simulation.getTime()
                        fp = fwd_pos(road, tc.vehicle.getLanePosition(target))
                        back_fp = f"{road}:{round(fp, 1) if fp is not None else ''}"
            tc.close()
            rows.append(dict(case=case, seed=seed, vehicle=target, t_cmd=t_cmd, error=err, reached_opposite=reached,
                             t_reach=t_reach, fp_reach=fp_reach, t_back=t_back, back_at=back_fp,
                             collisions_60s=" ".join(dict.fromkeys(coll))))
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, keys)
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3])
    ap.add_argument("--end", type=float, default=600)
    ap.add_argument("--nproc", type=int, default=6)
    ap.add_argument("--cases", nargs="*", default=None)
    a = ap.parse_args()
    for n in NETS:
        build_net(n)
    jobs = [(c, n, l, s, x, seed, a.end) for c, n, l, s, x in CASES if not a.cases or c in a.cases for seed in a.seeds]
    with Pool(a.nproc) as p:
        res = p.map(run_case, jobs)
        tr = p.map(traci_cmd_job, [(s, a.end) for s in a.seeds])
    write_csv(HERE / "results.csv", [r for r, _ in res])
    write_csv(HERE / "episodes.csv", [e for _, eps in res for e in eps] or [{"none": ""}])
    write_csv(HERE / "traci_cmd.csv", [r for rows in tr for r in rows])
    for r, _ in res:
        print({k: r.get(k) for k in ("error","case", "seed", "n_opp_episodes", "n_opp_while_queue", "n_virtual_episodes",
                                 "gain_users", "teleports", "coll_lane", "coll_junction", "pending_insert")})
    for rows in tr:
        for r in rows:
            print(r)


def traci_cmd_job(a):
    return traci_cmd(*a)


if __name__ == "__main__":
    main()
