"""LLM client, LLM-facing schema, params_only lock, prompts and feedback (plan Task 12, Review Focus 2).

The openai backend talks to a mocked HTTP server (httpx.MockTransport); the file backend (stand-in) uses temp dirs."""

import copy
import csv
import json

import pytest
import yaml

try:  # openai >= 3 ships its HTTP layer as httpx2; openai 1.x uses httpx
    import httpx2 as httpx
except ImportError:
    import httpx
from jsonschema import Draft202012Validator

from thesis_sumo.config import REPO_ROOT, load_experiment, load_site
from thesis_sumo.evaluate import EvalResult
from thesis_sumo.llm.client import HARNESS_KEYS, LLMClient, PendingResponse, llm_config, llm_schema
from thesis_sumo.llm.feedback import (DayDataLeak, assert_no_day_data, build_context, build_feedback,
                                      calibration_targets, system_prompt)
from thesis_sumo.metrics.distance import DistanceReport, MetricReport
from thesis_sumo.rules.schema import load_bounds, load_excluded
from thesis_sumo.rules.validator import structure_issues, validate

B1 = REPO_ROOT / "rules" / "specs" / "B1_manual.json"
PROXY_SITE = REPO_ROOT / "config" / "site.proxy.yaml"
UNSUPPORTED = {"if", "then", "else", "propertyNames", "uniqueItems", "not", "allOf", "$ref", "$defs", "pattern",
               "patternProperties", "prefixItems", "dependentRequired", "dependentSchemas"}


@pytest.fixture(scope="module")
def site():
    return load_site(PROXY_SITE)


@pytest.fixture
def base() -> dict:
    return json.loads(B1.read_text(encoding="utf-8"))


def _answer(spec: dict) -> dict:
    """What the LLM returns: the spec without the harness fields."""
    return {k: v for k, v in copy.deepcopy(spec).items() if k not in HARNESS_KEYS}


def _bad(spec: dict) -> dict:
    a = _answer(spec)
    a["driver_archetypes"][0]["params"]["tau"] = 99.0  # out_of_bounds
    return a


def _completion(content: str) -> dict:
    return {"id": "c", "object": "chat.completion", "created": 0, "model": "m",
            "choices": [{"index": 0, "finish_reason": "stop",
                         "message": {"role": "assistant", "content": content, "reasoning": "thinking text"}}]}


def _openai_client(tmp_path, site, answers: list[str], reject_schema: bool = False):
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        calls.append(body)
        if reject_schema and "response_format" in body:
            return httpx.Response(400, json={"error": {"message": "response_format not supported"}})
        return httpx.Response(200, json=_completion(answers[len([c for c in calls if not (
            reject_schema and "response_format" in c)]) - 1]))

    cfg = {"runtime": "openai", "server": "ollama", "base_url": "http://llm.test/v1", "model": "qwen3.5:9b",
           "temperature": 0.7, "quant": "Q4_K_M", "seed": 42, "max_attempts": 3, "prompt_version": "v001", "profile": "test"}
    client = LLMClient(cfg, site=site, campaign="t12", log_root=tmp_path,
                       http_client=httpx.Client(transport=httpx.MockTransport(handler)))
    return client, calls


MSGS = [{"role": "system", "content": "sys"}, {"role": "user", "content": "ctx"}]


def _validity_rows(client) -> list[dict]:
    with client.validity.path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def test_retry_on_invalid_then_success(tmp_path, site, base):
    client, calls = _openai_client(tmp_path, site, ["this is not json", json.dumps(_bad(base)),
                                                    "```json\n" + json.dumps(_answer(base)) + "\n```"])
    spec, rec = client.generate_spec(MSGS, "params_only", base, iteration=1, sample_idx=2)
    assert spec is not None and rec["valid"] and len(rec["attempts"]) == 3 and len(calls) == 3
    assert spec["spec_id"] == "t12_it01_s02" and spec["source"] == "llm"
    assert spec["provenance"] == {"model": "qwen3.5:9b", "prompt_version": "v001", "iteration": 1, "sample_idx": 2,
                                  "runtime": "ollama"}
    assert validate(spec, site) == []
    assert [a["issues"][0]["code"] for a in rec["attempts"][:2]] == ["schema", "out_of_bounds"]
    assert calls[0]["response_format"]["type"] == "json_schema" and calls[0]["seed"] == 44
    assert "out_of_bounds" in calls[2]["messages"][-1]["content"]          # structured issues fed back
    assert calls[2]["messages"][-2] == {"role": "assistant", "content": json.dumps(_bad(base))}
    logs = sorted((tmp_path / "t12").glob("t12__it01_s02_a*.json"))
    assert len(logs) == 3
    last = json.loads(logs[-1].read_text(encoding="utf-8"))
    assert last["valid"] and last["response"]["reasoning"] == "thinking text" and last["request"]["schema"]
    assert [r["valid"] for r in _validity_rows(client)] == ["False", "False", "True"]


