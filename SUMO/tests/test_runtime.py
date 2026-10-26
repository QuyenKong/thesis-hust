"""TraCI runtime controller and rules (PLAN 4.5): one tiny-net scenario per rule, ignored commands, mode restore,
libsumo/traci parity and the runner integration."""

import csv
import json
import random
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest
import sumolib

from thesis_sumo.config import REPO_ROOT, Site, load_site
from thesis_sumo.rules.compiler import compile_spec
from thesis_sumo.runtime.controller import Controller, load_rules
from thesis_sumo.runtime.rules import RULE_REGISTRY
from thesis_sumo.runtime.rules.base import LOG_COLUMNS
from thesis_sumo.runtime.rules.swarm_red_running import SwarmRedRunning
from thesis_sumo.sim import runner

# as the runner: warnings stay on (R22), junction collisions are checked (R28)
SUMO_OPTS = ["--step-length", "0.1", "--lateral-resolution", "0.4", "--no-step-log", "true",
             "--collision.check-junctions", "true"]
DEFAULT_SPEED_MODE, DEFAULT_LC_MODE = 31, 1621  # TraCI/Change_Vehicle_State: speed mode 31, lane change mode 1621
W_GREEN_ONSET = 45.0  # tiny cross program: N-S green 0-42 s, N-S yellow 42-45 s, W-E green 45-87 s, W-E yellow 87-90
PROXY_SITE = REPO_ROOT / "config" / "site.proxy.yaml"
VTYPES = (  # SUMO vClass defaults except where a scenario needs otherwise
    '<vType id="moto" vClass="motorcycle" laneChangeModel="SL2015"/>'
    '<vType id="car" vClass="passenger" laneChangeModel="SL2015" lcSpeedGain="0" lcKeepRight="0" lcCooperative="0"/>'
    '<vType id="rule_moto" vClass="motorcycle" laneChangeModel="SL2015"/>'
    '<vType id="rule_car" vClass="passenger" laneChangeModel="SL2015" lcSpeedGain="0" lcKeepRight="0" lcCooperative="0"/>'
    '<vType id="foe" vClass="passenger" jmDriveAfterYellowTime="10"/>'
    '<vType id="vio" vClass="custom1" length="2.2" width="0.9" minGap="2.5" accel="6" decel="10" '
    'emergencyDecel="10" maxSpeed="55.55" guiShape="motorcycle" laneChangeModel="SL2015"/>')


# ---------------------------------------------------------------- tiny scenario helpers


def _cross(d: Path, lanes: int = 1, connections: str | None = None, radius: float | None = None) -> Path:
    """Signalised cross, arms 150 m, carrying the site street names (approaches LVL_W = WC, LVL_E = EC,
    HDT_N = NC, HDT_S = SC); netconvert's default 2-phase program (see W_GREEN_ONSET)."""
    d.mkdir(parents=True, exist_ok=True)
    (d / "n.nod.xml").write_text(
        '<nodes><node id="C" x="0" y="0" type="traffic_light"/><node id="W" x="-150" y="0"/>'
        '<node id="E" x="150" y="0"/><node id="S" x="0" y="-150"/><node id="N" x="0" y="150"/></nodes>',
        encoding="utf-8")
    edges = [("WC", "W", "C", "Le Van Luong"), ("CE", "C", "E", "Le Van Luong"), ("EC", "E", "C", "Le Van Luong"),
             ("CW", "C", "W", "Le Van Luong"), ("SC", "S", "C", "Hoang Dao Thuy"), ("CN", "C", "N", "Hoang Dao Thuy"),
             ("NC", "N", "C", "Hoang Dao Thuy"), ("CS", "C", "S", "Hoang Dao Thuy")]
    (d / "n.edg.xml").write_text("<edges>" + "".join(
        f'<edge id="{i}" from="{f}" to="{t}" name="{n}" numLanes="{lanes}" speed="13.9"/>' for i, f, t, n in edges)
        + "</edges>", encoding="utf-8")
    cmd = [sumolib.checkBinary("netconvert"), "-n", str(d / "n.nod.xml"), "-e", str(d / "n.edg.xml"),
           "-o", str(d / "tiny.net.xml")]
    if connections:
        (d / "c.con.xml").write_text(f"<connections>{connections}</connections>", encoding="utf-8")
        cmd += ["-x", str(d / "c.con.xml")]
    if radius is not None:
        cmd += ["--default.junctions.radius", str(radius)]
    subprocess.run(cmd, check=True, capture_output=True)
    return d / "tiny.net.xml"


