"""Distance between simulation and observed days (PLAN 5.3, Task 10).

- dist metric: W1 between the samples, normalised by the observed sample's IQR (linear quantiles); when the IQR is 0
  the scale falls back to the standard deviation, then |mean|, then 1, so a constant observed sample still gives a
  finite distance. scalar metric: relative error |sim - obs| / |obs|.
- Empty rule (plan "Review focus" 5): a sample with no events on exactly one side, or an undefined scalar (NaN) on
  exactly one side, or a positive scalar against an observed 0 is `D_EMPTY` away; nothing on both sides is 0. A share
  of 0 against a positive share is an ordinary relative error of 1. Every per-day distance is capped at `D_EMPTY`
  (ruling R35), so an optimiser cannot lower the score by suppressing a behaviour until it has no events.
- d = mean over (sim run, observed day) of the distance normalised by that observed day; d_day_day = mean over
  ordered pairs (a, b), a != b, of the observed days (normalised by b); R = d / d_day_day (NaN with one observed day;
  d / R_FLOOR when the days agree exactly).
- Weights (experiment.yaml score.weights) are per metric group M1..M8: a group's weight is split equally over its
  sub-metrics (M7a, M7b, M7c; M1 has one) and then over their keys; only scored keys take weight (a key is unscored
  when its MetricValue says so or no observed day has events). S = sum of weight x d over the scored keys; the
  report also splits S into the parts from keys with sourced and with assumed targets (ruling R13).
"""

from __future__ import annotations

import itertools
import re
from dataclasses import dataclass, field
from functools import lru_cache

import numpy as np
import yaml
from scipy.stats import wasserstein_distance

from thesis_sumo.config import REPO_ROOT, load_experiment
from thesis_sumo.metrics import (
    m1_headway,
    m2_early_start,
    m3_red_running,
    m4_lateral,
    m5_queue,
    m6_traversal,
    m7_illegal_left,
    m8_wrong_lane,
)
from thesis_sumo.metrics.common import MetricContext, MetricValue

D_EMPTY = 2.0    # one side has no events / undefined: worse than a share that is off by 100 %
R_FLOOR = 0.05   # noise floor used when the observed days agree exactly
MODULES = (m1_headway, m2_early_start, m3_red_running, m4_lateral, m5_queue, m6_traversal, m7_illegal_left,
           m8_wrong_lane)
TARGETS = REPO_ROOT / "data" / "proxy" / "targets.yaml"


def compute_all(tables: dict, ctx: MetricContext) -> dict[str, MetricValue]:
    out = {}
    for mod in MODULES:
        out.update(mod.compute(tables, ctx))
    return out


def _scale(obs: np.ndarray) -> float:
    q1, q3 = np.percentile(obs, [25, 75])
    for s in (q3 - q1, np.std(obs), abs(np.mean(obs))):
        if s > 0:
            return float(s)
    return 1.0


def w1_normalised(sim: np.ndarray, obs: np.ndarray) -> float:
    sim, obs = np.asarray(sim, dtype=float), np.asarray(obs, dtype=float)
    if not sim.size and not obs.size:
        return 0.0
    if not sim.size or not obs.size:
        return D_EMPTY
    return float(wasserstein_distance(sim, obs) / _scale(obs))


def rel_error(sim: float, obs: float) -> float:
    if np.isnan(sim) and np.isnan(obs):
        return 0.0
    if np.isnan(sim) or np.isnan(obs):
        return D_EMPTY
    if obs == 0:
        return 0.0 if sim == 0 else D_EMPTY
    return abs(sim - obs) / abs(obs)


def metric_distance(sim: MetricValue, obs: MetricValue) -> float:
    """Capped at D_EMPTY (ruling R35): producing no events is never cheaper than producing them wrongly."""
    d = w1_normalised(sim.values, obs.values) if sim.kind == "dist" else rel_error(sim.values, obs.values)
    return min(d, D_EMPTY)


def pair_stats(sim: list[MetricValue], obs: list[MetricValue]) -> tuple[float, float]:
    """(d, d_day_day) of one metric key."""
    d = float(np.mean([metric_distance(s, o) for s in sim for o in obs]))
    pairs = [metric_distance(a, b) for a, b in itertools.permutations(obs, 2)]
    return d, float(np.mean(pairs)) if pairs else float("nan")


def ratio(d: float, d_day_day: float) -> float:
    if np.isnan(d_day_day):
        return float("nan")
    if d_day_day == 0:
        return 0.0 if d == 0 else d / R_FLOOR
    return d / d_day_day


def _group(key: str) -> str:
    return re.match(r"M\d+", key).group(0)