def test_gives_up_after_3(tmp_path, site, base):
    client, calls = _openai_client(tmp_path, site, [json.dumps(_bad(base))] * 5)
    spec, rec = client.generate_spec(MSGS, "full", iteration=0, sample_idx=0)
    assert spec is None and not rec["valid"] and len(rec["attempts"]) == 3 and len(calls) == 3
    assert len(_validity_rows(client)) == 3


def test_structured_output_rejected_falls_back_to_plain(tmp_path, site, base):
    client, calls = _openai_client(tmp_path, site, [json.dumps(_answer(base))], reject_schema=True)
    spec, rec = client.generate_spec(MSGS, "params_only", base, iteration=0, sample_idx=0)
    assert spec is not None and not client.structured
    assert "response_format" in calls[0] and "response_format" not in calls[1]


def test_file_backend_pending_then_resume(tmp_path, site, base):
    cfg = {**llm_config(), "runtime": "file", "model": "claude-sonnet (stand-in)"}
    client = LLMClient(cfg, site=site, campaign="t12f", log_root=tmp_path)
    run = lambda: client.generate_spec(MSGS, "params_only", base, iteration=2, sample_idx=1)  # noqa: E731
    with pytest.raises(PendingResponse) as e:
        run()
    assert e.value.request_id == "t12f__it02_s01_a1"
    req = json.loads((tmp_path / "t12f" / "requests" / "t12f__it02_s01_a1.json").read_text(encoding="utf-8"))
    assert req["messages"] == MSGS and req["mode"] == "params_only" and req["attempt"] == 1 and req["schema"]
    e.value.path.parent.mkdir(parents=True, exist_ok=True)
    e.value.path.write_text(json.dumps({"content": _bad(base), "reasoning": "r1"}), encoding="utf-8")
    with pytest.raises(PendingResponse) as e2:
        run()
    assert e2.value.request_id == "t12f__it02_s01_a2"
    e2.value.path.write_text(json.dumps(_answer(base)), encoding="utf-8")   # bare spec object also accepted
    spec, rec = run()
    assert spec is not None and [a["cached"] for a in rec["attempts"]] == [True, False]
    assert spec["provenance"]["model"] == "claude-sonnet (stand-in)" and spec["provenance"]["runtime"] == "file"
    assert [r["valid"] for r in _validity_rows(client)] == ["False", "True"]   # resume does not re-count


def test_params_only_rejects_structure_change(tmp_path, site, base):
    ok = copy.deepcopy(base)
    ok["driver_archetypes"][0]["params"]["tau"] = 1.5
    ok["driver_archetypes"][0]["share"], ok["driver_archetypes"][1]["share"] = 0.8, 0.2
    ok["traci_rules"][0]["params"]["p0"] = 0.3
    ok["traci_rules"].reverse()
    assert validate(ok, site) == [] and structure_issues(ok, base) == []

    changes = {
        "vclass": lambda s: s["driver_archetypes"][4].update(base_vclass="motorcycle"),
        "new_param": lambda s: s["driver_archetypes"][0]["params"].update(sigma=0.5),
        "applies_to": lambda s: s["traci_rules"][1]["applies_to"].pop(),
        "drop_rule": lambda s: s["traci_rules"].pop(),
        "rename": lambda s: (s["driver_archetypes"][0].update(id="car_x")),
    }
    for name, change in changes.items():
        s = copy.deepcopy(base)
        change(s)
        assert "structure_locked" in {i["code"] for i in structure_issues(s, base)}, name

    bad = _answer(base)
    bad["driver_archetypes"][0]["params"]["sigma"] = 0.5   # valid in full mode, locked in params_only
    client, _ = _openai_client(tmp_path, site, [json.dumps(bad)] * 3)
    spec, rec = client.generate_spec(MSGS, "params_only", base, iteration=0, sample_idx=0)
    assert spec is None and rec["attempts"][0]["issues"][0]["code"] == "structure_locked"


def test_default_prefixed_id_rejected(site, base):
    base["driver_archetypes"][2]["id"] = "DEFAULT_moto"
    for r in base["traci_rules"]:
        r["applies_to"] = ["DEFAULT_moto" if a == "moto_saval" else a for a in r["applies_to"]]
    issues = validate(base, site)
    assert [(i["code"], i["path"]) for i in issues] == [("schema", "driver_archetypes[2].id")]


