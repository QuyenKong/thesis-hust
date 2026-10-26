"""Observed-data schema (PLAN 5.1), shared by the video pipeline, the proxy-data generator, the
simulation-side converter (`thesis_sumo.sim.outputs`) and the metrics (ruling R3: one copy only).

Conventions every producer of `data/observed/<day>/` and of `observed_schema/` follows:

- Times `t`, `interval_*`, `t_green_onset`, `t_clear_*` are seconds from the start of the observed window
  (simulation seconds on the SUMO side).
- `approach` is a site approach id (`LVL_W`, `LVL_E`, `HDT_N`, `HDT_S`). `approach_group` in
  `signal_events.csv` is the approach id as well: the state of the approach's main signal head, i.e. of
  its straight movement (`thesis_sumo.sim.outputs.signal_events` checks that all straight links agree).
- Signal states are `G` (green, incl. SUMO's yielding `g`), `y` (yellow) and `r` (everything else that
  stops traffic: red, red-yellow) -- `normalise_state`.
- `vclass` is `car` or `moto` (`moto_violator` vehicles are motorcycles: `moto`; `car_violator` ones are `car`).
- Cycles, per approach: a **green onset** is a change of the approach's state to `G` from a non-`G`
  state; the first state of a record is never an onset (it only tells the state at the start of the
  window). Cycle `k` (0-based) is `[onset_k, onset_{k+1})`; times before the first onset are cycle `-1`
  (partial, metrics drop it). See `green_onsets`, `cycle_id_at`, `cycle_table`.

box_queue (binding for the simulation converter and the proxy-data generator alike), for each approach
with an illegal left (`illegal_l`), whose through green must overlap the opposing approach's through green:

- one row per end of the opposing approach's through green (its G -> y/r change); `t` = that time;
  `cycle_id` = the illegal-left approach's cycle at `t`;
- `n_waiting_in_box` = halting (speed < 5 km/h) illegal-left vehicles inside the box at `t`;
- `t_clear_start` / `t_clear_end` = first / last box exit among ALL illegal-left vehicles that entered the
  box during that cycle, including those that left early through gaps, so `t_clear_start` may precede `t`;
  NaN `t_clear_start` = no such vehicle left the box; NaN `t_clear_end` (with a `t_clear_start`) = one of
  them is still in the box when the record ends. A vehicle that vanishes from the box (simulation:
  teleport/removal) is left out of both clearing times.

traversals (tier-1 extension of PLAN 5.1, one row per stop-line crossing, `track_id` as in
stopline_crossings): `movement` in `MOVEMENTS`; `exit_approach` = approach id of the arm the vehicle leaves
by; `lat_m_at_stopline` = `lane_or_lat_m` of its crossing; `t_range_entry` = time its front crosses
`observation.queue_range_m` upstream of the stop line (NaN if first seen inside that range);
`t_stopline` = crossing time; `t_exit` = time its front enters the outbound lane (NaN if not before the
record ends). Supports M6 (traversal time) and M8 (lane vs movement).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# PLAN 5.1 columns, in order (+ traversals)
TURN_COUNT_COLUMNS = ["interval_start", "interval_end", "approach", "movement", "vclass", "count"]
SIGNAL_EVENT_COLUMNS = ["t", "approach_group", "state"]
STOPLINE_CROSSING_COLUMNS = ["t", "approach", "lane_or_lat_m", "vclass", "track_id", "signal_state_at_t"]
QUEUE_SNAPSHOT_COLUMNS = ["cycle_id", "t_green_onset", "approach", "queue_length_m", "n_car", "n_moto", "area_m2"]
LATERAL_SNAPSHOT_COLUMNS = ["cycle_id", "approach", "track_id", "vclass", "lat_m", "long_m_from_stopline"]
BOX_QUEUE_COLUMNS = ["cycle_id", "t", "approach", "n_waiting_in_box", "t_clear_start", "t_clear_end"]
TRAVERSAL_COLUMNS = ["track_id", "vclass", "approach", "movement", "exit_approach", "lat_m_at_stopline",
                     "t_range_entry", "t_stopline", "t_exit"]

TABLES: dict[str, list[str]] = {
    "turn_counts": TURN_COUNT_COLUMNS,
    "signal_events": SIGNAL_EVENT_COLUMNS,
    "stopline_crossings": STOPLINE_CROSSING_COLUMNS,
    "queue_snapshots": QUEUE_SNAPSHOT_COLUMNS,
    "lateral_snapshots": LATERAL_SNAPSHOT_COLUMNS,
    "box_queue": BOX_QUEUE_COLUMNS,
    "traversals": TRAVERSAL_COLUMNS,  # tier-1 extension of PLAN 5.1 (derived)
}

INTERVAL_S = 900  # turn_counts bin: 15 min
MOVEMENTS = ("l", "s", "r", "u", "illegal_l")
VCLASSES = ("car", "moto")
SIGNAL_STATES = ("G", "y", "r")
# SUMO tlLogic state characters (sumo.dlr.de/docs/Simulation/Traffic_Lights.html#signal_state_definitions)
SUMO_STATE_TO_SCHEMA = {"G": "G", "g": "G", "y": "y", "Y": "y", "r": "r", "R": "r", "u": "r", "s": "r"}


def normalise_state(sumo_char: str) -> str:
    """SUMO link state character -> schema state G/y/r; off states (o, O) are not expected and raise."""
    try:
        return SUMO_STATE_TO_SCHEMA[sumo_char]
    except KeyError:
        raise ValueError(f"signal state {sumo_char!r} has no schema state (known: {sorted(SUMO_STATE_TO_SCHEMA)})") from None


def green_onsets(signal_events: pd.DataFrame, approach_group: str) -> np.ndarray:
    """Sorted green-onset times of `approach_group` (state changes to G; the first record is not one)."""
    ev = signal_events[signal_events["approach_group"] == approach_group].sort_values("t", kind="stable")
    prev = ev["state"].shift()
    return ev.loc[(ev["state"] == "G") & prev.notna() & (prev != "G"), "t"].to_numpy(dtype=float)


def cycle_id_at(onsets: np.ndarray, t) -> np.ndarray:
    """Cycle id of each time in `t` given the green onsets of one approach (-1 before the first onset)."""
    return np.searchsorted(np.asarray(onsets, dtype=float), np.asarray(t, dtype=float), side="right") - 1


def cycle_table(signal_events: pd.DataFrame, approach_group: str) -> pd.DataFrame:
    """One row per cycle of `approach_group`: cycle_id, t_green_onset, t_yellow_onset, t_red_onset,
    t_next_green_onset (NaN where the record ends before that change: an incomplete cycle)."""
    ev = signal_events[signal_events["approach_group"] == approach_group].sort_values("t", kind="stable")
    onsets = green_onsets(signal_events, approach_group)
    rows = []
    for k, t0 in enumerate(onsets):
        t1 = onsets[k + 1] if k + 1 < len(onsets) else np.nan
        inside = ev[(ev["t"] > t0) & ~(ev["t"] >= t1)]
        first = {s: inside.loc[inside["state"] == s, "t"].min() for s in ("y", "r")}
        rows.append({"cycle_id": k, "t_green_onset": t0, "t_yellow_onset": first["y"],
                     "t_red_onset": first["r"], "t_next_green_onset": t1})
    return pd.DataFrame(rows, columns=["cycle_id", "t_green_onset", "t_yellow_onset", "t_red_onset",
                                       "t_next_green_onset"])

