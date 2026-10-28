"""sumocfg baseline (PLAN Phase 2.3): options from experiment.yaml, output additional, short real run.
SSM modes and warning aggregation: ruling R22."""

import copy
import gzip
import math
import subprocess
from pathlib import Path

import pytest
import sumolib
from lxml import etree

from thesis_sumo.config import REPO_ROOT, load_experiment
from thesis_sumo.demand.build_demand import build_candidate_routes, build_demand
from thesis_sumo.net.build_net import inbound_edges, target_node, target_tls
from thesis_sumo.demand.build_demand import VEHICLE_TYPES
from thesis_sumo.sim.sumocfg import FCD_ZONE_ID, OUTPUT_FILES, SSM_MODES, VIOLATOR_TYPE, violator_ids, write_sumocfg

NET = REPO_ROOT / "scenario" / "net" / "site.proxy.net.xml"
B0_VTYPES = REPO_ROOT / "rules" / "compiled" / "B0" / "vtypes.add.xml"
COUNTS = REPO_ROOT / "data" / "observed" / "SYNTHETIC" / "turn_counts.csv"
SHORT_END_S = 300
CAR_LENGTH_M = 5.0  # passenger default length, Vehicle_Type_Parameter_Defaults


def _xml_root(path: Path):
    """Parse `.xml` or `.xml.gz`."""
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rb") as f:
        return etree.parse(f).getroot()


def _options(cfg: Path) -> dict[str, str]:
    return {el.tag: el.get("value") for section in etree.parse(str(cfg)).getroot() for el in section
            if isinstance(el.tag, str)}


def _exp(ssm_mode: str | None = None, end_s: float = SHORT_END_S) -> dict:
    e = copy.deepcopy(load_experiment())
    e["sim"]["end_s"] = end_s
    if ssm_mode is not None:
        e["sim"]["ssm"]["mode"] = ssm_mode
    return e


@pytest.fixture(scope="module")
def exp():
    return _exp("all")  # the short real run below checks every output, the SSM log included


@pytest.fixture(scope="module")
def routes(tmp_path_factory):
    d = tmp_path_factory.mktemp("routes")
    cands = build_candidate_routes(NET, d / "candidate_routes.rou.xml")
    return build_demand(COUNTS, cands, d / "routes.rou.xml", seed=1)


@pytest.fixture(scope="module")
def cfg(tmp_path_factory, routes, exp):
    run_dir = tmp_path_factory.mktemp("run") / "seed_01"
    return write_sumocfg(run_dir, NET, routes, [B0_VTYPES], seed=1, exp=exp)


