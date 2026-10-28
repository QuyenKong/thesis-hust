"""thesis_sumo.llm.loop: pending stop/resume, R44 budget, invalid samples, feedback, params_only lock, best via
select_best, idempotent rerun. evaluate_spec is mocked (real validation, real RunBudget, real DistanceReport, S a
fixed function of the spec); the LLM is the file backend (stand-in) answered by the test."""

import copy
import csv
import json

import pytest

from thesis_sumo import evaluate
from thesis_sumo.config import REPO_ROOT, load_experiment, load_site
from thesis_sumo.llm import client as llm_client
from thesis_sumo.llm import loop
from thesis_sumo.llm.client import HARNESS_KEYS
from thesis_sumo.metrics.distance import DistanceReport, MetricReport
from thesis_sumo.rules.validator import structure_issues, validate

PROXY_SITE = REPO_ROOT / "config" / "site.proxy.yaml"
B1 = json.loads((REPO_ROOT / "rules" / "specs" / "B1_manual.json").read_text(encoding="utf-8"))
CAL = load_experiment()["data_split"]["calibration_days"]


def _report(S: float) -> DistanceReport:
    m = MetricReport(key="M1/moto", label="discharge headway", unit="s", kind="dist", target=None,
                     evidence="literature", d=S, d_day_day=0.5, R=2 * S, direction="sim>obs", scored=True,
                     sim_mean=1.0, obs_mean=0.8, weight=1.0)
    return DistanceReport({m.key: m}, n_sim=3, n_obs_days=3)


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setattr(evaluate, "CAMPAIGNS_DIR", tmp_path / "campaigns")
    monkeypatch.setattr(llm_client, "LOGS_DIR", tmp_path / "logs")

    def fake_targets(days, *, exp=None, site=None):
        evaluate.check_days(days, exp)
        return {"M1/moto": {"label": "discharge headway", "unit": "s", "obs_mean": 0.8, "evidence": "literature"}}

    monkeypatch.setattr(loop, "calibration_targets", fake_targets)
    site = load_site(PROXY_SITE)
    st = {"calls": [], "eval_ids": [], "reject": set(), "crash": set()}

    def fake_eval(spec, days, seeds, budget, *, campaign, site_path=None, nproc=1, sim_end_s=None):
        evaluate.check_days(days, evaluate.load_experiment())
        sid = spec["spec_id"]
        st["eval_ids"].append(sid)
        d = evaluate.CAMPAIGNS_DIR / campaign / "compiled" / sid
        if (d / "spec.json").is_file():
            raise ValueError(f"spec id {sid!r} was already evaluated")
        issues = validate(spec, site) or ([{"path": "x", "code": "logic", "message": "compile"}]
                                          if sid in st["reject"] else [])
        if issues:
            return evaluate.EvalResult(sid, campaign, False, issues)
        budget.consume(len(days) * len(seeds))
        d.mkdir(parents=True)
        (d / "spec.json").write_text(json.dumps(spec), encoding="utf-8")
        st["calls"] += [(sid, day, s) for day in days for s in seeds]
        if sid in st["crash"]:
            st["crash"].discard(sid)
            raise KeyboardInterrupt   # charged, compiled, no result: the process dies here
        S = abs(spec["driver_archetypes"][0]["params"]["tau"] - 1.2)
        runs = [{"day": day, "seed": s, "reasons": [], "eligibility": "eligible", "collisions_per_hour": 0.0,
                 "lane_collisions_per_hour": 0.0, "jam_yield_teleports_per_hour": 0.0} for day in days for s in seeds]
        return evaluate.EvalResult(sid, campaign, True, [], _report(S), runs,
                                   {"illegal_left_box": {"attempted": 3, "executed": 2}})

    monkeypatch.setattr(evaluate, "evaluate_spec", fake_eval)
    st["logs"] = tmp_path / "logs"
    return st


