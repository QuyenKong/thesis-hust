"""M5: queue at green onset (PLAN 5.2), from `queue_snapshots` rows whose `t_green_onset` is in the window.

- M5/length: queue_length_m, pooled over approaches (PLAN says "by approach"; with 11-12 cycles per approach in the
  1500 s window a per-approach W1 rests on too few values, so approaches are pooled).
- M5/moto_density: n_moto / area_m2 (proxy_targets.md §3), rows with area_m2 > 0.
- M5/share_censored (ruling R8, reported, not scored): share of rows with queue_length_m >= observation.queue_range_m
  (the converter and the generator cap a queue reaching the range at exactly the range). The observed days are
  never censored, so a relative error against 0 is not defined; censored rows still enter M5/length at the cap, a
  lower bound of their true length.
"""

from __future__ import annotations

from thesis_sumo.metrics.common import MetricContext, dist, scalar, share

TARGET = "M5_queue.queue_length_and_density"
CENSOR_TOL_M = 1e-6


def compute(tables: dict, ctx: MetricContext | None = None) -> dict:
    ctx = ctx or MetricContext.from_config()
    q = tables["queue_snapshots"]
    q = q[ctx.in_window(q["t_green_onset"])]
    area = q["area_m2"].to_numpy(dtype=float)
    pos = area > 0
    censored = int((q["queue_length_m"] >= ctx.queue_range_m - CENSOR_TOL_M).sum())
    return {
        "M5/length": dist(q["queue_length_m"], "queue length at green onset", "m", TARGET),
        "M5/moto_density": dist(q["n_moto"].to_numpy(dtype=float)[pos] / area[pos],
                                "motorcycle density in the queue at green onset", "veh/m2", TARGET),
        "M5/share_censored": scalar(share(censored, len(q)),
                                    f"share of queues reaching the observed range ({ctx.queue_range_m:g} m)", "share",
                                    TARGET, scored=False),
    }
