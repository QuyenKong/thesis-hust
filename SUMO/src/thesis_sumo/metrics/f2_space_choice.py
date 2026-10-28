"""F2: probability of choosing each alternative space by queue length (PLAN 5.2, F2 group), from
`space_seeking_events`, `queue_timeseries` and `traversals`. REPORTED, NOT SCORED (keys `F2/...` belong to no
weighted group): per bin the counts are small (a few events per bin and day), so each relative error would mostly be
noise and an empty bin costs D_EMPTY (ruling R35); the scored part of the same information is M9a/M10a (how many)
and M9c/M10b (at which queue).

F2/p/<space>/<bin> = (candidates with an event of that space) / candidates, where a candidate is a vehicle whose
`t_range_entry` is in the window and the queue it met there (`queue_timeseries` of its approach at the last grid
time <= `t_range_entry`) falls in the bin; NaN without candidates. Candidates: `right_lane` -- straight vehicles of
continuous-right-lane approaches (event: seen standing in lane 0, `schema_observed`); `sidewalk` -- straight motorcycles of sidewalk approaches; `wrong_lane` -- turning
vehicles (r, l, u). Bins of 20 m up to `observation.queue_range_m` R, plus `ge<R>` for censored queues (>= R).
`opposite` is not reported (ruling R38).
"""

from __future__ import annotations

import numpy as np

from thesis_sumo.metrics.common import (
    MetricContext,
    continuous_right_approaches,
    scalar,
    share,
    sidewalk_approaches,
)
from thesis_sumo.schema_observed import queue_at_times

BIN_M = 20.0
TARGET = {"right_lane": "M9_right_lane.right_lane_choice_prob", "sidewalk": "M10_sidewalk.sidewalk_choice_prob",
          "wrong_lane": "M8_wrong_lane.wrong_lane_share"}


def bins(range_m: float) -> tuple[np.ndarray, list[str]]:
    edges = np.append(np.arange(0.0, range_m, BIN_M), range_m)
    labels = [f"q{lo:g}-{hi:g}" for lo, hi in zip(edges[:-1], edges[1:])] + [f"ge{range_m:g}"]
    return edges, labels


def choice_probability(tables: dict, ctx: MetricContext, space: str) -> dict[str, float]:
    tr = tables["traversals"]
    tr = tr[ctx.in_window(tr["t_range_entry"])]
    if space == "right_lane":
        cand = tr[(tr["movement"] == "s") & tr["approach"].isin(continuous_right_approaches(ctx))]
    elif space == "sidewalk":
        cand = tr[(tr["movement"] == "s") & (tr["vclass"] == "moto") & tr["approach"].isin(sidewalk_approaches(ctx))]
    else:
        cand = tr[tr["movement"].isin(("r", "l", "u"))]
    q = np.full(len(cand), np.nan)
    for app in cand["approach"].unique():
        sel = (cand["approach"] == app).to_numpy()
        q[sel] = queue_at_times(tables["queue_timeseries"], app, cand.loc[sel, "t_range_entry"])
    ev = tables["space_seeking_events"]
    chose = cand["track_id"].isin(set(ev.loc[ev["space"] == space, "track_id"])).to_numpy()
    edges, labels = bins(ctx.queue_range_m)
    b = np.digitize(q, edges[1:-1], right=False)  # 0 .. len(edges) - 2 below R
    b[q >= ctx.queue_range_m] = len(labels) - 1
    ok = ~np.isnan(q)
    return {lab: share(int((chose & ok & (b == i)).sum()), int((ok & (b == i)).sum())) for i, lab in enumerate(labels)}


def compute(tables: dict, ctx: MetricContext | None = None) -> dict:
    ctx = ctx or MetricContext.from_config()
    out = {}
    for space in ("right_lane", "sidewalk", "wrong_lane"):
        for lab, v in choice_probability(tables, ctx, space).items():
            out[f"F2/p/{space}/{lab}"] = scalar(v, f"P(choose {space} | queue {lab} m at range entry)", "share",
                                                TARGET[space], scored=False)
    return out
