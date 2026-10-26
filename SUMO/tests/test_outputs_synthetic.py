"""to_observed_schema against independent truth: hand-written SUMO outputs on a tiny cross net, expected rows
computed by hand (net lengths / lane ids read with sumolib, not with the code under test)."""

import gzip
import json
import math
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import sumolib

from thesis_sumo.schema_observed import TABLES
from thesis_sumo.sim import outputs

RANGE_M = 30.0  # observation.queue_range_m of the fixture
WIDTH_M = 3.0   # every lane
NAN = float("nan")
# approach of each inbound edge of the tiny net (W/E arms named Le Van Luong, N/S Hoang Dao Thuy)
EDGE_APPROACH = {"WC": "LVL_W", "EC": "LVL_E", "NC": "HDT_N", "SC": "HDT_S"}
# (t, state of LVL_W/LVL_E, state of HDT_N/HDT_S); t=5 repeats a state (must not create an event)
PROGRAM = [(0, "G", "r"), (5, "G", "r"), (10, "y", "r"), (12, "r", "G"), (18, "r", "y"), (20, "G", "r"),
           (30, "y", "r"), (32, "r", "G"), (40, "G", "r")]
END_S = 45.0
TIMESTEPS = [3.0, 3.5, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 12.0, 13.0, 13.4, 13.5, 13.9, 19.0, 20.0, 20.9, 21.1, 22.0,
             22.5, 23.0, 25.0, 28.0, 30.0, 31.0, 32.0, 33.0, 40.0, 45.0]


def _build_net(d: Path) -> Path:
    (d / "n.nod.xml").write_text(
        '<nodes><node id="C" x="0" y="0" type="traffic_light"/><node id="W" x="-150" y="0"/>'
        '<node id="E" x="150" y="0"/><node id="S" x="0" y="-150"/><node id="N" x="0" y="150"/></nodes>',
        encoding="utf-8")
    edges = [("WC", "W", "C", "Le Van Luong"), ("CE", "C", "E", "Le Van Luong"), ("EC", "E", "C", "Le Van Luong"),
             ("CW", "C", "W", "Le Van Luong"), ("SC", "S", "C", "Hoang Dao Thuy"), ("CN", "C", "N", "Hoang Dao Thuy"),
             ("NC", "N", "C", "Hoang Dao Thuy"), ("CS", "C", "S", "Hoang Dao Thuy")]
    (d / "n.edg.xml").write_text("<edges>" + "".join(
        f'<edge id="{i}" from="{f}" to="{t}" name="{n}" numLanes="2" speed="13.9" width="{WIDTH_M}"/>'
        for i, f, t, n in edges) + "</edges>", encoding="utf-8")
    # WC: explicit connections replace the guessed ones; the left WC_1 -> CN_1 is custom1-only (illegal_l)
    (d / "n.con.xml").write_text(
        '<connections><connection from="WC" to="CE" fromLane="0" toLane="0"/>'
        '<connection from="WC" to="CE" fromLane="1" toLane="1"/><connection from="WC" to="CS" fromLane="0" toLane="0"/>'
        '<connection from="WC" to="CN" fromLane="1" toLane="1" allow="custom1"/></connections>', encoding="utf-8")
    net = d / "box.net.xml"
    subprocess.run([sumolib.checkBinary("netconvert"), "-n", str(d / "n.nod.xml"), "-e", str(d / "n.edg.xml"),
                    "-x", str(d / "n.con.xml"), "-o", str(net)], check=True, capture_output=True)
    return net


def _state(net, we: str, ns: str) -> str:
    tls = net.getTrafficLights()[0]
    chars = {}
    for in_lane, out_lane, idx in tls.getConnections():
        app = EDGE_APPROACH[in_lane.getEdge().getID()]
        s = we if app.startswith("LVL") else ns
        (conn,) = [c for c in in_lane.getOutgoing() if c.getToLane() == out_lane]
        chars[idx] = "g" if s == "G" and conn.getDirection() in ("l", "t") else s
    return "".join(chars[i] for i in range(len(chars)))


def _via(net, frm: str, to: str) -> list:
    """Internal-lane chain of the connection frm -> to (lane ids)."""
    (conn,) = [c for c in net.getLane(frm).getOutgoing() if c.getToLane().getID() == to]
    chain = [net.getLane(conn.getViaLaneID())]
    while True:
        nxt = [c.getViaLaneID() for c in chain[-1].getOutgoing() if c.getViaLaneID()]
        if not nxt:
            return [ln.getID() for ln in chain]
        chain.append(net.getLane(nxt[0]))