def _site(d: Path, lane_movements: dict | None = None, illegal: bool = False) -> Site:
    edges = {"LVL_W": "WC", "LVL_E": "EC", "HDT_N": "NC", "HDT_S": "SC"}
    data = {"site_source": "LITERATURE_PROXY",
            "approaches": [{"id": a, "edge": e, "lane_movements": (lane_movements or {}).get(a),
                            "left_turn_banned": illegal and a == "LVL_W"} for a, e in edges.items()],
            "illegal_left": {"approaches": ["LVL_W"] if illegal else None}}
    return Site(data, d / "site.tiny.yaml")


def _rule(rule_type: str, vtype_ids: list[str], **params) -> dict:
    return {"rule_type": rule_type, "vtype_ids": vtype_ids, "params": params}


def _simulate(backend, net: Path, routes_xml: str, rules: list[dict], site: Site, d: Path, end: float,
              seed: int = 1, probe=None):
    """Run `routes_xml` with a Controller; `probe(backend, t, ctl)` after each controller step.
    Returns (controller, log rows as dicts)."""
    routes = d / "r.rou.xml"
    routes.write_text(f"<routes>{VTYPES}{routes_xml}</routes>", encoding="utf-8")
    log = d / "interventions.csv"
    backend.start([sumolib.checkBinary("sumo"), "-n", str(net), "-r", str(routes), "--seed", str(seed), *SUMO_OPTS])
    try:
        ctl = Controller(rules, backend, site, log, radius_m=200.0, seed=seed)
        while backend.simulation.getTime() < end - 1e-9:
            backend.simulationStep()
            ctl.on_step()
            if probe is not None:
                probe(backend, backend.simulation.getTime(), ctl)
        ctl.close()
    finally:
        backend.close()
    with log.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert list(rows[0]) == list(LOG_COLUMNS) if rows else True
    return ctl, rows


@pytest.fixture(scope="module")
def one_lane(tmp_path_factory):
    return _cross(tmp_path_factory.mktemp("cross1"))


def _creeper(foes: bool) -> str:
    xml = '<vehicle id="v" type="rule_moto" depart="0"><route edges="WC CE"/></vehicle>'
    if foes:  # dense crossing stream through the end of the N-S green and its yellow
        xml += ('<flow id="f" type="foe" begin="0" end="50" period="0.7" departSpeed="max">'
                '<route edges="NC CS"/></flow>')
    return xml


EARLY = _rule("early_start", ["rule_moto"], t_before_green=10.0, p=1.0, v_max=2.0)


# ---------------------------------------------------------------- early_start


def test_early_start_fires(one_lane, tmp_path):
    import libsumo
    speeds = []
    ctl, rows = _simulate(libsumo, one_lane, _creeper(False), [EARLY], _site(tmp_path), tmp_path, 60,
                          probe=lambda b, t, c: speeds.append((t, b.vehicle.getSpeed("v"), b.vehicle.getLaneID("v")))
                          if "v" in b.vehicle.getIDList() else None)
    assert len(rows) == 1
    r = rows[0]
    assert (r["veh_id"], r["rule"], r["action"], r["executed"], r["reason"]) == \
        ("v", "early_start", "creep_over_stop_line", "True", "")
    t0, t1 = float(r["t"]), float(r["t_end"])
    assert W_GREEN_ONSET - 10.0 - 1e-6 <= t0 < t1 < W_GREEN_ONSET  # inside the window, crossed before green
    assert all(v <= 2.0 + 1e-9 for t, v, _ in speeds if t0 < t <= t1)  # creep speed capped at v_max
    crossed = min(t for t, _, lane in speeds if lane.startswith(":"))
    assert crossed == pytest.approx(t1)  # SUMO really moved it over the line at the logged time
    assert ctl.summary()["early_start"] == {"attempted": 1, "executed": 1, "not_executed": {},
                                            "counters": {"draws": 1}}
    out = min(t for t, _, lane in speeds if lane == "CE_0")  # R30: the window closes past the junction
    assert ctl.intervened("v", (t0 + t1) / 2) and ctl.intervened("v", out - 0.1) and not ctl.intervened("v", out + 0.1)
    assert not ctl.intervened("v", t0 - 0.1)


