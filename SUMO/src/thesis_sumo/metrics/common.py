"""Shared pieces of the metrics M1-M8 (PLAN 5.2): the value type, the context (window, observed range, site) and
table helpers. Every metric runs unchanged on observed days (`data/observed/<day>/`) and on simulation output
converted by `thesis_sumo.sim.outputs.to_observed_schema` (`<run_dir>/observed_schema/`).

Window (ruling R31): a metric only uses events whose own time lies in `MetricContext.window` = [w0, w1)
(`experiment.yaml observation.metric_window_s`, [300, 1800) s: 300 s warm-up, calibration runs end at 1800 s), on
both sides. The event time is the green onset (M1 discharge, M2 first-crossing delay, M4, M5, M7c), the stop-line
crossing (M2/M3 shares, M6, M8) or the box_queue row time `t` (M7a/b); a cycle (M3 per-cycle counts) must lie
inside the window. Green onsets at or after w1 are ignored, so a simulation that ends at w1 and an observed day that
goes on are cut the same way.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from thesis_sumo.config import Site, load_experiment, load_site
from thesis_sumo.schema_observed import TABLES, cycle_id_at, green_onsets

OBSERVED_DIR = "observed_schema"  # thesis_sumo.sim.outputs.OBSERVED_DIR (not imported: that pulls sumolib)


@dataclass
class MetricValue:
    """One (sub-)metric of one table set. `kind` "dist": `values` is the event sample (np.ndarray, may be empty);
    "scalar": `values` is a float (NaN = undefined, e.g. a share without any vehicle). `target` is the targets.yaml
    key (`<group>.<name>`) whose evidence label the metric reports (ruling R13); `scored` False = reported only."""

    kind: str
    values: np.ndarray | float
    label: str
    unit: str
    target: str | None = None
    scored: bool = True

    def __post_init__(self):
        if self.kind == "dist":
            self.values = np.asarray(self.values, dtype=float).ravel()
            self.values = self.values[~np.isnan(self.values)]
        elif self.kind == "scalar":
            self.values = float(self.values)
        else:
            raise ValueError(f"MetricValue kind must be 'dist' or 'scalar', got {self.kind!r}")

    @property
    def n(self) -> int:
        """Number of events (dist) or 1/0 for a defined/undefined scalar."""
        return int(self.values.size) if self.kind == "dist" else int(not np.isnan(self.values))

    @property
    def empty(self) -> bool:
        return self.n == 0

    def mean(self) -> float:
        if self.empty:
            return float("nan")
        return float(np.mean(self.values)) if self.kind == "dist" else self.values


def dist(values, label: str, unit: str, target: str | None, scored: bool = True) -> MetricValue:
    return MetricValue("dist", values, label, unit, target, scored)


def scalar(value, label: str, unit: str, target: str | None, scored: bool = True) -> MetricValue:
    return MetricValue("scalar", value, label, unit, target, scored)


def share(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else float("nan")


@dataclass(frozen=True)
class MetricContext:
    """`window` [w0, w1) s; `queue_range_m` = experiment.yaml observation.queue_range_m (M5 censoring); `site` = the
    site file (M8 lane widths and lane markings). None = the measured config/site.yaml, read when M8 needs it, so a
    null lane value raises MissingFieldDataError (never a fallback to the proxy)."""

    window: tuple[float, float]
    queue_range_m: float
    site: Site | None = None

    def __post_init__(self):
        w0, w1 = (float(x) for x in self.window)
        if not w0 < w1:
            raise ValueError(f"metric window {self.window} is empty")
        object.__setattr__(self, "window", (w0, w1))

    @classmethod
    def from_config(cls, experiment: dict | None = None, site: Site | None = None,
                    window: tuple[float, float] | None = None) -> "MetricContext":
        exp = experiment if experiment is not None else load_experiment()
        obs = exp.get("observation") or {}
        for key in ("metric_window_s", "queue_range_m"):
            if obs.get(key) is None and not (key == "metric_window_s" and window is not None):
                raise ValueError(f"experiment config observation.{key} is missing or null")
        return cls(window=tuple(window if window is not None else obs["metric_window_s"]),
                   queue_range_m=float(obs["queue_range_m"]), site=site)

    def require_site(self) -> Site:
        return self.site if self.site is not None else load_site()

    def lanes(self, approach: str) -> tuple[np.ndarray, list[list[str]]]:
        """(cumulative lane widths from the right edge, permitted movements per lane) of an approach."""
        site = self.require_site()
        ids = [a.get("id") for a in site.require("approaches")]
        if approach not in ids:
            raise ValueError(f"approach {approach!r} is not in {site.path} (approaches {ids})")
        i = ids.index(approach)
        widths = site.require(f"approaches.{i}.lane_widths_m")
        movements = site.require(f"approaches.{i}.lane_movements")
        if len(widths) != len(movements):
            raise ValueError(f"{site.path} approach {approach}: {len(movements)} lane_movements for {len(widths)} lanes")
        return np.cumsum(np.asarray(widths, dtype=float)), [list(m) for m in movements]

    def in_window(self, t) -> np.ndarray:
        t = np.asarray(t, dtype=float)
        return (t >= self.window[0]) & (t < self.window[1])


def read_tables(path: Path) -> dict[str, pd.DataFrame]:
    """The schema tables of an observed day directory or a run directory (its `observed_schema/`); each table is
    read from `<name>.csv` or `<name>.csv.gz`."""
    path = Path(path)
    if (path / OBSERVED_DIR).is_dir():
        path = path / OBSERVED_DIR
    out = {}
    for name in TABLES:
        f = next((p for p in (path / f"{name}.csv", path / f"{name}.csv.gz") if p.is_file()), None)
        if f is None:
            raise FileNotFoundError(f"{path}: no {name}.csv(.gz)")
        out[name] = pd.read_csv(f)
    return out


# ---------------------------------------------------------------- table helpers


def approaches(tables: dict) -> list[str]:
    return sorted(tables["signal_events"]["approach_group"].unique())


def onsets(tables: dict, approach: str, ctx: MetricContext) -> np.ndarray:
    """Green onsets of `approach` before the window end (all of them, also before the window start)."""
    on = green_onsets(tables["signal_events"], approach)
    return on[on < ctx.window[1]]


def red_onset_after(tables: dict, approach: str, t: float) -> float:
    """First change of `approach` to `r` after `t` (inf if none in the record)."""
    ev = tables["signal_events"]
    e = ev[(ev["approach_group"] == approach) & (ev["state"] == "r") & (ev["t"] > t)]
    return float(e["t"].min()) if len(e) else np.inf


def crossings(tables: dict) -> pd.DataFrame:
    """stopline_crossings with the vehicle's movement (from traversals, same track_id)."""
    cr = tables["stopline_crossings"]
    mv = tables["traversals"].set_index("track_id")["movement"]
    return cr.assign(movement=cr["track_id"].map(mv)).sort_values(["t", "track_id"], kind="stable")


def opposing(approach: str, all_approaches) -> str:
    """The opposing approach: the only other approach on the same road (`<ROAD>_<side>`), as in sim.outputs and the
    proxy generator."""
    same = [a for a in all_approaches if a != approach and a.split("_")[0] == approach.split("_")[0]]
    if len(same) != 1:
        raise ValueError(f"approach {approach}: no unique opposing approach (same road prefix) in {list(all_approaches)}")
    return same[0]


def cycle_of(tables: dict, approach: str, t, ctx: MetricContext) -> np.ndarray:
    return cycle_id_at(onsets(tables, approach, ctx), t)