def _result(spec_id: str, days: list[str]) -> EvalResult:
    m = MetricReport(key="M3/share/moto", label="red-light running share", unit="-", kind="scalar", target=None,
                     evidence="literature", d=0.4, d_day_day=0.2, R=2.0, direction="sim>obs", scored=True,
                     sim_mean=0.1, obs_mean=0.065, weight=0.1)
    runs = [{"day": d, "seed": 1, "reasons": ["max_end_backlog: 300 > 0"], "eligibility": "excluded",
             "collisions_per_hour": 2.0, "lane_collisions_per_hour": 0.0, "jam_yield_teleports_per_hour": 4.0}
            for d in days]
    return EvalResult(spec_id, "c", True, [], DistanceReport({m.key: m}, n_sim=len(runs), n_obs_days=3), runs,
                      {"queue_space_seeking": {"attempted": 5, "executed": 4, "not_executed": {"lane_blocked": 1},
                                               "counters": {"drawn_right_lane": 3}}})


def test_feedback_has_no_validation_days(base):
    exp = load_experiment()
    cal, val = exp["data_split"]["calibration_days"], exp["data_split"]["validation_days"]
    text = build_feedback([_result("c_it01_s00", cal)], {"c_it01_s01": [{"path": "x", "code": "logic", "message": "m"}]})
    assert "PROXY_D" not in text and not any(d in text for d in cal + val)
    assert "M3/share/moto" in text and "R 2.00" in text and "drawn_right_lane" in text and "[logic]" in text
    assert "max_end_backlog" in text
    with pytest.raises(DayDataLeak):
        build_feedback([_result("c_it01_s00", cal + val[:1])])
    with pytest.raises(DayDataLeak):
        assert_no_day_data(f"obs mean on {val[1]}: 0.07")
    with pytest.raises(ValueError):
        calibration_targets(val)


def test_context_lists_only_bounds_attrs(site, base):
    bounds = load_bounds()
    targets = {"M1/moto": {"label": "discharge headway", "unit": "s", "obs_mean": 0.25, "evidence": "literature"}}
    for mode in ("full", "params_only"):
        text = build_context(mode, base, site, bounds, targets, schema=llm_schema(mode, base))
        section = text.split("### vType attributes")[1].split("### TraCI rules")[0]
        listed = {line.split("`")[1] for line in section.splitlines() if line.startswith("- `")}
        assert listed == {n for n, b in bounds.items() if not b.fixed}
        for name in [*load_excluded(), *(n for n, b in bounds.items() if b.fixed)]:
            assert name not in text, name
        assert "LITERATURE_PROXY" in text and "queue_space_seeking" in text and "$" not in text.split("```json")[0]
    assert "Base spec" in text and "structure_locked" in text
    assert "DEFAULT_" in system_prompt()


def test_v002_context_describes_28_10_scenario(site, base):
    """Scenario of 2026-10-28 (site.proxy.yaml): banned lefts at HDT_N / HDT_S, legal protected LVL lefts and
    U-turns, 3 signal stages, sidewalks on LVL_W and LVL_E, continuous right lane on every approach."""
    assert llm_config()["prompt_version"] == "v002"   # default for new campaigns
    targets = {"M1/moto": {"label": "discharge headway", "unit": "s", "obs_mean": 0.25, "evidence": "literature"}}
    text = build_context("full", None, site, load_bounds(), targets, schema=llm_schema("full"), prompt_version="v002")
    site_part = text.split("## Intersection")[1].split("## Behaviours")[0]
    assert "from HDT_N, HDT_S" in site_part
    assert "LVL_straight 42 s (green LVL_W:s, LVL_E:s)" in site_part
    assert "LVL_left 16 s (green LVL_W:l, LVL_W:t, LVL_E:l, LVL_E:t)" in site_part
    assert "HDT_N:l (banned, custom1 only)" in site_part and "LVL_W:r" not in site_part
    assert site_part.count("rideable sidewalk") == 2 and site_part.count("continuous right-turn lane") == 4
    # 2026-10-28 round 2: no bollards, straight from lane 0 legal on green, no right_lane option on this net
    assert "bollard" not in site_part and site_part.count("straight from it legal on the approach's straight green") == 4
    behaviours = text.split("## Behaviours")[1].split("## Parameter dictionary")[0]
    assert "bollard" not in behaviours and "`p_right_lane` does not exist on this site" in behaviours
    assert "HDT_N and HDT_S" in behaviours and "LVL_W and LVL_E" in behaviours and "LVL_left" in behaviours
    assert "LVL_green" not in text and "PROXY_D" not in text
    old = build_context("full", None, site, load_bounds(), targets, schema={}, prompt_version="v001")
    assert "HDT_N and HDT_S" not in old.split("## Behaviours")[1] and system_prompt("v001")   # v001 still loads