def test_early_start_p_zero_draws_once_never_fires(one_lane, tmp_path):
    import libsumo
    rule = _rule("early_start", ["rule_moto"], t_before_green=10.0, p=0.0, v_max=2.0)
    ctl, rows = _simulate(libsumo, one_lane, _creeper(False), [rule], _site(tmp_path), tmp_path, 60)
    assert rows == [] and ctl.summary()["early_start"]["counters"] == {"draws": 1}


def test_ignored_command_logged(one_lane, tmp_path):
    """The creep command is sent (bit4 cleared, setSpeed) but SUMO keeps the vehicle behind the line: with bit3 kept it
    yields to the crossing stream until the red ends -> executed False."""
    import libsumo
    modes = []
    ctl, rows = _simulate(libsumo, one_lane, _creeper(True), [EARLY], _site(tmp_path), tmp_path, 60,
                          probe=lambda b, t, c: modes.append((t, b.vehicle.getSpeedMode("v"), b.vehicle.getLaneID("v")))
                          if "v" in b.vehicle.getIDList() else None)
    assert len(rows) == 1
    r = rows[0]
    assert (r["action"], r["executed"], r["reason"]) == ("creep_over_stop_line", "False", "red_ended_before_crossing")
    assert float(r["t_end"]) == pytest.approx(W_GREEN_ONSET, abs=0.11)  # TLS switch seen one step later (state.py)
    assert any(m == DEFAULT_SPEED_MODE & ~16 for t, m, _ in modes if t < W_GREEN_ONSET)  # the command was applied
    assert not any(lane.startswith(":") for t, _, lane in modes if t < W_GREEN_ONSET)
    assert ctl.summary()["early_start"]["not_executed"] == {"red_ended_before_crossing": 1}


def test_modes_restored(one_lane, tmp_path):
    import libsumo
    seen = []
    _, rows = _simulate(libsumo, one_lane, _creeper(False), [EARLY], _site(tmp_path), tmp_path, 60,
                        probe=lambda b, t, c: seen.append((t, b.vehicle.getSpeedMode("v"), b.vehicle.getLaneChangeMode("v"),
                                                           b.vehicle.getSpeed("v")))
                        if "v" in b.vehicle.getIDList() else None)
    t0, t1 = float(rows[0]["t"]), float(rows[0]["t_end"])
    assert {m for t, m, _, _ in seen if t < t0} == {DEFAULT_SPEED_MODE}
    assert {m for t, m, _, _ in seen if t0 <= t < t1} == {DEFAULT_SPEED_MODE & ~16}  # only bit4 cleared
    after = [(m, v) for t, m, _, v in seen if t >= t1]
    assert after and {m for m, _ in after} == {DEFAULT_SPEED_MODE}
    assert {lc for _, _, lc, _ in seen} == {DEFAULT_LC_MODE}  # never touched
    assert max(v for _, v in after) > 2.0 + 0.5  # the setSpeed cap was lifted


# ---------------------------------------------------------------- swarm_red_running


def test_swarm_window_counts():
    info = SimpleNamespace(lanes={"A": []})
    rule = SwarmRedRunning({"p0": 0.1, "k": 0.2, "p_max": 0.6, "dt": 2.0}, ["x"], info,
                           SimpleNamespace(b=None), random.Random(0))
    rule._violations["A"].extend([1.0, 2.0, 2.5])
    assert rule.n_recent("A", 3.0) == 2   # window (1.0, 3.0]
    assert rule.n_recent("A", 4.5) == 0


