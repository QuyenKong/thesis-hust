"""M7: illegal left turns waiting in the junction box (PLAN 5.2, focus scenario), from `box_queue` (binding
definition in `thesis_sumo.schema_observed`, ruling R11), `traversals` and `stopline_crossings`. Box rows count
when their `t` (the opposing through green end) is in the window; the entrants of a row are the `illegal_l`
traversals of its approach whose stop-line crossing falls in the row's cycle (`cycle_id`), as in the generator.

- M7a/n_waiting: `n_waiting_in_box` per row.
- M7a/release_time: per entrant with an exit, `t_exit - t` of its row (PLAN "release times within the cycle";
  negative = left early through a gap).
- M7b/clear_lag, labelled "PET proxy (box clear lag)" (ruling R16, targets.yaml M7_illegal_left.clear_lag_s,
  proxy_targets.md §2): per row, the first entrant exit at or after `t` minus max(t, last stop-line crossing of the
  opposing approach's straight movement before that exit). Rows without such an exit give no value. SUMO SSM PET
  is not used.
- M7c/slope (scalar): least-squares slope of the crossing road's start delay (green onset to its first stop-line
  crossing, `m2_early_start.first_delays`) on the box waiters at the last box time at or before that onset (sum of
  `n_waiting_in_box` over the rows at that time: with illegal lefts from both approaches of one road, HDT_N and
  HDT_S, both boxes hold the crossing road), if that time is less than one cycle (the median onset spacing) before
  it. Crossing roads = approaches that are neither an illegal-left approach nor its opposing approach. NaN
  (undefined) with fewer than two distinct x values.
"""

from __future__ import annotations

import numpy as np

from thesis_sumo.metrics.common import MetricContext, approaches, cycle_of, dist, onsets, opposing, scalar
from thesis_sumo.metrics.m2_early_start import first_delays

PET_LABEL = "PET proxy (box clear lag)"


def _rows(tables: dict, ctx: MetricContext):
    box = tables["box_queue"]
    return box[ctx.in_window(box["t"])].sort_values("t", kind="stable")


def release_and_lag(tables: dict, ctx: MetricContext) -> tuple[list[float], list[float]]:
    tr = tables["traversals"]
    apps = approaches(tables)
    release, lags = [], []
    rows = _rows(tables, ctx)
    for app, rr in rows.groupby("approach"):
        v = tr[(tr["approach"] == app) & (tr["movement"] == "illegal_l")]
        cyc = cycle_of(tables, app, v["t_stopline"], ctx)
        opp = tr[(tr["approach"] == opposing(app, apps)) & (tr["movement"] == "s")]
        opp_t = np.sort(opp["t_stopline"].to_numpy(dtype=float))
        for r in rr.itertuples():
            ex = np.sort(v.loc[cyc == r.cycle_id, "t_exit"].dropna().to_numpy(dtype=float))
            release += list(ex - r.t)
            late = ex[ex >= r.t]
            if len(late):
                before = opp_t[opp_t < late[0]]
                lags.append(float(late[0] - max(r.t, before[-1] if len(before) else -np.inf)))
    return release, lags


def start_delay_points(tables: dict, ctx: MetricContext) -> tuple[np.ndarray, np.ndarray]:
    """(box waiters at the last box time, crossing-road start delay) per crossing-road onset in the window."""
    box = tables["box_queue"].sort_values("t", kind="stable")
    if not len(box):
        return np.array([]), np.array([])
    apps = approaches(tables)
    illegal = set(box["approach"])
    blocked = illegal | {opposing(a, apps) for a in illegal}
    crossing_road = [a for a in apps if a not in blocked]
    bt, bn = box["t"].to_numpy(dtype=float), box["n_waiting_in_box"].to_numpy(dtype=float)
    x, y = [], []
    for app, g, delay in first_delays(tables, ctx, crossing_road):
        cycle = float(np.median(np.diff(onsets(tables, app, ctx))))
        i = np.searchsorted(bt, g, side="right") - 1
        if i >= 0 and g - bt[i] < cycle:
            x.append(bn[bt == bt[i]].sum())
            y.append(delay)
    return np.array(x), np.array(y)


def _slope(x: np.ndarray, y: np.ndarray) -> float:
    if len(np.unique(x)) < 2:
        return float("nan")
    return float(np.polyfit(x, y, 1)[0])


def compute(tables: dict, ctx: MetricContext | None = None) -> dict:
    ctx = ctx or MetricContext.from_config()
    release, lags = release_and_lag(tables, ctx)
    return {
        "M7a/n_waiting": dist(_rows(tables, ctx)["n_waiting_in_box"], "illegal lefts halting in the box at the opposing "
                              "green end", "veh", "M7_illegal_left.n_waiting_in_box"),
        "M7a/release_time": dist(release, "box exit time after the opposing green end", "s",
                                 "M7_illegal_left.box_exit_headway_s"),
        "M7b/clear_lag": dist(lags, f"{PET_LABEL}: first box exit after the opposing stream ends", "s",
                              "M7_illegal_left.clear_lag_s"),
        "M7c/slope": scalar(_slope(*start_delay_points(tables, ctx)), "crossing-road start delay per box waiter",
                            "s/veh", "M7_illegal_left.crossing_start_delay_per_waiter_s"),
    }
