"""M9: blocking of the continuous right-turn lane (PLAN 5.2, behaviour 6), from `space_seeking_events` (space
`right_lane`) and `right_turn_delay` (definitions in `thesis_sumo.schema_observed`), on the approaches with
`continuous_right_lane: true`. An event counts when its `t` is in the window, a right turn when its `t_exit` is.

- M9a/per_cycle: straight vehicles standing (halting) in lane 0 per complete cycle (as M3), pooled over approaches.
  PLAN asks for straight vehicles *standing* in the right lane at green onset; the tables count every straight vehicle
  seen halting in lane 0 within R in the cycle, not only at the onset snapshot. Driving straight through lane 0 is
  legal on green since 2026-10-28 (no bollards) and is no event. The dependence on the queue is M9c / F2.
- M9b/delay_blocked: `t_exit - t_enter` of the blocked right turns (PLAN "right-turn delay distribution"; the delay of
  all right turns is already M6/approach/r, so M9 scores only the blocked ones). M9b/share_blocked: blocked / right
  turns with a `t_enter`.
- M9c/queue_at_choice: `queue_length_m_at_t` of the right-lane events: the queue length at which straight vehicles
  take the right lane (constrains `q` of queue_space_seeking). The per-queue-bin probability is reported in F2.
"""

from __future__ import annotations

from thesis_sumo.metrics.common import (
    MetricContext,
    continuous_right_approaches,
    dist,
    events_per_cycle,
    scalar,
    share,
)


def compute(tables: dict, ctx: MetricContext | None = None) -> dict:
    ctx = ctx or MetricContext.from_config()
    apps = continuous_right_approaches(ctx)
    ev = tables["space_seeking_events"]
    ev = ev[(ev["space"] == "right_lane") & ev["approach"].isin(apps) & ctx.in_window(ev["t"])]
    rt = tables["right_turn_delay"]
    rt = rt[rt["approach"].isin(apps) & ctx.in_window(rt["t_exit"]) & rt["t_enter"].notna()]
    blocked = rt["blocked"].astype(bool)
    delay = (rt["t_exit"] - rt["t_enter"])[blocked]
    return {
        "M9a/per_cycle": dist(events_per_cycle(tables, "right_lane", apps, ctx),
                              "straight vehicles standing in the right-turn lane per cycle", "veh/cycle",
                              "M9_right_lane.right_lane_choice_prob"),
        "M9b/delay_blocked": dist(delay, "delay of blocked right-turners (range entry to stop line)", "s",
                                  "M9_right_lane.lane0_hold_s"),
        "M9b/share_blocked": scalar(share(int(blocked.sum()), len(rt)), "share of right-turners blocked in lane 0",
                                    "share", "M9_right_lane.lane0_hold_s"),
        "M9c/queue_at_choice": dist(ev["queue_length_m_at_t"], "approach queue when a straight vehicle takes the "
                                    "right-turn lane", "m", "M9_right_lane.choice_ramp_queue_m",
                                    scored=False),  # R43: saturated by the sim queue censoring (R42), reported only
    }