def test_swarm_probability_rises(one_lane, tmp_path):
    import libsumo
    flow = ('<flow id="m" type="rule_moto" begin="0" end="12" period="1" departSpeed="max">'
            '<route edges="WC CE"/></flow>')
    rule = _rule("swarm_red_running", ["rule_moto"], p0=0.3, k=0.4, p_max=1.0, dt=30.0)
    ctl, rows = _simulate(libsumo, one_lane, flow, [rule], _site(tmp_path), tmp_path, 44, seed=4)  # seed 4: m.0 runs
    swarm = ctl.rules[0]
    draws = swarm.draw_log
    assert draws and draws[0][2] == 0 and draws[0][3] == pytest.approx(0.3)
    for _t, _vid, n, p, _ran in draws:
        assert p == pytest.approx(min(1.0, 0.3 + 0.4 * n))
    assert max(p for *_, p, _ in draws) > 0.3  # earlier red runners raised p
    runs = [r for r in rows if r["action"] == "run_red"]
    assert runs and all(r["executed"] == "True" for r in runs)
    assert len(runs) == sum(ran for *_, ran in draws)
    assert all(float(r["t_end"]) < W_GREEN_ONSET for r in runs)


def test_intervened_window_until_past_junction(one_lane, tmp_path):
    """R30: a red runner whose intervention ended at the stop-line crossing (overrides undone) and that collides
    inside the junction is still counted as intervened. The foe is a test-only vehicle inserted near the N stop line
    once the (slow) runner is in the junction, with speed mode 0 so that it drives into it."""
    import libsumo
    seen = {"t_in": None, "t_out": None}
    collisions = []

    def probe(b, t, c):
        collisions.extend({"time": str(t), "type": x.type, "lane": x.lane, "collider": x.collider, "victim": x.victim}
                          for x in b.simulation.getCollisions())
        if "r" not in b.vehicle.getIDList():
            return
        lane = b.vehicle.getLaneID("r")
        if lane.startswith(":") and seen["t_in"] is None:
            seen["t_in"] = t
        if lane.startswith(":") and b.vehicle.getLanePosition("r") >= 3.0 and "foe" not in seen:
            seen["foe"] = False  # inserted at standstill 1 m before the N stop line, then driven blind at 12 m/s
            b.vehicle.add("foe", "foe_route", typeID="car", departPos=str(b.lane.getLength("NC_0") - 1.0),
                          departSpeed="0")
        elif "foe" in b.vehicle.getIDList() and seen.get("foe") is False:
            b.vehicle.setSpeedMode("foe", 0)
            b.vehicle.setSpeed("foe", 12.0)
            seen["foe"] = True
        if lane == "CE_0" and seen["t_out"] is None:
            seen["t_out"] = t

    xml = ('<vType id="slow_moto" vClass="motorcycle" accel="0.8"/><route id="foe_route" edges="NC CS"/>'
           '<vehicle id="r" type="slow_moto" depart="0" departPos="140" departSpeed="0"><route edges="WC CE"/>'
           '</vehicle>')  # starts halted 1.0 m before the red W stop line
    rule = _rule("swarm_red_running", ["slow_moto"], p0=1.0, k=0.0, p_max=1.0, dt=10.0)
    ctl, rows = _simulate(libsumo, one_lane, xml, [rule], _site(tmp_path), tmp_path, 60, probe=probe)
    (run,) = [r for r in rows if r["veh_id"] == "r"]
    assert run["executed"] == "True" and float(run["t_end"]) == pytest.approx(seen["t_in"])
    junction = [c for c in collisions if runner.is_junction_collision(c) and "r" in (c["collider"], c["victim"])]
    assert junction, "the foe did not hit the runner inside the junction"
    t_coll = float(junction[0]["time"])
    assert float(run["t_end"]) < t_coll  # after the overrides were undone ...
    assert ctl.intervened("r", t_coll) and runner.count_intervened(junction[:1], ctl) == 1  # ... still attributed
    if seen["t_out"] is not None:  # the window closes on the first lane past the junction
        assert not ctl.intervened("r", seen["t_out"] + 1.0)


