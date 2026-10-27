"""Shared evaluation of one rule spec + SUMO-run budget (plan Task 11; PLAN Phase 6.3 / 7.1).

Every method (LLM loop P1/P2, Optuna B2/H) scores specs through `evaluate_spec` and pays from a `RunBudget`
counted in SUMO runs (1 spec x 1 day x 1 seed = 1 run). Campaign layout, `experiments/campaigns/<campaign>/`:
`budget.json` (`RunBudget`), `compiled/<spec_id>/` (vtypes + traci_rules + `spec.json`; never
rules/compiled/, so spec ids may repeat across campaigns), `runs/<spec_id>__<day>/seed_XX/`, `validity_log.csv`.

Decisions (rulings in docs/PROGRESS.md):
- Spec ids are unique within a campaign: evaluating an id whose compiled spec.json exists raises (callers assign
  ids, e.g. llm_it{i}_s{j}); runner.run would otherwise replace the earlier runs.
- An invalid spec costs 0 runs; the budget is charged BEFORE running, and a run that crashes is not refunded.
- S is computed over ALL runs of the spec, excluded ones included (R23: M1-M8/R/S are reported for every run,
  "G0 fail" too; R42: on the overloaded proxy net nothing may be eligible, and the R32 fallback still ranks by S).
  Eligibility only decides best-spec selection (`select_best`), never which runs enter S.
- Run eligibility (R10/R28): G0 GEH gate against the run's own observed day AND `runner.is_eligible`. While any
  `experiment.yaml validity.*` threshold is null the run is `unknown` (a G0 failure is still `excluded`).
- A spec is eligible only when every one of its runs is eligible (not a majority).
- Best spec (`select_best`): R10 cap on mean LANE collisions/h <= B0 + 1 (R28); the R32 fallback ignores the cap (R42).
"""

from __future__ import annotations

import json
import math
import multiprocessing
import os
import time
from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from thesis_sumo.config import REPO_ROOT, load_experiment, load_site
from thesis_sumo.metrics import distance, g0_geh
from thesis_sumo.metrics.common import MetricContext, read_tables
from thesis_sumo.net.apply_patches import site_net_name
from thesis_sumo.rules.compiler import InvalidSpecError, compile_spec
from thesis_sumo.rules.validator import ValidityLog
from thesis_sumo.sim import runner

CAMPAIGNS_DIR = REPO_ROOT / "experiments" / "campaigns"
OBSERVED_DIR = REPO_ROOT / "data" / "observed"


class BudgetExhausted(RuntimeError):
    pass


class RunBudget:
    """SUMO-run budget of a campaign, always persisted at CAMPAIGNS_DIR/<campaign>/budget.json as {"total", "used"}
    so a resumed or re-run campaign keeps its count. `used` is read from disk; `consume` re-reads and writes it
    under an exclusive lock file (O_CREAT | O_EXCL, Windows and Linux), so two RunBudget objects or processes on
    the same campaign never overwrite each other. Another `total` for an existing file raises (the budget of a
    campaign never changes silently)."""

    LOCK_TIMEOUT_S = 10.0

    def __init__(self, total: int, campaign: str):
        self.total, self.campaign = int(total), campaign
        self.path = CAMPAIGNS_DIR / campaign / "budget.json"
        self._read()

    def _read(self) -> int:
        if not self.path.is_file():
            return 0
        saved = json.loads(self.path.read_text(encoding="utf-8"))
        if int(saved["total"]) != self.total:
            raise ValueError(f"{self.path}: saved budget total {saved['total']} != requested {self.total}")
        return int(saved["used"])

    @property
    def used(self) -> int:
        return self._read()

    @property
    def remaining(self) -> int:
        return self.total - self.used

    @contextmanager
    def _locked(self):
        lock = self.path.with_suffix(".lock")
        lock.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + self.LOCK_TIMEOUT_S
        while True:
            try:
                fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                break
            except FileExistsError:
                if time.monotonic() > deadline:
                    raise RuntimeError(f"{lock} held for > {self.LOCK_TIMEOUT_S:g} s ({lock.read_text(errors='replace')}"
                                       f"): another process is charging this budget, or a crashed one left a stale "
                                       f"lock; delete the file only if no process of campaign {self.campaign!r} "
                                       f"is running") from None
                time.sleep(0.05)
        try:
            os.write(fd, f"pid {os.getpid()}".encode())
            os.close(fd)
            yield
        finally:
            lock.unlink(missing_ok=True)

    def consume(self, n: int) -> None:
        if n < 0:
            raise ValueError(f"cannot consume {n} runs")
        with self._locked():
            used = self._read()
            if n > self.total - used:
                raise BudgetExhausted(f"campaign {self.campaign!r}: {n} SUMO runs requested, "
                                      f"{self.total - used} of {self.total} left")
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps({"total": self.total, "used": used + n}), encoding="utf-8")
            os.replace(tmp, self.path)


