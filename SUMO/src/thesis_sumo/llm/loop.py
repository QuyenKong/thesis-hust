"""LLM loop (PLAN Phase 6.3-6.4, 7.2; plan Task 13): per iteration `n_samples` specs from the LLM, each validated,
compiled, run and scored by `evaluate.evaluate_spec` against one campaign `RunBudget`; feedback on every previous
iteration goes into the next prompt; best spec by `evaluate.select_best` (R10/R32/R42).

    .venv/bin/python -m thesis_sumo.llm.loop --campaign P1 --mode params_only --base rules/specs/B1_manual.json \
        --budget 36 --iters 3 --nproc 9 --site config/site.proxy.yaml --b0-lane-collisions 1.333 \
        [--write-best rules/specs/P1_best.json]
    .venv/bin/python -m thesis_sumo.llm.loop --campaign P2 --mode full --budget 36 --iters 3 --nproc 9 ...
    .venv/bin/python -m thesis_sumo.llm.loop pending --campaign P1      # unanswered stand-in request files

Modes (PLAN 7.2): params_only = P1, the structure of `--base` (B1) is locked (client + validator structure_locked);
full = P2, the LLM writes structure and values. Decision: full takes NO base spec (not even as an example), so P2's
structure comes from the context alone and E2 (B2 vs H vs P2) is not anchored on B1; `--base` with full is refused.

Budget (R44): one spec = len(days) x len(seeds) runs (default calibration days PROXY_D1-D3 x seed 1 = 3), so 36 runs
= 3 iterations x 4 samples. An iteration starts only if one more spec is affordable; within an iteration only as many
specs are evaluated as the remaining budget covers (the rest are `unaffordable`, 0 runs). A spec that never validates
(client gives up after max_attempts, or evaluate rejects it) is `invalid`, 0 runs. A network error of the openai
backend skips the sample (`network_error`, 0 runs).
R45 (controller): the loop stops when the budget is spent, like Optuna (PLAN 6.3, same budget per method). After the
planned `n_iter` iterations, further iterations (same n_samples, the last possibly part `unaffordable`) run while one
more spec is affordable, capped at `max_iter` (5). stop_reason: `budget` (fewer runs left than one spec costs) or
`max_iter` (cap reached with budget left). Every iter_{i}.json says whether it was planned or an R45 extra and why;
loop.json `status` has the number of iterations and the stop reason.

Validity, two definitions:
- per attempt: every LLM answer the client validated (experiments/llm_logs/<campaign>/validity_log.csv, one row per
  attempt) = the thesis's "valid-spec rate of LLM outputs"; copied into loop.json `status.validity.per_attempt_rate`.
- per sample: final status of each requested spec after up to max_attempts tries. answered = evaluated + invalid +
  lost + unaffordable (network_error: no answer); valid = answered - invalid (unaffordable specs passed the client
  validator but were never compiled). Counts per iteration in iter_{i}.json `validity`, cumulative in loop.json.

A rerun after a crash scans the iteration's pickles / lost samples first; an iteration with started samples is
completed even when the budget is spent (its unstarted samples become `unaffordable`, the LLM is not asked). The runs
accounted for by the samples must equal budget.json `used`; otherwise loop.json `status.error` is written and
RuntimeError raised.

Resume (state under experiments/campaigns/<campaign>/loop/; the LLM logs stay in experiments/llm_logs/<campaign>/):
- `loop.json` locks mode, base spec, days, seeds, n_samples, n_iter/max_iter, budget, sim end, resolved site path, B0
  lane-collision cap and the LLM setup; a resume with other values raises. Its `status` key is rewritten each run.
  Each sample's EvalResult is pickled (tmp + replace) as soon as its evaluate_spec returns. `results/<spec_id>.pkl` = the EvalResult of every evaluated or invalid sample, loaded instead of
  re-evaluating (evaluate refuses repeated ids and never refunds). A sample whose compiled spec.json exists without a
  pickle was charged but interrupted: `lost`, its runs stay charged, never re-run.
- `iter_{i}.json` is written once every sample of iteration i has a final status; a finished iteration is never
  regenerated. Prompts are rebuilt deterministically from the pickles, so the client replays logged attempts.
- File backend: all samples of an iteration are generated first; if any answer is missing (also a retry attempt),
  every pending request is collected and `LoopPending` is raised (CLI exit 3, request paths printed). Nothing of
  that iteration is evaluated before all of its answers exist.
- `specs/<spec_id>.json`: copy of every valid spec; `convergence.csv`: SUMO runs used vs best S (min S over valid
  specs, as the Optuna baseline's convergence.csv).

Prompt: [system, context (calibration targets of `days`, mode, base for params_only)] + for every previous iteration
one user message with its specs as a compact JSON block and `feedback.build_feedback` of its results (validator
issues included); every added text passes `assert_no_day_data`.

Specs are evaluated concurrently (threads, each evaluate_spec using a spawn pool of min(nproc, runs per spec)) only
when that pool has >= 2 workers: with 1 worker evaluate runs SUMO in-process (libsumo is a process singleton).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import pickle
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

from thesis_sumo import evaluate
from thesis_sumo.config import load_experiment, load_site
from thesis_sumo.llm import client as llm_client
from thesis_sumo.llm.client import HARNESS_KEYS, LLMClient, PendingResponse, llm_config, llm_schema
from thesis_sumo.llm.feedback import (assert_no_day_data, build_context, build_feedback, calibration_targets,
                                      system_prompt)
from thesis_sumo.rules.schema import load_bounds
from thesis_sumo.rules.validator import ValidityLog, validate

try:
    import openai
    NETWORK_ERRORS: tuple = (openai.APITimeoutError, openai.APIConnectionError)
except ImportError:  # pragma: no cover - openai is a project dependency
    NETWORK_ERRORS = ()

BEST_FILES = {"params_only": "P1_best", "full": "P2_best"}
LLM_RECORD_KEYS = ("profile", "runtime", "server", "model", "quant", "temperature", "seed", "prompt_version",
                   "max_attempts")


class LoopPending(Exception):
    """Stand-in answers missing; write them to `paths` (one JSON per request) and run the loop again."""

    def __init__(self, campaign: str, iteration: int, paths: list[Path]):
        self.campaign, self.iteration, self.paths = campaign, iteration, [Path(p) for p in paths]
        super().__init__(f"campaign {campaign!r} iteration {iteration}: {len(paths)} LLM response(s) pending")


@dataclass
class LoopResult:
    campaign: str
    mode: str
    results: list[evaluate.EvalResult]     # every evaluated or invalid sample, in iteration/sample order
    best: evaluate.EvalResult | None
    best_spec: dict | None
    iterations: list[dict]                 # the iter_{i}.json documents
    runs_used: int
    stop_reason: str                       # budget | max_iter
    validity: dict = field(default_factory=dict)   # per-sample counts (module doc) + per_attempt_rate
    convergence: list[dict] = field(default_factory=list)

    @property
    def validity_rate(self) -> float:
        return self.validity["valid_rate_per_sample"] if self.validity.get("n_answered") else math.nan


STATUSES = ("evaluated", "invalid", "lost", "network_error", "unaffordable")


def _validity(statuses: list[str]) -> dict:
    c = {k: statuses.count(k) for k in STATUSES}
    answered = len(statuses) - c["network_error"]
    valid = answered - c["invalid"]
    return {"n_samples": len(statuses), **{f"n_{k}": v for k, v in c.items()}, "n_answered": answered,
            "n_valid": valid, "valid_rate_per_sample": valid / answered if answered else None}


def _sha(doc) -> str:
    return hashlib.sha256(json.dumps(doc, sort_keys=True).encode()).hexdigest()[:16]


def _write_json(path: Path, doc) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(doc, indent=1, default=str), encoding="utf-8")
    tmp.replace(path)


def _write_pickle(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_bytes(pickle.dumps(obj))
    tmp.replace(path)


def _answer(spec: dict) -> dict:
    """The spec as the LLM wrote it (harness fields dropped), keyed by its id in the prompt."""
    return {k: v for k, v in spec.items() if k not in HARNESS_KEYS}


def _history_message(iteration: int, specs: dict[str, dict], results: list, prompt_version: str) -> dict:
    block = json.dumps({sid: _answer(s) for sid, s in specs.items()}, separators=(",", ":"), ensure_ascii=False)
    text = (f"# Iteration {iteration}: your specs\n\n```json\n{block}\n```\n\n"
            + build_feedback(results, prompt_version=prompt_version))
    return {"role": "user", "content": assert_no_day_data(text)}


def pending_requests(campaign: str, log_root: Path | None = None) -> list[Path]:
    """Request files of the file backend with no response file yet."""
    d = Path(log_root if log_root is not None else llm_client.LOGS_DIR) / campaign
    return sorted(p for p in (d / "requests").glob("*.json") if not (d / "responses" / p.name).is_file())


def run_loop(campaign: str, mode: str, base_spec: dict | None, *, b0_lane_collisions_per_hour: float,
             n_iter: int = 3, max_iter: int = 5, n_samples: int | None = None, budget_runs: int = 36,
             days: list[str] | None = None, seeds: list[int] = (1,), nproc: int = 1, site_path: Path | None = None,
             sim_end_s: float | None = None, prompt_version: str | None = None) -> LoopResult:
    """Run (or resume) the loop of `campaign`: `n_iter` planned iterations, then R45 extras up to `max_iter` while
    the budget covers a spec (module doc). `b0_lane_collisions_per_hour` (R10 cap of select_best) is required, as in
    the Optuna baseline. `prompt_version` overrides llm.yaml's (locked per campaign). Raises LoopPending."""
    if mode not in BEST_FILES:
        raise ValueError(f"mode must be one of {tuple(BEST_FILES)}, got {mode!r}")
    if mode == "params_only" and base_spec is None:
        raise ValueError("params_only needs the base spec whose structure is locked (--base)")
    if mode == "full" and base_spec is not None:
        raise ValueError("full (P2) takes no base spec: the LLM writes the structure from the context alone")
    if b0_lane_collisions_per_hour is None or not math.isfinite(float(b0_lane_collisions_per_hour)):
        raise ValueError("b0_lane_collisions_per_hour is required (R10 cap of select_best, same as the Optuna run)")
    if not 1 <= n_iter <= max_iter:
        raise ValueError(f"need 1 <= n_iter ({n_iter}) <= max_iter ({max_iter})")
    exp = load_experiment()
    days = list(days) if days else list(exp["data_split"]["calibration_days"])
    seeds = [int(s) for s in seeds]
    evaluate.check_days(days, exp)
    cfg = llm_config()
    if prompt_version is not None:
        cfg["prompt_version"] = prompt_version
    n_samples = int(n_samples if n_samples is not None else cfg.get("n_samples") or 0)
    if n_samples < 1:
        raise ValueError(f"llm.yaml {cfg.get('profile')}.n_samples is null (TODO_DECIDE); no default")
    site, bounds = load_site(site_path), load_bounds()
    if base_spec is not None and (issues := validate(base_spec, site, bounds)):
        raise ValueError(f"base spec {base_spec.get('spec_id')!r} is not valid: {issues[:3]}")
    llm = LLMClient(cfg, site=site, campaign=campaign)
    pv = cfg["prompt_version"]
    cost = len(days) * len(seeds)
    root = evaluate.CAMPAIGNS_DIR / campaign
    loop_dir, spec_dir, res_dir = root / "loop", root / "specs", root / "loop" / "results"
    budget = evaluate.RunBudget(budget_runs, campaign)

    llm_record = {k: cfg.get(k) for k in LLM_RECORD_KEYS}
    lock = {"mode": mode, "base_spec": None if base_spec is None else base_spec.get("spec_id"),
            "base_sha": None if base_spec is None else _sha(base_spec), "days": days, "seeds": seeds,
            "n_samples": n_samples, "n_iter": n_iter, "max_iter": max_iter, "budget_runs": budget_runs,
            "sim_end_s": sim_end_s, "site": str(Path(site_path).resolve()) if site_path is not None else None,
            "b0_lane_collisions_per_hour": float(b0_lane_collisions_per_hour), "llm": llm_record}
    lock_path = loop_dir / "loop.json"
    if lock_path.is_file():
        saved = json.loads(lock_path.read_text(encoding="utf-8"))
        diff = {k: (saved.get(k), v) for k, v in lock.items() if saved.get(k) != v}
        if diff:
            raise ValueError(f"campaign {campaign!r} was started with other settings {diff} (saved, now)")
    else:
        _write_json(lock_path, lock)
    vlog = root / "validity_log.csv"   # header written once here, not by parallel first appends in evaluate
    if not vlog.is_file() or vlog.stat().st_size == 0:
        vlog.parent.mkdir(parents=True, exist_ok=True)
        with vlog.open("w", encoding="utf-8", newline="") as f:
            csv.writer(f).writerow(ValidityLog.COLUMNS)

    messages = [{"role": "system", "content": system_prompt(pv)},
                {"role": "user", "content": build_context(
                    mode, base_spec, site, bounds, calibration_targets(days, exp=exp, site=site),
                    schema=llm_schema(mode, base_spec, bounds), prompt_version=pv, exp=exp)}]
    all_results: list[evaluate.EvalResult] = []
    iterations, conv, best_s, stop = [], [], math.inf, "max_iter"
    all_status: list[str] = []

    for it in range(1, max_iter + 1):
        iter_path = loop_dir / f"iter_{it}.json"
        sids = [f"{campaign}_it{it:02d}_s{j:02d}" for j in range(n_samples)]
        done = iter_path.is_file()
        prev_used = conv[-1]["runs_used"] if conv else 0
        reason = "planned" if it <= n_iter else \
            f"R45 extra: {budget.total - prev_used} of {budget.total} runs left after {it - 1} iterations"

        # status per sample: evaluated | invalid | lost | network_error | unaffordable. Scan BEFORE the budget check:
        # evaluate charges before simulating, so a crash in the last affordable spec leaves remaining < cost
        status, results, specs = {}, {}, {}
        for j, sid in enumerate(sids):
            pkl = res_dir / f"{sid}.pkl"
            if pkl.is_file():
                results[sid] = pickle.loads(pkl.read_bytes())
                status[sid] = "evaluated" if results[sid].valid else "invalid"
                if (spec_dir / f"{sid}.json").is_file():
                    specs[sid] = json.loads((spec_dir / f"{sid}.json").read_text(encoding="utf-8"))
            elif (root / "compiled" / sid / "spec.json").is_file():   # charged, interrupted before the pickle
                status[sid] = "lost"
                specs[sid] = json.loads((root / "compiled" / sid / "spec.json").read_text(encoding="utf-8"))
        starved = not done and budget.remaining < cost
        if starved and not status:   # nothing of this iteration was started
            stop = "budget"
            break
        if done:   # finished iteration: no LLM call, no evaluation
            saved = json.loads(iter_path.read_text(encoding="utf-8"))
            status.update({s["spec_id"]: s["status"] for s in saved["samples"] if s["spec_id"] not in status})
        elif starved:   # started, then interrupted with the budget spent: the rest is never asked
            status.update({sid: "unaffordable" for sid in sids if sid not in status})
        else:
            pending, record = [], {}
            for j, sid in enumerate(sids):
                if sid in status:
                    continue
                try:
                    spec, record[sid] = llm.generate_spec(messages, mode, base_spec, iteration=it, sample_idx=j)
                except PendingResponse as e:
                    pending.append(e.path)
                    continue
                except NETWORK_ERRORS as e:
                    print(f"{sid}: LLM network error, sample skipped (0 runs): {e!r}", file=sys.stderr)
                    status[sid] = "network_error"
                    continue
                if spec is None:
                    issues = record[sid]["attempts"][-1]["issues"]
                    results[sid] = evaluate.EvalResult(sid, campaign, False, issues)
                    status[sid] = "invalid"
                    _write_pickle(res_dir / f"{sid}.pkl", results[sid])
                else:
                    specs[sid] = spec
                    _write_json(spec_dir / f"{sid}.json", spec)
            if pending:
                raise LoopPending(campaign, it, pending)

            todo = [sid for sid in sids if sid not in status]
            affordable = max(0, budget.remaining // cost)
            for sid in todo[affordable:]:
                status[sid] = "unaffordable"
            todo = todo[:affordable]
            per_spec = min(nproc, cost)
            workers = max(1, nproc // cost) if per_spec > 1 else 1

            def _eval(sid):
                try:
                    r = evaluate.evaluate_spec(specs[sid], days, seeds, budget, campaign=campaign,
                                               site_path=site_path, nproc=per_spec, sim_end_s=sim_end_s)
                except evaluate.BudgetExhausted:
                    return sid, None
                except Exception as e:   # keep the other specs' results; re-raised below
                    return sid, e
                _write_pickle(res_dir / f"{sid}.pkl", r)   # now: an interruption must not lose a charged result
                return sid, r

            with ThreadPoolExecutor(max_workers=workers) as pool:
                outcomes = list(pool.map(_eval, todo))
            for sid, r in outcomes:
                if r is None:
                    status[sid] = "unaffordable"
                elif isinstance(r, evaluate.EvalResult):
                    results[sid], status[sid] = r, ("evaluated" if r.valid else "invalid")
            errors = [r for _, r in outcomes if isinstance(r, Exception)]
            if errors:
                raise errors[0]

        it_results = [results[s] for s in sids if s in results]
        all_results += it_results
        best = evaluate.select_best(all_results, b0_lane_collisions_per_hour)
        rows = []
        for sid in sids:
            r, st = results.get(sid), status[sid]
            runs = cost if st in ("evaluated", "lost") else 0
            if r is not None and r.valid and not math.isnan(r.S):
                best_s = min(best_s, r.S)
            used = (conv[-1]["runs_used"] if conv else 0) + runs
            conv.append({"iteration": it, "spec_id": sid, "status": st, "runs": runs, "runs_used": used,
                         "S": "" if r is None else r.S, "best_S": "" if math.isinf(best_s) else best_s})
            rows.append({"spec_id": sid, "status": st, "runs": runs,
                         "row": None if r is None else r.to_row(),
                         "S": None if r is None else r.S, "eligibility": None if r is None else r.eligibility,
                         "rank_key": None if r is None else list(r.rank_key)})
        all_status += [status[s] for s in sids]
        summary = {"campaign": campaign, "iteration": it, "planned": it <= n_iter, "reason": reason, "mode": mode,
                   "spec_ids": sids, "samples": rows, "validity": _validity([status[s] for s in sids]),
                   "best_so_far": None if best is None else {"spec_id": best.spec_id, "S": best.S,
                                                             "eligibility": best.eligibility},
                   "runs_used": conv[-1]["runs_used"], "budget": {"total": budget.total, "used": budget.used},
                   "llm": llm_record, "days": days, "seeds": seeds}
        if done:
            summary = saved
        else:
            _write_json(iter_path, summary)
        iterations.append(summary)
        if any(status[s] == "unaffordable" for s in sids):
            stop = "budget"
            break
        messages = messages + [_history_message(it, {s: specs[s] for s in sids if s in specs},
                                                it_results, pv)]

    if stop == "max_iter" and budget.remaining < cost:   # cap reached exactly as the budget ran out
        stop = "budget"
    with (loop_dir / "convergence.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["iteration", "spec_id", "status", "runs", "runs_used", "S", "best_S"])
        w.writeheader()
        w.writerows(conv)
    best = evaluate.select_best(all_results, b0_lane_collisions_per_hour)
    best_spec = None if best is None else json.loads((spec_dir / f"{best.spec_id}.json").read_text(encoding="utf-8"))
    runs_used = conv[-1]["runs_used"] if conv else 0
    validity = {**_validity(all_status), "per_attempt_rate": llm.validity.valid_rate()}
    status_doc = {
        "n_iterations": len(iterations), "n_planned": n_iter, "n_extra_r45": max(0, len(iterations) - n_iter),
        "stop_reason": stop, "runs_used": runs_used, "budget_used": budget.used,
        "budget_remaining": budget.remaining, "validity": validity,
        "best": None if best is None else {"spec_id": best.spec_id, "S": best.S, "eligibility": best.eligibility}}
    if runs_used != budget.used:   # charged runs not explained by results/lost samples: never report it as fine
        status_doc["error"] = (f"runs accounted for by samples ({runs_used}) != budget.json used ({budget.used}); "
                               f"inspect {root} before using these results")
        _write_json(lock_path, {**lock, "status": status_doc})
        raise RuntimeError(f"campaign {campaign!r}: {status_doc['error']}")
    _write_json(lock_path, {**lock, "status": status_doc})
    return LoopResult(campaign, mode, all_results, best, best_spec, iterations, runs_used, stop, validity, conv)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["pending"]:
        ap = argparse.ArgumentParser(prog="python -m thesis_sumo.llm.loop pending",
                                     description="list unanswered stand-in request files of a campaign")
        ap.add_argument("--campaign", required=True)
        args = ap.parse_args(argv[1:])
        for p in pending_requests(args.campaign):
            print(p)
        return 0
    ap = argparse.ArgumentParser(prog="python -m thesis_sumo.llm.loop", description=__doc__.split("\n\n")[0])
    ap.add_argument("--campaign", required=True, help="experiments/campaigns/<campaign>/ (resumed if it exists)")
    ap.add_argument("--mode", required=True, choices=tuple(BEST_FILES))
    ap.add_argument("--base", type=Path, default=None, help="locked structure for params_only (refused for full)")
    ap.add_argument("--budget", type=int, required=True, help="SUMO runs (R44: 36)")
    ap.add_argument("--iters", type=int, default=3, help="planned iterations (R45: extras while budget is left)")
    ap.add_argument("--max-iters", type=int, default=5, help="R45 cap on iterations")
    ap.add_argument("--samples", type=int, default=None, help="specs per iteration (default llm.yaml n_samples)")
    ap.add_argument("--days", nargs="+", default=None, help="default: experiment.yaml calibration_days")
    ap.add_argument("--seeds", type=int, nargs="+", default=[1], help="R44: seed 1")
    ap.add_argument("--nproc", type=int, default=1)
    ap.add_argument("--site", type=Path, default=None, help="site file (default: the measured config/site.yaml)")
    ap.add_argument("--end", type=float, default=None, help="sim end in s (default: experiment.yaml calib_end_s)")
    ap.add_argument("--b0-lane-collisions", type=float, required=True,
                    help="B0 mean lane collisions/h for the R10 cap of select_best (same value as the Optuna run)")
    ap.add_argument("--prompt-version", default=None,
                    help="prompts/<version>/ (default: llm.yaml prompt_version); locked per campaign")
    ap.add_argument("--write-best", type=Path, default=None,
                    help=f"write the best spec here (spec_id = file stem), e.g. rules/specs/{BEST_FILES['params_only']}"
                         f".json")
    args = ap.parse_args(argv)
    base = json.loads(args.base.read_text(encoding="utf-8")) if args.base else None
    try:
        res = run_loop(args.campaign, args.mode, base, n_iter=args.iters, max_iter=args.max_iters,
                       n_samples=args.samples,
                       budget_runs=args.budget, days=args.days, seeds=args.seeds, nproc=args.nproc,
                       site_path=args.site, sim_end_s=args.end, b0_lane_collisions_per_hour=args.b0_lane_collisions,
                       prompt_version=args.prompt_version)
    except LoopPending as e:
        print(f"{e}; answer each request file with the response file next to it, then rerun:")
        for p in e.paths:
            print(f"{p.parent.parent / 'requests' / p.name} -> {p}")
        return 3
    v = res.validity
    print(f"campaign {res.campaign} ({res.mode}): {len(res.iterations)} iterations, {v['n_valid']}/{v['n_answered']}"
          f" valid samples (per attempt {v['per_attempt_rate']}), {res.runs_used} SUMO runs, stopped on "
          f"{res.stop_reason}")
    if res.best is None:
        print("no valid spec")
        return 1
    print(f"best {res.best.spec_id}: S {res.best.S:.4f}, eligibility {res.best.eligibility}")
    if args.write_best:
        spec = res.best_spec | {"spec_id": args.write_best.stem}
        spec["description"] = (spec.get("description") or "") + \
            f" Best spec {res.best.spec_id} of LLM campaign {res.campaign} (evaluate.select_best)."
        args.write_best.write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {args.write_best}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
