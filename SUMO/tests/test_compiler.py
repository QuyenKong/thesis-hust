"""Rule-spec compiler (PLAN 4.4): spec -> vtypes.add.xml (vTypeDistributions car / moto / moto_violator) +
traci_rules.json."""

import copy
import json
import subprocess

import pytest
import sumolib
from lxml import etree

from thesis_sumo.config import REPO_ROOT, MissingFieldDataError, load_experiment, load_site
from thesis_sumo.rules import compiler
from thesis_sumo.rules.compiler import (CUSTOM1_MOTORCYCLE_DEFAULTS, CUSTOM2_PASSENGER_DEFAULTS, InvalidSpecError,
                                        compile_spec, fmt_value)
from thesis_sumo.rules.schema import DISTRIBUTION_OF_VCLASS, load_bounds, load_excluded

SPECS = REPO_ROOT / "rules" / "specs"
B1 = SPECS / "B1_manual.json"
B0 = SPECS / "B0.json"
B0_HANDWRITTEN = REPO_ROOT / "rules" / "compiled" / "B0" / "vtypes.add.xml"
SNAPSHOT = REPO_ROOT / "tests" / "snapshots" / "B1_vtypes.add.xml"
PROXY_SITE = REPO_ROOT / "config" / "site.proxy.yaml"
PROXY_NET = REPO_ROOT / "scenario" / "net" / "site.proxy.net.xml"
ROUTES_D1 = REPO_ROOT / "scenario" / "demand" / "routes_PROXY_D1.rou.xml"


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def site():
    return load_site(PROXY_SITE)


@pytest.fixture
def b1():
    return _load(B1)


@pytest.fixture(scope="module")
def compiled_b1(tmp_path_factory, site):
    return compile_spec(_load(B1), tmp_path_factory.mktemp("B1"), site=site)


def _vtypes(path):
    """{distribution id: [vType attribute dict, ...]} in file order."""
    root = etree.parse(str(path)).getroot()
    return {d.get("id"): [dict(t.attrib) for t in d.findall("vType")] for d in root.iter("vTypeDistribution")}


def _split_moto(spec):
    """B1 with the motorcycle distribution split into two archetypes (0.7 / 0.3)."""
    spec = copy.deepcopy(spec)
    moto = next(a for a in spec["driver_archetypes"] if a["base_vclass"] == "motorcycle")
    other = copy.deepcopy(moto)
    other.update(id="moto_slow", share=0.3)
    other["params"]["speedFactor"] = 0.8
    moto["share"] = 0.7
    spec["driver_archetypes"].insert(spec["driver_archetypes"].index(moto) + 1, other)
    return spec


# ---------------------------------------------------------------- tests named in the brief


def test_snapshot_B1(compiled_b1):
    data = compiled_b1.vtypes.read_bytes()
    assert b"\r" not in data
    assert data == SNAPSHOT.read_bytes()


def test_distribution_ids(compiled_b1, b1):
    dists = _vtypes(compiled_b1.vtypes)
    assert list(dists) == ["car", "moto", "moto_violator"]
    for arch in b1["driver_archetypes"]:
        (vt,) = [t for t in dists[DISTRIBUTION_OF_VCLASS[arch["base_vclass"]]] if t["id"] == arch["id"]]
        assert vt["vClass"] == arch["base_vclass"]
        assert vt["laneChangeModel"] == "SL2015"
        assert float(vt["probability"]) == arch["share"]
    assert all(t["laneChangeModel"] == "SL2015" for ts in dists.values() for t in ts)


