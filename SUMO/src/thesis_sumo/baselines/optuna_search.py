"""Optuna baseline (PLAN 7.1): tune only the PARAMETERS of a fixed spec STRUCTURE. B2 = structure of B1_manual,
H = structure produced by the LLM.

    .venv/bin/python -m thesis_sumo.baselines.optuna_search --structure rules/specs/B1_manual.json --campaign B2 \
        --budget 36 --nproc 3 --site config/site.proxy.yaml --b0-lane-collisions 1.333 \
        [--write-best rules/specs/B2_best.json]

Ruling R44: one trial = calibration days PROXY_D1-D3 x seed 1 = 3 runs, so 36 runs = 12 trials (CLI defaults: days
= experiment.yaml calibration_days, seeds = [1]). TPE uses N_STARTUP_TRIALS = 4 random trials, not Optuna's
default 10: with 12 trials the default would leave TPE random search for all but 2 trials. The value is stored in
the study user attrs and in every spec's provenance. `--b0-lane-collisions` (R10 cap of select_best) is required;
its documented source is `b0_lane_collisions_per_hour()`: the mean lane-collision rate of the R28 B0 runs on the
final F2 net (experiments/runs/B0__PROXY_D1-D3/seed_01-03 manifests) = 12/9 = 1.333/h.

Same objective (`evaluate.evaluate_spec(...).S`, lower is better) and the same SUMO-run budget (`evaluate.RunBudget`,
1 spec x 1 day x 1 seed = 1 run) as the LLM loop; best spec by `evaluate.select_best` (R10/R32/R42), never by S
alone. Campaign files (experiments/campaigns/<campaign>/, next to evaluate's budget.json / compiled/ / runs/):
`study.journal` (Optuna JournalStorage), `optuna_results/<spec_id>.pkl` (the EvalResult of each finished trial),
`convergence.csv` (SUMO runs used vs best S so far).

Search space (`search_space`, ruling R20), structure = what the spec declares:
- Archetype params: exactly the attributes present in the structure, range `Bound.for_vclass(base_vclass)`;
  categorical attributes (latAlignment) sample their `values`; `fixed` rows keep their value. Absent attributes
  stay absent (SUMO default), never switched on: adding one would change the structure.
- lcPushy / lcPushyGap: only the one the structure declares is sampled (both declared = invalid structure, the
  validator rejects it). lcPushyGap is sampled as a fraction of the archetype's minGapLat (declared value, else the
  vclass default the validator uses), so lcPushyGap <= minGapLat by construction.
- minGapLat: upper bound clipped to the narrowest site lane (`lane_width_m`), as the validator checks.
- Rule params: every param present in each rule, range from `TRACI_RULE_PARAMS`; optional params absent from the
  structure (queue_space_seeking t_w) stay absent. swarm_red_running: p_max = p0 + p_max_frac * (1 - p0), so
  p0 <= p_max. queue_space_seeking: p_total in [0, 1] split over the declared options by stick-breaking, so
  sum p_* = p_total <= 1 (a flat prior on the total keeps small seeking probabilities reachable; a flat Dirichlet
  over options + "no seeking" would put P(sum <= 0.2) at 0.8%).
- Shares: per vTypeDistribution with k >= 2 archetypes, k - 1 stick-breaking draws u in [1e-3, 1 - 1e-3] with
  v_j = 1 - (1 - u_j)^(1 / (k - 1 - j)), i.e. a flat Dirichlet prior on the simplex (no redundant scale dimension,
  shares > 0 as the schema requires, sum = 1 to rounding). One-archetype distributions have no share param.
The same stick-breaking (exponent form) splits queue_space_seeking's p_total.

Budget and resume: a trial is asked only if the remaining budget covers len(days) x len(seeds) runs; an invalid
spec costs 0 runs (evaluate_spec) and is told FAIL. The study persists; on resume a trial left RUNNING with a saved
EvalResult is completed from it, one without is told FAIL (its runs stay charged, as evaluate never refunds), and
the sampler is reseeded with sampler_seed + number of existing trials, so TPE's random start-up points are not
repeated. Days, seeds and structure are stored in the study and a resume with other values is refused.
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import math
import pickle
import sys
from dataclasses import dataclass, field
from pathlib import Path

import optuna
from optuna.distributions import CategoricalDistribution, FloatDistribution
from optuna.storages.journal import JournalFileBackend, JournalStorage
from optuna.trial import TrialState

from thesis_sumo import evaluate
from thesis_sumo.config import REPO_ROOT, load_experiment, load_site
from thesis_sumo.rules.schema import TRACI_RULE_PARAMS, Bound, load_bounds
from thesis_sumo.rules.validator import SEEK_OPTIONS, narrowest_lane, distribution_of, validate

SHARE_EPS = 1e-3
N_STARTUP_TRIALS = 4   # R44: 12 trials per campaign; Optuna's default 10 would be random search


@dataclass(frozen=True)
class Param:
    """One search dimension: float in [low, high], or one of `choices`."""

    name: str
    low: float = 0.0
    high: float = 1.0
    choices: tuple | None = None

    @property
    def distribution(self):
        return CategoricalDistribution(self.choices) if self.choices else FloatDistribution(self.low, self.high)


def _stick(us: list[float], total: float = 1.0) -> list[float]:
    """k - 1 draws in [0, 1] -> k parts summing to `total`, flat Dirichlet prior for uniform draws."""
    k, rest, out = len(us) + 1, total, []
    for j, u in enumerate(us):
        part = rest * (1.0 - (1.0 - u) ** (1.0 / (k - 1 - j)))
        out.append(part)
        rest -= part
    return out + [max(rest, 0.0)]


def _distributions(structure: dict) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for a in structure["driver_archetypes"]:
        out.setdefault(distribution_of(a), []).append(a)
    return out


def search_space(structure_spec: dict, bounds: dict[str, Bound], *, lane_width_m: float | None = None) -> list[Param]:
    """The dimensions Optuna samples for this structure (module doc, R20)."""
    out = []
    for a in structure_spec["driver_archetypes"]:
        vc, params = a["base_vclass"], a["params"]
        if "lcPushy" in params and "lcPushyGap" in params:
            raise ValueError(f"structure archetype {a['id']}: lcPushy and lcPushyGap both declared (validator logic)")
        for name in params:
            b = bounds[name]
            if b.fixed:
                continue
            if b.values is not None:
                out.append(Param(f"arch.{a['id']}.{name}", choices=b.values))
            elif name == "lcPushyGap":
                out.append(Param(f"arch.{a['id']}.lcPushyGap_frac"))
            else:
                r = b.for_vclass(vc)
                hi = min(r.max, lane_width_m) if name == "minGapLat" and lane_width_m is not None else r.max
                out.append(Param(f"arch.{a['id']}.{name}", r.min, hi))
    for i, rule in enumerate(structure_spec["traci_rules"]):
        rt, params, ranges = rule["rule_type"], rule["params"], TRACI_RULE_PARAMS[rule["rule_type"]]
        pre = f"rule.{i}.{rt}"
        opts = [o for o in SEEK_OPTIONS if f"p_{o}" in params] if rt == "queue_space_seeking" else []
        for name in params:
            if rt == "swarm_red_running" and name == "p_max" and "p0" in params:
                out.append(Param(f"{pre}.p_max_frac"))
            elif name in {f"p_{o}" for o in opts}:
                continue
            else:
                out.append(Param(f"{pre}.{name}", ranges[name].min, ranges[name].max))
        if opts:
            out.append(Param(f"{pre}.p_total"))
            out += [Param(f"{pre}.split_{o}") for o in opts[:-1]]
    for dist, archs in _distributions(structure_spec).items():
        out += [Param(f"share.{dist}.{a['id']}", SHARE_EPS, 1.0 - SHARE_EPS) for a in archs[:-1]]
    return out


def build_spec(structure_spec: dict, params: dict, *, spec_id: str = "optuna", provenance: dict | None = None,
               bounds: dict[str, Bound] | None = None) -> dict:
    """`structure_spec` with the sampled values of `params` (names of `search_space`), source optuna."""
    bounds = bounds if bounds is not None else load_bounds()
    spec = copy.deepcopy(structure_spec)
    sid = structure_spec.get("spec_id", "?")
    for a in spec["driver_archetypes"]:
        pre = f"arch.{a['id']}."
        for name in a["params"]:
            if pre + name in params:
                a["params"][name] = params[pre + name]
        if pre + "lcPushyGap_frac" in params:
            lat = a["params"].get("minGapLat", bounds["minGapLat"].for_vclass(a["base_vclass"]).default)
            a["params"]["lcPushyGap"] = params[pre + "lcPushyGap_frac"] * lat
    for i, rule in enumerate(spec["traci_rules"]):
        pre, p = f"rule.{i}.{rule['rule_type']}.", rule["params"]
        for name in p:
            if pre + name in params:
                p[name] = params[pre + name]
        if pre + "p_max_frac" in params:
            p["p_max"] = p["p0"] + params[pre + "p_max_frac"] * (1.0 - p["p0"])
        if pre + "p_total" in params:
            opts = [o for o in SEEK_OPTIONS if f"p_{o}" in p]
            parts = _stick([params[f"{pre}split_{o}"] for o in opts[:-1]], params[pre + "p_total"])
            p.update({f"p_{o}": v for o, v in zip(opts, parts)})
    for dist, archs in _distributions(spec).items():
        if len(archs) > 1:
            for a, s in zip(archs, _stick([params[f"share.{dist}.{a['id']}"] for a in archs[:-1]])):
                a["share"] = s
    spec.update(spec_id=spec_id, source="optuna", provenance=provenance or {},
                description=f"Optuna parameter values in the structure of {sid} (PLAN 7.1); archetype and rule "
                            f"rationales are inherited from {sid} and describe its structure, not these values.")
    return spec


@dataclass
class OptunaResult:
    campaign: str
    results: list[evaluate.EvalResult]            # every finished trial with an EvalResult (valid or not)
    best: evaluate.EvalResult | None
    best_spec: dict | None
    n_trials: int
    n_invalid: int
    runs_used: int
    stop_reason: str
    convergence: list[dict] = field(default_factory=list)


def b0_lane_collisions_per_hour(runs_dir: Path | None = None, days: list[str] | None = None) -> float:
    """Mean lane collisions per hour of the B0 runs (R28 source of the R10 cap): every
    <runs_dir>/B0__<day>/seed_*/manifest.json of the calibration days."""
    runs_dir = Path(runs_dir) if runs_dir is not None else REPO_ROOT / "experiments" / "runs"
    days = days or load_experiment()["data_split"]["calibration_days"]
    rates = []
    for day in days:
        for mp in sorted((runs_dir / f"B0__{day}").glob("seed_*/manifest.json")):
            m = json.loads(mp.read_text(encoding="utf-8"))
            hours = (float(m["config"]["sim"]["end_s"]) - float(m["config"]["sim"]["begin_s"])) / 3600.0
            rates.append(m["n_collisions_lane"] / hours)
    if not rates:
        raise FileNotFoundError(f"no B0 manifests for {days} under {runs_dir}")
    return sum(rates) / len(rates)


def _structure_hash(structure: dict) -> str:
    return hashlib.sha256(json.dumps(structure, sort_keys=True).encode()).hexdigest()[:16]


def _spec_id(campaign: str, number: int) -> str:
    return f"{campaign}_t{number:03d}"


def run_optuna(structure: dict, campaign: str, budget_runs: int, seeds: list[int], days: list[str] | None = None, *,
               sampler_seed: int = 0, nproc: int = 1, site_path: Path | None = None, max_trials: int | None = None,
               sim_end_s: float | None = None, b0_lane_collisions_per_hour: float | None = None) -> OptunaResult:
    """TPE search in `structure` until the next trial cannot be afforded or `max_trials` (default `budget_runs`:
    every valid trial costs >= 1 run, so this only bounds a stream of invalid trials) trials exist."""
    days = list(days) if days else list(load_experiment()["data_split"]["calibration_days"])
    seeds = [int(s) for s in seeds]
    site = load_site(site_path)
    bounds = load_bounds()
    issues = validate(structure, site, bounds)
    if issues:
        raise ValueError(f"structure {structure.get('spec_id')!r} is not a valid spec: {issues[:3]}")
    space = search_space(structure, bounds, lane_width_m=narrowest_lane(site)[0])
    dists = {p.name: p.distribution for p in space}
    cost = len(days) * len(seeds)
    max_trials = budget_runs if max_trials is None else max_trials
    root = evaluate.CAMPAIGNS_DIR / campaign
    res_dir = root / "optuna_results"
    res_dir.mkdir(parents=True, exist_ok=True)
    budget = evaluate.RunBudget(budget_runs, campaign)

    study = optuna.create_study(study_name=campaign, storage=JournalStorage(JournalFileBackend(
        str(root / "study.journal"))), direction="minimize", load_if_exists=True)
    seed = sampler_seed + len(study.trials)   # a resumed study must not replay the start-up draws
    study.sampler = optuna.samplers.TPESampler(seed=seed, n_startup_trials=N_STARTUP_TRIALS)
    lock = {"days": days, "seeds": seeds, "structure": structure.get("spec_id"),
            "structure_sha": _structure_hash(structure), "sampler_seed": sampler_seed,
            "sampler": "TPESampler", "n_startup_trials": N_STARTUP_TRIALS,
            # same objective across a resume: simulated window and site file (as llm/loop.py locks them)
            "sim_end_s": sim_end_s, "site": str(Path(site_path).resolve()) if site_path is not None else None}
    for k, v in lock.items():
        if k in study.user_attrs and study.user_attrs[k] != v:
            raise ValueError(f"campaign {campaign!r} was started with {k} = {study.user_attrs[k]!r}, not {v!r}")
        study.set_user_attr(k, v)

    def pkl(number: int) -> Path:
        return res_dir / f"{_spec_id(campaign, number)}.pkl"

    for t in study.get_trials(states=(TrialState.RUNNING,)):   # interrupted run: recover or fail, never re-charge
        r = pickle.loads(pkl(t.number).read_bytes()) if pkl(t.number).is_file() else None
        if r is not None and r.valid:
            study.tell(t.number, r.S)
        else:
            study.tell(t.number, state=TrialState.FAIL)

    while True:
        if budget.remaining < cost:
            stop = "budget"
            break
        if len(study.trials) >= max_trials:
            stop = "max_trials"
            break
        trial = study.ask(dists)
        sid = _spec_id(campaign, trial.number)
        spec = build_spec(structure, trial.params, spec_id=sid, bounds=bounds, provenance={
            # the schema's provenance keys are LLM-shaped: sampler data packed into model / reference
            "model": "optuna-tpe", "prompt_version": None, "iteration": trial.number, "sample_idx": 0,
            "reference": f"sampler_seed={seed};trial={trial.number};n_startup={N_STARTUP_TRIALS}"})
        try:
            r = evaluate.evaluate_spec(spec, days, seeds, budget, campaign=campaign, site_path=site_path,
                                       nproc=nproc, sim_end_s=sim_end_s)
        except evaluate.BudgetExhausted:
            study.tell(trial, state=TrialState.FAIL)
            stop = "budget"
            break
        except Exception:
            study.tell(trial, state=TrialState.FAIL)
            raise
        pkl(trial.number).write_bytes(pickle.dumps(r))
        trial.set_user_attr("valid", r.valid)
        if r.valid:
            study.tell(trial, r.S)
        else:
            trial.set_user_attr("issues", [i["code"] for i in r.issues])
            study.tell(trial, state=TrialState.FAIL)

    results, conv, used, best_s = [], [], 0, math.inf
    for t in sorted(study.trials, key=lambda t: t.number):
        sid = _spec_id(campaign, t.number)
        r = pickle.loads(pkl(t.number).read_bytes()) if pkl(t.number).is_file() else None
        if r is None and t.state == TrialState.COMPLETE:   # .pkl is git-ignored: never rank without it
            raise FileNotFoundError(f"{pkl(t.number)} missing for finished trial {sid}; copy optuna_results/ "
                                    f"from the machine that ran the campaign")
        if r is not None:
            results.append(r)
        # evaluate writes compiled/<id>/spec.json only once the runs are charged
        runs = cost if (root / "compiled" / sid / "spec.json").is_file() else 0
        used += runs
        if r is not None and r.valid and not math.isnan(r.S):
            best_s = min(best_s, r.S)
        conv.append({"trial": t.number, "spec_id": sid, "state": t.state.name,
                     "valid": None if r is None else r.valid, "runs": runs, "runs_used": used,
                     "S": "" if r is None else r.S, "best_S": "" if math.isinf(best_s) else best_s})
    with (root / "convergence.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["trial", "spec_id", "state", "valid", "runs", "runs_used", "S", "best_S"])
        w.writeheader()
        w.writerows(conv)

    best = evaluate.select_best(results, b0_lane_collisions_per_hour)
    best_spec = None if best is None else \
        json.loads((root / "compiled" / best.spec_id / "spec.json").read_text(encoding="utf-8"))
    return OptunaResult(campaign, results, best, best_spec, len(study.trials),
                        sum(1 for r in results if not r.valid), used, stop, conv)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m thesis_sumo.baselines.optuna_search",
                                 description=__doc__.split("\n\n")[0])
    ap.add_argument("--structure", type=Path, required=True, help="spec whose structure is kept (rules/specs/*.json)")
    ap.add_argument("--campaign", required=True, help="experiments/campaigns/<campaign>/ (resumed if it exists)")
    ap.add_argument("--budget", type=int, required=True, help="SUMO runs (same as the LLM loop)")
    ap.add_argument("--seeds", type=int, nargs="+", default=[1], help="default [1] (R44)")
    ap.add_argument("--days", nargs="+", default=None,
                    help="default: experiment.yaml data_split.calibration_days (validation days are refused)")
    ap.add_argument("--nproc", type=int, default=1)
    ap.add_argument("--sampler-seed", type=int, default=0)
    ap.add_argument("--site", type=Path, default=None, help="site file (default: the measured config/site.yaml)")
    ap.add_argument("--end", type=float, default=None, help="sim end in s (default: experiment.yaml calib_end_s)")
    ap.add_argument("--b0-lane-collisions", type=float, required=True,
                    help="B0 mean lane collisions/h for the R10 cap of select_best: b0_lane_collisions_per_hour() of "
                         "the B0 runs on the current net (1.333 was the pre-2026-10-28 net)")
    ap.add_argument("--write-best", type=Path, default=None,
                    help="write the best spec here (spec_id = file stem), e.g. rules/specs/B2_best.json")
    args = ap.parse_args(argv)
    structure = json.loads(args.structure.read_text(encoding="utf-8"))
    res = run_optuna(structure, args.campaign, args.budget, args.seeds, args.days, sampler_seed=args.sampler_seed,
                     nproc=args.nproc, site_path=args.site, sim_end_s=args.end,
                     b0_lane_collisions_per_hour=args.b0_lane_collisions)
    print(f"campaign {res.campaign}: {res.n_trials} trials ({res.n_invalid} invalid), {res.runs_used} SUMO runs, "
          f"stopped on {res.stop_reason}")
    if res.best is None:
        print("no valid trial")
        return 1
    print(f"best {res.best.spec_id}: S {res.best.S:.4f}, eligibility {res.best.eligibility}")
    if args.write_best:
        spec = res.best_spec | {"spec_id": args.write_best.stem}
        spec["description"] += f" Best trial {res.best.spec_id} of campaign {res.campaign} (evaluate.select_best)."
        args.write_best.write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {args.write_best}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