@pytest.fixture(scope="module")
def case(tmp_path_factory):
    d = tmp_path_factory.mktemp("synthetic")
    net_path = _build_net(d)
    net = sumolib.net.readNet(str(net_path), withInternal=True)
    L = net.getLane("WC_0").getLength()
    box1, box2 = _via(net, "WC_1", "CN_1")
    straight_w0 = _via(net, "WC_0", "CE_0")[0]
    box1_len = net.getLane(box1).getLength()

    rows = {t: [] for t in TIMESTEPS}

    def at(t, vid, typ, lane, pos, pos_lat=0.0, speed=0.0):
        rows[t].append((vid, typ, lane, pos, pos_lat, speed))

    def hold(vid, typ, lane, pos, t0, t1, speed=0.0, pos_lat=0.0):
        for t in TIMESTEPS:
            if t0 <= t <= t1:
                at(t, vid, typ, lane, pos, pos_lat, speed)

    # crossers
    at(3.0, "m1", "moto_B0", "WC_1", L - 34); at(3.5, "m1", "moto_B0", "WC_1", L - 26, speed=16)
    at(5.0, "m1", "moto_B0", "WC_1", L - 0.5, 0.4, 16)
    at(12.0, "c1", "car_B0", "WC_0", L - 20, speed=10); at(13.4, "c1", "car_B0", "WC_0", L - 0.3, -0.2, 10)
    at(13.0, "c2", "car_B0", "NC_0", L - 31, speed=4); at(13.5, "c2", "car_B0", "NC_0", L - 29, speed=4)
    at(13.9, "c2", "car_B0", "NC_0", L - 0.4, 0.0, 10)
    at(19.0, "v1", "viol_B0", "WC_1", L - 40, speed=10); at(20.0, "v1", "viol_B0", "WC_1", L - 10, speed=8)
    at(20.9, "v1", "viol_B0", "WC_1", L - 0.5, 0.0, 6)
    for t, sp in ((21.1, 5.0), (22.0, 4.0), (22.5, 3.0), (23.0, 2.0)):
        at(t, "v1", "viol_B0", box1, 0.5, 0.0, sp)
    hold("v1", "viol_B0", box1, 3.0, 25.0, 32.0)
    at(33.0, "v1", "viol_B0", "CN_1", 0.05, 0.0, 3)
    # queue at the LVL_W green onset t=20 (cycle 0)
    at(20.0, "q1", "moto_B0", "WC_0", L - 1.0, 0.5)
    at(20.0, "q2", "car_B0", "WC_1", L - 3.0, 0.0, 0.1)
    at(20.0, "q3", "moto_B0", "WC_0", L - 15.0, -0.5)
    at(20.0, "q5", "car_B0", "WC_0", L - 26.0)
    at(20.0, "q6", "moto_B0", "WC_1", L - 35.0)               # halting but outside the range
    at(20.0, "o1", "moto_B0", straight_w0, 1.5, 0.3)          # overshoot past the stop line
    at(20.0, "n1", "car_B0", "NC_0", L - 5.0)                 # other approach
    # box: cycle -1 = [0, 20): v3 halts and vanishes (no row at 8.0), v5 passes through
    hold("v3", "viol_B0", box1, 2.0, 5.0, 7.0)
    for t in (6.0, 7.0, 8.0):
        at(t, "v5", "viol_B0", box1, 1.0 + (t - 6.0), 0.0, 4.0)
    at(9.0, "v5", "viol_B0", "CN_1", 0.5, 0.0, 4.0)
    # box: cycle 0 = [20, 40)
    hold("v0", "viol_B0", box2, 1.0, 20.0, 30.0, pos_lat=-0.2)
    at(31.0, "v0", "viol_B0", "CN_1", 0.5, 0.0, 3.0)
    at(22.0, "v2", "viol_B0", box1, 1.0, 0.0, 6.0); at(22.5, "v2", "viol_B0", box2, 0.5, 0.0, 6.0)
    at(23.0, "v2", "viol_B0", "CN_1", 1.0, 0.0, 6.0)           # early exit through a gap
    at(28.0, "v4", "viol_B0", box1, 1.0, 0.0, 3.0)
    hold("v4", "viol_B0", box1, 2.0, 30.0, END_S)              # still in the box at the end

    run = d / "run"
    run.mkdir()
    with (run / "fcd.xml").open("w", encoding="utf-8") as f:  # plain .xml: reader falls back from fcd.xml.gz
        f.write("<fcd-export>\n")
        for t in TIMESTEPS:
            f.write(f'  <timestep time="{t:.2f}">\n')
            for vid, typ, lane, pos, plat, sp in rows[t]:
                f.write(f'    <vehicle id="{vid}" x="0" y="0" angle="0" type="{typ}" speed="{sp:.2f}" pos="{pos:.2f}" '
                        f'lane="{lane}" posLat="{plat:.2f}"/>\n')
            f.write("  </timestep>\n")
        f.write("</fcd-export>\n")
    tls = ['<tlsStates>'] + [f'<tlsState time="{t:.2f}" id="C" programID="0" phase="0" state="{_state(net, we, ns)}"/>'
                             for t, we, ns in PROGRAM] + ["</tlsStates>"]
    with gzip.open(run / "tls_states.xml.gz", "wt", encoding="utf-8") as f:  # .gz: reader falls back from .xml
        f.write("\n".join(tls))
    det = [("in__WC_1", 5.03, "m1", "moto_B0"), ("in__WC_0", 5.05, "m1", "moto_B0"), ("out__CE_1", 7.0, "m1", "moto_B0"),
           ("in__WC_0", 13.5, "c1", "car_B0"), ("in__NC_0", 14.0, "c2", "car_B0"), ("out__CS_0", 16.0, "c2", "car_B0"),
           ("in__WC_1", 21.0, "v1", "viol_B0"), ("out__CN_1", 33.05, "v1", "viol_B0")]
    (run / "detectors.xml").write_text(
        "<instantE1>\n" + "".join(
            f'<instantOut id="{i}" time="{t:.2f}" state="enter" vehID="{v}" speed="5" length="2" type="{ty}"/>\n'
            f'<instantOut id="{i}" time="{t + 0.05:.2f}" state="leave" vehID="{v}" speed="5" length="2" type="{ty}"/>\n'
            for i, t, v, ty in det) + "</instantE1>\n", encoding="utf-8")
    routes = d / "r.rou.xml"
    routes.write_text('<routes><route id="ws" edges="WC CE"/>'
                      '<vehicle id="m1" depart="0" route="ws"/><vehicle id="c1" depart="0"><route edges="WC CE"/></vehicle>'
                      '<vehicle id="c2" depart="0"><route edges="NC CS"/></vehicle>'
                      '<vehicle id="v1" depart="0"><route edges="WC CN"/></vehicle></routes>', encoding="utf-8")
    (run / "run.sumocfg").write_text(f'<configuration><input><net-file value="{net_path}"/>'
                                     f'<route-files value="{routes}"/></input></configuration>', encoding="utf-8")
    (run / "manifest.json").write_text(json.dumps({"config": {
        "sim": {"begin_s": 0, "end_s": END_S, "fcd_radius_m": 100}, "observation": {"queue_range_m": RANGE_M}}}),
        encoding="utf-8")
    (run / "vtypes.json").write_text(json.dumps({
        "car_B0": {"vclass": "passenger", "length": 5.0}, "moto_B0": {"vclass": "motorcycle", "length": 2.2},
        "viol_B0": {"vclass": "custom1", "length": 2.2}}), encoding="utf-8")
    return {"tables": outputs.to_observed_schema(run), "run": run, "L": L, "box1_len": box1_len}


