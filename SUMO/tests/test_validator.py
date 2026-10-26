"""Rule-spec space (PLAN 4.1-4.3): parameter bounds, TraCI rule params, validator and validity log.

Validator issues are fed back to the LLM verbatim (Task 12), so the tests also check that messages name the
allowed range / names."""

import copy
import csv
import json
import subprocess

import pytest
import sumolib

from thesis_sumo.config import REPO_ROOT, MissingFieldDataError, Site, load_site
from thesis_sumo.rules.schema import (BEHAVIOR_GROUPS, DISTRIBUTION_OF_VCLASS, RULE_VCLASSES, TRACI_RULE_PARAMS,
                                      VCLASSES, load_bounds, load_json_schema)
from thesis_sumo.rules.validator import ISSUE_CODES, ValidityLog, validate

B1 = REPO_ROOT / "rules" / "specs" / "B1_manual.json"
PROXY_SITE = REPO_ROOT / "config" / "site.proxy.yaml"
NET = REPO_ROOT / "scenario" / "net" / "site.proxy.net.xml"
CANDIDATES = (  # PLAN 4.2 candidate list
    "tau", "minGap", "accel", "decel", "sigma", "speedFactor", "speedDev",
    "minGapLat", "maxSpeedLat", "latAlignment",
    "lcSublane", "lcPushy", "lcPushyGap", "lcAssertive", "lcImpatience", "lcTimeToImpatience", "lcAccelLat",
    "lcMaxSpeedLatStanding", "lcSpeedGain",
    "impatience", "jmDriveAfterRedTime", "jmDriveRedSpeed", "jmDriveAfterYellowTime", "jmIgnoreFoeProb",
    "jmIgnoreFoeSpeed", "jmTimegapMinor",
)


@pytest.fixture(scope="module")
def site() -> Site:
    return load_site(PROXY_SITE)


@pytest.fixture
def spec() -> dict:
    return json.loads(B1.read_text(encoding="utf-8"))


def _dodge_net(d, connections: str = "") -> tuple:
    """Two-lane signalised cross with the site street names (LVL_W = WC, ...); the site marks LVL_W lane 1 l/u, so it
    is a wrong lane for straight traffic, while netconvert connects it straight on (a usable dodge, ruling R27)."""
    d.mkdir(parents=True, exist_ok=True)
    (d / "n.nod.xml").write_text('<nodes><node id="C" x="0" y="0" type="traffic_light"/><node id="W" x="-150" y="0"/>'
                                 '<node id="E" x="150" y="0"/><node id="S" x="0" y="-150"/><node id="N" x="0" y="150"/>'
                                 '</nodes>', encoding="utf-8")
    edges = [("WC", "W", "C", "Le Van Luong"), ("CE", "C", "E", "Le Van Luong"), ("EC", "E", "C", "Le Van Luong"),
             ("CW", "C", "W", "Le Van Luong"), ("SC", "S", "C", "Hoang Dao Thuy"), ("CN", "C", "N", "Hoang Dao Thuy"),
             ("NC", "N", "C", "Hoang Dao Thuy"), ("CS", "C", "S", "Hoang Dao Thuy")]
    (d / "n.edg.xml").write_text("<edges>" + "".join(
        f'<edge id="{i}" from="{f}" to="{t}" name="{n}" numLanes="2" speed="13.9"/>' for i, f, t, n in edges)
        + "</edges>", encoding="utf-8")
    cmd = [sumolib.checkBinary("netconvert"), "-n", str(d / "n.nod.xml"), "-e", str(d / "n.edg.xml"),
           "-o", str(d / "tiny.net.xml")]
    if connections:
        (d / "c.con.xml").write_text(f"<connections>{connections}</connections>", encoding="utf-8")
        cmd += ["-x", str(d / "c.con.xml")]
    subprocess.run(cmd, check=True, capture_output=True)
    data = copy.deepcopy(dict(load_site(PROXY_SITE)))
    edge = {"LVL_W": "WC", "LVL_E": "EC", "HDT_N": "NC", "HDT_S": "SC"}
    for a in data["approaches"]:
        a["edge"], a["lane_widths_m"] = edge[a["id"]], [3.5, 3.5]
        a["lane_movements"] = [["r", "s"], ["l", "u"]] if a["id"] == "LVL_W" else [["r", "s"], ["s", "l", "u"]]
    return Site(data, d / "site.tiny.yaml"), d / "tiny.net.xml"