def test_feedback_lists_every_per_approach_metric(base):
    """Feedback passes every metric of the report through (no approach filter)."""
    keys = ["M7/HDT_N", "M7/HDT_S", "M10/LVL_W", "M10/LVL_E"]
    ms = {k: MetricReport(key=k, label=k, unit="-", kind="scalar", target=None, evidence="assumed", d=0.1,
                          d_day_day=0.1, R=1.0, direction="sim>obs", scored=True, sim_mean=1.0, obs_mean=0.9,
                          weight=0.25) for k in keys}
    r = EvalResult("c_it01_s00", "c", True, [], DistanceReport(ms, n_sim=3, n_obs_days=3),
                   [{"day": d, "seed": 1, "reasons": [], "eligibility": "eligible", "collisions_per_hour": 0.0,
                     "lane_collisions_per_hour": 0.0, "jam_yield_teleports_per_hour": 0.0}
                    for d in load_experiment()["data_split"]["calibration_days"]], {})
    text = build_feedback([r], prompt_version="v002")
    assert all(f"- {k}: sim" in text for k in keys)


def _keywords(node, out: set) -> set:
    if isinstance(node, dict):
        for k, v in node.items():
            out.add(k)
            _keywords(v if k != "properties" else list(v.values()), out)
    elif isinstance(node, list):
        for v in node:
            _keywords(v, out)
    return out


def test_llm_schema_has_no_unsupported_keywords(base):
    for mode in ("full", "params_only"):
        schema = llm_schema(mode, base)
        Draft202012Validator.check_schema(schema)
        assert not _keywords(schema, set()) & UNSUPPORTED, mode
    props = llm_schema("full")["properties"]["driver_archetypes"]["items"]["properties"]["params"]["properties"]
    assert set(props) == {n for n, b in load_bounds().items() if not b.fixed}


def test_b1_round_trips_params_only_lock(tmp_path, site, base):
    answer = _answer(base)
    for mode in ("params_only", "full"):
        assert list(Draft202012Validator(llm_schema(mode, base)).iter_errors(answer)) == [], mode
    client, _ = _openai_client(tmp_path, site, [json.dumps(answer)])
    spec, rec = client.generate_spec(MSGS, "params_only", base, iteration=0, sample_idx=0)
    assert len(rec["attempts"]) == 1 and structure_issues(spec, base) == []
    assert {k: v for k, v in spec.items() if k not in HARNESS_KEYS} == answer


def test_replay_refuses_other_llm_setup(tmp_path, site, base):
    """A stand-in answer logged under one profile is never replayed (and relabelled) under another."""
    standin = {**llm_config(), "runtime": "file", "model": "claude-sonnet (stand-in)"}
    client = LLMClient(standin, site=site, campaign="t12p", log_root=tmp_path)
    resp = tmp_path / "t12p" / "responses" / "t12p__it00_s00_a1.json"
    resp.parent.mkdir(parents=True)
    resp.write_text(json.dumps(_answer(base)), encoding="utf-8")
    spec, _ = client.generate_spec(MSGS, "params_only", base, iteration=0, sample_idx=0)
    assert spec["provenance"]["model"] == "claude-sonnet (stand-in)"
    doc = yaml.safe_load((REPO_ROOT / "config" / "llm.yaml").read_text(encoding="utf-8"))
    ollama = {**llm_config({**doc, "active": "ollama"}), "quant": "Q4_K_M"}  # quant is TODO_DECIDE in the file
    other = LLMClient(ollama, site=site, campaign="t12p", log_root=tmp_path)
    with pytest.raises(ValueError, match="another LLM setup"):
        other.generate_spec(MSGS, "params_only", base, iteration=0, sample_idx=0)


@pytest.mark.parametrize("key", ["temperature", "quant", "base_url"])
def test_openai_required_keys(site, key):
    doc = yaml.safe_load((REPO_ROOT / "config" / "llm.yaml").read_text(encoding="utf-8"))
    cfg = {**llm_config({**doc, "active": "ollama"}), "quant": "Q4_K_M", key: None}
    with pytest.raises(ValueError, match=f"ollama.{key} is null"):
        LLMClient(cfg, site=site, campaign="t12k")