def _good(it: int, j: int) -> dict:
    a = {k: v for k, v in copy.deepcopy(B1).items() if k not in HARNESS_KEYS}
    a["driver_archetypes"][0]["params"]["tau"] = round(1.0 + 0.1 * j + 0.05 * it, 3)
    return a


def _answer_all(env, campaign, fn=_good) -> int:
    """Write a response for every pending request; fn(iteration, sample) -> answer object (None = leave pending)."""
    n = 0
    for req in loop.pending_requests(campaign):
        it, j = (int(x[2:]) for x in req.stem.split("__")[1].split("_")[:2])
        ans = fn(it, j)
        if ans is not None:
            resp = req.parent.parent / "responses" / req.name
            resp.parent.mkdir(parents=True, exist_ok=True)
            resp.write_text(json.dumps({"content": ans}), encoding="utf-8")
            n += 1
    return n


def _run(campaign="P1", **kw):
    kw = {"budget_runs": 36, "site_path": PROXY_SITE, "b0_lane_collisions_per_hour": 1.333, **kw}
    return loop.run_loop(campaign, kw.pop("mode", "params_only"), kw.pop("base", B1), **kw)


def _drive(env, campaign="P1", fn=_good, **kw):
    """Run, answer, rerun until the loop finishes (the controller's cycle)."""
    for _ in range(20):
        try:
            return _run(campaign, **kw)
        except loop.LoopPending as e:
            assert len(e.paths) and _answer_all(env, campaign, fn)
    raise AssertionError("loop never finished")


def test_r44_budget_exactly_36(env):
    res = _drive(env, nproc=9)   # 3 specs evaluated concurrently, budget charged under its lock
    assert res.runs_used == 36 and res.stop_reason == "budget" and len(res.iterations) == 3
    assert evaluate.RunBudget(36, "P1").used == 36
    assert len(env["calls"]) == 36 and {(d, s) for _, d, s in env["calls"]} == {(d, 1) for d in CAL}
    assert res.validity["n_valid"] == res.validity["n_answered"] == 12 and res.validity_rate == 1.0
    root = evaluate.CAMPAIGNS_DIR / "P1"
    status = json.loads((root / "loop" / "loop.json").read_text(encoding="utf-8"))["status"]
    assert status["n_iterations"] == 3 and status["n_extra_r45"] == 0 and status["stop_reason"] == "budget"
    assert status["validity"]["n_evaluated"] == 12 and status["validity"]["per_attempt_rate"] == 1.0
    assert len(list((root / "specs").glob("P1_it0*_s0*.json"))) == 12
    with (root / "loop" / "convergence.csv").open(encoding="utf-8") as f:
        conv = list(csv.DictReader(f))
    assert [int(r["runs_used"]) for r in conv] == list(range(3, 37, 3))
    it1 = json.loads((root / "loop" / "iter_1.json").read_text(encoding="utf-8"))
    assert it1["spec_ids"] == [f"P1_it01_s{j:02d}" for j in range(4)] and it1["llm"]["model"]
    assert it1["samples"][0]["row"]["S"] == pytest.approx(it1["samples"][0]["S"]) and it1["samples"][0]["rank_key"]


def test_pending_stop_and_resume_without_recharge(env):
    with pytest.raises(loop.LoopPending) as e:
        _run()
    assert e.value.iteration == 1 and len(e.value.paths) == 4 and not env["eval_ids"]   # all 4 asked at once
    assert loop.main(["pending", "--campaign", "P1"]) == 0 and len(loop.pending_requests("P1")) == 4
    _answer_all(env, "P1", lambda it, j: _good(it, j) if j < 2 else None)
    with pytest.raises(loop.LoopPending) as e:
        _run()
    assert len(e.value.paths) == 2 and not env["eval_ids"]           # nothing evaluated while answers are missing
    _answer_all(env, "P1")
    with pytest.raises(loop.LoopPending) as e:                       # iteration 1 evaluated, iteration 2 asked
        _run()
    assert e.value.iteration == 2 and evaluate.RunBudget(36, "P1").used == 12
    n_eval = len(env["eval_ids"])
    with pytest.raises(loop.LoopPending):                            # rerun while pending: no re-evaluation
        _run()
    assert len(env["eval_ids"]) == n_eval and evaluate.RunBudget(36, "P1").used == 12
    res = _drive(env)
    assert res.runs_used == 36 and len(env["eval_ids"]) == 12          # every spec evaluated exactly once


