"""thesis_sumo.evaluate: budget, validity, G0 exclusion, day guard, best-spec rule. SUMO is mocked (`_run_all`): a
fake run's observed_schema is a copy of its observed day (so G0 passes) unless the test scales its turn counts."""

import copy
import json
import math
import os
import shutil

import pandas as pd
import pytest

from thesis_sumo import evaluate
from thesis_sumo.config import REPO_ROOT, load_experiment
from thesis_sumo.metrics.distance import DistanceReport
from thesis_sumo.sim import runner
from thesis_sumo.sim.runner import RunResult

PROXY_SITE = REPO_ROOT / "config" / "site.proxy.yaml"
THRESHOLDS = {"max_noncollision_teleports": 0, "max_end_backlog": 0, "max_collisions_per_hour": 5,
              "max_junction_collisions_per_hour": 118, "max_intervened_collisions": 1}


def _spec() -> dict:
    return json.loads((REPO_ROOT / "rules" / "specs" / "B0.json").read_text(encoding="utf-8")) | {"spec_id": "t_spec"}


def _manifest(day, seed, **kw) -> dict:
    m = {"run_id": f"t_spec__{day}", "spec_id": "t_spec", "day": day, "seed": seed,
         "config": {"sim": {"begin_s": 0, "end_s": 1800}}, "n_teleports_noncollision": 0, "insertion_backlog": 0,
         "n_collisions": 0, "n_collisions_lane": 0, "n_collisions_junction": 0, "n_collisions_intervened": 0,
         "teleports": {"jam": 0.0, "yield": 0.0}, "valid_strict": True,
         "interventions": {"illegal_left_box": {"attempted": 2, "executed": 1, "not_executed": {"gone": 1},
                                                "counters": {}}}}
    return m | kw


@pytest.fixture
def env(tmp_path, monkeypatch):
    """Campaigns under tmp; thresholds set (the real ones may still be null); `calls` records the fake runs."""
    monkeypatch.setattr(evaluate, "CAMPAIGNS_DIR", tmp_path / "campaigns")
    exp = copy.deepcopy(load_experiment())
    exp["validity"] = dict(THRESHOLDS)
    monkeypatch.setattr(evaluate, "load_experiment", lambda: exp)
    calls, gate_fail, manifest_kw = [], set(), {}

    def fake_run_all(jobs, nproc):
        out = []
        for spec_dir, spec_id, day, seed, *_rest, runs_root in jobs:
            calls.append((spec_id, day, seed))
            run_dir = runs_root / f"{spec_id}__{day}" / f"seed_{seed:02d}"
            shutil.rmtree(run_dir, ignore_errors=True)        # runner.run replaces an existing seed dir too
            shutil.copytree(evaluate.OBSERVED_DIR / day, run_dir / "observed_schema")
            if (day, seed) in gate_fail:
                tc = run_dir / "observed_schema" / "turn_counts.csv"
                df = pd.read_csv(tc)
                df["count"] *= 3
                df.to_csv(tc, index=False)
            out.append(RunResult(run_dir, _manifest(day, seed, **manifest_kw.get((day, seed), {}))))
        return out

    monkeypatch.setattr(evaluate, "_run_all", fake_run_all)
    return {"exp": exp, "calls": calls, "gate_fail": gate_fail, "manifest_kw": manifest_kw, "tmp": tmp_path}


def _eval(budget, days=("PROXY_D1",), seeds=(1,), spec_id="t_spec", **kw):
    return evaluate.evaluate_spec(_spec() | {"spec_id": spec_id}, list(days), list(seeds), budget,
                                  campaign=budget.campaign, site_path=PROXY_SITE, **kw)


def test_invalid_spec_costs_nothing(env):
    budget = evaluate.RunBudget(4, "c")
    spec = _spec()
    spec["driver_archetypes"][0]["params"]["noSuchAttr"] = 1.0
    res = evaluate.evaluate_spec(spec, ["PROXY_D1"], [1, 2], budget, campaign="c", site_path=PROXY_SITE)
    assert not res.valid and res.issues and res.n_runs == 0 and math.isnan(res.S)
    assert budget.remaining == 4 and env["calls"] == []
    assert res.rank_key == (2, math.inf, math.inf)
    log = evaluate.ValidityLog(env["tmp"] / "campaigns" / "c" / "validity_log.csv").rows()
    assert [r["valid"] for r in log] == ["False"]