def _records(df):
    return [[None if isinstance(v, float) and math.isnan(v) else v for v in row] for row in df.values.tolist()]


def test_all_tables_with_columns(case):
    for name, cols in TABLES.items():
        assert list(case["tables"][name].columns) == cols
        assert list(pd.read_csv(case["run"] / outputs.OBSERVED_DIR / f"{name}.csv").columns) == cols


def test_signal_events_truth(case):
    ev = case["tables"]["signal_events"]
    for g in ("LVL_W", "LVL_E"):
        assert ev[ev["approach_group"] == g][["t", "state"]].values.tolist() == \
            [[0, "G"], [10, "y"], [12, "r"], [20, "G"], [30, "y"], [32, "r"], [40, "G"]]
    for g in ("HDT_N", "HDT_S"):
        assert ev[ev["approach_group"] == g][["t", "state"]].values.tolist() == \
            [[0, "r"], [12, "G"], [18, "y"], [20, "r"], [32, "G"], [40, "r"]]


def test_crossings_truth(case):
    cr = case["tables"]["stopline_crossings"]
    assert _records(cr) == [
        [5.03, "LVL_W", pytest.approx(4.5 + 0.4), "moto", "m1", "G"],   # duplicate enter at 5.05 ignored
        [13.5, "LVL_W", pytest.approx(1.5 - 0.2), "car", "c1", "r"],    # signal_events: LVL_W red from 12
        [14.0, "HDT_N", pytest.approx(1.5), "car", "c2", "G"],
        [21.0, "LVL_W", pytest.approx(4.5), "moto", "v1", "G"],
    ]


