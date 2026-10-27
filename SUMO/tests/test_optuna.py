"""thesis_sumo.baselines.optuna_search: search space (R20), spec building, budget stop, resume, determinism, best via
select_best. evaluate_spec is mocked: real validation, real RunBudget, S a fixed function of the spec."""

import csv
import json
import random
from types import SimpleNamespace

import optuna
import pytest

from thesis_sumo import evaluate
from thesis_sumo.baselines import optuna_search as opt
from thesis_sumo.config import REPO_ROOT, load_site
from thesis_sumo.rules.schema import load_bounds
from thesis_sumo.rules.validator import narrowest_lane, validate

PROXY_SITE = REPO_ROOT / "config" / "site.proxy.yaml"
B1 = json.loads((REPO_ROOT / "rules" / "specs" / "B1_manual.json").read_text(encoding="utf-8"))
optuna.logging.set_verbosity(optuna.logging.WARNING)


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setattr(evaluate, "CAMPAIGNS_DIR", tmp_path / "campaigns")
    site = load_site(PROXY_SITE)
    st = {"calls": [], "invalid": set(), "interrupt": set()}

    def fake_eval(spec, days, seeds, budget, *, campaign, site_path=None, nproc=1, sim_end_s=None):
        evaluate.check_days(days, evaluate.load_experiment())
        sid = spec["spec_id"]
        issues = validate(spec, site)
        if sid in st["invalid"]:
            issues = [{"path": "x", "code": "logic", "message": "forced"}]
        if issues:
            return evaluate.EvalResult(sid, campaign, False, issues)
        budget.consume(len(days) * len(seeds))
        d = evaluate.CAMPAIGNS_DIR / campaign / "compiled" / sid
        d.mkdir(parents=True)
        (d / "spec.json").write_text(json.dumps(spec), encoding="utf-8")
        st["calls"] += [(sid, day, s) for day in days for s in seeds]
        if sid in st["interrupt"]:
            raise KeyboardInterrupt
        car = spec["driver_archetypes"][0]["params"]
        S = (car["accel"] - 2.0) ** 2 + spec["traci_rules"][2]["params"]["p_right_lane"]
        runs = [{"eligibility": "eligible", "collisions_per_hour": 0.0, "lane_collisions_per_hour": 0.0,
                 "jam_yield_teleports_per_hour": 0.0}] * (len(days) * len(seeds))
        return evaluate.EvalResult(sid, campaign, True, [], SimpleNamespace(S=S), runs)

    monkeypatch.setattr(evaluate, "evaluate_spec", fake_eval)
    return st


def _run(campaign, budget=36, **kw):
    return opt.run_optuna(B1, campaign, budget, [1], None, site_path=PROXY_SITE, **kw)   # R44: D1-D3 x seed 1


def _space():
    return opt.search_space(B1, load_bounds(), lane_width_m=narrowest_lane(load_site(PROXY_SITE))[0])


def test_search_space_b1_names():
    names = {p.name for p in _space()}
    for a in B1["driver_archetypes"]:   # exactly the declared attributes, nothing switched on
        assert {n.split(".")[2] for n in names if n.startswith(f"arch.{a['id']}.")} == set(a["params"])
    assert {"rule.2.queue_space_seeking.p_total", "rule.2.queue_space_seeking.split_wrong_lane",
            "rule.2.queue_space_seeking.split_right_lane", "rule.0.swarm_red_running.p_max_frac",
            "share.car.car_saval", "share.moto.moto_saval"} <= names
    assert not any(n.endswith((".p_wrong_lane", ".p_right_lane", ".p_sidewalk", ".p_max", ".t_w")) for n in names)
    assert not any(n.startswith("share.moto_violator") for n in names)   # one archetype: no share param
    assert len(names) == 41


def test_built_spec_keeps_structure():
    params = {p.name: (p.choices[0] if p.choices else p.high) for p in _space()}
    spec = opt.build_spec(B1, params, spec_id="B2_t000", provenance={"iteration": 0})
    assert spec["source"] == "optuna" and spec["spec_id"] == "B2_t000"
    for a, b in zip(spec["driver_archetypes"], B1["driver_archetypes"]):
        assert (a["id"], a.get("distribution"), set(a["params"])) == (b["id"], b.get("distribution"), set(b["params"]))
    for r, b in zip(spec["traci_rules"], B1["traci_rules"]):
        assert (r["rule_type"], r["applies_to"], set(r["params"])) == (b["rule_type"], b["applies_to"], set(b["params"]))
    qss = spec["traci_rules"][2]["params"]
    assert qss["p_wrong_lane"] + qss["p_right_lane"] + qss["p_sidewalk"] == pytest.approx(1.0)
    assert spec["traci_rules"][0]["params"]["p_max"] == pytest.approx(1.0)


def test_random_trials_all_valid():
    space, site, bounds = _space(), load_site(PROXY_SITE), load_bounds()
    rng = random.Random(0)
    bad = 0
    for i in range(200):
        params = {p.name: rng.choice(p.choices) if p.choices else rng.uniform(p.low, p.high) for p in space}
        bad += bool(validate(opt.build_spec(B1, params, spec_id=f"r{i}", bounds=bounds), site, bounds))
    assert bad == 0