def test_sumo_loads_compiled(compiled_b1):
    """SUMO 1.27 loads the compiled additional (XSD-validated through its schema declaration) for 10 s."""
    root = etree.parse(str(compiled_b1.vtypes)).getroot()
    assert root.get("{http://www.w3.org/2001/XMLSchema-instance}noNamespaceSchemaLocation", "").endswith(
        "additional_file.xsd")
    sim = load_experiment()["sim"]
    proc = subprocess.run([sumolib.checkBinary("sumo"), "-n", str(PROXY_NET.resolve()),
                           "-r", str(ROUTES_D1.resolve()), "-a", str(compiled_b1.vtypes.resolve()),
                           "--end", "10", "--step-length", str(sim["step_length_s"]),
                           "--lateral-resolution", str(sim["lateral_resolution_m"]), "--seed", "1",
                           "--no-step-log"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert proc.returncode == 0, proc.stderr
    out = proc.stderr + proc.stdout
    assert "Warning" not in out and "Error" not in out, out


# ---------------------------------------------------------------- vType content


def test_custom1_defaults_match_handwritten_B0():
    """The motorcycle defaults the compiler gives custom1 are exactly those of the hand-written B0 file
    (which tests/test_demand.py checks against SUMO's motorcycle vClass)."""
    (mv,) = _vtypes(B0_HANDWRITTEN)["moto_violator"]
    base = {k: v for k, v in mv.items() if k not in ("id", "vClass", "laneChangeModel", "probability")}
    assert {k: fmt_value(v) for k, v in CUSTOM1_MOTORCYCLE_DEFAULTS.items()} == base
    assert list(CUSTOM1_MOTORCYCLE_DEFAULTS) == list(base)  # same attribute order


def test_spec_params_override_custom1_defaults(compiled_b1, b1):
    (mv,) = _vtypes(compiled_b1.vtypes)["moto_violator"]
    params = next(a for a in b1["driver_archetypes"] if a["base_vclass"] == "custom1")["params"]
    for k, v in params.items():
        assert mv[k] == fmt_value(v), k
    for k, v in CUSTOM1_MOTORCYCLE_DEFAULTS.items():
        if k not in params:
            assert mv[k] == fmt_value(v), k


def test_custom1_matches_motorcycle_in_sumo(tmp_path, site, b1):
    """custom1 and motorcycle archetypes with the same params are identical in every SUMO vType getter."""
    import libsumo

    spec = copy.deepcopy(b1)
    moto = next(a for a in spec["driver_archetypes"] if a["base_vclass"] == "motorcycle")
    mv = next(a for a in spec["driver_archetypes"] if a["base_vclass"] == "custom1")
    mv["params"] = dict(moto["params"])
    out = compile_spec(spec, tmp_path, site=site)
    libsumo.start([sumolib.checkBinary("sumo"), "-n", str(PROXY_NET), "-a", str(out.vtypes), "--end", "1",
                   "--no-step-log", "true"])
    try:
        vt = libsumo.vehicletype
        skip = {"getIDList", "getIDCount", "getVehicleClass"}
        getters = [g for g in dir(vt) if g.startswith("get") and g not in skip
                   and "Subscription" not in g and "Parameter" not in g]
        assert len(getters) > 20
        diffs = {g: (getattr(vt, g)(moto["id"]), getattr(vt, g)(mv["id"])) for g in getters
                 if getattr(vt, g)(moto["id"]) != getattr(vt, g)(mv["id"])}
        assert diffs == {}
        assert vt.getVehicleClass(mv["id"]) == "custom1"
        assert vt.getMinGap(moto["id"]) == moto["params"]["minGap"]
    finally:
        libsumo.close()


def test_only_allowed_attributes(compiled_b1):
    bounds, excluded = load_bounds(), load_excluded()
    allowed = {"id", "vClass", "laneChangeModel", "probability"} | set(CUSTOM1_MOTORCYCLE_DEFAULTS) | set(bounds)
    names = {k for ts in _vtypes(compiled_b1.vtypes).values() for t in ts for k in t}
    assert names <= allowed
    assert not names & set(excluded)


def test_default_valued_params_written_explicitly(compiled_b1):
    """B1 sets jmTimegapMinor = 1.0 (its SUMO default): the compiler writes it, never drops it."""
    (mv,) = _vtypes(compiled_b1.vtypes)["moto_violator"]
    assert mv["jmTimegapMinor"] == "1"


def test_param_order_independent_of_spec(tmp_path, site, b1):
    shuffled = copy.deepcopy(b1)
    for a in shuffled["driver_archetypes"]:
        a["params"] = dict(reversed(list(a["params"].items())))
    a = compile_spec(b1, tmp_path / "a", site=site)
    b = compile_spec(shuffled, tmp_path / "b", site=site)
    assert a.vtypes.read_bytes() == b.vtypes.read_bytes()
    assert a.traci_rules.read_bytes() == b.traci_rules.read_bytes()


@pytest.mark.parametrize("value, text", [(1.0, "1"), (1, "1"), (0.3, "0.3"), (55.55555555555556, "55.55555555555556"),
                                         (-1.0, "-1"), (2.5, "2.5"), (0.1 + 0.2, "0.30000000000000004"),
                                         ("center", "center"), ("1.5", "1.5")])
def test_fmt_value(value, text):
    assert fmt_value(value) == text


def test_shares_become_probabilities(tmp_path, site, b1):
    out = compile_spec(_split_moto(b1), tmp_path, site=site)
    moto = _vtypes(out.vtypes)["moto"]
    assert [(t["id"], t["probability"]) for t in moto] == [("moto_saval", "0.7"), ("moto_slow", "0.3")]
    assert moto[1]["speedFactor"] == "0.8"


def test_vehicles_get_member_vtype_id(tmp_path, site, b1):
    """A vehicle of type 'moto' (a vTypeDistribution) reports the drawn member vType id via getTypeID: the
    runtime controller (Task 9) matches vehicles to archetypes through traci_rules.json `vtype_ids`."""
    import libsumo

    out = compile_spec(_split_moto(b1), tmp_path, site=site)
    rules = _load(out.traci_rules)
    dist_of = {a["vtype_id"]: a["distribution"] for a in rules["archetypes"].values()}
    sim = load_experiment()["sim"]
    libsumo.start([sumolib.checkBinary("sumo"), "-n", str(PROXY_NET), "-r", str(ROUTES_D1), "-a", str(out.vtypes),
                   "--end", "60", "--step-length", str(sim["step_length_s"]), "--lateral-resolution",
                   str(sim["lateral_resolution_m"]), "--seed", "1", "--no-step-log", "true", "--no-warnings", "true"])
    seen = {}
    try:
        while libsumo.simulation.getTime() < 60:
            libsumo.simulationStep()
            for vid in libsumo.simulation.getDepartedIDList():
                seen[vid] = libsumo.vehicle.getTypeID(vid)
    finally:
        libsumo.close()
    assert seen
    assert set(seen.values()) <= set(dist_of)
    assert {"moto_saval", "moto_slow"} <= set(seen.values())  # both members of 'moto' are drawn
    for vid, tid in seen.items():  # route-file vehicle ids start with the distribution id
        assert vid.rsplit("_", 2)[0] == dist_of[tid], (vid, tid)


# ---------------------------------------------------------------- traci_rules.json


def test_traci_rules_json(compiled_b1, b1):
    data = compiled_b1.traci_rules.read_bytes()
    assert b"\r" not in data and data.endswith(b"\n")
    doc = json.loads(data)
    assert doc["spec_id"] == "B1_manual"
    assert doc["archetypes"] == {
        a["id"]: {"base_vclass": a["base_vclass"], "distribution": DISTRIBUTION_OF_VCLASS[a["base_vclass"]],
                  "vtype_id": a["id"], "share": a["share"]} for a in b1["driver_archetypes"]}
    assert [r["rule_type"] for r in doc["rules"]] == [r["rule_type"] for r in b1["traci_rules"]]
    for got, want in zip(doc["rules"], b1["traci_rules"]):
        assert got["applies_to"] == want["applies_to"]
        assert got["vtype_ids"] == [doc["archetypes"][a]["vtype_id"] for a in want["applies_to"]]
        assert got["params"] == want["params"]
    # every vtype id in the JSON exists in the compiled vtypes file
    ids = {t["id"] for ts in _vtypes(compiled_b1.vtypes).values() for t in ts}
    assert {a["vtype_id"] for a in doc["archetypes"].values()} == ids


def test_no_rules_no_traci_file(tmp_path, site):
    """A spec without TraCI rules writes no traci_rules.json (the runner requires a controller whenever the
    file exists) and removes a stale one."""
    (tmp_path / "traci_rules.json").write_text("{}", encoding="utf-8")
    out = compile_spec(_load(B0), tmp_path, site=site)
    assert out.traci_rules is None
    assert not (tmp_path / "traci_rules.json").exists()


# ---------------------------------------------------------------- refusal


def test_invalid_spec_refused(tmp_path, site, b1):
    b1["driver_archetypes"][0]["params"]["tau"] = 99.0
    b1["driver_archetypes"][1]["params"]["jmIgnoreFoeProb"] = 0.5
    with pytest.raises(InvalidSpecError) as exc:
        compile_spec(b1, tmp_path / "out", site=site)
    codes = {i["code"] for i in exc.value.issues}
    assert codes == {"out_of_bounds", "unknown_attr"}
    assert "tau" in str(exc.value) and "jmIgnoreFoeProb" in str(exc.value)
    assert not (tmp_path / "out").exists()


def test_measured_site_without_lane_widths_raises(tmp_path, b1):
    """B1 sets minGapLat: against the measured site file (lane widths TODO_MEASURE) compiling raises."""
    with pytest.raises(MissingFieldDataError):
        compile_spec(b1, tmp_path, site=load_site())


def test_handwritten_B0_dir_protected(site):
    with pytest.raises(ValueError, match="hand-written"):
        compile_spec(_load(B0), site=site)


# ---------------------------------------------------------------- B0 as a spec


def test_B0_spec_equivalent_to_handwritten(tmp_path, site):
    """rules/specs/B0.json compiles to the same vTypes, attribute by attribute, as the hand-written
    rules/compiled/B0/vtypes.add.xml (which is kept; only comments and the schema declaration differ)."""
    out = compile_spec(_load(B0), tmp_path, site=site)
    assert _vtypes(out.vtypes) == _vtypes(B0_HANDWRITTEN)
    assert list(_vtypes(out.vtypes)) == ["car", "moto", "moto_violator", "car_violator"]


def test_custom2_defaults_match_handwritten_B0():
    """The passenger defaults the compiler gives custom2 are exactly those of the hand-written B0 car_violator
    (which tests/test_demand.py checks against SUMO's passenger vClass), in the custom1 attribute order."""
    (cv,) = _vtypes(B0_HANDWRITTEN)["car_violator"]
    base = {k: v for k, v in cv.items() if k not in ("id", "vClass", "laneChangeModel", "probability")}
    assert {k: fmt_value(v) for k, v in CUSTOM2_PASSENGER_DEFAULTS.items()} == base
    assert list(CUSTOM2_PASSENGER_DEFAULTS) == list(base) == list(CUSTOM1_MOTORCYCLE_DEFAULTS)


def test_car_violator_optional(tmp_path, site, b1):
    """No custom2 archetype (B1): valid, and no car_violator distribution (nothing references it yet); with one,
    car_violator comes after moto_violator and spec params override the passenger defaults."""
    assert not any(a["base_vclass"] == "custom2" for a in b1["driver_archetypes"])
    spec = copy.deepcopy(b1)
    spec["driver_archetypes"].append({"id": "car_vio", "base_vclass": "custom2", "share": 1.0,
                                      "params": {"minGap": 1.5}})
    dists = _vtypes(compile_spec(spec, tmp_path, site=site).vtypes)
    assert list(dists) == ["car", "moto", "moto_violator", "car_violator"]
    (cv,) = dists["car_violator"]
    assert cv["vClass"] == "custom2" and cv["minGap"] == "1.5" and cv["length"] == "5"


# ---------------------------------------------------------------- CLI


def test_cli(tmp_path, capsys):
    rc = compiler.main([str(B1), "--site", str(PROXY_SITE), "--out", str(tmp_path)])
    assert rc == 0
    assert (tmp_path / "vtypes.add.xml").read_bytes() == SNAPSHOT.read_bytes()
    assert (tmp_path / "traci_rules.json").is_file()
    assert "vtypes.add.xml" in capsys.readouterr().out


def test_cli_measured_site_missing_lane_widths(tmp_path, capsys):
    rc = compiler.main([str(B1), "--out", str(tmp_path / "out")])
    assert rc == 2
    assert "lane_widths_m" in capsys.readouterr().err
    assert not (tmp_path / "out").exists()


def test_cli_invalid(tmp_path, capsys, b1):
    b1["driver_archetypes"][0]["params"]["tau"] = 99.0
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(b1), encoding="utf-8")
    rc = compiler.main([str(bad), "--site", str(PROXY_SITE), "--out", str(tmp_path / "out")])
    assert rc == 1
    assert "out_of_bounds" in capsys.readouterr().out
    assert not (tmp_path / "out").exists()