@pytest.fixture(scope="module")
def ran(cfg):
    proc = subprocess.run([sumolib.checkBinary("sumo"), "-c", str(cfg)], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", cwd=cfg.parent)
    assert proc.returncode == 0, proc.stderr[-3000:]
    return cfg.parent


@pytest.fixture(scope="module")
def net():
    return sumolib.net.readNet(str(NET))


def test_sumocfg_options(cfg, exp):
    o = _options(cfg)
    assert int(o["aggregate-warnings"]) == exp["sim"]["aggregate_warnings"] == 20
    assert "no-warnings" not in o  # R22: never -W
    assert float(o["step-length"]) == exp["sim"]["step_length_s"] == 0.1
    assert float(o["lateral-resolution"]) == exp["sim"]["lateral_resolution_m"] == 0.4
    assert o["seed"] == "1"
    assert float(o["begin"]) == exp["sim"]["begin_s"] and float(o["end"]) == SHORT_END_S
    assert float(o["device.rerouting.probability"]) == 0
    assert float(o["device.ssm.probability"]) == 1
    assert o["device.ssm.measures"] == "PET"
    assert "posLat" in o["fcd-output.attributes"].split(",")
    assert o["fcd-output.filter-shapes"] == FCD_ZONE_ID
    for key in ("tripinfo-output", "fcd-output", "lanechange-output", "device.ssm.file"):
        assert o[key] == OUTPUT_FILES[key], key
    assert "ignore-route-errors" not in o
    adds = o["additional-files"].split(",")
    assert Path(adds[0]) == B0_VTYPES and len(adds) == 2


def test_output_additional(cfg, net, exp):
    root = etree.parse(str(cfg.parent / OUTPUT_FILES["outputs-additional"])).getroot()
    node = target_node(target_tls(net))
    loops = {el.get("lane"): el for el in root.iter("instantInductionLoop")}
    entry = {ln.getID() for e in inbound_edges(node) for ln in e.getLanes()}
    exit_ = {ln.getID() for e in node.getOutgoing() for ln in e.getLanes()}
    assert set(loops) == entry | exit_ and len(entry) == 14 and len(exit_) == 12  # 12 road + 2 sidewalk lanes (LVL_W, LVL_E)
    for lane_id, el in loops.items():
        length = net.getLane(lane_id).getLength()
        pos = float(el.get("pos"))
        assert (pos > length - 0.5) if lane_id in entry else (pos < 0.5), (lane_id, pos, length)
    (ev,) = root.iter("timedEvent")
    assert ev.get("type") == "SaveTLSStates" and ev.get("source") == target_tls(net).getID()
    (poly,) = root.iter("poly")
    assert poly.get("id") == FCD_ZONE_ID
    cx, cy = node.getCoord()
    pts = [tuple(map(float, p.split(","))) for p in poly.get("shape").split()]
    assert all(math.isclose(math.dist(p, (cx, cy)), exp["sim"]["fcd_radius_m"], rel_tol=1e-3) for p in pts)


def test_short_run_writes_outputs(ran, net, exp):
    trips = list(_xml_root(ran / OUTPUT_FILES["tripinfo-output"]).iter("tripinfo"))
    assert len(trips) > 50
    states = list(_xml_root(ran / OUTPUT_FILES["tls-states"]).iter("tlsState"))
    assert len(states) > 0
    assert {s.get("phase") for s in states} >= {"0", "1"}
    events = list(_xml_root(ran / OUTPUT_FILES["detectors"]).iter("instantOut"))
    entered = {e.get("id").split("__")[0] for e in events if e.get("state") == "enter"}
    assert entered == {"in", "out"}
    assert (ran / OUTPUT_FILES["lanechange-output"]).is_file()
    assert _xml_root(ran / OUTPUT_FILES["device.ssm.file"]).tag == "SSMLog"


def test_fcd_filtered_with_lateral_position(ran, net, exp):
    cx, cy = target_node(target_tls(net)).getCoord()
    rows = list(_xml_root(ran / OUTPUT_FILES["fcd-output"]).iter("vehicle"))
    assert len(rows) > 1000
    assert all("posLat" in r.attrib for r in rows)
    # SUMO keeps a vehicle while any part of its body overlaps the zone (checked: x/y = front bumper of a
    # car_B0 reaches radius + 5 m, its length), so the bound is radius + the longest vehicle (car, 5 m)
    far = max(math.dist((float(r.get("x")), float(r.get("y"))), (cx, cy)) for r in rows)
    assert exp["sim"]["fcd_radius_m"] - 1.0 < far <= exp["sim"]["fcd_radius_m"] + CAR_LENGTH_M


# ---------------------------------------------------------------- SSM modes (R22)


def test_experiment_ssm_defaults():
    sim = load_experiment()["sim"]
    assert sim["ssm"]["mode"] == "off"  # a string: an unquoted YAML off would load as False
    assert sim["aggregate_warnings"] == 20
    assert SSM_MODES == ("off", "violators", "all") and VIOLATOR_TYPE in VEHICLE_TYPES


def test_ssm_off_writes_no_device(tmp_path, routes):
    o = _options(write_sumocfg(tmp_path / "off", NET, routes, [B0_VTYPES], seed=1, exp=_exp("off")))
    assert not [k for k in o if k.startswith("device.ssm")], o
    assert int(o["aggregate-warnings"]) == 20


def test_ssm_violators_explicit_ids(tmp_path, routes):
    ids = violator_ids(routes)
    assert ids and all(i.startswith(VIOLATOR_TYPE) for i in ids)
    o = _options(write_sumocfg(tmp_path / "viol", NET, routes, [B0_VTYPES], seed=1, exp=_exp("violators")))
    assert o["device.ssm.explicit"].replace(",", " ").split() == ids
    assert "device.ssm.probability" not in o
    assert o["device.ssm.measures"] == "PET" and o["device.ssm.file"] == OUTPUT_FILES["device.ssm.file"]


def test_violator_ids_from_gz_and_types(tmp_path):
    xml = ('<routes><vehicle id="m1" type="moto_violator" depart="0"><route edges="a"/></vehicle>'
           '<vehicle id="c1" type="car" depart="1"><route edges="a"/></vehicle>'
           '<vehicle id="m2" type="moto_violator" depart="2"><route edges="a"/></vehicle></routes>')
    with gzip.open(tmp_path / "r.rou.xml.gz", "wt", encoding="utf-8") as f:
        f.write(xml)
    assert violator_ids(tmp_path / "r.rou.xml.gz") == ["m1", "m2"]


def test_ssm_mode_rejected(tmp_path, routes):
    for mode, match in ((False, "quote"), ("some", "ssm.mode")):
        with pytest.raises(ValueError, match=match):
            write_sumocfg(tmp_path / str(mode), NET, routes, [B0_VTYPES], seed=1, exp=_exp(mode))
    (tmp_path / "none.rou.xml").write_text('<routes><vehicle id="c" type="car" depart="0"><route edges="a"/>'
                                           '</vehicle></routes>', encoding="utf-8")
    with pytest.raises(ValueError, match=VIOLATOR_TYPE):
        write_sumocfg(tmp_path / "v", NET, tmp_path / "none.rou.xml", [B0_VTYPES], seed=1, exp=_exp("violators"))


def test_ssm_violators_run_logs_only_violators(tmp_path, routes):
    """A real run: with `--device.ssm.explicit` only the named violators carry an SSM device (ego ids)."""
    cfg = write_sumocfg(tmp_path / "run", NET, routes, [B0_VTYPES], seed=1, exp=_exp("violators", end_s=200))
    proc = subprocess.run([sumolib.checkBinary("sumo"), "-c", str(cfg)], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", cwd=cfg.parent)
    assert proc.returncode == 0, proc.stderr[-3000:]
    egos = {c.get("ego") for c in _xml_root(cfg.parent / OUTPUT_FILES["device.ssm.file"]).iter("conflict")}
    assert egos and egos <= set(violator_ids(routes)), egos


def test_relative_run_dir(tmp_path, monkeypatch, routes):
    """M1: a relative run_dir works (sumo runs with cwd=run_dir, so the config path must be absolute)."""
    monkeypatch.chdir(tmp_path)
    cfg = write_sumocfg(Path("rel") / "seed_01", NET, routes, [B0_VTYPES], seed=1, exp=_exp("off"))
    assert cfg.is_absolute() and cfg == (tmp_path / "rel" / "seed_01" / "run.sumocfg") and cfg.is_file()