@pytest.fixture(scope="module")
def dodge(tmp_path_factory):
    return _dodge_net(tmp_path_factory.mktemp("dodge"))


def _arch(spec: dict, vclass: str) -> dict:
    return next(a for a in spec["driver_archetypes"] if a["base_vclass"] == vclass)


def _rule(spec: dict, rule_type: str) -> dict:
    return next(r for r in spec["traci_rules"] if r["rule_type"] == rule_type)


def _codes(issues) -> list[str]:
    return [i["code"] for i in issues]


# ---------------------------------------------------------------- bounds


def test_bounds_rows_sourced():
    bounds = load_bounds()
    assert bounds
    for name, b in bounds.items():
        assert b.source_url.startswith("https://sumo.dlr.de/docs/"), name
        assert b.model in ("vType", "carFollow", "LC", "junction"), name
        assert b.behavior_group and set(b.behavior_group) <= set(BEHAVIOR_GROUPS), name
        assert b.unit is not None, name
        for vc in VCLASSES:
            r = b.for_vclass(vc)
            if b.values is None:
                assert r.min <= r.max, (name, vc)
            if b.fixed:
                assert r.min == r.max == r.default, (name, vc)
        if b.range_source is not None:
            assert b.range_evidence in ("literature", "literature_transferred", "assumed", "docs", "ruling"), name


def test_bounds_cover_candidates_except_excluded():
    bounds = load_bounds()
    assert set(bounds) <= set(CANDIDATES)
    # R15: jmIgnoreFoe* create real collisions by design; excluded from the space
    assert "jmIgnoreFoeProb" not in bounds and "jmIgnoreFoeSpeed" not in bounds
    assert set(CANDIDATES) - set(bounds) == {"jmIgnoreFoeProb", "jmIgnoreFoeSpeed"}


def test_bounds_rulings_r15():
    bounds = load_bounds()
    for vc in ("motorcycle", "custom1"):
        r = bounds["minGap"].for_vclass(vc)
        assert (r.min, r.max) == (0.5, 2.5)
    car = bounds["minGap"].for_vclass("passenger")  # separate passenger range (R15 is for motorcycles)
    assert (car.min, car.max) == (1.0, 3.0)
    assert bounds["minGapLat"].for_vclass("motorcycle").min == 0.3
    r = bounds["jmTimegapMinor"].for_vclass("custom1")
    assert (r.min, r.max, r.default) == (0.5, 3.0, 1.0)
    assert "illegal_left_box" in bounds["jmTimegapMinor"].behavior_group
    assert bounds["jmTimegapMinor"].vclasses == ("custom1",) and "R15" in bounds["jmTimegapMinor"].vclasses_reason


def test_traci_rule_params():
    assert set(TRACI_RULE_PARAMS) == {"early_start", "swarm_red_running", "wrong_lane_dodge", "illegal_left_box",
                                      "slow_lane_center"}
    assert set(TRACI_RULE_PARAMS["early_start"]) == {"t_before_green", "p", "v_max"}
    assert set(TRACI_RULE_PARAMS["swarm_red_running"]) == {"p0", "k", "p_max", "dt"}
    assert set(TRACI_RULE_PARAMS["wrong_lane_dodge"]) == {"q_min", "v_creep"}
    assert set(TRACI_RULE_PARAMS["slow_lane_center"]) == {"lat_offset"}
    box = TRACI_RULE_PARAMS["illegal_left_box"]  # rulings R15, R25 (max_clear_into_cross_green_s dropped)
    assert set(box) == {"release_lag_s"}
    assert (box["release_lag_s"].min, box["release_lag_s"].max) == (0, 4)
    for rule, params in TRACI_RULE_PARAMS.items():
        for name, p in params.items():
            assert p.min < p.max and p.unit and p.reason, (rule, name)
    assert RULE_VCLASSES["illegal_left_box"] == ("custom1",)
    for rule in ("early_start", "swarm_red_running", "wrong_lane_dodge"):  # ruling R19: cars too
        assert {"passenger", "motorcycle"} <= set(RULE_VCLASSES[rule]), rule
    assert RULE_VCLASSES["slow_lane_center"] == ("motorcycle",)
    assert "custom1" not in RULE_VCLASSES["wrong_lane_dodge"]
    assert set(DISTRIBUTION_OF_VCLASS.values()) == {"car", "moto", "moto_violator", "car_violator"}