def test_turn_counts_truth(case):
    tc = case["tables"]["turn_counts"]
    nonzero = tc[tc["count"] > 0][["approach", "movement", "vclass", "count"]].values.tolist()
    assert sorted(nonzero) == [["HDT_N", "s", "car", 1], ["LVL_W", "illegal_l", "moto", 1], ["LVL_W", "s", "car", 1],
                               ["LVL_W", "s", "moto", 1]]
    assert (tc["interval_start"] == 0).all() and (tc["interval_end"] == 900).all()
    assert len(tc) == 15 * 2 - 1  # 15 movements x 2 vclasses, no car illegal_l


def test_queue_snapshots_truth(case):
    q = case["tables"]["queue_snapshots"]
    w = q[q["approach"] == "LVL_W"]
    # q1 (1.0 m, moto), q2 (3.0, car, rear 8.0), q3 (15.0 <= 8+10, moto, rear 17.2), q5 (26.0 <= 27.2, car,
    # rear 31.0) -> tail 31.0 capped at the 30 m range (censored); q6 outside the range; o1 past the stop line
    assert _records(w) == [[0, 20.0, "LVL_W", 30.0, 2, 2, 30.0 * 2 * WIDTH_M], [1, 40.0, "LVL_W", 0.0, 0, 0, 0.0]]
    assert (q.loc[q["approach"] != "LVL_W", ["queue_length_m", "n_car", "n_moto"]] == 0).all().all()
    assert q[q["approach"] == "HDT_N"]["t_green_onset"].tolist() == [12.0, 32.0]


def test_lateral_snapshots_truth(case):
    lat = case["tables"]["lateral_snapshots"]
    assert _records(lat) == [
        [0, "LVL_W", "v0", "moto", pytest.approx(4.5 - 0.2), pytest.approx(-(case["box1_len"] + 1.0))],
        [0, "LVL_W", "o1", "moto", pytest.approx(1.5 + 0.3), pytest.approx(-1.5)],
        [0, "LVL_W", "q1", "moto", pytest.approx(1.5 + 0.5), pytest.approx(1.0)],
        [0, "LVL_W", "q2", "car", pytest.approx(4.5), pytest.approx(3.0)],
        [0, "LVL_W", "q3", "moto", pytest.approx(1.5 - 0.5), pytest.approx(15.0)],
        [0, "LVL_W", "q5", "car", pytest.approx(1.5), pytest.approx(26.0)],
        [1, "LVL_W", "v4", "moto", pytest.approx(4.5), pytest.approx(-2.0)],
    ]


def test_box_queue_truth(case):
    b = case["tables"]["box_queue"]
    # opposing LVL_E through green ends at 10 and 30
    # cycle -1: v3 halts then vanishes at 8.0 (left out), v5 leaves at 9.0
    # cycle 0: halting at 30 = v0, v1, v4; exits v2 23.0 (early, through a gap), v0 31.0, v1 33.0; v4 never
    assert _records(b) == [[-1, 10.0, "LVL_W", 0, 9.0, 9.0], [0, 30.0, "LVL_W", 3, 23.0, None]]


def test_traversals_truth(case):
    tr = case["tables"]["traversals"]
    assert _records(tr) == [
        ["m1", "moto", "LVL_W", "s", "LVL_E", pytest.approx(4.9), pytest.approx(3.0 + 4 / 8 * 0.5), 5.03, 7.0],
        ["c1", "car", "LVL_W", "s", "LVL_E", pytest.approx(1.3), None, 13.5, None],  # first seen inside range
        ["c2", "car", "HDT_N", "s", "HDT_S", pytest.approx(1.5), pytest.approx(13.0 + 1 / 2 * 0.5), 14.0, 16.0],
        ["v1", "moto", "LVL_W", "illegal_l", "HDT_N", pytest.approx(4.5), pytest.approx(19.0 + 10 / 30), 21.0, 33.05],
    ]


def test_opposing_missing_raises(case):
    net_path, _ = outputs._sumocfg_inputs(case["run"])
    geo = outputs.junction_geometry(net_path)
    with pytest.raises(ValueError, match="'XYZ' has no opposing approach"):
        geo.opposing_of("XYZ")


def test_shared_green_required():
    ev = pd.DataFrame([(0, "A", "G"), (0, "B", "r"), (10, "A", "r"), (10, "B", "G")],
                      columns=["t", "approach_group", "state"])
    with pytest.raises(ValueError, match="never share a green phase"):
        outputs.check_shared_green(ev, "A", "B")
    outputs.check_shared_green(pd.DataFrame([(0, "A", "G"), (0, "B", "G")], columns=ev.columns), "A", "B")


def test_queue_range_required():
    with pytest.raises(ValueError, match="queue_range_m"):
        outputs.queue_range_m({"observation": {"queue_range_m": None}})
    assert np.isclose(outputs.queue_range_m({"observation": {"queue_range_m": 80}}), 80.0)