def split_weights(keys, group_weights: dict) -> dict[str, float]:
    """key -> weight; groups weighted by `group_weights` (renormalised over the groups present)."""
    keys = list(keys)
    missing = sorted({_group(k) for k in keys} - set(group_weights))
    if missing:
        raise ValueError(f"score weights have no entry for {missing}")
    subs: dict[str, dict[str, list[str]]] = {}
    for k in keys:
        subs.setdefault(_group(k), {}).setdefault(k.split("/")[0], []).append(k)
    total = sum(float(group_weights[g]) for g in subs)
    if total <= 0:
        raise ValueError(f"score weights of {sorted(subs)} sum to {total}")
    out = {}
    for g, by_sub in subs.items():
        for members in by_sub.values():
            for k in members:
                out[k] = float(group_weights[g]) / total / len(by_sub) / len(members)
    return out


@lru_cache(maxsize=1)
def _targets() -> dict:
    return yaml.safe_load(TARGETS.read_text(encoding="utf-8"))["targets"]


def evidence(target: str | None) -> str | None:
    if target is None:
        return None
    group, name = target.split(".", 1)
    return _targets()[group][name]["evidence"]


def _pooled_mean(values: list[MetricValue]) -> float:
    if values[0].kind == "scalar":
        v = [m.values for m in values if not m.empty]
        return float(np.mean(v)) if v else float("nan")
    v = np.concatenate([m.values for m in values])
    return float(np.mean(v)) if v.size else float("nan")


def _direction(sim: list[MetricValue], obs: list[MetricValue]) -> str:
    s_empty, o_empty = all(m.empty for m in sim), all(m.empty for m in obs)
    if sim[0].kind == "dist" and s_empty != o_empty:
        return "sim<obs" if s_empty else "sim>obs"
    s, o = _pooled_mean(sim), _pooled_mean(obs)
    if np.isnan(s) or np.isnan(o):
        return "undefined"
    if np.isclose(s, o, rtol=0, atol=1e-12):
        return "sim=obs"
    return "sim>obs" if s > o else "sim<obs"


@dataclass
class MetricReport:
    key: str
    label: str
    unit: str
    kind: str
    target: str | None
    evidence: str | None
    d: float
    d_day_day: float
    R: float
    direction: str
    scored: bool
    sim_mean: float
    obs_mean: float
    weight: float = 0.0


@dataclass
class DistanceReport:
    metrics: dict[str, MetricReport]
    n_sim: int
    n_obs_days: int
    S: float = field(init=False)
    S_sourced: float = field(init=False)
    S_assumed: float = field(init=False)

    def __post_init__(self):
        part = {"assumed": 0.0, "sourced": 0.0}
        for m in self.metrics.values():
            if m.scored:
                part["assumed" if m.evidence == "assumed" else "sourced"] += m.weight * m.d
        self.S_assumed, self.S_sourced = part["assumed"], part["sourced"]
        self.S = self.S_assumed + self.S_sourced

    @property
    def direction(self) -> dict[str, str]:
        return {k: m.direction for k, m in self.metrics.items()}

    def to_row(self) -> dict:
        row = {"S": self.S, "S_sourced": self.S_sourced, "S_assumed": self.S_assumed, "n_sim": self.n_sim,
               "n_obs_days": self.n_obs_days}
        for k, m in self.metrics.items():
            row.update({f"{k}.d": m.d, f"{k}.R": m.R, f"{k}.w": m.weight})
        return row

    def summary_lines(self) -> list[str]:
        """One line per metric for LLM feedback / logs; no day names (validation days must never leak)."""
        return [f"{k}: sim {m.sim_mean:.4g} vs obs {m.obs_mean:.4g} {m.unit} ({m.direction}); d {m.d:.3f}, "
                f"R {m.R:.2f}, weight {m.weight:.3f}{'' if m.scored else ', not scored'}; target evidence "
                f"{m.evidence}" for k, m in sorted(self.metrics.items())]


def compare(sim_tables: list[dict], obs_days: list[dict], weights: dict | None = None,
            ctx: MetricContext | None = None) -> DistanceReport:
    """Every metric of the simulation runs against the observed days."""
    if not sim_tables or not obs_days:
        raise ValueError("compare needs at least one simulation run and one observed day")
    ctx = ctx or MetricContext.from_config()
    if weights is None:
        weights = (load_experiment().get("score") or {}).get("weights")
        if weights is None:
            raise ValueError("experiment.yaml score.weights is null (TODO_DECIDE)")
    sims = [compute_all(t, ctx) for t in sim_tables]
    obs = [compute_all(t, ctx) for t in obs_days]
    reports = {}
    for key in sorted(obs[0]):
        s, o = [r[key] for r in sims], [r[key] for r in obs]
        d, ddd = pair_stats(s, o)
        reports[key] = MetricReport(
            key=key, label=o[0].label, unit=o[0].unit, kind=o[0].kind, target=o[0].target,
            evidence=evidence(o[0].target), d=d, d_day_day=ddd, R=ratio(d, ddd), direction=_direction(s, o),
            scored=o[0].scored and any(not m.empty for m in o), sim_mean=_pooled_mean(s), obs_mean=_pooled_mean(o))
    for k, w in split_weights([k for k, m in reports.items() if m.scored], weights).items():
        reports[k].weight = w
    return DistanceReport(reports, n_sim=len(sims), n_obs_days=len(obs))