def test_cli_pending_exit_code(env, capsys):
    rc = loop.main(["--campaign", "P1", "--mode", "params_only", "--base",
                    str(REPO_ROOT / "rules" / "specs" / "B1_manual.json"), "--budget", "36",
                    "--site", str(PROXY_SITE), "--b0-lane-collisions", "1.333"])
    out = capsys.readouterr().out
    assert rc == 3 and out.count("P1__it01_s0") == 8   # request -> response, 4 samples
    with pytest.raises(SystemExit):                    # the B0 cap is required, as for Optuna
        loop.main(["--campaign", "P1", "--mode", "full", "--budget", "36"])
    with pytest.raises(ValueError, match="required"):
        _run(b0_lane_collisions_per_hour=None)


def test_new_campaign_id_has_own_budget_and_state(env):
    """A new campaign id (e.g. P1_n28) never shares budget.json, loop state or LLM logs with an old campaign; 2
    planned iterations x 4 specs x 3 calibration days x seed 1 = 24 runs."""
    evaluate.RunBudget(36, "P1").consume(12)   # an old, partly spent campaign
    res = _drive(env, "P1_n28", budget_runs=24, n_iter=2)
    assert (res.runs_used, len(res.iterations), res.stop_reason) == (24, 2, "budget")
    assert evaluate.RunBudget(24, "P1_n28").used == 24 and evaluate.RunBudget(36, "P1").used == 12
    assert (evaluate.CAMPAIGNS_DIR / "P1_n28" / "loop" / "loop.json").is_file()
    assert not (evaluate.CAMPAIGNS_DIR / "P1" / "loop").exists()
    assert {p.parent.name for p in env["logs"].glob("*/*.json")} == {"P1_n28"}


def test_prompt_version_default_override_and_lock(env):
    res = _drive(env, "P1_n28", n_iter=1, budget_runs=12)
    lock = json.loads((evaluate.CAMPAIGNS_DIR / "P1_n28" / "loop" / "loop.json").read_text(encoding="utf-8"))
    assert lock["llm"]["prompt_version"] == "v002" and res.best_spec["provenance"]["prompt_version"] == "v002"
    with pytest.raises(ValueError, match="other settings"):   # a campaign keeps its prompt version
        _run("P1_n28", n_iter=1, budget_runs=12, prompt_version="v001")
    with pytest.raises(ValueError, match="prompt"):
        _run("Px", prompt_version="v999")
    assert not (evaluate.CAMPAIGNS_DIR / "Px" / "loop").exists()
    rc = loop.main(["--campaign", "P1_old", "--mode", "params_only", "--base",
                    str(REPO_ROOT / "rules" / "specs" / "B1_manual.json"), "--budget", "36", "--site", str(PROXY_SITE),
                    "--b0-lane-collisions", "1.333", "--prompt-version", "v001"])
    lock = json.loads((evaluate.CAMPAIGNS_DIR / "P1_old" / "loop" / "loop.json").read_text(encoding="utf-8"))
    assert rc == 3 and lock["llm"]["prompt_version"] == "v001"