# ---------------------------------------------------------------- wrong_lane_dodge


def test_wrong_lane_dodge_fires(tmp_path):
    """Two-lane W approach: lane 0 (r, s) queues; lane 1 is marked l/u in the site file, so it is a wrong lane for a
    straight vehicle, but the net connects it straight on (executed); for a right-turner it has no connection to
    its next edge (logged no_connection, no command)."""
    import libsumo
    net = _cross(tmp_path / "net", lanes=2)
    queue = ('<flow id="q" type="car" begin="0" end="12" period="1" departLane="0" departSpeed="max">'
             '<route edges="WC CE"/></flow>')
    dodgers = ('<vehicle id="d_s" type="rule_car" depart="14" departLane="0" departSpeed="max"><route edges="WC CE"/>'
               '</vehicle><vehicle id="d_r" type="rule_car" depart="16" departLane="0" departSpeed="max">'
               '<route edges="WC CS"/></vehicle>')
    marks = {"LVL_W": [["r", "s"], ["l", "u"]], "LVL_E": [["r", "s"], ["s", "l", "u"]],
             "HDT_N": [["r", "s"], ["s", "l", "u"]], "HDT_S": [["r", "s"], ["s", "l", "u"]]}
    lanes = {}
    rule = _rule("wrong_lane_dodge", ["rule_car"], q_min=30.0, v_creep=2.0)
    ctl, rows = _simulate(libsumo, net, queue + dodgers, [rule], _site(tmp_path, marks), tmp_path, 44,
                          probe=lambda b, t, c: lanes.update({v: b.vehicle.getLaneID(v) for v in ("d_s", "d_r")
                                                              if v in b.vehicle.getIDList()}))
    by = {r["veh_id"]: r for r in rows}
    assert set(by) == {"d_s", "d_r"}
    assert (by["d_s"]["action"], by["d_s"]["executed"]) == ("change_lane_to_1", "True")
    assert (by["d_r"]["action"], by["d_r"]["executed"], by["d_r"]["reason"]) == \
        ("change_lane_to_1", "False", "no_connection")
    assert lanes["d_s"] == "WC_1" and lanes["d_r"] == "WC_0"
    s = ctl.summary()["wrong_lane_dodge"]
    assert (s["attempted"], s["executed"], s["not_executed"]) == (2, 1, {"no_connection": 1})


# ---------------------------------------------------------------- illegal_left_box


@pytest.fixture(scope="module")
def box_net(tmp_path_factory):
    """One lane per arm; the W left (WC -> CN) is custom1-only and waits at an internal junction for the opposing
    E -> W through (the proxy net's illegal left in miniature). Junction radius 1 m: the waiting point is 0.25 m
    from the centreline of the N -> S through internal lane (sumolib geometry; 1.6 m with the default radius, 11.6 m
    with 15 m), so a waiter standing there is inside the N-S stream, as on the proxy net (R25: 0.03 m from the HDT_N
    lane-2 centreline)."""
    conns = ('<connection from="WC" to="CS" fromLane="0" toLane="0"/>'
             '<connection from="WC" to="CE" fromLane="0" toLane="0"/>'
             '<connection from="WC" to="CN" fromLane="0" toLane="0" allow="custom1"/>')
    return _cross(tmp_path_factory.mktemp("box"), connections=conns, radius=1)


BOX_ROUTES = ('<flow id="opp" type="car" begin="40" end="90" period="1" departSpeed="max"><route edges="EC CW"/></flow>'
              '<flow id="vio" type="vio" begin="40" end="47" period="1" departSpeed="max"><route edges="WC CN"/></flow>')