def test_budget_exhausted_raises(env):
    budget = evaluate.RunBudget(3, "c")
    with pytest.raises(evaluate.BudgetExhausted):
        _eval(budget, days=["PROXY_D1", "PROXY_D2"], seeds=[1, 2])
    assert env["calls"] == [] and budget.remaining == 3


def test_budget_persisted_and_resumed(env):
    b = evaluate.RunBudget(10, "c")
    assert b.path == env["tmp"] / "campaigns" / "c" / "budget.json"
    b.consume(3)
    b.consume(4)
    resumed = evaluate.RunBudget(10, "c")
    assert resumed.remaining == 3
    with pytest.raises(evaluate.BudgetExhausted):
        resumed.consume(4)
    assert evaluate.RunBudget(10, "c").remaining == 3 and not b.path.with_suffix(".lock").exists()
    with pytest.raises(ValueError, match="total"):
        evaluate.RunBudget(12, "c")


def test_two_budget_objects_share_count(env):
    """Two objects (or processes) on one campaign: each charge re-reads the file under the lock."""
    a, b = evaluate.RunBudget(5, "c"), evaluate.RunBudget(5, "c")
    a.consume(2)
    b.consume(2)
    assert a.remaining == b.remaining == 1
    with pytest.raises(evaluate.BudgetExhausted):
        a.consume(2)


def test_stale_lock_clear_error(env, monkeypatch):
    b = evaluate.RunBudget(5, "c")
    b.path.parent.mkdir(parents=True)
    b.path.with_suffix(".lock").write_text("pid 1")
    monkeypatch.setattr(evaluate.RunBudget, "LOCK_TIMEOUT_S", 0.1)
    with pytest.raises(RuntimeError, match="stale"):
        b.consume(1)
    assert b.remaining == 5


def test_budget_of_other_campaign_refused(env):
    budget = evaluate.RunBudget(4, "other")
    with pytest.raises(ValueError, match="not the budget of campaign"):
        evaluate.evaluate_spec(_spec(), ["PROXY_D1"], [1], budget, campaign="c", site_path=PROXY_SITE)
    assert env["calls"] == [] and budget.remaining == 4


def test_repeated_spec_id_refused(env):
    """A second evaluation of one spec id in a campaign would replace its compiled spec and runs."""
    budget = evaluate.RunBudget(4, "c")
    _eval(budget)
    with pytest.raises(ValueError, match="already evaluated"):
        _eval(budget)
    assert budget.remaining == 3 and len(env["calls"]) == 1
    _eval(evaluate.RunBudget(4, "c2"))                   # the same id in another campaign is fine


def test_eligible_runs_scored(env):
    budget = evaluate.RunBudget(4, "c")
    res = _eval(budget, days=["PROXY_D1", "PROXY_D2"], seeds=[1, 2])
    assert budget.remaining == 0 and res.n_runs == 4 and len(env["calls"]) == 4
    assert res.eligibility == "eligible" and isinstance(res.report, DistanceReport) and math.isfinite(res.S)
    assert res.rank_key == (0, 0.0, res.S)
    assert res.interventions_summary["illegal_left_box"] == {"attempted": 8, "executed": 4,
                                                             "not_executed": {"gone": 4}, "counters": {}}
    row = res.to_row()
    assert row["S"] == res.S and row["n_eligible"] == 4
    assert (env["tmp"] / "campaigns" / "c" / "compiled" / "t_spec" / "spec.json").is_file()


def test_gate_failure_excluded(env):
    env["gate_fail"].add(("PROXY_D1", 2))
    res = _eval(evaluate.RunBudget(2, "c"), seeds=[1, 2])
    (bad,) = res.excluded_runs
    assert bad["seed"] == 2 and not bad["g0_pass"] and "G0" in bad["reasons"][0]
    assert len(res.eligible_runs) == 1 and res.eligibility == "excluded"
    assert res.report.n_sim == 2 and math.isfinite(res.S)          # S still over all runs (R23)


def test_null_thresholds_reported_unknown(env):
    env["exp"]["validity"]["max_collisions_per_hour"] = None
    env["gate_fail"].add(("PROXY_D1", 2))
    res = _eval(evaluate.RunBudget(2, "c"), seeds=[1, 2])
    assert [r["eligibility"] for r in res.runs] == ["unknown", "excluded"]
    env["gate_fail"].clear()
    res = _eval(evaluate.RunBudget(1, "c2"))
    assert res.eligibility == "unknown"
    with pytest.raises(ValueError, match="unknown"):
        evaluate.select_best([res])