@dataclass
class EvalResult:
    spec_id: str
    campaign: str
    valid: bool
    issues: list = field(default_factory=list)
    report: distance.DistanceReport | None = None
    runs: list[dict] = field(default_factory=list)   # per run: day, seed, run_dir, G0, eligibility, reasons, rates
    interventions_summary: dict = field(default_factory=dict)
    wall_time_s: float = 0.0

    @property
    def S(self) -> float:
        return self.report.S if self.report is not None else math.nan

    @property
    def n_runs(self) -> int:
        return len(self.runs)

    @property
    def eligible_runs(self) -> list[dict]:
        return [r for r in self.runs if r["eligibility"] == "eligible"]

    @property
    def excluded_runs(self) -> list[dict]:
        return [r for r in self.runs if r["eligibility"] == "excluded"]

    @property
    def eligibility(self) -> str:
        """eligible (every run eligible) | excluded (some run excluded, or invalid spec) | unknown."""
        if not self.valid or self.excluded_runs:
            return "excluded"
        return "eligible" if len(self.eligible_runs) == self.n_runs else "unknown"

    @property
    def collisions_per_hour(self) -> float:
        return float(np.mean([r["collisions_per_hour"] for r in self.runs])) if self.runs else math.nan

    @property
    def lane_collisions_per_hour(self) -> float:
        return float(np.mean([r["lane_collisions_per_hour"] for r in self.runs])) if self.runs else math.nan

    @property
    def jam_yield_teleports_per_hour(self) -> float:
        return float(np.mean([r["jam_yield_teleports_per_hour"] for r in self.runs])) if self.runs else math.nan

    @property
    def rank_key(self) -> tuple:
        """Sort key for tables/plots: eligible specs by S, the rest by mean jam+yield teleports/h, then S. NOT the
        best-spec rule: that needs the B0 lane-collision cap, use `select_best`."""
        if not self.valid:
            return (2, math.inf, math.inf)
        if self.eligibility == "eligible":
            return (0, 0.0, self.S)
        return (1, self.jam_yield_teleports_per_hour, self.S)

    def to_row(self) -> dict:
        row = {"campaign": self.campaign, "spec_id": self.spec_id, "valid": self.valid, "n_issues": len(self.issues),
               "n_runs": self.n_runs, "n_eligible": len(self.eligible_runs), "n_excluded": len(self.excluded_runs),
               "eligibility": self.eligibility, "collisions_per_hour": self.collisions_per_hour,
               "lane_collisions_per_hour": self.lane_collisions_per_hour,
               "jam_yield_teleports_per_hour": self.jam_yield_teleports_per_hour, "wall_time_s": self.wall_time_s}
        row.update(self.report.to_row() if self.report is not None else {"S": math.nan})
        return row


def _run_job(spec_dir: Path, spec_id: str, day: str, seed: int, site_path, sim_end_s, runs_root) -> runner.RunResult:
    # runner.resolve_inputs only knows rules/compiled/<spec_id>; same inputs, campaign-local compiled dir
    site = load_site(site_path)
    inputs = runner.RunInputs(spec_id, day, site, runner.NET_DIR / site_net_name(site),
                              runner.DEMAND_DIR / f"routes_{day}.rou.xml", Path(spec_dir))
    return runner.run(spec_id, day, seed, site_path=site_path, sim_end_s=sim_end_s, runs_root=runs_root,
                      inputs=inputs)


def _run_all(args: list[tuple], nproc: int, job=_run_job) -> list[runner.RunResult]:
    """`job` (a module-level function; tests swap it) per args tuple; one SUMO per spawned worker, as
    runner.run_many."""
    if nproc <= 1:
        return [job(*a) for a in args]
    with multiprocessing.get_context("spawn").Pool(nproc, maxtasksperchild=1) as pool:
        return pool.starmap(job, args)


def _sum_interventions(manifests: list[dict]) -> dict:
    out: dict = {}
    for m in manifests:
        for rule, st in (m.get("interventions") or {}).items():
            o = out.setdefault(rule, {"attempted": 0, "executed": 0, "not_executed": Counter(), "counters": Counter()})
            o["attempted"] += st["attempted"]
            o["executed"] += st["executed"]
            o["not_executed"].update(st.get("not_executed") or {})
            o["counters"].update(st.get("counters") or {})
    return {k: {**v, "not_executed": dict(v["not_executed"]), "counters": dict(v["counters"])} for k, v in out.items()}


def check_days(days: list[str], exp: dict, allow_validation: bool = False) -> None:
    """Raise unless `days` are calibration days (PLAN 5.4); `allow_validation` is for the final benchmark only."""
    split = exp.get("data_split") or {}
    allowed = set(split.get("calibration_days") or [])
    if allow_validation:
        allowed |= set(split.get("validation_days") or [])
    bad = [d for d in days if d not in allowed]
    if not days or bad:
        raise ValueError(f"days {bad or days} not allowed: only experiment.yaml data_split.calibration_days "
                         f"{sorted(split.get('calibration_days') or [])} may be evaluated outside the benchmark")