CROSS_FLOWS = ('<flow id="ns" type="car" begin="80" end="135" period="2" departSpeed="max"><route edges="NC CS"/></flow>'
               '<flow id="sn" type="car" begin="80" end="135" period="2" departSpeed="max"><route edges="SC CN"/></flow>')
OPP_GREEN_END = 87.0  # E-W green ends (G -> y); N-S green from 90 s


def _box_run(box_net, d, lag, ignore_held=False):
    """Returns (controller, rows, first time each violator is off the hold lanes, junction collisions, teleports).
    `ignore_held` = negative control only (R25/R29): crossing vehicles get junctionModel.ignoreIDs = the held ids."""
    import libsumo
    d.mkdir()
    exits, coll, tp = {}, [], []

    def probe(b, t, c):
        hold = c.info.hold_lanes["LVL_W"]
        coll.extend(x for x in b.simulation.getCollisions()
                    if runner.is_junction_collision({"type": x.type, "lane": x.lane}))
        tp.extend(b.simulation.getStartingTeleportIDList())
        held = " ".join(sorted(c.rules[0].active))
        for v in b.vehicle.getIDList():
            if v.startswith("vio") and v not in exits and b.vehicle.getLaneID(v) not in hold and t > 50                     and b.vehicle.getRoadID(v) != "WC":
                exits[v] = t
            if ignore_held and v[:2] in ("ns", "sn"):
                b.vehicle.setParameter(v, "junctionModel." + "ignoreIDs", held)

    rule = _rule("illegal_left_box", ["vio"], release_lag_s=lag)
    ctl, rows = _simulate(libsumo, box_net, BOX_ROUTES + CROSS_FLOWS, [rule], _site(d, illegal=True), d, 140,
                          probe=probe)
    return ctl, rows, exits, coll, tp


def test_illegal_left_box_fires(box_net, tmp_path):
    _, rows0, exits0, _, _ = _box_run(box_net, tmp_path / "lag0", 0.0)
    ctl, rows3, exits3, _, _ = _box_run(box_net, tmp_path / "lag3", 3.0)
    assert ctl.info.hold_lanes["LVL_W"] and ctl.info.box_lanes["LVL_W"][-1] not in ctl.info.hold_lanes["LVL_W"]
    waiting0 = sorted(t for t in exits0.values() if t > OPP_GREEN_END)
    waiting3 = sorted(t for t in exits3.values() if t > OPP_GREEN_END)
    assert waiting0, "no vehicle waited in the box until the opposing green end"
    assert rows0 == []  # lag 0 = native release, no command
    holds = [r for r in rows3 if r["action"] == "hold_release_lag"]
    assert holds and all(r["executed"] == "True" for r in holds)
    t_nat = min(float(r["t"]) for r in holds)
    assert OPP_GREEN_END < t_nat < waiting0[0] + 0.5  # the native release instant of the lag-0 run
    assert waiting3[0] >= t_nat + 3.0 - 0.15          # first box exit delayed by the lag
    assert all(float(r["t_end"]) == pytest.approx(t_nat + 3.0) for r in holds)


def test_box_hold_in_crossing_stream_no_junction_collisions(box_net, tmp_path):
    """R25/R29: a waiter held into the N-S green stands inside the N-S stream. Plain hold (lag 3) and native (lag 0):
    no junction collision, no teleport. Negative control (test only): the same hold with the crossing vehicles told
    to ignore the held waiter collides."""
    ctl, rows, _, coll3, tp3 = _box_run(box_net, tmp_path / "lag3", 3.0)
    held = [r for r in rows if r["action"] == "hold_release_lag"]
    assert held and max(float(r["t_end"]) for r in held) > 90.0 + 0.5  # the hold reaches into the N-S green
    assert coll3 == [] and tp3 == []
    _, _, _, coll0, tp0 = _box_run(box_net, tmp_path / "lag0", 0.0)
    assert coll0 == [] and tp0 == []
    _, _, _, coll_neg, _ = _box_run(box_net, tmp_path / "neg", 3.0, ignore_held=True)
    assert len(coll_neg) > 0