def test_validation_days_refused(env):
    budget = evaluate.RunBudget(5, "c")
    with pytest.raises(ValueError, match="calibration_days"):
        _eval(budget, days=["PROXY_D1", "PROXY_D4"])
    assert env["calls"] == [] and budget.remaining == 5
    _eval(budget, days=["PROXY_D4"], allow_validation=True)
    assert budget.remaining == 4


def _result(spec_id, S, eligible, lane=0.0, tp=0.0, valid=True, junction=0.0) -> evaluate.EvalResult:
    rep = DistanceReport({}, 1, 1)
    rep.S = S
    run = {"eligibility": "eligible" if eligible else "excluded", "collisions_per_hour": lane + junction,
           "lane_collisions_per_hour": lane, "jam_yield_teleports_per_hour": tp}
    return evaluate.EvalResult(spec_id, "c", valid, [], rep if valid else None, [run] if valid else [])


def test_select_best_R10():
    """Cap on LANE collisions only (R28): b's junction collisions do not count against B0 + 1/h."""
    a = _result("a", 0.5, True, lane=9.0)
    b = _result("b", 0.7, True, lane=2.0, junction=100.0)
    c = _result("c", 0.1, False)
    assert evaluate.select_best([a, b, c], b0_lane_collisions_per_hour=1.5).spec_id == "b"   # a over the cap 2.5
    assert evaluate.select_best([a, b, c]).spec_id == "a"                               # no B0 reference: no cap
    assert evaluate.select_best([_result("x", 0, False, valid=False)]) is None


def test_select_best_fallback_ignores_cap():
    """R42: with no eligible spec under the cap, the R32 fallback ranks by teleports then S, cap not applied."""
    r = [_result("eligible_over_cap", 0.9, True, lane=20.0), _result("jam", 0.1, False, tp=5.0)]
    assert evaluate.select_best(r, b0_lane_collisions_per_hour=1.0).spec_id == "eligible_over_cap"


def test_select_best_fallback_R32():
    """No eligible spec (R42): fewest jam+yield teleports per hour wins, S breaks ties."""
    r = [_result("gridlock", 0.1, False, tp=40.0), _result("lessjam", 0.9, False, tp=6.0),
         _result("lessjam_betterS", 0.8, False, tp=6.0), _result("invalid", 0, False, valid=False)]
    assert evaluate.select_best(r).spec_id == "lessjam_betterS"


def _echo_job(*args):
    """Module-level (picklable) stand-in for evaluate._run_job, run in a spawned worker."""
    import os
    return {"args": args, "pid": os.getpid()}


def test_run_all_pool_path():
    """nproc > 1 goes through the spawn pool, one worker per job (maxtasksperchild=1), results in job order."""
    jobs = [("dir", "s", "PROXY_D1", 1), ("dir", "s", "PROXY_D1", 2)]
    out = evaluate._run_all(jobs, 2, job=_echo_job)
    assert [o["args"] for o in out] == jobs
    assert len({o["pid"] for o in out} | {os.getpid()}) == 3


def test_spec_json_path(tmp_path):
    """Manifest spec_json_hash hashes the spec actually run: campaign-local spec.json first, then rules/specs."""
    assert runner.spec_json_path(tmp_path, "B0") == runner.SPECS_DIR / "B0.json"
    (tmp_path / "spec.json").write_text("{}", encoding="utf-8")
    assert runner.spec_json_path(tmp_path, "B0") == tmp_path / "spec.json"


def test_run_job_uses_campaign_compiled_dir(env, monkeypatch):
    """_run_job hands runner.run the campaign-local compiled spec, the site's net and the day's routes."""
    spec_dir = env["tmp"] / "campaigns" / "c" / "compiled" / "t_spec"
    evaluate.compile_spec(_spec(), spec_dir, site=evaluate.load_site(PROXY_SITE))
    seen = {}
    monkeypatch.setattr(runner, "run", lambda *a, **kw: seen.update(args=a, **kw) or "ok")
    assert evaluate._run_job(spec_dir, "t_spec", "PROXY_D1", 2, PROXY_SITE, 900, env["tmp"] / "runs") == "ok"
    inputs = seen["inputs"]
    assert seen["args"] == ("t_spec", "PROXY_D1", 2) and seen["runs_root"] == env["tmp"] / "runs"
    assert seen["sim_end_s"] == 900 and seen["site_path"] == PROXY_SITE
    assert inputs.spec_dir == spec_dir and inputs.vtypes.is_file() and inputs.site.source == "LITERATURE_PROXY"
    assert inputs.net.is_file() and inputs.routes == runner.DEMAND_DIR / "routes_PROXY_D1.rou.xml"
    assert inputs.routes.is_file()