def test_lcpushygap_reparametrised():
    s = json.loads(json.dumps(B1))
    s["driver_archetypes"][2]["params"]["lcPushyGap"] = 0.2
    names = {p.name for p in opt.search_space(s, load_bounds())}
    assert "arch.moto_saval.lcPushyGap_frac" in names and not any("lcPushy." in n for n in names)
    params = {p.name: p.high for p in opt.search_space(s, load_bounds())}
    a = opt.build_spec(s, params)["driver_archetypes"][2]["params"]
    assert a["lcPushyGap"] == pytest.approx(a["minGapLat"]) and "lcPushy" not in a
    s["driver_archetypes"][2]["params"]["lcPushy"] = 0.5
    with pytest.raises(ValueError, match="both"):
        opt.search_space(s, load_bounds())


def test_stick_flat_and_sums():
    assert sum(opt._stick([0.3, 0.9])) == pytest.approx(1.0)
    assert opt._stick([0.4]) == pytest.approx([0.4, 0.6])
    assert sum(opt._stick([0.5, 0.5], 0.3)) == pytest.approx(0.3)


def test_budget_stop_36_runs_12_trials_r44(env):
    res = _run("B2")
    assert (res.n_trials, res.runs_used, res.stop_reason, res.n_invalid) == (12, 36, "budget", 0)
    assert len(env["calls"]) == 36 and evaluate.RunBudget(36, "B2").remaining == 0
    rows = list(csv.DictReader((evaluate.CAMPAIGNS_DIR / "B2" / "convergence.csv").open(encoding="utf-8")))
    assert [int(r["runs_used"]) for r in rows] == list(range(3, 37, 3))
    best = [float(r["best_S"]) for r in rows]
    assert best == sorted(best, reverse=True)


def test_invalid_trial_costs_nothing(env):
    env["invalid"].add("B2_t001")
    res = _run("B2", budget=9)
    assert (res.n_trials, res.n_invalid, res.runs_used) == (4, 1, 9)
    assert {c[0] for c in env["calls"]} == {"B2_t000", "B2_t002", "B2_t003"}


def test_resume_does_not_recharge(env):
    first = _run("B2", max_trials=4)
    assert (first.n_trials, first.runs_used, first.stop_reason) == (4, 12, "max_trials")
    env["interrupt"].add("B2_t004")                # killed after charging: left RUNNING in the study
    with pytest.raises(KeyboardInterrupt):
        _run("B2")
    res = _run("B2")
    assert res.runs_used == 36 and len(env["calls"]) == 36
    assert len({c[0] for c in env["calls"]}) == 12   # no spec id evaluated twice
    states = [r["state"] for r in res.convergence]
    assert states[4] == "FAIL" and states.count("COMPLETE") == 11
    with pytest.raises(ValueError, match="seeds"):
        opt.run_optuna(B1, "B2", 36, [1, 2], None, site_path=PROXY_SITE)
    with pytest.raises(ValueError, match="sim_end_s"):
        opt.run_optuna(B1, "B2", 36, [1], None, site_path=PROXY_SITE, sim_end_s=600)


def test_deterministic_with_sampler_seed(env):
    params = []
    for c, seed in (("a", 0), ("b", 0), ("c", 1)):
        _run(c, budget=12, sampler_seed=seed)
        study = optuna.load_study(study_name=c, storage=optuna.storages.journal.JournalStorage(
            optuna.storages.journal.JournalFileBackend(str(evaluate.CAMPAIGNS_DIR / c / "study.journal"))))
        params.append([t.params for t in study.trials])
    assert params[0] == params[1] and params[0] != params[2]


def test_best_via_select_best(env, monkeypatch, tmp_path):
    seen = {}

    def fake_select(results, b0=None):
        seen.update(n=len(results), b0=b0)
        return results[1]

    monkeypatch.setattr(evaluate, "select_best", fake_select)
    res = _run("B2", budget=9, b0_lane_collisions_per_hour=1.3)
    assert seen == {"n": 3, "b0": 1.3}
    assert res.best.spec_id == "B2_t001" and res.best_spec["spec_id"] == "B2_t001"
    out = tmp_path / "B2_best.json"
    assert opt.main(["--structure", str(REPO_ROOT / "rules/specs/B1_manual.json"), "--campaign", "B2", "--budget",
                     "9", "--site", str(PROXY_SITE),
                     "--b0-lane-collisions", "1.3", "--write-best", str(out)]) == 0
    written = json.loads(out.read_text(encoding="utf-8"))
    assert written["spec_id"] == "B2_best" and written["source"] == "optuna"
    assert written["provenance"]["model"] == "optuna-tpe"
    assert written["provenance"]["reference"] == "sampler_seed=0;trial=1;n_startup=4"
    with pytest.raises(SystemExit):   # the R10 cap value is never implicit
        opt.main(["--structure", str(REPO_ROOT / "rules/specs/B1_manual.json"), "--campaign", "B2", "--budget", "9"])
    assert validate(written, load_site(PROXY_SITE)) == []


def test_n_startup_recorded(env):
    _run("B2", budget=3)
    study = optuna.load_study(study_name="B2", storage=optuna.storages.journal.JournalStorage(
        optuna.storages.journal.JournalFileBackend(str(evaluate.CAMPAIGNS_DIR / "B2" / "study.journal"))))
    assert study.user_attrs["n_startup_trials"] == opt.N_STARTUP_TRIALS == 4


def test_b0_lane_collisions_from_r28_manifests():
    assert opt.b0_lane_collisions_per_hour() == pytest.approx(12 / 9)
