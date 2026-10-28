"""M1: discharge headway after green onset, by vehicle class (PLAN 5.2).

Definition (docs/research/proxy_targets.md §2, as the proxy generator builds it): at each green onset `g` of an
approach in the window, the queue is the set of vehicles in that cycle's `lateral_snapshots` that have not crossed
the stop line before `g` (box waiters and stop-line overshooters that already crossed are not discharged); the
discharge is the first len(queue) stop-line crossings of the approach (all lanes) at or after `g`; the headway of
queue position n >= 2 is the time since the previous crossing and is filed under the class of the n-th vehicle.
Added here (no change on the observed days, whose queues always clear in green): the discharge stops at the
approach's next red onset, so a queue left over into the next cycle does not add one red-long "headway".
Right turns of `continuous_right_lane` approaches (`common.uncontrolled_tracks`, not signal controlled) and the
movements on a signal head of their own (`common.own_head_tracks`, e.g. the LVL left arrow) are in neither the queue
nor the discharge.
Output: one headway distribution per vclass, positions pooled.
"""

from __future__ import annotations

import numpy as np

from thesis_sumo.metrics.common import (
    MetricContext,
    approaches,
    dist,
    onsets,
    own_head_tracks,
    red_onset_after,
    uncontrolled_tracks,
)
from thesis_sumo.schema_observed import VCLASSES

TARGET = {"moto": "M1_headway.moto_saturation_headway_s", "car": "M1_headway.car_headway_factor"}


def headways(tables: dict, ctx: MetricContext) -> list[tuple[str, int, float]]:
    """(vclass, queue position, headway) of every discharged vehicle at position >= 2."""
    free = uncontrolled_tracks(tables, ctx) | own_head_tracks(tables, ctx)
    cr = tables["stopline_crossings"].sort_values(["t", "track_id"], kind="stable")
    cr = cr[~cr["track_id"].isin(free)]
    t_cross = cr.set_index("track_id")["t"]
    lat = tables["lateral_snapshots"]
    lat = lat[~lat["track_id"].isin(free)]
    out = []
    for app in approaches(tables):
        c = cr[cr["approach"] == app]
        times, vcs = c["t"].to_numpy(dtype=float), c["vclass"].to_numpy()
        snap = lat[lat["approach"] == app]
        for k, g in enumerate(onsets(tables, app, ctx)):
            if not ctx.in_window(g):
                continue
            ids = snap.loc[snap["cycle_id"] == k, "track_id"]
            n_queue = int((~(ids.map(t_cross) < g)).sum())  # not crossed before the onset (NaN: never crossed)
            stop = red_onset_after(tables, app, g)
            sel = np.flatnonzero((times >= g) & (times < stop))[:n_queue]
            for pos, (a, b) in enumerate(zip(sel[:-1], sel[1:]), start=2):
                out.append((vcs[b], pos, float(times[b] - times[a])))
    return out


def compute(tables: dict, ctx: MetricContext | None = None) -> dict:
    ctx = ctx or MetricContext.from_config()
    h = headways(tables, ctx)
    return {f"M1/{vc}": dist([x for v, _, x in h if v == vc], f"discharge headway after green ({vc})", "s",
                             TARGET[vc]) for vc in VCLASSES}