def test_no_ignore_ids_in_src():
    """R25: no junctionModel.ignoreIDs anywhere in the source tree."""
    hits = [p for p in (REPO_ROOT / "src").rglob("*.py") if "ignoreIDs" in p.read_text(encoding="utf-8")]
    assert hits == []


# ---------------------------------------------------------------- slow_lane_center


def test_slow_lane_center_fires(one_lane, tmp_path):
    import libsumo
    lat = []
    rule = _rule("slow_lane_center", ["rule_moto"], lat_offset=0.8)
    xml = '<vehicle id="v" type="rule_moto" depart="0" departPosLat="-0.5"><route edges="WC CE"/></vehicle>'
    ctl, rows = _simulate(libsumo, one_lane, xml, [rule], _site(tmp_path), tmp_path, 20,
                          probe=lambda b, t, c: lat.append(b.vehicle.getLateralLanePosition("v"))
                          if "v" in b.vehicle.getIDList() else None)
    assert rows and rows[0]["action"] == "center_in_lane" and rows[0]["executed"] == "True"
    assert abs(lat[0] + 0.5) < 0.05 and abs(lat[-1] - 0.8) <= 0.2


# ---------------------------------------------------------------- controller, parity, runner


def test_load_rules_rejects_malformed(tmp_path):
    p = tmp_path / "traci_rules.json"
    p.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="traci_rules.json"):
        load_rules(p)
    p.write_text(json.dumps({"rules": [{"rule_type": "early_start", "vtype_ids": ["a"], "params": {"p": 1}}]}),
                 encoding="utf-8")
    with pytest.raises(ValueError, match="params"):
        load_rules(p)
    assert set(RULE_REGISTRY) == {"early_start", "swarm_red_running", "wrong_lane_dodge", "illegal_left_box",
                                  "slow_lane_center"}


def test_libsumo_traci_same_interventions(one_lane, tmp_path):
    import libsumo
    import traci
    flow = ('<flow id="m" type="rule_moto" begin="0" end="12" period="1" departSpeed="max">'
            '<route edges="WC CE"/></flow>')
    rules = [_rule("swarm_red_running", ["rule_moto"], p0=0.3, k=0.4, p_max=1.0, dt=30.0), EARLY]
    out = []
    for name, backend in (("libsumo", libsumo), ("traci", traci)):
        d = tmp_path / name
        d.mkdir()
        _simulate(backend, one_lane, flow, rules, _site(d), d, 60, seed=4)
        out.append((d / "interventions.csv").read_text(encoding="utf-8"))
    assert out[0] == out[1] and out[0].count("\n") > 2


def test_runner_runs_B1_with_controller(tmp_path):
    spec = json.loads((REPO_ROOT / "rules" / "specs" / "B1_manual.json").read_text(encoding="utf-8"))
    compiled = compile_spec(spec, tmp_path / "B1_manual", site=load_site(PROXY_SITE))
    assert compiled.traci_rules is not None
    inputs = runner.RunInputs("B1_manual", "SYNTHETIC", load_site(PROXY_SITE),
                              REPO_ROOT / "scenario" / "net" / "site.proxy.net.xml",
                              REPO_ROOT / "scenario" / "demand" / "routes_SYNTHETIC.rou.xml", tmp_path / "B1_manual")
    res = runner.run("B1_manual", "SYNTHETIC", seed=1, sim_end_s=200, runs_root=tmp_path / "runs", inputs=inputs)
    m = res.manifest
    assert set(m["interventions"]) == {"swarm_red_running", "early_start"}  # B1 has no box rule (R26)
    for s in m["interventions"].values():
        assert s["executed"] <= s["attempted"]
    assert m["interventions_log"] == "interventions.csv"
    with (res.run_dir / "interventions.csv").open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert tuple(rows[0]) == LOG_COLUMNS if rows else True
    assert sum(s["attempted"] for s in m["interventions"].values()) == len(rows)
    assert m["interventions"]["swarm_red_running"]["counters"]["draws"] > 0
