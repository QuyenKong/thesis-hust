"""G0: GEH gate on the 15-min turn counts (PLAN 5.2; gate only, not part of the score).

A cell is (interval_start, approach, movement, vclass) of `turn_counts` with the whole interval inside the window
(default [0, experiment.yaml sim.calib_end_s), ruling R31: the two 15-min bins of 0-1800 s). Cells missing on one
side count 0 there. GEH = sqrt(2 (m - c)^2 / (m + c)) on the 15-min counts themselves, as PLAN states it and as the
Task 4b operator diagnostic did (an hourly-rate version, counts x 4, would double every GEH); 0 when both are 0. The
run passes when the share of cells with GEH < threshold is at least min_share (experiment.yaml score.geh_gate).
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from thesis_sumo.config import load_experiment

KEY = ["interval_start", "approach", "movement", "vclass"]


def geh(m: float, c: float) -> float:
    return 0.0 if m + c == 0 else math.sqrt(2.0 * (m - c) ** 2 / (m + c))


def cells(sim: dict, obs: dict, window: tuple[float, float]) -> pd.DataFrame:
    """KEY columns, count_sim, count_obs, geh of every cell inside `window`."""
    w0, w1 = window

    def inside(tc: pd.DataFrame) -> pd.Series:
        tc = tc[(tc["interval_start"] >= w0) & (tc["interval_end"] <= w1)]
        return tc.groupby(KEY)["count"].sum()

    j = pd.concat({"count_sim": inside(sim["turn_counts"]), "count_obs": inside(obs["turn_counts"])}, axis=1)
    j = j.fillna(0.0).reset_index()
    j["geh"] = [geh(m, c) for m, c in zip(j["count_sim"], j["count_obs"])]
    return j


def _defaults(threshold, min_share, window):
    if threshold is None or min_share is None or window is None:
        exp = load_experiment()
        gate_cfg = (exp.get("score") or {}).get("geh_gate") or {}
        threshold = gate_cfg.get("threshold") if threshold is None else threshold
        min_share = gate_cfg.get("min_share") if min_share is None else min_share
        if window is None:
            window = (float(exp["sim"]["begin_s"]), float(exp["sim"]["calib_end_s"]))
        if threshold is None or min_share is None:
            raise ValueError("experiment.yaml score.geh_gate.threshold / min_share is null")
    return float(threshold), float(min_share), (float(window[0]), float(window[1]))


def gate(sim: dict, obs: dict, threshold: float | None = None, min_share: float | None = None,
         window: tuple[float, float] | None = None) -> tuple[bool, float]:
    """(passes, share of cells with GEH < threshold) of one simulation run against its observed day."""
    threshold, min_share, window = _defaults(threshold, min_share, window)
    j = cells(sim, obs, window)
    if not len(j):
        raise ValueError(f"no turn-count cells inside the G0 window {window}")
    share = float(np.mean(j["geh"].to_numpy() < threshold))
    return share >= min_share, share