def test_invalid_sample_costs_zero(env):
    def fn(it, j):
        a = _good(it, j)
        if (it, j) == (1, 0):
            a["driver_archetypes"][0]["params"]["tau"] = 99.0   # out of bounds on every attempt
        return a

    res = _drive(env, fn=fn, n_iter=1, budget_runs=9)
    it1 = res.iterations[0]
    assert [s["status"] for s in it1["samples"]] == ["invalid", "evaluated", "evaluated", "evaluated"]
    assert res.runs_used == 9 and evaluate.RunBudget(9, "P1").used == 9 and it1["samples"][0]["runs"] == 0
    assert it1["validity"]["n_invalid"] == 1 and it1["validity"]["n_answered"] == 4 and res.validity_rate == 0.75
    assert res.validity["per_attempt_rate"] == pytest.approx(3 / 6)   # 3 failed attempts + 3 first-try successes
    assert len(list(env["logs"].glob("P1/P1__it01_s00_a*.json"))) == 3   # 3 attempts, then given up


def test_feedback_iteration2(env):
    for _ in range(2):   # iteration 1 asked, answered; then iteration 2 asked
        with pytest.raises(loop.LoopPending):
            _run()
        _answer_all(env, "P1", lambda it, j: _good(it, j) if it == 1 else None)
    with pytest.raises(loop.LoopPending) as e:
        _run()
    assert e.value.iteration == 2
    req = json.loads((env["logs"] / "P1" / "requests" / "P1__it02_s00_a1.json").read_text(encoding="utf-8"))
    msgs = req["messages"]
    assert [m["role"] for m in msgs] == ["system", "user", "user"]
    fb = msgs[2]["content"]
    for j in range(4):
        assert f"## Spec P1_it01_s{j:02d}: S = " in fb and f'"P1_it01_s{j:02d}"' in fb
    assert "illegal_left_box" in fb and "provenance" not in fb
    exp = load_experiment()
    text = json.dumps(msgs)
    assert "PROXY_D" not in text
    assert not any(d in text for d in exp["data_split"]["calibration_days"] + exp["data_split"]["validation_days"])


def test_params_only_structure_enforced(env):
    def fn(it, j):
        a = _good(it, j)
        if j == 1:
            a["driver_archetypes"][0]["params"]["sigma"] = 0.5   # adds an attribute: structure_locked
        return a

    res = _drive(env, fn=fn, n_iter=1, budget_runs=9)
    assert [s["status"] for s in res.iterations[0]["samples"]][1] == "invalid"
    assert "P1_it01_s01" not in env["eval_ids"]
    assert res.results[1].issues[0]["code"] == "structure_locked"
    for r in res.results:
        if r.valid:
            spec = json.loads((evaluate.CAMPAIGNS_DIR / "P1" / "specs" / f"{r.spec_id}.json").read_text())
            assert structure_issues(spec, B1) == []
    with pytest.raises(ValueError, match="no base spec"):
        _run("P2", mode="full")
    with pytest.raises(ValueError, match="needs the base spec"):
        _run("P1x", base=None)


def test_best_via_select_best(env, monkeypatch):
    seen = []
    real = evaluate.select_best

    def spy(results, b0=None):
        seen.append(([r.spec_id for r in results], b0))
        return real(results, b0)

    monkeypatch.setattr(evaluate, "select_best", spy)
    res = _drive(env, b0_lane_collisions_per_hour=1.3)
    assert seen[-1][1] == 1.3 and len(seen[-1][0]) == 12
    assert res.best.spec_id == min((r for r in res.results if r.valid), key=lambda r: r.S).spec_id
    assert res.best_spec["spec_id"] == res.best.spec_id
    out = evaluate.CAMPAIGNS_DIR / "P1_best.json"
    monkeypatch.setattr(loop, "run_loop", lambda *a, **k: res)
    assert loop.main(["--campaign", "P1", "--mode", "params_only", "--budget", "36", "--b0-lane-collisions", "1.3",
                      "--write-best", str(out)]) == 0
    written = json.loads(out.read_text(encoding="utf-8"))
    assert written["spec_id"] == "P1_best" and res.best.spec_id in written["description"]


