"""M2: early start (crossing in the last N s of red) and the delay from green onset to the first crossing (PLAN 5.2).

Classification shared with M3 (docs/research/proxy_targets.md §2): a stop-line crossing in state `r` that lies at
most N = 10 s before the next green onset of its approach is an early start; any other crossing in `r` is red
running. Only crossings before the approach's last green onset in the record (and before the window end) can be
classified; `illegal_l` vehicles are left out (as in the generator's share definition), and so are the right turns
of `continuous_right_lane` approaches (`common.uncontrolled_tracks`: not signal controlled, PLAN 0) and the movements
on a signal head of their own (`common.own_head_tracks`: the LVL left / U-turn arrow of the three-stage plan; the
approach state in `signal_events` is the straight head's), in numerator and denominator, also for the first-crossing
delay.

- M2/early/<vclass>: early starts / classifiable crossings of that class in the window, pooled over approaches
  (targets.yaml: share of the approach's class total; scalar).
- M2/first_delay: per green onset in the window, time to the approach's first crossing at or after it (before the
  next red onset); all approaches.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from thesis_sumo.metrics.common import (
    MetricContext,
    approaches,
    crossings,
    own_head_tracks,
    uncontrolled_tracks,
    dist,
    onsets,
    red_onset_after,
    scalar,
    share,
)
from thesis_sumo.schema_observed import VCLASSES, cycle_id_at

EARLY_START_N_S = 10.0  # proxy_targets.md §2 (= targets.yaml M3_red_running.early_start_exclusion_s)


def classified(tables: dict, ctx: MetricContext) -> pd.DataFrame:
    """Classifiable crossings in the window (no illegal_l): approach, vclass, t, cycle_id, kind
    ("early" | "red" | "go")."""
    cr = crossings(tables)
    cr = cr[~cr["track_id"].isin(uncontrolled_tracks(tables, ctx) | own_head_tracks(tables, ctx))]
    parts = []
    for app in approaches(tables):
        on = onsets(tables, app, ctx)
        if not len(on):
            continue
        c = cr[(cr["approach"] == app) & (cr["movement"] != "illegal_l") & ctx.in_window(cr["t"]) & (cr["t"] < on[-1])]
        t = c["t"].to_numpy(dtype=float)
        lead = on[np.searchsorted(on, t, side="left")] - t
        red = c["signal_state_at_t"].to_numpy() == "r"
        early = red & (lead > 0) & (lead <= EARLY_START_N_S)
        kind = np.where(early, "early", np.where(red, "red", "go"))
        parts.append(pd.DataFrame({"approach": app, "vclass": c["vclass"].to_numpy(), "t": t,
                                   "cycle_id": cycle_id_at(on, t), "kind": kind}))
    cols = ["approach", "vclass", "t", "cycle_id", "kind"]
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=cols)


def first_delays(tables: dict, ctx: MetricContext, apps=None) -> list[tuple[str, float, float]]:
    """(approach, onset, delay to the first crossing at or after it, before the next red onset) per onset in the
    window; onsets without such a crossing are skipped."""
    cr = tables["stopline_crossings"]
    cr = cr[~cr["track_id"].isin(uncontrolled_tracks(tables, ctx) | own_head_tracks(tables, ctx))]
    out = []
    for app in apps if apps is not None else approaches(tables):
        t = np.sort(cr.loc[cr["approach"] == app, "t"].to_numpy(dtype=float))
        for g in onsets(tables, app, ctx):
            if not ctx.in_window(g):
                continue
            i = np.searchsorted(t, g, side="left")
            if i < len(t) and t[i] < red_onset_after(tables, app, g):
                out.append((app, float(g), float(t[i] - g)))
    return out


def compute(tables: dict, ctx: MetricContext | None = None) -> dict:
    ctx = ctx or MetricContext.from_config()
    c = classified(tables, ctx)
    out = {}
    for vc in VCLASSES:
        sub = c[c["vclass"] == vc]
        out[f"M2/early/{vc}"] = scalar(share(int((sub["kind"] == "early").sum()), len(sub)),
                                       f"early-start share, last {EARLY_START_N_S:g} s of red ({vc})", "share",
                                       "M2_early_start.early_start_share")
    out["M2/first_delay"] = dist([d for _, _, d in first_delays(tables, ctx)], "green onset to first crossing", "s",
                                 "M2_early_start.first_crossing_delay_s")
    return out
