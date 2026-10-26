"""M4: lateral position of halting motorcycles at green onset and stop-line overshoot (PLAN 5.2).

Rows: `lateral_snapshots` of green onsets in the window, motorcycles, without the vehicles that crossed the stop
line in G or y before the onset (box waiters, vehicles still inside the junction from an earlier green).
On the observed days this is exactly the generator's set (proxy_targets.md §2 / tests/test_proxy.py: "halting
motorcycles that have not crossed yet"; the only snapshot rows that crossed before the onset are box waiters,
which crossed in G). A motorcycle that crossed in red and halts past the line is kept: in SUMO a vehicle past the
stop line has always passed the entry loop, so dropping every earlier crossing would make overshoot impossible
in simulation (such a vehicle also counts as early start / red runner in M2/M3).

- M4/lat_moto: lat_m (m from the right road edge); M4/overshoot_share: share with long_m_from_stopline < 0;
  M4/overshoot_depth: -long_m_from_stopline of the overshooters.
"""

from __future__ import annotations

import numpy as np

from thesis_sumo.metrics.common import MetricContext, approaches, dist, onsets, scalar, share


def queued_motos(tables: dict, ctx: MetricContext):
    lat = tables["lateral_snapshots"]
    cr = tables["stopline_crossings"].set_index("track_id")
    parts = []
    for app in approaches(tables):
        on = onsets(tables, app, ctx)
        s = lat[(lat["approach"] == app) & (lat["vclass"] == "moto") & (lat["cycle_id"] >= 0)
                & (lat["cycle_id"] < len(on))]
        g = on[s["cycle_id"].to_numpy(dtype=int)]
        s = s[ctx.in_window(g)]
        g = g[ctx.in_window(g)]
        t = s["track_id"].map(cr["t"]).to_numpy(dtype=float)
        state = s["track_id"].map(cr["signal_state_at_t"]).to_numpy()
        earlier_go = (t < g) & (state != "r")
        parts.append(s[~earlier_go])
    return parts


def compute(tables: dict, ctx: MetricContext | None = None) -> dict:
    ctx = ctx or MetricContext.from_config()
    parts = queued_motos(tables, ctx)
    lat = np.concatenate([p["lat_m"].to_numpy(dtype=float) for p in parts]) if parts else np.array([])
    long = np.concatenate([p["long_m_from_stopline"].to_numpy(dtype=float) for p in parts]) if parts else np.array([])
    return {
        "M4/lat_moto": dist(lat, "lateral position of halting motorcycles at green onset", "m",
                            "M4_lateral.moto_lateral_distribution"),
        "M4/overshoot_share": scalar(share(int((long < 0).sum()), len(long)),
                                     "share of halting motorcycles past the stop line at green onset", "share",
                                     "M4_lateral.overshoot_share_moto"),
        "M4/overshoot_depth": dist(-long[long < 0], "stop-line overshoot depth of motorcycles", "m",
                                   "M4_lateral.overshoot_depth_m"),
    }