def test_rerun_after_completion_is_noop(env):
    res1 = _drive(env)
    root = evaluate.CAMPAIGNS_DIR / "P1"
    before = {p: p.read_bytes() for p in (root / "loop").glob("iter_*.json")}
    n_logs = len(list(env["logs"].rglob("*.json")))
    res2 = _run()
    assert len(env["eval_ids"]) == 12 and evaluate.RunBudget(36, "P1").used == 36
    assert {p: p.read_bytes() for p in (root / "loop").glob("iter_*.json")} == before
    assert len(list(env["logs"].rglob("*.json"))) == n_logs
    assert res2.best.spec_id == res1.best.spec_id and res2.convergence == res1.convergence
    with pytest.raises(ValueError, match="other settings"):
        _run(seeds=[1, 2])


def test_budget_stops_mid_iteration(env):
    res = _drive(env, budget_runs=30)
    assert res.stop_reason == "budget" and res.runs_used == 30
    assert [s["status"] for s in res.iterations[2]["samples"]] == ["evaluated"] * 2 + ["unaffordable"] * 2


def test_network_error_skips_sample(env, monkeypatch):
    import openai
    try:  # openai >= 3 ships its HTTP layer as httpx2 (as tests/test_llm.py)
        import httpx2 as httpx
    except ImportError:
        import httpx

    real = llm_client.LLMClient.generate_spec

    def flaky(self, messages, mode, base_spec=None, *, iteration, sample_idx):
        if (iteration, sample_idx) == (1, 2):
            raise openai.APITimeoutError(request=httpx.Request("POST", "http://llm.test/v1"))
        return real(self, messages, mode, base_spec, iteration=iteration, sample_idx=sample_idx)

    monkeypatch.setattr(llm_client.LLMClient, "generate_spec", flaky)
    res = _drive(env, n_iter=1, budget_runs=9)
    assert [s["status"] for s in res.iterations[0]["samples"]][2] == "network_error"
    assert res.runs_used == 9 and res.validity["n_answered"] == 3 and res.validity["n_network_error"] == 1


def test_crash_resume_keeps_results(env):
    env["crash"].add("P1_it01_s01")
    with pytest.raises(loop.LoopPending):
        _run()
    _answer_all(env, "P1")
    with pytest.raises(KeyboardInterrupt):
        _run()
    res_dir = evaluate.CAMPAIGNS_DIR / "P1" / "loop" / "results"
    assert (res_dir / "P1_it01_s00.pkl").is_file() and not (res_dir / "P1_it01_s01.pkl").exists()
    used, n_eval = evaluate.RunBudget(36, "P1").used, len(env["eval_ids"])
    assert used == 3 * n_eval
    res = _drive(env)
    assert [s["status"] for s in res.iterations[0]["samples"]][:2] == ["evaluated", "lost"]
    assert res.iterations[0]["samples"][1]["runs"] == 3 and res.runs_used == 36 == evaluate.RunBudget(36, "P1").used
    assert len(env["eval_ids"]) == len(set(env["eval_ids"])) == 12          # nothing evaluated twice


def test_full_mode_p2_iteration(env):
    res = _drive(env, "P2", mode="full", base=None, n_iter=1, budget_runs=12)
    assert res.runs_used == 12 and [s["status"] for s in res.iterations[0]["samples"]] == ["evaluated"] * 4
    req = json.loads((env["logs"] / "P2" / "requests" / "P2__it01_s00_a1.json").read_text(encoding="utf-8"))
    assert req["mode"] == "full" and req["schema"] == loop.llm_schema("full")
    ctx = req["messages"][1]["content"]
    assert "You may change the structure" in ctx and "Base spec" not in ctx
    lock = json.loads((evaluate.CAMPAIGNS_DIR / "P2" / "loop" / "loop.json").read_text(encoding="utf-8"))
    assert lock["mode"] == "full" and lock["base_spec"] is None