def test_bounds_load_in_sumo(tmp_path):
    """Every bounded attribute at its min and max loads in SUMO 1.27 with XSD validation and no warning."""
    bounds = load_bounds()
    vtypes = []
    for vc in VCLASSES:
        for end in ("min", "max"):
            attrs = {}
            for name, b in bounds.items():
                if vc not in b.vclasses:
                    continue
                r = b.for_vclass(vc)
                attrs[name] = b.values[0 if end == "min" else -1] if b.values else getattr(r, end)
            # lcPushyGap is ignored by SUMO when lcPushy is set (validator logic check): own vType, with the
            # largest minGapLat so that lcPushyGap <= minGapLat holds at its max
            gap = {"lcPushyGap": attrs.pop("lcPushyGap"), "minGapLat": bounds["minGapLat"].for_vclass(vc).max}
            for vid, at in ((f"{vc}_{end}", attrs), (f"{vc}_{end}_pushygap", gap)):
                a = " ".join(f'{k}="{v}"' for k, v in at.items())
                vtypes.append(f'<vType id="{vid}" vClass="{vc}" laneChangeModel="SL2015" {a}/>')
    add = tmp_path / "bounds.add.xml"
    add.write_text('<additional xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                   'xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/additional_file.xsd">\n'
                   + "\n".join(vtypes) + "\n</additional>\n", encoding="utf-8")
    proc = subprocess.run([sumolib.checkBinary("sumo"), "-n", str(NET), "-a", str(add), "--end", "1",
                           "--step-length", "0.1", "--lateral-resolution", "0.4", "--xml-validation", "always",
                           "--no-step-log"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert proc.returncode == 0, proc.stderr
    assert "Warning" not in proc.stderr + proc.stdout, proc.stderr


# ---------------------------------------------------------------- validator


def test_schema_file_is_draft_2020_12():
    assert load_json_schema()["$schema"] == "https://json-schema.org/draft/2020-12/schema"


def test_valid_spec_passes(spec, site):
    assert validate(spec, site) == []


def test_B1_rationales_cite_saval_or_assumed(spec):
    items = spec["driver_archetypes"] + spec["traci_rules"]
    for item in items:
        text = item["rationale"]
        assert "Saval" in text or "assumed" in text, item.get("id", item.get("rule_type"))


def test_schema_error(spec, site):
    del spec["spec_id"]
    spec["traci_rules"][0]["rule_type"] = "teleport_through"
    issues = validate(spec, site)
    assert issues and set(_codes(issues)) == {"schema"}
    assert any("spec_id" in i["message"] for i in issues)
    assert any("teleport_through" in i["message"] and "illegal_left_box" in i["message"] for i in issues)


@pytest.mark.parametrize("bad", [[], "spec", None, {"spec_id": "x"}])
def test_non_spec_input(bad, site):
    issues = validate(bad, site)
    assert issues and set(_codes(issues)) == {"schema"}


def test_nan_value(spec, site):
    _arch(spec, "motorcycle")["params"]["tau"] = float("nan")
    assert _codes(validate(spec, site)) == ["out_of_bounds"]


def _llm(spec: dict) -> dict:
    spec["source"] = "llm"
    spec["provenance"] = {"model": "qwen3.5:9b", "prompt_version": "v001", "iteration": 1, "sample_idx": 0}
    return spec


def _where(issues) -> list[tuple[str, str]]:
    return [(i["code"], i["path"]) for i in issues]


def test_llm_spec_valid(spec, site):
    assert validate(_llm(spec), site) == []


def test_llm_spec_needs_provenance(spec, site):
    spec = _llm(spec)
    del spec["provenance"]
    issues = validate(spec, site)
    assert _where(issues) == [("schema", "(spec)")]
    assert "'provenance' is a required property" in issues[0]["message"]


@pytest.mark.parametrize("field", ["model", "prompt_version", "iteration", "sample_idx"])
def test_llm_provenance_fields_required(spec, site, field):
    spec = _llm(spec)
    del spec["provenance"][field]
    issues = validate(spec, site)
    assert _where(issues) == [("schema", "provenance")]
    assert f"'{field}' is a required property" in issues[0]["message"]


@pytest.mark.parametrize("field,value", [("model", None), ("prompt_version", " "), ("iteration", None)])
def test_llm_provenance_fields_filled(spec, site, field, value):
    spec = _llm(spec)
    spec["provenance"][field] = value
    issues = validate(spec, site)
    assert _where(issues) == [("schema", f"provenance.{field}")]
    assert repr(value) in issues[0]["message"]


def test_manual_spec_provenance_may_be_null(spec, site):
    spec["provenance"]["model"] = None  # B1 has no model; only source=llm requires the provenance fields
    assert validate(spec, site) == []


def test_llm_spec_needs_archetype_rationale(spec, site):
    spec = _llm(spec)
    del spec["driver_archetypes"][0]["rationale"]
    issues = validate(spec, site)
    assert _where(issues) == [("schema", "driver_archetypes[0]")]
    assert "'rationale' is a required property" in issues[0]["message"]


def test_llm_spec_needs_rule_rationale(spec, site):
    spec = _llm(spec)
    del spec["traci_rules"][1]["rationale"]
    issues = validate(spec, site)
    assert _where(issues) == [("schema", "traci_rules[1]")]
    assert "'rationale' is a required property" in issues[0]["message"]


@pytest.mark.parametrize("where", ["driver_archetypes", "traci_rules"])
def test_blank_rationale(spec, site, where):
    spec = _llm(spec)
    spec[where][0]["rationale"] = " \t\n"
    issues = validate(spec, site)
    assert _where(issues) == [("schema", f"{where}[0].rationale")]
    assert "does not match" in issues[0]["message"]


def test_unknown_attr(spec, site):
    _arch(spec, "motorcycle")["params"]["minGapp"] = 1.0
    issues = validate(spec, site)
    assert _codes(issues) == ["unknown_attr"]
    assert "minGapp" in issues[0]["path"] and "minGap" in issues[0]["message"]  # names the allowed attributes


def test_excluded_attr_explained(spec, site):
    _arch(spec, "custom1")["params"]["jmIgnoreFoeProb"] = 0.1
    issues = validate(spec, site)
    assert _codes(issues) == ["unknown_attr"]
    assert "collision" in issues[0]["message"]


def test_out_of_bounds(spec, site):
    _arch(spec, "motorcycle")["params"]["minGap"] = 3.0
    issues = validate(spec, site)
    assert _codes(issues) == ["out_of_bounds"]
    assert "[0.5, 2.5]" in issues[0]["message"] and "motorcycle" in issues[0]["message"]


def test_bounds_per_vclass(spec, site):
    _arch(spec, "passenger")["params"]["minGap"] = 2.8  # passenger range differs from the motorcycle one
    assert validate(spec, site) == []
    _arch(spec, "custom1")["params"]["minGap"] = 2.8
    assert _codes(validate(spec, site)) == ["out_of_bounds"]


def test_categorical_attr(spec, site):
    arch = _arch(spec, "motorcycle")
    arch["params"]["latAlignment"] = "right"
    assert validate(spec, site) == []
    arch["params"]["latAlignment"] = "sideways"
    issues = validate(spec, site)
    assert _codes(issues) == ["out_of_bounds"] and "center" in issues[0]["message"]
    arch["params"]["latAlignment"] = 0.3
    assert _codes(validate(spec, site)) == ["out_of_bounds"]
    arch["params"]["latAlignment"] = "right"
    arch["params"]["minGap"] = "1.5"  # numeric attribute as string
    assert _codes(validate(spec, site)) == ["out_of_bounds"]


def test_fixed_attr(spec, site):
    fixed = [n for n, b in load_bounds().items() if b.fixed]
    assert fixed
    name = fixed[0]
    b = load_bounds()[name]
    _arch(spec, "motorcycle")["params"][name] = b.for_vclass("motorcycle").default + 0.5
    issues = validate(spec, site)
    assert _codes(issues) == ["out_of_bounds"] and "fixed" in issues[0]["message"]


def test_share_sum(spec, site):
    moto = _arch(spec, "motorcycle")
    moto["share"] = 0.6
    twin = copy.deepcopy(moto)
    twin["id"] = "moto_twin"
    spec["driver_archetypes"].append(twin)
    issues = validate(spec, site)
    assert _codes(issues) == ["share_sum"]
    assert "motorcycle" in issues[0]["message"] and "1.2" in issues[0]["message"]


def test_share_sum_tolerance(spec, site):
    moto = _arch(spec, "motorcycle")
    moto["share"] = 1 / 3
    for k in range(2):
        twin = copy.deepcopy(moto)
        twin["id"] = f"moto_{k}"
        spec["driver_archetypes"].append(twin)
    assert validate(spec, site) == []


def test_missing_distribution(spec, site):
    spec["driver_archetypes"] = [a for a in spec["driver_archetypes"] if a["base_vclass"] != "custom1"]
    spec["traci_rules"] = [r for r in spec["traci_rules"] if r["rule_type"] != "illegal_left_box"]
    for r in spec["traci_rules"]:
        r["applies_to"] = [a for a in r["applies_to"] if any(x["id"] == a for x in spec["driver_archetypes"])]
    issues = validate(spec, site)
    assert _codes(issues) == ["logic"] and "moto_violator" in issues[0]["message"]


def test_archetype_ids(spec, site):
    spec["driver_archetypes"][1]["id"] = spec["driver_archetypes"][0]["id"]
    assert "logic" in _codes(validate(spec, site))
    spec = json.loads(B1.read_text(encoding="utf-8"))
    old = _arch(spec, "passenger")["id"]
    _arch(spec, "passenger")["id"] = "car"  # clashes with the vTypeDistribution id (SUMO refuses to load)
    for r in spec["traci_rules"]:
        r["applies_to"] = ["car" if a == old else a for a in r["applies_to"]]
    issues = validate(spec, site)
    assert _codes(issues) == ["logic"] and "vTypeDistribution" in issues[0]["message"]


def test_minGapLat_wider_than_lane(spec, site):
    narrow = copy.deepcopy(dict(site))
    narrow["approaches"][2]["lane_widths_m"] = [3.5, 0.8, 3.5]
    narrow_site = Site(narrow, site.path)
    _arch(spec, "motorcycle")["params"]["minGapLat"] = 0.9
    issues = validate(spec, narrow_site)
    assert _codes(issues) == ["logic"]
    assert "0.8" in issues[0]["message"] and "HDT_N" in issues[0]["message"]
    assert validate(spec, site) == []


def test_minGapLat_needs_lane_widths(spec):
    """The measured site file has lane widths `null # TODO_MEASURE`: no silent default."""
    _arch(spec, "motorcycle")["params"]["minGapLat"] = 0.5
    with pytest.raises(MissingFieldDataError, match="lane_widths_m"):
        validate(spec, load_site())


def test_lcPushy_and_lcPushyGap(spec, site):
    arch = _arch(spec, "motorcycle")
    arch["params"]["lcPushyGap"] = 0.2
    assert validate(spec, site) == []
    arch["params"]["lcPushy"] = 0.5  # SUMO then ignores lcPushyGap (experiment in the Task 7 report)
    assert _codes(validate(spec, site)) == ["logic"]
    del arch["params"]["lcPushy"]
    arch["params"]["lcPushyGap"] = 0.5  # > minGapLat 0.3 of the B1 motorcycle archetype
    issues = validate(spec, site)
    assert _codes(issues) == ["logic"] and "minGapLat" in issues[0]["message"]


def test_rule_params_invalid(spec, site):
    rule = _rule(spec, "swarm_red_running")
    rule["params"]["p0"] = 1.5
    issues = validate(spec, site)
    assert "rule_params" in _codes(issues)
    assert any("[0, 1]" in i["message"] for i in issues)

    spec = json.loads(B1.read_text(encoding="utf-8"))
    rule = _rule(spec, "swarm_red_running")
    del rule["params"]["dt"]
    rule["params"]["dtt"] = 5
    issues = validate(spec, site)
    assert _codes(issues) == ["rule_params", "rule_params"]
    assert any("dt" in i["message"] and "missing" in i["message"] for i in issues)
    assert any("dtt" in i["message"] for i in issues)

    spec = json.loads(B1.read_text(encoding="utf-8"))
    rule = _rule(spec, "swarm_red_running")
    rule["params"].update(p0=0.6, p_max=0.4)
    assert _codes(validate(spec, site)) == ["rule_params"]


def test_rule_applies_to_unknown_archetype(spec, site):
    _rule(spec, "swarm_red_running")["applies_to"].append("ghost")
    issues = validate(spec, site)
    assert _codes(issues) == ["logic"] and "ghost" in issues[0]["message"]


EXTRA_RULES = {"wrong_lane_dodge": {"q_min": 20, "v_creep": 2}, "slow_lane_center": {"lat_offset": 0.0}}


def test_rule_wrong_vclass(spec, site, dodge):
    moto_id = _arch(spec, "motorcycle")["id"]
    spec["traci_rules"].append({"rule_type": "illegal_left_box", "applies_to": [moto_id],  # B1 has none (R26)
                                "params": {"release_lag_s": 0.0}, "rationale": "test"})
    issues = validate(spec, site)
    assert [(i["code"], i["path"]) for i in issues] == [("logic", "traci_rules[2].applies_to[0]")]
    assert "custom1" in issues[0]["message"] and moto_id in issues[0]["message"]
    dodge_site, dodge_net = dodge
    for rule_type, vclass in (("wrong_lane_dodge", "custom1"), ("slow_lane_center", "passenger"),
                              ("slow_lane_center", "custom1")):
        spec = json.loads(B1.read_text(encoding="utf-8"))
        spec["traci_rules"].append({"rule_type": rule_type, "applies_to": [_arch(spec, vclass)["id"]],
                                    "params": EXTRA_RULES[rule_type], "rationale": "test"})
        issues = validate(spec, dodge_site, net=dodge_net)  # a net where the dodge is usable (R27 check silent)
        assert _codes(issues) == ["logic"], (rule_type, vclass)
        assert f"has base_vclass {vclass}" in issues[0]["message"]


def test_car_rules_allowed(spec, dodge):
    """Ruling R19: early start, red running and lane dodging apply to car archetypes too (M2/M3/M8 car targets);
    checked on a net where the dodge is usable (R27)."""
    site, net = dodge
    car_id, moto_id = _arch(spec, "passenger")["id"], _arch(spec, "motorcycle")["id"]
    for rule_type in ("early_start", "swarm_red_running"):
        _rule(spec, rule_type)["applies_to"].append(car_id)
    spec["traci_rules"].append({"rule_type": "wrong_lane_dodge", "applies_to": [car_id, moto_id],
                                "params": EXTRA_RULES["wrong_lane_dodge"], "rationale": "test"})
    spec["traci_rules"].append({"rule_type": "slow_lane_center", "applies_to": [moto_id],
                                "params": EXTRA_RULES["slow_lane_center"], "rationale": "test"})
    assert validate(spec, site, net=net) == []


def _with_dodge(spec: dict, *vclasses: str) -> dict:
    spec["traci_rules"].append({"rule_type": "wrong_lane_dodge", "applies_to": [_arch(spec, v)["id"] for v in vclasses],
                                "params": EXTRA_RULES["wrong_lane_dodge"], "rationale": "test"})
    return spec


def test_wrong_lane_dodge_inapplicable_on_proxy_site(spec, site):
    """Ruling R27: on the proxy net the lane markings equal the connections, so no wrong lane has a connection for
    the same movement: the rule could never execute and the validator says so."""
    issues = validate(_with_dodge(spec, "passenger", "motorcycle"), site)
    assert [(i["code"], i["path"]) for i in issues] == [("logic", "traci_rules[2].applies_to[0]"),
                                                       ("logic", "traci_rules[2].applies_to[1]")]
    assert all("inapplicable on this site" in i["message"] for i in issues)


def test_wrong_lane_dodge_checks_vclass_permission(spec, tmp_path):
    """The usable connection (LVL_W lane 1 straight on) allows motorcycles only: the rule is inapplicable for the car
    archetype and fine for the motorcycle one."""
    conns = ('<connection from="WC" to="CS" fromLane="0" toLane="0"/><connection from="WC" to="CE" fromLane="0" '
             'toLane="0"/><connection from="WC" to="CE" fromLane="1" toLane="1" allow="motorcycle"/>'
             '<connection from="WC" to="CN" fromLane="1" toLane="1"/>')
    site, net = _dodge_net(tmp_path, conns)
    issues = validate(_with_dodge(spec, "passenger", "motorcycle"), site, net=net)
    assert [(i["code"], i["path"]) for i in issues] == [("logic", "traci_rules[2].applies_to[0]")]
    assert "inapplicable on this site" in issues[0]["message"] and "passenger" in issues[0]["message"]


@pytest.mark.parametrize("vclass", ["passenger", "motorcycle"])
def test_jmTimegapMinor_custom1_only(spec, site, vclass):
    i = next(k for k, a in enumerate(spec["driver_archetypes"]) if a["base_vclass"] == vclass)
    spec["driver_archetypes"][i]["params"]["jmTimegapMinor"] = 1.0
    issues = validate(spec, site)
    assert [(x["code"], x["path"]) for x in issues] == [("logic", f"driver_archetypes[{i}].params.jmTimegapMinor")]
    msg = issues[0]["message"]
    assert "base_vclass custom1" in msg and "R15" in msg and vclass in msg


def test_duplicate_rule_on_archetype(spec, site):
    spec["traci_rules"].append(copy.deepcopy(_rule(spec, "early_start")))
    assert _codes(validate(spec, site)) == ["logic"]


def test_issue_shape(spec, site):
    _arch(spec, "motorcycle")["params"]["minGap"] = 9
    (issue,) = validate(spec, site)
    assert set(issue) == {"path", "code", "message"} and issue["code"] in ISSUE_CODES
    assert issue["path"].startswith("driver_archetypes[")


# ---------------------------------------------------------------- validity log


def test_validity_log(tmp_path, spec, site):
    log = ValidityLog(tmp_path / "sub" / "validity_log.csv")
    log.record("B1_manual", validate(spec, site), source="manual")
    _arch(spec, "motorcycle")["params"]["minGap"] = 9
    log.record("bad_1", validate(spec, site), source="llm")
    with (tmp_path / "sub" / "validity_log.csv").open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert [r["spec_id"] for r in rows] == ["B1_manual", "bad_1"]
    assert [r["valid"] for r in rows] == ["True", "False"]
    assert rows[1]["n_issues"] == "1" and rows[1]["codes"] == "out_of_bounds:1"
    assert rows[1]["source"] == "llm" and rows[0]["timestamp"]
    assert log.valid_rate() == 0.5
    assert log.valid_rate(source="manual") == 1.0