def evaluate_spec(spec: dict, days: list[str], seeds: list[int], budget: RunBudget, *, campaign: str,
                  site_path: Path | None = None, nproc: int = 1, sim_end_s: float | None = None,
                  allow_validation: bool = False) -> EvalResult:
    """Validate, compile, charge len(days) x len(seeds) runs, run, gate and score `spec` (module doc)."""
    t0 = time.perf_counter()
    if budget.path != CAMPAIGNS_DIR / campaign / "budget.json":
        raise ValueError(f"budget {budget.path} is not the budget of campaign {campaign!r}")
    exp = load_experiment()
    check_days(days, exp, allow_validation)
    if not seeds:
        raise ValueError("no seeds")
    spec_id = spec.get("spec_id", "?") if isinstance(spec, dict) else "?"
    root = CAMPAIGNS_DIR / campaign
    site = load_site(site_path)
    spec_dir = root / "compiled" / spec_id
    if (spec_dir / "spec.json").is_file():
        raise ValueError(f"spec id {spec_id!r} was already evaluated in campaign {campaign!r} ({spec_dir}); "
                         f"give every spec a unique spec_id")
    try:
        compile_spec(spec, spec_dir, site=site)
        issues = []
    except InvalidSpecError as e:
        issues = e.issues
    ValidityLog(root / "validity_log.csv").record(spec_id, issues, source=campaign)
    if issues:
        return EvalResult(spec_id, campaign, False, issues, wall_time_s=round(time.perf_counter() - t0, 2))
    observed = {d: read_tables(OBSERVED_DIR / d) for d in days}   # before charging: missing data costs nothing
    budget.consume(len(days) * len(seeds))
    # written only once charged, so a failed read or BudgetExhausted does not lock the id; enters manifest spec_hash
    (spec_dir / "spec.json").write_text(json.dumps(spec, indent=2), encoding="utf-8")
    jobs = [(spec_dir, spec_id, d, int(s), site_path, sim_end_s, root / "runs") for d in days for s in seeds]
    results = _run_all(jobs, nproc)

    limits = exp.get("validity") or {}
    thresholds_known = all(limits.get(k) is not None for k in runner.VALIDITY_KEYS)
    gate_window = (float(exp["sim"]["begin_s"]),
                   float(sim_end_s if sim_end_s is not None else exp["sim"]["calib_end_s"]))
    sim_tables, runs = [], []
    for res in results:
        m, tables = res.manifest, read_tables(res.run_dir)
        sim_tables.append(tables)
        passed, share = g0_geh.gate(tables, observed[m["day"]], window=gate_window)
        reasons = [] if passed else [f"G0 GEH gate: {share:.3f} of cells with GEH < threshold"]
        if not thresholds_known:
            eligibility = "excluded" if reasons else "unknown"
        else:
            reasons += runner.is_eligible(m, exp)[1]
            eligibility = "excluded" if reasons else "eligible"
        hours = (float(m["config"]["sim"]["end_s"]) - float(m["config"]["sim"]["begin_s"])) / 3600.0
        tp = m.get("teleports") or {}
        runs.append({"day": m["day"], "seed": m["seed"], "run_dir": str(res.run_dir), "g0_pass": passed,
                     "geh_share": share, "eligibility": eligibility, "reasons": reasons,
                     "valid_strict": m.get("valid_strict"), "collisions_per_hour": m["n_collisions"] / hours,
                     "lane_collisions_per_hour": m["n_collisions_lane"] / hours,
                     "jam_yield_teleports_per_hour": (tp.get("jam", 0) + tp.get("yield", 0)) / hours})
    ctx = MetricContext.from_config(exp, site=site)
    report = distance.compare(sim_tables, list(observed.values()), ctx=ctx)
    return EvalResult(spec_id, campaign, True, [], report, runs, _sum_interventions([r.manifest for r in results]),
                      round(time.perf_counter() - t0, 2))


def select_best(results: list[EvalResult], b0_lane_collisions_per_hour: float | None = None) -> EvalResult | None:
    """Best spec. R10: among eligible specs (every run eligible, not a majority) whose mean LANE collision rate is
    <= the B0 mean + 1/h (R28: junction collisions are already capped per run by
    validity.max_junction_collisions_per_hour; cap skipped when `b0_lane_collisions_per_hour` is None), the lowest
    S. R32/R42: if none qualifies, every valid spec ranked by mean jam+yield teleports per hour, then S, WITHOUT the
    collision cap (R42: rank by R32 when nothing is eligible; report it as "least gridlock", not as eligible).
    None when no spec is valid. Raises while eligibility is unknown (validity thresholds still null)."""
    valid = [r for r in results if r.valid and r.n_runs]
    unknown = [r.spec_id for r in valid if r.eligibility == "unknown"]
    if unknown:
        raise ValueError(f"eligibility unknown for {unknown}: experiment.yaml validity thresholds are null")
    cap = None if b0_lane_collisions_per_hour is None else b0_lane_collisions_per_hour + 1.0
    ok = [r for r in valid if r.eligibility == "eligible" and (cap is None or r.lane_collisions_per_hour <= cap)]
    if ok:
        return min(ok, key=lambda r: r.S)
    return min(valid, key=lambda r: (r.jam_yield_teleports_per_hour, r.S), default=None)
