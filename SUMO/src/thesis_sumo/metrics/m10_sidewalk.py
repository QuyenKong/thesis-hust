"""M10: sidewalk riding (PLAN 5.2, behaviour 7), from `space_seeking_events` (space `sidewalk`; definition in
`thesis_sumo.schema_observed`), on the sidewalk approaches (site `f2_measured_approaches`). An approach without a
sidewalk contributes nothing; with none at all both keys are empty on both sides (distance 0, not scored).

- M10a/per_cycle: riders seen on the sidewalk per complete cycle (as M3), pooled over the sidewalk approaches.
- M10b/queue_at_choice: `queue_length_m_at_t` of the sidewalk events (PLAN "by queue length"; constrains `q`). The
  per-queue-bin probability is reported in F2.
"""

from __future__ import annotations

from thesis_sumo.metrics.common import MetricContext, dist, events_per_cycle, sidewalk_approaches


def compute(tables: dict, ctx: MetricContext | None = None) -> dict:
    ctx = ctx or MetricContext.from_config()
    apps = sidewalk_approaches(ctx)
    ev = tables["space_seeking_events"]
    ev = ev[(ev["space"] == "sidewalk") & ev["approach"].isin(apps) & ctx.in_window(ev["t"])]
    return {
        "M10a/per_cycle": dist(events_per_cycle(tables, "sidewalk", apps, ctx), "motorcycles seen on the sidewalk per "
                               "cycle", "veh/cycle", "M10_sidewalk.sidewalk_choice_prob"),
        "M10b/queue_at_choice": dist(ev["queue_length_m_at_t"], "approach queue when a motorcycle takes the sidewalk",
                                     "m", "M9_right_lane.choice_ramp_queue_m",
                                     scored=False),  # R43: saturated by the sim queue censoring (R42), reported only
    }
