"""PLAN Phase 3B: does a custom1 (moto_violator) vehicle enter a sidewalk lane, ride it to its end and merge back at
the right place, and is there jamming / teleporting at the merge point? Toy scenario only; the main net, src/,
config/, scenario/, rules/ and data/ are not touched (rules/compiled/B0/vtypes.add.xml is only read).

    .venv/bin/python experiments/phase3b/sidewalk.py [--seeds 1 2 3] [--end 900] [--nproc 6]

Toy approach (heading east into a signalised node J; every number below is an EXPERIMENT SETTING, not field data):
road lanes 3.5 m, 3 of them: road lane 0 = continuous right turn (link state `g` in every phase), road lanes 1-2
straight (fixed signal 64 G / 4 y / 52 r = 120 s). Bollards between the right-turn lane and the straight lanes on
the last 20 m (changeLeft/changeRight="emergency" = only vClass emergency, absent here, may cross, sumo.dlr.de/docs/Networks/PlainXML.html
"Lane change restrictions"). Sidewalk: allow="custom1" only, speed SIDEWALK_SPEED, width = 2.0 or 3.0 m.
Geometry (distance to the stop line): `up` 420..170 m (insertion, 3 road lanes), sidewalk 170..0 m (a, c) or
170..20 m (b). Note: "ignoring" (the documented strongest restriction) is silently dropped by netconvert 1.27 (the
attribute does not reach the .net.xml), hence "emergency".

Topologies:
- `ctrl`: no sidewalk (reference for travel times and blocking); same segments as (a) with 3 lanes.
- `a`: sidewalk = extra lane 0 of the same edges (road lanes become 1..3). S1 (170..150 m) opening (lane changes
  allowed), S2 (150..20 m) closed (sidewalk changeLeft="emergency", road lane 1 changeRight="emergency"), S3 (last
  20 m) opening between sidewalk and right-turn lane, bollards between road lanes 1|2. At J the sidewalk lane has
  its own links: right -> out_r (g always) and straight -> out_s (g in the through green, y, r) for custom1.
- `b`: sidewalk = separate one-lane edge `sw` from diverge node D (170 m) to merge node M (20 m), parallel to the
  3-lane road edge `mid`; `sw` (priority 1) yields to `mid` (priority 2) at M and connects into `ap_end` lane 0
  (right turners) and lane 1 (straight). Node J and its TLS link indices are identical to `ctrl`.
  Use of `sw` is a route choice: in `b` every custom1 is routed over `sw` (mechanics test).
- `c`: as `b`, but `sw` runs from D to the stop line J itself and has its own links there (right -> out_r g always,
  straight -> out_s g in the through green). Its two TLS links are pinned to indices 3, 4 (toy.pin.tll.xml via
  netconvert -i), so the road links keep the `ctrl` indices 0..2.
Variant flags after the topology letter (variant id = <topology><flags>_w<width>):
- `t`: custom1 routed over the road; a TraCI trigger moves it to the sidewalk when the queue back is
  >= TRIGGER_QUEUE_M: `a` changeLane(v, 0, 5 s) on S1; `b`/`c` setRoute over `sw` when <= TRIGGER_DECIDE_M from J.
  Without `t`, every custom1 of `b`/`c` is routed over `sw` (mechanics test); `a` without `t` = SL2015 alone.
- `p`: sidewalk has priority at the merge (`b`: sw edge priority 3 > mid 2; `c`: sidewalk straight link G, not g,
  given to netconvert so the junction response matrix makes the road links yield).
- `f`: sidewalk speed SIDEWALK_SPEED_FAST instead of SIDEWALK_SPEED.

Demand (`DEMAND`, veh/h, flows Poisson arrivals, period="exp(rate)"): `heavy` gives a queue beyond the sidewalk
start, `light` = 25 % of it (queue only during red). custom1 = moto_violator_B0 (motorcycle defaults copied, B0).

Settings: sublane --lateral-resolution 0.4, SL2015 (B0 vtypes), step 0.1 s, --collision.check-junctions (R28),
collision.action default, time-to-teleport default (teleports are counted, not hidden).

Outputs in experiments/phase3b/: toy/<variant>/ (plain XML, net, tll, routes), out/<run>/ (tripinfo, statistics,
collisions), results_runs.csv (one row per run), results_vehicles.csv (one row per custom1 vehicle),
results_summary.csv (mean over seeds). Report: docs/research/phase3b_sidewalk.md.
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
import subprocess
import xml.etree.ElementTree as ET
from multiprocessing import Pool
from pathlib import Path

import sumolib

ROOT = Path(__file__).resolve().parents[2]  # SUMO/
HERE = Path(__file__).resolve().parent
TOY, OUT = HERE / "toy", HERE / "out"
VTYPES = ROOT / "rules" / "compiled" / "B0" / "vtypes.add.xml"

LANE_W = 3.5           # setting
ROAD_SPEED = 13.89     # setting (50 km/h)
SIDEWALK_SPEED = 5.0   # setting (18 km/h)
SIDEWALK_SPEED_FAST = 8.33  # setting (30 km/h), variants with flag f
WIDTHS = (2.0, 3.0)    # settings, NOT field values (sidewalk_width_m is TODO_MEASURE)
PHASES = ((64, "G"), (4, "y"), (52, "r"))  # setting, cycle 120 s
SW_START, SW_OPEN, BOLLARD = 170.0, 150.0, 20.0  # m to the stop line
UP_START = 420.0
TRIGGER_QUEUE_M, TRIGGER_DECIDE_M = 60.0, 300.0  # settings for `bt`
HALT = 1.0             # m/s, "halting" for queue back / sidewalk waits

SW_ROUTE = {"b": "up sw ap_end", "c": "up sw"}
DEMAND = {  # veh/h by (direction, flow type id)
    "heavy": {("s", "car"): 600, ("s", "moto"): 4500, ("s", "moto_violator"): 400,
              ("r", "car"): 150, ("r", "moto"): 600, ("r", "moto_violator"): 150},
}
DEMAND["light"] = {k: v * 0.25 for k, v in DEMAND["heavy"].items()}
VARIANTS = ["ctrl"] + [f"{t}_w{w:g}" for t in ("a", "at", "b", "bt", "bp", "c", "ct", "cp", "cpt", "cpf") for w in WIDTHS]


def topo(variant: str) -> tuple[str, float]:
    """`at`/`bt`/`ct` = topology a/b/c + TraCI trigger; returns (base topology, width)."""
    t, _, w = variant.partition("_w")
    return (t if t == "ctrl" else t[0]), float(w) if w else 0.0


def triggered(variant: str) -> bool:
    return variant != "ctrl" and "t" in variant.split("_")[0][1:]


def prio(variant: str) -> bool:
    """`bp`: sw has priority over mid at M; `cp`: the sidewalk straight link at J is G (not g) in the green."""
    return variant != "ctrl" and "p" in variant.split("_")[0][1:]


def link_state(kind: str, s: str, p: bool) -> str:
    """kind: road_r / road_s / sw_r / sw_s; s: G, y or r of the through phase."""
    if kind.endswith("_r"):
        return "g"  # continuous right turn, not signal controlled
    if kind == "sw_s" and s == "G" and not p:
        return "g"
    return s


# ---------------------------------------------------------------- network
def _lane(i, **attrs) -> str:
    return f'<lane index="{i}" ' + " ".join(f'{k}="{v}"' for k, v in attrs.items()) + "/>"


def build_net(variant: str) -> Path:
    t, w = topo(variant)
    SIDEWALK_SPEED = SIDEWALK_SPEED_FAST if "f" in variant.split("_")[0][1:] else globals()["SIDEWALK_SPEED"]
    d = TOY / variant
    d.mkdir(parents=True, exist_ok=True)
    nodes = {"U": -UP_START, "J": 0.0}
    edges, cons = [], []
    road = 'speed="%s" width="%s"' % (ROAD_SPEED, LANE_W)
    bollard_l = 'changeLeft="emergency"'
    bollard_r = 'changeRight="emergency"'
    if t in ("ctrl", "a"):
        nodes.update(S1=-SW_START, S2=-SW_OPEN, S3=-BOLLARD)
        k = 1 if t == "a" else 0  # index of the road right-turn lane
        n = 3 + k
        sw = (f'<lane index="0" allow="custom1" speed="{SIDEWALK_SPEED}" width="{w}"/>' if t == "a" else "")
        edges += [
            f'<edge id="up" from="U" to="S1" numLanes="3" {road} priority="2"/>',
            f'<edge id="S1" from="S1" to="S2" numLanes="{n}" {road} priority="2">{sw}</edge>',
            f'<edge id="S2" from="S2" to="S3" numLanes="{n}" {road} priority="2">'
            + (f'<lane index="0" allow="custom1" speed="{SIDEWALK_SPEED}" width="{w}" {bollard_l}/>'
               + _lane(1, changeRight="emergency") if t == "a" else "") + "</edge>",
            f'<edge id="S3" from="S3" to="J" numLanes="{n}" {road} priority="2">{sw}'
            + _lane(k, changeLeft="emergency") + _lane(k + 1, changeRight="emergency") + "</edge>",
        ]
        cons += [f'<connection from="up" to="S1" fromLane="{i}" toLane="{i + k}"/>' for i in range(3)]
        cons += [f'<connection from="{a}" to="{b}" fromLane="{i}" toLane="{i}"/>'
                 for a, b in (("S1", "S2"), ("S2", "S3")) for i in range(n)]
        last = "S3"
        if t == "a":
            cons += ['<connection from="S3" to="out_r" fromLane="0" toLane="0" allow="custom1"/>',
                     '<connection from="S3" to="out_s" fromLane="0" toLane="0" allow="custom1"/>']
    else:  # b, c (sw ends at M before the stop line, or at J itself)
        nodes.update(D=-SW_START, M=-BOLLARD)
        sw_to = "M" if t == "b" else "J"
        x_end = -BOLLARD if t == "b" else 0.0
        y = -(3 * LANE_W + w / 2)
        edges += [
            f'<edge id="up" from="U" to="D" numLanes="3" {road} priority="2"/>',
            f'<edge id="mid" from="D" to="M" numLanes="3" {road} priority="2"/>',
            f'<edge id="sw" from="D" to="{sw_to}" numLanes="1" priority="{3 if prio(variant) else 1}" speed="{SIDEWALK_SPEED}" width="{w}" '
            f'allow="custom1" spreadType="center" shape="{-SW_START},{-LANE_W * 1.5} {-SW_START + 10},{y} '
            f'{x_end - 10},{y} {x_end},{-LANE_W * 1.5}"/>',
            f'<edge id="ap_end" from="M" to="J" numLanes="3" {road} priority="2">'
            + _lane(0, changeLeft="emergency") + _lane(1, changeRight="emergency") + "</edge>",
        ]
        cons += [f'<connection from="{a}" to="{b}" fromLane="{i}" toLane="{i}"/>'
                 for a, b in (("up", "mid"), ("mid", "ap_end")) for i in range(3)]
        cons += ['<connection from="up" to="sw" fromLane="0" toLane="0" allow="custom1"/>']
        cons += ([f'<connection from="sw" to="ap_end" fromLane="0" toLane="{i}" allow="custom1"/>' for i in (0, 1)]
                 if t == "b" else
                 [f'<connection from="sw" to="{o}" fromLane="0" toLane="0" allow="custom1"/>' for o in ("out_r", "out_s")])
        last, k = "ap_end", 0
    nodes.update(E=200.0)
    edges += [f'<edge id="out_s" from="J" to="E" numLanes="2" {road} priority="2"/>',
              f'<edge id="out_r" from="J" to="R" numLanes="1" {road} priority="2"/>']
    cons += [f'<connection from="{last}" to="out_r" fromLane="{k}" toLane="0"/>',
             f'<connection from="{last}" to="out_s" fromLane="{k + 1}" toLane="0"/>',
             f'<connection from="{last}" to="out_s" fromLane="{k + 2}" toLane="1"/>']
    nod = ['<node id="R" x="0" y="-200" type="dead_end"/>']
    for nid, x in nodes.items():
        typ = 'type="traffic_light" tlType="static"' if nid == "J" else (
            'type="dead_end"' if nid in ("U", "E") else 'type="priority"')
        nod.append(f'<node id="{nid}" x="{x}" y="0" {typ}/>')
    (d / "toy.nod.xml").write_text("<nodes>\n  " + "\n  ".join(nod) + "\n</nodes>\n")
    (d / "toy.edg.xml").write_text("<edges>\n  " + "\n  ".join(edges) + "\n</edges>\n")
    (d / "toy.con.xml").write_text("<connections>\n  " + "\n  ".join(cons) + "\n</connections>\n")
    net = d / "toy.net.xml"
    pin = []
    if t == "c":  # pin the road links to the ctrl indices 0..2, sidewalk links appended as 3, 4 (netconvert would put them first)
        pin = ["-i", d / "toy.pin.tll.xml"]
        links = [("ap_end", "out_r", 0, 0), ("ap_end", "out_s", 1, 0), ("ap_end", "out_s", 2, 1),
                 ("sw", "out_r", 0, 0), ("sw", "out_s", 0, 0)]
        (d / "toy.pin.tll.xml").write_text(
            '<tlLogics>\n  <tlLogic id="J" type="static" programID="0" offset="0">\n'
            + "".join(f'    <phase duration="{du}" state="'
                      + "".join(link_state(k, s, prio(variant)) for k in ("road_r", "road_s", "road_s", "sw_r", "sw_s"))
                      + '"/>\n' for du, s in PHASES)
            + "  </tlLogic>\n" + "".join(f'  <connection from="{a}" to="{b}" fromLane="{i}" toLane="{j}" tl="J" '
                                         f'linkIndex="{k}"/>\n' for k, (a, b, i, j) in enumerate(links))
            + "</tlLogics>\n")
    subprocess.run([sumolib.checkBinary("netconvert"), "-n", d / "toy.nod.xml", "-e", d / "toy.edg.xml",
                    "-x", d / "toy.con.xml", *pin, "-o", net, "--no-turnarounds", "--default.spreadtype", "right"], check=True, capture_output=True)
    write_tll(net, d / "toy.tll.add.xml", prio(variant))
    return net


def write_tll(net_path: Path, out: Path, p: bool) -> None:
    """Own static program (programID p3b): right links g always, straight links G/y/r; the extra sidewalk straight
    link of (a) gets g (yields) instead of G."""
    net = sumolib.net.readNet(str(net_path))
    links = sorted(net.getTLS("J").getConnections(), key=lambda c: c[2])
    n = links[-1][2] + 1
    states = []
    for _, s in PHASES:
        st = ["r"] * n
        for in_lane, out_lane, idx in links:
            kind = ("road" if in_lane.allows("passenger") else "sw") + (
                "_r" if out_lane.getEdge().getID() == "out_r" else "_s")
            st[idx] = link_state(kind, s, p)
        states.append("".join(st))
    ph = "\n    ".join(f'<phase duration="{d}" state="{st}"/>' for (d, _), st in zip(PHASES, states))
    out.write_text(f'<additional>\n  <tlLogic id="J" type="static" programID="p3b" offset="0">\n    {ph}\n'
                   f"  </tlLogic>\n</additional>\n")


def write_routes(variant: str, demand: str, end: int) -> Path:
    t, _ = topo(variant)
    path = TOY / variant / f"routes_{demand}.rou.xml"
    road = {"ctrl": "up S1 S2 S3", "a": "up S1 S2 S3", "b": "up mid ap_end", "c": "up mid ap_end"}[t]
    rows = []
    for (dr, typ), vph in sorted(DEMAND[demand].items()):
        edges = road
        if t in ("b", "c") and not triggered(variant) and typ == "moto_violator":
            edges = SW_ROUTE[t]
        exit_ = "out_s" if dr == "s" else "out_r"
        rows.append(f'<flow id="{dr}_{typ}" type="{typ}" begin="0" end="{end}" period="exp({vph / 3600:.6f})" '
                    f'departLane="best" departPosLat="random" departSpeed="max" route="{dr}_{typ}_r"/>')
        rows.insert(0, f'<route id="{dr}_{typ}_r" edges="{edges} {exit_}"/>')
    path.write_text("<routes>\n  " + "\n  ".join(rows) + "\n</routes>\n")
    return path


# ---------------------------------------------------------------- run
def run_one(args) -> dict:
    try:
        return _run_one(*args)
    except Exception as ex:  # libsumo exceptions do not pickle across the Pool
        raise RuntimeError(f"{args}: {ex}") from None


def _run_one(variant: str, demand: str, seed: int, end: int) -> dict:
    import libsumo as traci  # one SUMO per process

    t, w = topo(variant)
    d = TOY / variant
    o = OUT / f"{variant}__{demand}__s{seed}"
    o.mkdir(parents=True, exist_ok=True)
    traci.start([sumolib.checkBinary("sumo"), "-n", str(d / "toy.net.xml"),
                 "-r", str(d / f"routes_{demand}.rou.xml"),
                 "-a", f"{VTYPES},{d / 'toy.tll.add.xml'}",
                 "--seed", str(seed), "--step-length", "0.1", "--lateral-resolution", "0.4",
                 "--collision.check-junctions", "--end", str(end),
                 "--tripinfo-output", str(o / "tripinfo.xml"), "--statistic-output", str(o / "stats.xml"),
                 "--collision-output", str(o / "collisions.xml"), "--no-step-log"])
    assert traci.trafficlight.getProgram("J") == "p3b"
    lanes_len = {e: traci.lane.getLength(f"{e}_0") for e in traci.edge.getIDList() if not e.startswith(":")}
    trig = triggered(variant)
    order = ["up", "S1", "S2", "S3"] if t in ("ctrl", "a") else ["up", "mid", "ap_end"]
    off, acc = {}, 0.0
    for e in reversed(order):
        acc += lanes_len[e]
        off[e] = acc  # distance from the start of e to the stop line
    if t in ("b", "c"):
        off["sw"] = lanes_len["sw"] + (off["ap_end"] if t == "b" else 0.0)
    sidewalk = {"a": {"S1_0", "S2_0", "S3_0"}, "b": {"sw_0"}, "c": {"sw_0"}}.get(t, set())
    net = sumolib.net.readNet(str(d / "toy.net.xml"), withInternal=True)
    sidewalk |= {c.getViaLaneID() for ln in sidewalk for c in net.getLane(ln).getOutgoing()
                 if c.getToLane().getID() in sidewalk}  # internal lanes between sidewalk segments
    veh: dict[str, dict] = {}
    queue, queue_series, rerouted = 0.0, [], 0
    step = 0
    while traci.simulation.getMinExpectedNumber() > 0 and traci.simulation.getTime() < end:
        traci.simulationStep()
        step += 1
        now = traci.simulation.getTime()
        ids = traci.vehicle.getIDList()
        if step % 10 == 0:  # queue back every 1 s: farthest halting road vehicle
            q = 0.0
            for v in ids:
                ln = traci.vehicle.getLaneID(v)
                e = ln.rsplit("_", 1)[0]
                if e in off and ln not in sidewalk and traci.vehicle.getSpeed(v) < HALT:
                    q = max(q, off[e] - traci.vehicle.getLanePosition(v))
            queue = q
            queue_series.append(q)
            # compliant classes on the sidewalk (must stay 0)
        for v in ids:
            typ = traci.vehicle.getTypeID(v)
            ln = traci.vehicle.getLaneID(v)
            on_sw = ln in sidewalk
            if typ != "moto_violator_B0":
                if on_sw:
                    veh.setdefault("__compliant_on_sidewalk__", {"n": 0})["n"] += 1
                continue
            r = veh.setdefault(v, {"id": v, "dir": v[0], "used": 0, "q_at_170": None, "enter": "", "exit_to": "",
                                   "exit_pos": None, "sw_halt_s": 0.0, "sw_halt_end_s": 0.0, "sw_time_s": 0.0,
                                   "trig": ""})
            e = ln.rsplit("_", 1)[0]
            dist = off[e] - traci.vehicle.getLanePosition(v) if e in off else None
            if r["q_at_170"] is None and dist is not None and dist <= SW_START + 10:
                r["q_at_170"] = queue
            if trig and not r["trig"] and ((t == "a" and e == "S1") or (t != "a" and e == "up" and dist <= TRIGGER_DECIDE_M)):
                if queue >= TRIGGER_QUEUE_M:
                    try:
                        if t == "a":  # lane 0 of S1 = sidewalk; duration long enough to cover the 20 m opening
                            traci.vehicle.changeLane(v, 0, 5.0)
                        else:
                            traci.vehicle.setRoute(v, SW_ROUTE[t].split() + ["out_s" if v[0] == "s" else "out_r"])
                        r["trig"] = "set"
                        rerouted += 1
                    except traci.TraCIException as ex:
                        r["trig"] = f"fail:{ex}"
                else:
                    r["trig"] = "no"
            if on_sw:
                if not r["used"]:
                    r["used"], r["enter"] = 1, f"{ln}@{traci.vehicle.getLanePosition(v):.1f}"
                r["sw_time_s"] += 0.1
                r["last_sw"] = (ln, traci.vehicle.getLanePosition(v))
                if traci.vehicle.getSpeed(v) < HALT:
                    r["sw_halt_s"] += 0.1
                    if e == "S3" or (e in lanes_len and lanes_len[e] - traci.vehicle.getLanePosition(v) <= 20):
                        r["sw_halt_end_s"] += 0.1
            elif r["used"] and not r["exit_to"] and "last_sw" in r:
                r["exit_to"] = ln
                r["exit_pos"] = round(traci.vehicle.getLanePosition(v), 1)
    traci.close()
    compliant_on_sw = veh.pop("__compliant_on_sidewalk__", {"n": 0})["n"]
    return {"variant": variant, "demand": demand, "seed": seed, "end": end, "veh": veh,
            "compliant_on_sw_steps": compliant_on_sw, "rerouted": rerouted,
            "queue_mean": statistics.mean(queue_series), "queue_p90": sorted(queue_series)[int(.9 * len(queue_series))],
            "queue_max": max(queue_series)}


# ---------------------------------------------------------------- analysis
def analyse(res: dict) -> tuple[dict, list[dict]]:
    o = OUT / f"{res['variant']}__{res['demand']}__s{res['seed']}"
    st = ET.parse(o / "stats.xml").getroot()
    tp, sf, vs = st.find("teleports"), st.find("safety"), st.find("vehicles")
    cols = ET.parse(o / "collisions.xml").getroot().findall("collision")
    trips = {ti.get("id"): ti for ti in ET.parse(o / "tripinfo.xml").getroot().findall("tripinfo")}

    def tt(pred, key="duration"):
        xs = [float(ti.get(key)) for i, ti in trips.items() if pred(i)]
        return (round(statistics.mean(xs), 1) if xs else None), len(xs)

    vrows = []
    for v, r in res["veh"].items():
        ti = trips.get(v)
        vrows.append({"variant": res["variant"], "demand": res["demand"], "seed": res["seed"], "id": v,
                      "dir": r["dir"], "used_sidewalk": r["used"],
                      "q_at_170m": None if r["q_at_170"] is None else round(r["q_at_170"], 1),
                      "trigger": r["trig"], "enter": r["enter"], "exit_to": r["exit_to"], "exit_pos": r["exit_pos"],
                      "sw_time_s": round(r["sw_time_s"], 1), "sw_halt_s": round(r["sw_halt_s"], 1),
                      "sw_halt_last20m_s": round(r["sw_halt_end_s"], 1),
                      "duration_s": ti.get("duration") if ti is not None else "",
                      "timeLoss_s": ti.get("timeLoss") if ti is not None else ""})
    users = [r for r in vrows if r["used_sidewalk"]]
    row = {"variant": res["variant"], "demand": res["demand"], "seed": res["seed"],
           "inserted": vs.get("inserted"), "not_inserted": vs.get("waiting"), "arrived": len(trips),
           "teleports": tp.get("total"), "tp_jam": tp.get("jam"), "tp_yield": tp.get("yield"),
           "tp_wrongLane": tp.get("wrongLane"), "collisions": sf.get("collisions"),
           "coll_junction": sum(c.get("lane", "").startswith(":") for c in cols),
           "coll_sidewalk_lane": sum(c.get("lane", "") in ("S1_0", "S2_0", "S3_0", "sw_0") for c in cols
                                     if res["variant"] != "ctrl"),
           "queue_mean_m": round(res["queue_mean"], 1), "queue_p90_m": round(res["queue_p90"], 1),
           "queue_max_m": round(res["queue_max"], 1),
           "c1_seen": len(vrows), "c1_used": len(users), "compliant_on_sw_steps": res["compliant_on_sw_steps"],
           "bt_rerouted": res["rerouted"]}
    for dr in "sr":
        row[f"tt_c1_{dr}"], _ = tt(lambda i: i.startswith(f"{dr}_moto_violator"))
        row[f"tt_c1_{dr}_users"], _ = tt(lambda i: i.startswith(f"{dr}_moto_violator") and res["veh"].get(i, {}).get("used"))
        row[f"tt_moto_{dr}"], _ = tt(lambda i: i.startswith(f"{dr}_moto."))
        row[f"tl_compliant_{dr}"], _ = tt(lambda i: i.startswith(f"{dr}_") and "violator" not in i, "timeLoss")
    row["sw_halt_mean_s"] = round(statistics.mean(r["sw_halt_s"] for r in users), 1) if users else None
    row["sw_halt_last20_mean_s"] = round(statistics.mean(r["sw_halt_last20m_s"] for r in users), 1) if users else None
    exits = {}
    for r in users:
        k = f"{r['dir']}:{r['exit_to'] or 'none'}"  # first lane after the sidewalk (internal = via link)
        exits[k] = exits.get(k, 0) + 1
    row["exits"] = json.dumps(dict(sorted(exits.items())))
    return row, vrows


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0]))
        wr.writeheader()
        wr.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3])
    ap.add_argument("--end", type=int, default=900)
    ap.add_argument("--nproc", type=int, default=6)
    ap.add_argument("--variants", nargs="+", default=VARIANTS)
    ap.add_argument("--demands", nargs="+", default=["heavy", "light"])
    a = ap.parse_args()
    for v in a.variants:
        build_net(v)
        for dm in a.demands:
            write_routes(v, dm, a.end)
    jobs = [(v, dm, s, a.end) for v in a.variants for dm in a.demands for s in a.seeds]
    with Pool(a.nproc) as p:
        results = p.map(run_one, jobs)
    rows, vrows = [], []
    for r in results:
        row, vr = analyse(r)
        rows.append(row)
        vrows += vr
    write_csv(HERE / "results_runs.csv", rows)
    write_csv(HERE / "results_vehicles.csv", vrows)
    # mean over seeds per (variant, demand)
    summ = []
    for v in a.variants:
        for dm in a.demands:
            g = [r for r in rows if r["variant"] == v and r["demand"] == dm]
            s = {"variant": v, "demand": dm, "n_seeds": len(g)}
            for k in g[0]:
                if k in ("variant", "demand", "seed", "exits"):
                    continue
                xs = [float(r[k]) for r in g if r[k] not in (None, "")]
                s[k] = round(statistics.mean(xs), 2) if xs else None
            summ.append(s)
    write_csv(HERE / "results_summary.csv", summ)
    for s in summ:
        print(s)


if __name__ == "__main__":
    main()
