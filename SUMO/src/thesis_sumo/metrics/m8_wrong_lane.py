"""M8: wrong-lane share (PLAN 5.2, ruling R9; proxy_targets.md §2).

The lane of a crossing is found from `traversals.lat_m_at_stopline` and the cumulative lane widths of the site
file (lane i covers [edge_i, edge_{i+1}); a position beyond the roadway falls in the outermost lane, a negative one
in lane 0). A vehicle is in the wrong lane when its movement is not in the lane's `lane_movements`. Only turning
vehicles (r, l, u) count; illegal_l is permitted in no lane and is left out; rows without a lateral position are
dropped. M8/<vclass>: wrong / turning crossings of the class in the window.
"""

from __future__ import annotations

import numpy as np

from thesis_sumo.metrics.common import MetricContext, scalar, share
from thesis_sumo.schema_observed import VCLASSES

TURNING = ("r", "l", "u")


def wrong_lane(tables: dict, ctx: MetricContext):
    """(vclass array, wrong-lane flag array) of the turning crossings in the window."""
    tr = tables["traversals"]
    tr = tr[ctx.in_window(tr["t_stopline"]) & tr["movement"].isin(TURNING) & tr["lat_m_at_stopline"].notna()]
    vcs, flags = [], []
    for app, g in tr.groupby("approach"):
        edges, movements = ctx.lanes(app)
        lane = np.minimum(np.searchsorted(edges, g["lat_m_at_stopline"].to_numpy(dtype=float), side="right"),
                          len(movements) - 1)
        flags += [m not in movements[i] for m, i in zip(g["movement"], lane)]
        vcs += list(g["vclass"])
    return np.array(vcs, dtype=object), np.array(flags, dtype=bool)


def compute(tables: dict, ctx: MetricContext | None = None) -> dict:
    ctx = ctx or MetricContext.from_config()
    vcs, wrong = wrong_lane(tables, ctx)
    return {f"M8/{vc}": scalar(share(int(wrong[vcs == vc].sum()), int((vcs == vc).sum())),
                               f"wrong-lane share of turning vehicles ({vc})", "share", "M8_wrong_lane.wrong_lane_share")
            for vc in VCLASSES}