def test_lock_refuses_other_site_and_b0(env, tmp_path):
    with pytest.raises(loop.LoopPending):
        _run()
    other = tmp_path / "site.proxy.yaml"
    other.write_bytes(PROXY_SITE.read_bytes())
    with pytest.raises(ValueError, match="site"):
        _run(site_path=other)
    with pytest.raises(ValueError, match="b0_lane_collisions_per_hour"):
        _run(b0_lane_collisions_per_hour=2.0)


def test_r45_extra_iteration_spends_budget(env):
    def fn(it, j):
        a = _good(it, j)
        if it == 1 and j < 2:
            a["driver_archetypes"][0]["params"]["tau"] = 99.0
        return a

    res = _drive(env, fn=fn)
    assert res.runs_used == 36 and res.stop_reason == "budget" and len(res.iterations) == 4
    it4 = res.iterations[3]
    assert not it4["planned"] and it4["reason"].startswith("R45 extra: 6 of 36")
    assert [s["status"] for s in it4["samples"]] == ["evaluated"] * 2 + ["unaffordable"] * 2
    status = json.loads((evaluate.CAMPAIGNS_DIR / "P1" / "loop" / "loop.json").read_text(encoding="utf-8"))["status"]
    assert status["n_iterations"] == 4 and status["n_extra_r45"] == 1
    assert status["validity"]["n_invalid"] == 2 and status["validity"]["n_unaffordable"] == 2


def test_crash_on_last_affordable_spec(env):
    """Reviewer repro: the crash happens after the last charge, so on rerun remaining < cost from the start."""
    env["crash"].add("P1_it01_s03")
    with pytest.raises(loop.LoopPending):
        _run(budget_runs=12, n_iter=1, max_iter=1)
    _answer_all(env, "P1")
    with pytest.raises(KeyboardInterrupt):
        _run(budget_runs=12, n_iter=1, max_iter=1)
    n_eval = len(env["eval_ids"])
    res = _run(budget_runs=12, n_iter=1, max_iter=1)
    assert len(env["eval_ids"]) == n_eval == 4
    assert [s["status"] for s in res.iterations[0]["samples"]] == ["evaluated"] * 3 + ["lost"]
    assert res.runs_used == 12 and res.best is not None and res.stop_reason == "budget"
    status = json.loads((evaluate.CAMPAIGNS_DIR / "P1" / "loop" / "loop.json").read_text(encoding="utf-8"))["status"]
    assert status["n_iterations"] == 1 and status["runs_used"] == status["budget_used"] == 12 and "error" not in status


def test_crash_on_last_spec_of_r45_extra(env):
    def fn(it, j):
        a = _good(it, j)
        if it == 1 and j < 2:
            a["driver_archetypes"][0]["params"]["tau"] = 99.0
        return a

    env["crash"].add("P1_it04_s01")
    with pytest.raises(KeyboardInterrupt):
        _drive(env, fn=fn)
    res = _drive(env, fn=fn)
    assert res.runs_used == 36 and len(res.iterations) == 4 and len(env["eval_ids"]) == len(set(env["eval_ids"]))
    it4 = res.iterations[3]
    assert it4["reason"].startswith("R45 extra: 6 of 36")
    assert [s["status"] for s in it4["samples"]] == ["evaluated", "lost", "unaffordable", "unaffordable"]


def test_budget_mismatch_is_an_error(env):
    _drive(env, n_iter=1, max_iter=1, budget_runs=15)
    evaluate.RunBudget(15, "P1").consume(1)   # a charge no sample explains
    with pytest.raises(RuntimeError, match="!= budget.json used"):
        _run(n_iter=1, max_iter=1, budget_runs=15)
    status = json.loads((evaluate.CAMPAIGNS_DIR / "P1" / "loop" / "loop.json").read_text(encoding="utf-8"))["status"]
    assert "error" in status and status["runs_used"] == 12 and status["budget_used"] == 13
