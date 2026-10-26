"""M6: traversal times by movement x vclass (PLAN 5.2, ruling R9), from `traversals` rows whose `t_stopline` is in
the window.

- M6/junction/<movement>/<vclass>: t_exit - t_stopline (stop line to the outbound lane; for illegal_l it includes
  the box wait).
- M6/approach/<movement>/<vclass>: t_stopline - t_range_entry (last observation.queue_range_m before the line,
  queueing included). NaN times (not seen at the range entry / not exited before the record ends) are left out.
Keys are the fixed grid MOVEMENTS x VCLASSES without car x illegal_l, so every table set has the same keys.
"""

from __future__ import annotations

from thesis_sumo.metrics.common import MetricContext, dist
from thesis_sumo.schema_observed import MOVEMENTS, VCLASSES

TARGET = {"junction": "M6_traversal.crossing_speed_kmh", "approach": "M6_traversal.approach_speed_kmh"}
TARGET_ILLEGAL_JUNCTION = "M7_illegal_left.clear_lag_s"  # the illegal-left junction time is mostly the box wait


def keys() -> list[tuple[str, str]]:
    return [(m, vc) for m in MOVEMENTS for vc in VCLASSES if not (m == "illegal_l" and vc == "car")]


def compute(tables: dict, ctx: MetricContext | None = None) -> dict:
    ctx = ctx or MetricContext.from_config()
    tr = tables["traversals"]
    tr = tr[ctx.in_window(tr["t_stopline"])]
    times = {"junction": tr["t_exit"] - tr["t_stopline"], "approach": tr["t_stopline"] - tr["t_range_entry"]}
    what = {"junction": "stop line to outbound lane", "approach": "range entry to stop line"}
    out = {}
    for part in ("junction", "approach"):
        for m, vc in keys():
            sel = (tr["movement"] == m) & (tr["vclass"] == vc)
            target = TARGET_ILLEGAL_JUNCTION if (part, m) == ("junction", "illegal_l") else TARGET[part]
            out[f"M6/{part}/{m}/{vc}"] = dist(times[part][sel], f"time {what[part]} ({m}, {vc})", "s", target)
    return out
