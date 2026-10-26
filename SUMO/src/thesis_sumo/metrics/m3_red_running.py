"""M3: red-light running (PLAN 5.2). Red runner = crossing in `r` that is not an early start (classification in
`m2_early_start.classified`, docs/research/proxy_targets.md §2; right turns of `continuous_right_lane` approaches
are not signal controlled and never classified).

- M3/per_cycle: red runners per cycle, one value per approach and complete cycle in the window (onset >= w0, next
  onset before w1); a red crossing belongs to the cycle whose green it follows (`cycle_id_at`).
- M3/var_to_mean: mean over approaches (with a non-zero mean) of the per-cycle variance (ddof 1) / mean.
- M3/share/<vclass>: red runners / classifiable crossings of the class in the window, pooled over approaches.
PLAN's P(violation | k earlier violators within Δt) is not scored: no target defines it (the generator's
mid-red clusters are an assumed mechanism, not a target).
"""

from __future__ import annotations

import numpy as np

from thesis_sumo.metrics.common import MetricContext, approaches, dist, onsets, scalar, share
from thesis_sumo.metrics.m2_early_start import classified
from thesis_sumo.schema_observed import VCLASSES


def per_cycle_counts(tables: dict, ctx: MetricContext) -> dict[str, np.ndarray]:
    """approach -> red runners per complete cycle in the window."""
    c = classified(tables, ctx)
    red = c[c["kind"] == "red"]
    out = {}
    for app in approaches(tables):
        on = onsets(tables, app, ctx)
        ks = [k for k in range(len(on) - 1) if on[k] >= ctx.window[0]]
        n = red.loc[red["approach"] == app, "cycle_id"].value_counts()
        out[app] = np.array([int(n.get(k, 0)) for k in ks], dtype=float)
    return out


def _var_to_mean(counts: dict[str, np.ndarray]) -> float:
    r = [x.var(ddof=1) / x.mean() for x in counts.values() if len(x) > 1 and x.mean() > 0]
    return float(np.mean(r)) if r else float("nan")


def compute(tables: dict, ctx: MetricContext | None = None) -> dict:
    ctx = ctx or MetricContext.from_config()
    counts = per_cycle_counts(tables, ctx)
    out = {
        "M3/per_cycle": dist(np.concatenate(list(counts.values())) if counts else [],
                             "red-light violations per cycle", "veh/cycle", "M3_red_running.per_cycle_var_to_mean"),
        "M3/var_to_mean": scalar(_var_to_mean(counts), "red-light violations per cycle, variance/mean", "",
                                 "M3_red_running.per_cycle_var_to_mean"),
    }
    c = classified(tables, ctx)
    for vc in VCLASSES:
        sub = c[c["vclass"] == vc]
        out[f"M3/share/{vc}"] = scalar(share(int((sub["kind"] == "red").sum()), len(sub)),
                                       f"red-running share ({vc})", "share", "M3_red_running.red_run_share")
    return out
