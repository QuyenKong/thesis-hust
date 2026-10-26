"""Literature-proxy observed days PROXY_D1..D5 in the PLAN 5.1 schema (spec 4.2 and item 8).

    .venv/Scripts/python -m thesis_sumo.proxy.generate        # D1-D5 (seeds 101-105) + routes_PROXY_D*.rou.xml

**LITERATURE PROXY, not field data.** The days stand in for video until it exists; every number comes from
`data/proxy/targets.yaml` (each with `source` / `evidence`). The generator never reads SUMO output: its inputs are
the targets, the site file (signal plan, approaches, lane widths, lane markings `lane_movements`, bans, illegal-left
approaches), `scenario/net/edge_table.csv` (which arm each movement leaves by) and
`experiment.yaml observation.queue_range_m`. The tables follow the definitions of `thesis_sumo.schema_observed`
and `thesis_sumo.sim.outputs` (same columns, units, signs, cycles, box_queue rule R11), so the metrics run on both.

Event model, per approach (one draw per vehicle; day-level means scaled by a lognormal day factor per target,
which the CLI normalises to mean 1 over D1-D5, `campaign_day_factors`):
- arrivals at the range entry (`queue_range_m` upstream): Poisson per vclass x movement x 15-min bin; illegal-left
  motorcycles per cycle (negative binomial) instead, timed so they reach the stop line before the opposing green
  ends. Unimpeded approach speed -> time the vehicle would reach the stop line (`t_reach`).
- per cycle: vehicles reaching the line from the end of the previous yellow use to green onset face red. Red
  runners (count per cycle and vclass, NB) cross in red: right after the yellow ("late") or in mid-red in
  clusters. Early starters (NB) are the front of the queue and cross 4-10 s before green. The rest wait: motorcycles
  overshoot the stop line with a probability and wait at the front; the queue behind the line is packed by area
  (position = cumulative footprint / width of the signal-controlled lanes, `Approach.queue_width`). Discharge starts `first_crossing_delay` after green (plus the
  M7c box effect on the crossing road) with headways `h_sat[vclass] * ramp(position) * lognormal noise`;
  vehicles arriving in green cross at max(arrival, previous crossing + headway); after yellow use, they wait.
- continuous right-turn lane (`continuous_right_lane: true`, PLAN 0): right-turners of that approach are not
  signal controlled. They cross at `t_reach` (unimpeded), never queue and are never drawn as red runners or early
  starters; the red-run / early-start counts per cycle use the approach's rate without them (the M2/M3 shares are
  over the signal-controlled vehicles, as the metrics count them).
- lateral position: lane from the movement and `lane_movements` (turning vehicles in a non-permitting lane with
  `wrong_lane_share`; illegal lefts from the leftmost lane), uniform within the lane band (motorcycles) or normal
  around the lane centre (cars); kept from the queue to the stop line.
- exit: `path_length_m[movement] / crossing speed` after the stop line. Illegal lefts wait in the box: a share
  leaves early through gaps; the others leave `clear_lag` after max(opposing green end, last opposing straight
  crossing) and then one per `box_exit_headway`. Halting box waiters at a green onset of their approach are in
  that onset's lateral snapshot, as in sim.outputs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from thesis_sumo.config import REPO_ROOT, Site, load_experiment, load_site
from thesis_sumo.schema_observed import INTERVAL_S, TABLES, VCLASSES, cycle_id_at, green_onsets
from thesis_sumo.sim.outputs import TIME_DECIMALS, queue_range_m

TARGETS_PATH = REPO_ROOT / "data" / "proxy" / "targets.yaml"
PROXY_SITE = REPO_ROOT / "config" / "site.proxy.yaml"
EDGE_TABLE = REPO_ROOT / "scenario" / "net" / "edge_table.csv"
OBSERVED_ROOT = REPO_ROOT / "data" / "observed"
DEMAND_DIR = REPO_ROOT / "scenario" / "demand"
DAY_SEEDS = {f"PROXY_D{k}": 100 + k for k in range(1, 6)}  # spec item 10: independent seed per day
HALT_LEAD_S = 3.0  # a box entrant halts (speed < 5 km/h) once it has been in the box this long
TURNING = ("r", "l", "u")
SITE_DIR = {"r": "r", "s": "s", "l": "l", "t": "u"}  # edge_table connection dir -> turn_counts movement
LAT_DECIMALS = 2


# ---------------------------------------------------------------- sampling helpers


def _lognormal(rng, mean: float, cv: float) -> float:
    if cv <= 0:
        return float(mean)
    s2 = math.log1p(cv * cv)
    return float(rng.lognormal(math.log(mean) - s2 / 2, math.sqrt(s2)))


def _count(rng, mean: float, var_to_mean: float) -> int:
    """Negative binomial count with the given mean and variance/mean (Poisson when var/mean <= 1)."""
    if mean <= 0:
        return 0
    if var_to_mean <= 1:
        return int(rng.poisson(mean))
    return int(rng.negative_binomial(mean / (var_to_mean - 1), 1 / var_to_mean))


def _scale(value, f: float):
    if isinstance(value, dict):
        return {k: _scale(v, f) for k, v in value.items()}
    if isinstance(value, list):
        return [_scale(v, f) for v in value]
    return value * f if isinstance(value, (int, float)) and not isinstance(value, bool) else value


def draw_day_factors(targets: dict, seed: int) -> dict[str, float]:
    """One day's raw factor per target (lognormal, mean 1, cv `between_day_cv`; 1 where cv is 0), drawn from the
    first child of the day's seed (the second child drives the events)."""
    rng = np.random.default_rng(np.random.SeedSequence(seed).spawn(2)[0])
    out = {}
    for group, items in targets["targets"].items():
        for name, item in items.items():
            cv = float(item.get("between_day_cv") or 0.0)
            out[f"{group}.{name}"] = _lognormal(rng, 1.0, cv) if cv > 0 else 1.0
    return out


def campaign_day_factors(targets: dict, day_seeds: dict[str, int]) -> dict[str, dict[str, float]]:
    """Day factors of a set of days, each drawn from its own seed and then divided by the mean over the days, so
    the days' mean of every target equals its targets.yaml value by construction; the between-day spread is kept
    (the CV of the factors is unchanged by the common rescaling)."""
    raw = {d: draw_day_factors(targets, s) for d, s in day_seeds.items()}
    keys = next(iter(raw.values())).keys()
    mean = {k: float(np.mean([raw[d][k] for d in raw])) for k in keys}
    return {d: {k: raw[d][k] / mean[k] for k in keys} for d in raw}


class Params:
    """Day-level values of the targets: `value` x the day's factor (`draw_day_factors` / `campaign_day_factors`)."""

    def __init__(self, targets: dict, factor: dict[str, float]):
        self.items = targets["targets"]
        self.geometry = targets["geometry"]
        self.factor = dict(factor)

    def item(self, key: str) -> dict:
        group, name = key.split(".")
        return self.items[group][name]

    def __call__(self, key: str):
        value = self.item(key)["value"]
        if value is None:
            raise ValueError(f"target {key} has no value (derived targets are outputs, not inputs)")
        return _scale(value, self.factor[key])


# ---------------------------------------------------------------- site: approaches and signal


@dataclass
class Approach:
    id: str
    widths: list[float]
    lane_movements: list[list[str]]
    movements: list[str]                 # turn_counts movement codes of this approach
    exit_arm: dict[str, str]             # movement -> approach id of the arm it leaves by
    continuous_right: bool = False       # right turn not signal controlled (site continuous_right_lane)
    edges: np.ndarray = field(init=False)

    def __post_init__(self):
        self.edges = np.concatenate([[0.0], np.cumsum(self.widths)])

    @property
    def width(self) -> float:
        return float(self.edges[-1])

    @property
    def queue_width(self) -> float:
        """Width the signal queue spreads over: without the continuous right lane(s) (marked [r] only), which
        right-turners pass without queueing. `area_m2` stays length x roadway width, as on the sim side."""
        skip = self.continuous_right
        return float(sum(w for w, m in zip(self.widths, self.lane_movements) if not (skip and list(m) == ["r"])))


def approaches_of(site: Site, edge_table: Path = EDGE_TABLE) -> dict[str, Approach]:
    """Approaches with their movements (bans and illegal lefts from the site file) and exit arms (edge table)."""
    et = pd.read_csv(edge_table, dtype=str).set_index("edge_id")
    illegal = set(site.require("illegal_left.approaches"))
    arm_of = {}  # compass side -> approach id
    for i, a in enumerate(site.require("approaches")):
        arm_of[et.loc[site.require(f"approaches.{i}.edge"), "direction"].removeprefix("in from ")] = a["id"]
    out = {}
    for i, a in enumerate(site["approaches"]):
        key = f"approaches.{i}"
        conns = {}
        for part in str(et.loc[a["edge"], "connections"]).split():
            d, rest = part.split(">", 1)
            to_edge = rest.split("[", 1)[0]
            conns[SITE_DIR[d]] = arm_of[et.loc[to_edge, "direction"].removeprefix("out to ")]
        mv_exit = {m: conns[m] for m in ("r", "s") if m in conns}
        if "u" in conns and not site.require(f"{key}.u_turn_banned"):
            mv_exit["u"] = conns["u"]
        if "l" in conns:
            if not site.require(f"{key}.left_turn_banned"):
                mv_exit["l"] = conns["l"]
            elif a["id"] in illegal:
                mv_exit["illegal_l"] = conns["l"]
        lanes = site.require(f"{key}.lane_movements")
        widths = site.require(f"{key}.lane_widths_m")
        if len(lanes) != len(widths):
            raise ValueError(f"approach {a['id']}: {len(lanes)} lane_movements for {len(widths)} lanes")
        legal = {m for m in mv_exit if m != "illegal_l"}
        if {m for lane in lanes for m in lane} != legal:
            raise ValueError(f"approach {a['id']}: lane_movements {lanes} do not cover exactly its movements "
                             f"{sorted(legal)}")
        out[a["id"]] = Approach(a["id"], [float(w) for w in widths], lanes, list(mv_exit), mv_exit,
                                bool(site.require(f"{key}.continuous_right_lane")))
    return out


def signal_segments(site: Site, approaches) -> tuple[float, dict[str, list[tuple[float, str]]]]:
    """Cycle length and, per approach, the (offset, state) segments of one cycle (state of its straight movement)."""
    cycle = float(site.require("signal.cycle_s"))
    seg: dict[str, list[tuple[float, str]]] = {a: [] for a in approaches}
    t = 0.0
    for p in site.require("signal.phases"):
        for a in approaches:
            s = "G" if f"{a}:s" in p["green_movements"] else "y" if f"{a}:s" in (p["yellow_movements"] or []) else "r"
            if not seg[a] or seg[a][-1][1] != s:
                seg[a].append((t, s))
        t += float(p["duration_s"])
    if not math.isclose(t, cycle):
        raise ValueError(f"signal phases sum to {t} s, cycle_s is {cycle} s")
    return cycle, seg


def signal_events_table(cycle: float, seg: dict, window: float) -> pd.DataFrame:
    """signal_events: the state of every group at t=0, then one row per change (schema_observed)."""
    rows = []
    for a, parts in seg.items():
        last = None
        for c in range(int(math.ceil(window / cycle)) + 1):
            for t0, s in parts:
                t = c * cycle + t0
                if t < window and s != last:
                    rows.append((round(t, TIME_DECIMALS), a, s))
                    last = s
    ev = pd.DataFrame(rows, columns=TABLES["signal_events"])
    return ev.sort_values(["t", "approach_group"], kind="stable").reset_index(drop=True)


@dataclass
class Cycles:
    """Green onset / yellow onset / red onset of cycle j of one approach (single green per cycle)."""

    cycle: float
    g0: float
    y0: float
    r0: float
    yellow_use: float

    @classmethod
    def of(cls, cycle: float, parts: list[tuple[float, str]], yellow_use: float) -> "Cycles":
        greens = [i for i, (_, s) in enumerate(parts) if s == "G"]
        if len(greens) != 1:
            raise ValueError(f"expected one green per cycle, got segments {parts}")
        i = greens[0]
        g0 = parts[i][0]
        unrolled = [(t if t >= g0 else t + cycle, s) for t, s in parts[i + 1:] + parts[:i]]
        if not unrolled:
            raise ValueError(f"approach is green for the whole cycle: {parts}")
        y0 = unrolled[0][0]
        r0 = next((t for t, s in unrolled if s == "r"), g0 + cycle)
        return cls(cycle, g0, y0, r0, yellow_use)

    def g(self, j):
        return j * self.cycle + self.g0

    def y(self, j):
        return j * self.cycle + self.y0

    def r(self, j):
        return j * self.cycle + self.r0

    def stop(self, j):
        """Last time a vehicle reaching the stop line in cycle j still crosses legally (yellow use)."""
        return min(self.y(j) + self.yellow_use, self.r(j))


# ---------------------------------------------------------------- vehicles


@dataclass(slots=True)
class Veh:
    id: str
    approach: str
    vclass: str
    movement: str
    t_range: float     # front crosses the range entry
    t_reach: float     # would reach the stop line unimpeded
    lat: float
    t_cross: float = math.nan
    t_exit: float = math.nan
    box_long: float = math.nan  # long_m_from_stopline while waiting in the box (illegal lefts)


def _lane_lat(rng, ap: Approach, vclass: str, movement: str, p: Params) -> float:
    n = len(ap.widths)
    if movement == "illegal_l":
        lanes = [n - 1]  # leftmost lane (assumed)
    else:
        ok = [i for i, mv in enumerate(ap.lane_movements) if movement in mv]
        bad = [i for i in range(n) if i not in ok]
        lanes = bad if movement in TURNING and bad and rng.random() < p("M8_wrong_lane.wrong_lane_share")[vclass] else ok
    i = lanes[int(rng.integers(len(lanes)))]
    lo, hi = ap.edges[i], ap.edges[i + 1]
    if vclass == "car":
        half = 0.9  # car width 1.8 m: the centre stays inside the lane
        return float(np.clip(rng.normal((lo + hi) / 2, p("M4_lateral.car_lateral_sd_m")), lo + half, hi - half))
    m = p("M4_lateral.moto_lateral_margin_m")
    return float(rng.uniform(lo + m, hi - m))


def _speed_ms(rng, key: str, vclass: str, p: Params, lo: float, hi: float) -> float:
    mean, sd = p(key)[vclass], p.item(key)["sd"][vclass]
    return float(np.clip(rng.normal(mean, sd), lo, hi)) / 3.6


class _Ids:
    def __init__(self):
        self.n = {}

    def __call__(self, app: str) -> str:
        self.n[app] = self.n.get(app, 0) + 1
        return f"{app}_{self.n[app]:05d}"


def _legal_rates(ap: Approach, p: Params, cyc: Cycles) -> dict[tuple[str, str], float]:
    """(vclass, movement) -> arrivals per second (before the 15-min profile) of legal movements."""
    vol = p("G0_counts.approach_volume_veh_h")[ap.id]
    ms = min(p("G0_counts.moto_share"), 1.0)
    split = p("G0_counts.movement_split")["banned_left" if "l" not in ap.movements else "legal"]
    legal = [m for m in ap.movements if m != "illegal_l"]
    if set(split) != set(legal):
        raise ValueError(f"{ap.id}: movement_split {sorted(split)} does not match movements {sorted(legal)}")
    total = sum(split.values())
    moto = vol * ms
    if "illegal_l" in ap.movements:
        moto -= _box_entrants_mean(p) * 3600 / cyc.cycle
        if moto <= 0:
            raise ValueError(f"{ap.id}: illegal lefts exceed the motorcycle volume")
    return {(vc, m): (moto if vc == "moto" else vol * (1 - ms)) * split[m] / total / 3600
            for vc in VCLASSES for m in legal}


def _box_entrants_mean(p: Params) -> float:
    return p("M7_illegal_left.n_waiting_in_box") / (1 - p("M7_illegal_left.early_leave_share"))


def arrivals(rng, ap: Approach, p: Params, cyc: Cycles, t0: float, window: float, range_m: float,
             ids: _Ids, opposing_end) -> list[Veh]:
    """All vehicles of an approach that reach the range entry from t0 to the end of the window."""
    profile = p("G0_counts.profile_15min")
    bins = [(t0, 0.0, profile[0])] + [(b * INTERVAL_S, (b + 1) * INTERVAL_S, profile[b])
                                      for b in range(int(math.ceil(window / INTERVAL_S)))]
    out = []
    for (vc, m), rate in _legal_rates(ap, p, cyc).items():
        for lo, hi, f in bins:
            hi = min(hi, window)
            n = int(rng.poisson(rate * f * (hi - lo)))
            for t in np.sort(rng.uniform(lo, hi, n)):
                v = _speed_ms(rng, "M6_traversal.approach_speed_kmh", vc, p, 10, 50)
                out.append(Veh(ids(ap.id), ap.id, vc, m, float(t), float(t) + range_m / v, _lane_lat(rng, ap, vc, m, p)))
    if "illegal_l" in ap.movements:
        mean, vm = _box_entrants_mean(p), p("M7_illegal_left.entrants_var_to_mean")
        j = int(math.floor((t0 - cyc.g0) / cyc.cycle))
        while cyc.stop(j - 1) < window:
            lo, hi = max(cyc.stop(j - 1), t0 + range_m / (10 / 3.6)), opposing_end(j) - HALT_LEAD_S - 0.5
            for t_reach in np.sort(rng.uniform(lo, hi, _count(rng, mean, vm))):
                v = _speed_ms(rng, "M6_traversal.approach_speed_kmh", "moto", p, 10, 50)
                out.append(Veh(ids(ap.id), ap.id, "moto", "illegal_l", float(t_reach) - range_m / v, float(t_reach),
                               _lane_lat(rng, ap, "moto", "illegal_l", p)))
            j += 1
    out.sort(key=lambda v: (v.t_reach, v.id))
    return out


# ---------------------------------------------------------------- queue model


def _headway(rng, p: Params, vclass: str, position: int | None) -> float:
    h = p("M1_headway.moto_saturation_headway_s") * (p("M1_headway.car_headway_factor") if vclass == "car" else 1.0)
    if position is not None:
        ramp = p("M1_headway.startup_ramp")
        h *= 1 + ramp["a"] * math.exp(-(position - 2) / ramp["b"])
    return h * _lognormal(rng, 1.0, p.item("M1_headway.moto_saturation_headway_s")["cv"])


def _mid_red_end(cyc: Cycles, j: int, p: Params) -> float:
    """Red runners of the red before green j cross before this (later red crossings are early starts)."""
    return cyc.g(j) - p("M3_red_running.early_start_exclusion_s") - 0.01


def _red_runners(rng, cand: list[Veh], n: int, p: Params, cyc: Cycles, j: int) -> None:
    """Give `n` of `cand` (one vclass, reaching the line in the red before green j) a red-phase crossing."""
    vc = cand[0].vclass
    lw = p("M3_red_running.late_window_s")
    r_prev, hi = cyc.r(j - 1), _mid_red_end(cyc, j, p)
    chosen = sorted((cand[i] for i in rng.choice(len(cand), n, replace=False)), key=lambda v: (v.t_reach, v.id))
    mid = []
    for v in chosen:
        if v.t_reach < r_prev + lw and rng.random() < p("M3_red_running.late_share")[vc]:
            v.t_cross = max(v.t_reach, r_prev + rng.uniform(0, lw))
        else:
            mid.append(v)
    size, gap = p("M3_red_running.mid_red_cluster_size"), p("M3_red_running.cluster_gap_s")
    k = 0
    while k < len(mid):
        group = mid[k:k + 1 + int(rng.poisson(max(size - 1, 0)))]
        k += len(group)
        offsets = np.concatenate([[0.0], np.cumsum(rng.exponential(gap, len(group) - 1))])
        lo = max(max(v.t_reach for v in group), r_prev + lw)
        start = rng.uniform(lo, max(lo, hi - offsets[-1]))
        for v, o in zip(group, offsets):
            v.t_cross = float(min(max(start + o, v.t_reach), hi))


@dataclass
class Snapshot:
    t: float
    rows: list[tuple[Veh, float]]  # (vehicle, long_m_from_stopline) of the queue at green onset


def serve(rng, ap: Approach, vehicles: list[Veh], cyc: Cycles, p: Params, window: float,
          start_extra=lambda g: 0.0) -> list[Snapshot]:
    """Assign `t_cross` to the vehicles of one approach (cycle by cycle); return the queue at each green onset."""
    a = ap.id
    excl = p("M3_red_running.early_start_exclusion_s")
    lead = p("M2_early_start.early_start_lead_s")
    vm = p("M3_red_running.per_cycle_var_to_mean")
    for v in vehicles:
        if ap.continuous_right and v.movement == "r":
            v.t_cross = v.t_reach  # continuous right turn: not signal controlled, never queues
    vehicles = [v for v in vehicles if math.isnan(v.t_cross)]
    rates = {}
    for (vc, m), r in _legal_rates(ap, p, cyc).items():
        if not (ap.continuous_right and m == "r"):
            rates[vc] = rates.get(vc, 0.0) + r
    area = {"moto": p("M5_queue.moto_area_m2"), "car": p("M5_queue.car_area_m2")}
    depth = p("M4_lateral.overshoot_depth_m")
    snaps, carry, i = [], [], 0
    j = int(math.floor((vehicles[0].t_reach - cyc.g0) / cyc.cycle)) if vehicles else 0
    while cyc.stop(j - 1) < window:  # also the red before the first green after the window (red crossings in it)
        g = cyc.g(j)
        red = []
        while i < len(vehicles) and vehicles[i].t_reach < g:
            red.append(vehicles[i])
            i += 1
        for vc in VCLASSES:
            cand = [v for v in red if v.vclass == vc and v.movement != "illegal_l" and v.t_reach < _mid_red_end(cyc, j, p)]
            n = min(_count(rng, p("M3_red_running.red_run_share")[a][vc] * rates[vc] * cyc.cycle, vm), len(cand))
            if n:
                _red_runners(rng, cand, n, p, cyc, j)
        queue = carry + [v for v in red if math.isnan(v.t_cross)]
        for vc in VCLASSES:
            cand = [v for v in queue if v.vclass == vc and v.movement != "illegal_l" and v.t_reach <= g - lead["low"]]
            n = min(_count(rng, p("M2_early_start.early_start_share")[a][vc] * rates[vc] * cyc.cycle, vm), len(cand))
            for v in cand[:n]:
                v.t_cross = max(g - rng.uniform(lead["low"], lead["high"]), v.t_reach)
        queue = [v for v in queue if math.isnan(v.t_cross)]
        over = [v.vclass == "moto" and rng.random() < p("M4_lateral.overshoot_share_moto") for v in queue]
        front = [v for v, o in zip(queue, over) if o]
        back = [v for v, o in zip(queue, over) if not o]
        rows, cum = [], 0.0
        for v in front:
            rows.append((v, min(-rng.uniform(depth["low"], depth["high"]), -0.01)))  # never -0.0 after rounding
        for v in back:
            rows.append((v, cum / ap.queue_width))
            cum += area[v.vclass]
        snaps.append(Snapshot(g, rows))
        t, carry, stop = math.nan, [], cyc.stop(j)
        for n, v in enumerate(front + back):
            t = (g + _lognormal(rng, p("M2_early_start.first_crossing_delay_s"),
                                p.item("M2_early_start.first_crossing_delay_s")["cv"]) + start_extra(g)
                 if n == 0 else t + _headway(rng, p, v.vclass, n + 1))
            if t >= stop or carry:
                carry.append(v)
            else:
                v.t_cross = t
        last = t if not math.isnan(t) else g
        while i < len(vehicles) and vehicles[i].t_reach < stop:
            v = vehicles[i]
            i += 1
            c = max(v.t_reach, last + _headway(rng, p, v.vclass, None))
            if c >= stop or carry:
                carry.append(v)
            else:
                v.t_cross = last = c
        j += 1
    return snaps


def exits(rng, vehicles: list[Veh], p: Params) -> None:
    path = p.geometry["path_length_m"]
    for v in vehicles:
        if v.movement != "illegal_l" and not math.isnan(v.t_cross):
            v.t_exit = v.t_cross + path[v.movement] / _speed_ms(rng, "M6_traversal.crossing_speed_kmh", v.vclass, p, 8, 45)


def box(rng, vehicles: list[Veh], cyc: Cycles, opposing_end, opp_straight: np.ndarray, p: Params) -> None:
    """Box exit times of the illegal lefts of one approach (cycle by cycle)."""
    viol = sorted((v for v in vehicles if v.movement == "illegal_l" and not math.isnan(v.t_cross)),
                  key=lambda v: (v.t_cross, v.id))
    by_cycle: dict[int, list[Veh]] = {}
    for v in viol:
        by_cycle.setdefault(int(math.floor((v.t_cross - cyc.g0) / cyc.cycle)), []).append(v)
    for j, ent in sorted(by_cycle.items()):
        t_e = opposing_end(j)
        stay = []
        for v in ent:
            room = t_e - 0.5 - v.t_cross - HALT_LEAD_S
            if room > 0 and rng.random() < p("M7_illegal_left.early_leave_share"):
                v.t_exit = v.t_cross + HALT_LEAD_S + rng.uniform(0, room)
            else:
                stay.append(v)
        for v in ent:
            share = p.geometry["box_wait_position_share"]
            v.box_long = -p.geometry["path_length_m"]["illegal_l"] * rng.uniform(share["low"], share["high"])
        if not stay:
            continue
        lag = _lognormal(rng, p("M7_illegal_left.clear_lag_s"), p.item("M7_illegal_left.clear_lag_s")["cv"])
        anchor = t_e
        while True:  # first exit = lag after the last opposing straight crossing before it (or the green end)
            first = anchor + lag
            k = int(np.searchsorted(opp_straight, first, side="left")) - 1
            if k < 0 or opp_straight[k] <= anchor:
                break
            anchor = float(opp_straight[k])
        t = first
        cv = p.item("M7_illegal_left.box_exit_headway_s")["cv"]
        for n, v in enumerate(stay):
            if n:
                t += _lognormal(rng, p("M7_illegal_left.box_exit_headway_s"), cv)
            v.t_exit = max(t, v.t_cross + HALT_LEAD_S)


def add_box_waiters(snaps: list[Snapshot], vehicles: list[Veh]) -> None:
    """Halting illegal lefts still in the box at a green onset of their approach join that onset's lateral
    snapshot (sim.outputs: every halting vehicle of the approach past the stop line on its internal lanes)."""
    viol = [v for v in vehicles if v.movement == "illegal_l" and not math.isnan(v.t_cross)]
    for s in snaps:
        s.rows += [(v, v.box_long) for v in viol if v.t_cross <= s.t - HALT_LEAD_S and not v.t_exit <= s.t]


# ---------------------------------------------------------------- tables


def _rt(x: float) -> float:
    return round(float(x), TIME_DECIMALS)


def box_queue_table(approach: str, opposing: str, ev: pd.DataFrame, tr: pd.DataFrame) -> pd.DataFrame:
    """box_queue rows (schema_observed, ruling R11) from the written traversals: halting = in the box for at least
    HALT_LEAD_S; an exit after the end of the window is NaN (still in the box)."""
    onsets = green_onsets(ev, approach)
    e = ev[ev["approach_group"] == opposing].sort_values("t", kind="stable")
    prev = e["state"].shift()
    ends = e.loc[(prev == "G") & (e["state"] != "G"), "t"].to_numpy(dtype=float)
    v = tr[(tr["approach"] == approach) & (tr["movement"] == "illegal_l")]
    cyc = cycle_id_at(onsets, v["t_stopline"])
    rows = []
    for t in ends:
        k = int(cycle_id_at(onsets, [t])[0])
        n_waiting = int(((v["t_stopline"] <= t - HALT_LEAD_S) & ~(v["t_exit"] <= t)).sum())
        ent = v[cyc == k]
        ex = ent["t_exit"].dropna()
        start = float(ex.min()) if len(ex) else np.nan
        end = np.nan if ent["t_exit"].isna().any() or not len(ex) else float(ex.max())
        rows.append((k, float(t), approach, n_waiting, start, end))
    return pd.DataFrame(rows, columns=TABLES["box_queue"])


def _tables(aps: dict[str, Approach], vehicles: list[Veh], snaps: dict[str, list[Snapshot]], ev: pd.DataFrame,
            illegal: dict[str, str], window: float, range_m: float, lengths: dict[str, float]) -> dict[str, pd.DataFrame]:
    seen = [v for v in vehicles if 0 <= v.t_cross < window]
    df = pd.DataFrame({
        "track_id": [v.id for v in seen], "vclass": [v.vclass for v in seen], "approach": [v.approach for v in seen],
        "movement": [v.movement for v in seen],
        "exit_approach": [aps[v.approach].exit_arm[v.movement] for v in seen],
        "lat_m_at_stopline": [round(v.lat, LAT_DECIMALS) for v in seen],
        "t_range_entry": [_rt(v.t_range) if v.t_range >= 0 else np.nan for v in seen],
        "t_stopline": [_rt(v.t_cross) for v in seen],
        "t_exit": [_rt(v.t_exit) if v.t_exit < window else np.nan for v in seen],
    }).sort_values(["t_stopline", "track_id"], kind="stable").reset_index(drop=True)
    state = pd.Series("", index=df.index)
    for app in aps:
        e = ev[ev["approach_group"] == app].sort_values("t", kind="stable")
        idx = df.index[df["approach"] == app]
        k = np.searchsorted(e["t"].to_numpy(), df.loc[idx, "t_stopline"].to_numpy(), side="right") - 1
        state[idx] = e["state"].to_numpy()[k]
    cr = pd.DataFrame({"t": df["t_stopline"], "approach": df["approach"], "lane_or_lat_m": df["lat_m_at_stopline"],
                       "vclass": df["vclass"], "track_id": df["track_id"], "signal_state_at_t": state})
    b = df.assign(interval_start=(np.floor(df["t_stopline"] / INTERVAL_S) * INTERVAL_S).astype(int))
    counts = b.groupby(["interval_start", "approach", "movement", "vclass"]).size()
    tc = [(s, s + INTERVAL_S, app, m, vc, int(counts.get((s, app, m, vc), 0)))
          for s in range(0, int(math.ceil(window)), INTERVAL_S) for app, ap in aps.items() for m in ap.movements
          for vc in VCLASSES if not (m == "illegal_l" and vc == "car")]
    q_rows, lat_rows = [], []
    for app, ss in snaps.items():
        onsets = green_onsets(ev, app)
        for s in ss:
            if not 0 <= s.t < window:
                continue
            k = np.flatnonzero(np.isclose(onsets, _rt(s.t)))
            if not len(k):
                continue  # green at the start of the window: not an onset (schema_observed)
            k = k[0]
            inside = sorted(((v, round(d, LAT_DECIMALS)) for v, d in s.rows if d <= range_m), key=lambda x: (x[1], x[0].id))
            behind = [(v, d) for v, d in inside if d >= 0]
            tail = max((d + lengths[v.vclass] for v, d in behind), default=0.0)
            length = round(min(tail, range_m), LAT_DECIMALS)
            q_rows.append((int(k), _rt(s.t), app, length, sum(v.vclass == "car" for v, _ in behind),
                           sum(v.vclass == "moto" for v, _ in behind), round(length * aps[app].width, LAT_DECIMALS)))
            lat_rows += [(int(k), app, v.id, v.vclass, round(v.lat, LAT_DECIMALS), d) for v, d in inside]
    tables = {
        "turn_counts": pd.DataFrame(tc, columns=TABLES["turn_counts"]),
        "signal_events": ev,
        "stopline_crossings": cr,
        "queue_snapshots": pd.DataFrame(q_rows, columns=TABLES["queue_snapshots"]),
        "lateral_snapshots": pd.DataFrame(lat_rows, columns=TABLES["lateral_snapshots"]),
        "traversals": df[TABLES["traversals"]],
    }
    box_rows = [box_queue_table(a, o, ev, df) for a, o in illegal.items()]
    tables["box_queue"] = (pd.concat(box_rows, ignore_index=True) if box_rows
                           else pd.DataFrame(columns=TABLES["box_queue"]))
    return tables


# ---------------------------------------------------------------- main entry


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _git_commit() -> str | None:
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True, check=True)
        return out.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _opposing(site: Site, approach: str, approaches) -> str:
    same = [o for o in approaches if o != approach and o.split("_")[0] == approach.split("_")[0]]
    if len(same) != 1:
        raise ValueError(f"illegal-left approach {approach}: no unique opposing approach (same road prefix) "
                         f"in {list(approaches)}")
    return same[0]


def generate_day(targets: dict, site: Site, day_id: str, seed: int, out_dir: Path,
                 experiment: dict | None = None, edge_table: Path = EDGE_TABLE,
                 day_factors: dict[str, float] | None = None) -> None:
    """Write the `schema_observed.TABLES` CSVs (+ manifest.json) of one proxy day into `out_dir`.

    `day_factors`: this day's factors from `campaign_day_factors` (the CLI passes them, normalised over D1-D5);
    None = the day's own raw draw (`draw_day_factors`, not normalised)."""
    out_dir = Path(out_dir)
    range_m = queue_range_m(experiment if experiment is not None else load_experiment())
    window, warmup = float(targets["window_s"]), float(targets["warmup_s"])
    rng = np.random.default_rng(np.random.SeedSequence(seed).spawn(2)[1])
    normalised = day_factors is not None
    p = Params(targets, day_factors if normalised else draw_day_factors(targets, seed))
    lengths = {"moto": float(targets["geometry"]["moto_length_m"]), "car": float(targets["geometry"]["car_length_m"])}
    aps = approaches_of(site, edge_table)
    cycle, seg = signal_segments(site, aps)
    ev = signal_events_table(cycle, seg, window)
    cyc = {a: Cycles.of(cycle, seg[a], p("M6_traversal.yellow_use_s")) for a in aps}
    illegal = {a: _opposing(site, a, aps) for a in aps if "illegal_l" in aps[a].movements}

    def opposing_end_fn(a):
        """Opposing green end inside cycle j of illegal-left approach a; both must be green just before it."""
        own, opp = cyc[a], cyc[illegal[a]]

        def end(j):
            t = own.g(j) + (opp.y0 - own.g0) % cycle
            if not (own.g(j) < t <= own.y(j)):
                raise ValueError(f"illegal-left approach {a} and its opposing approach {illegal[a]} do not share a "
                                 f"green phase; the box_queue definition does not apply")
            return t
        return end

    ends = {a: opposing_end_fn(a) for a in illegal}
    ids, vehicles, snaps = _Ids(), {}, {}
    for a in aps:
        vehicles[a] = arrivals(rng, aps[a], p, cyc[a], -warmup, window, range_m, ids, ends.get(a))
    crossing_road = [a for a in aps if a not in illegal and a not in illegal.values()]
    order = list(illegal.values()) + list(illegal) + crossing_road
    waiting: list[tuple[float, int]] = []  # (opposing green end, n waiting) of all illegal-left boxes
    beta = p("M7_illegal_left.crossing_start_delay_per_waiter_s")

    def extra(g):
        prior = [n for t, n in waiting if 0 <= g - t < cycle]
        return beta * prior[-1] if prior else 0.0

    for a in order:
        snaps[a] = serve(rng, aps[a], vehicles[a], cyc[a], p, window, extra if a in crossing_road else (lambda g: 0.0))
        exits(rng, vehicles[a], p)
        if a in illegal:
            o = illegal[a]
            opp_s = np.sort([v.t_cross for v in vehicles[o] if v.movement == "s" and not math.isnan(v.t_cross)])
            box(rng, vehicles[a], cyc[a], ends[a], opp_s, p)
            add_box_waiters(snaps[a], vehicles[a])
            j = int(math.floor((-warmup - cyc[a].g0) / cycle))
            while cyc[a].g(j) < window:
                t_e = ends[a](j)
                n = sum(1 for v in vehicles[a] if v.movement == "illegal_l" and v.t_cross <= t_e - HALT_LEAD_S
                        and not v.t_exit <= t_e)
                waiting.append((t_e, n))
                j += 1
            waiting.sort()
    tables = _tables(aps, [v for a in aps for v in vehicles[a]], snaps, ev, illegal, window, range_m, lengths)
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, cols in TABLES.items():
        tables[name][cols].to_csv(out_dir / f"{name}.csv", index=False, lineterminator="\n")
    manifest = {
        "day": day_id, "seed": int(seed), "site_source": site.source, "data_kind": "LITERATURE_PROXY observed day "
        "(generated, not field data; spec 4.2)", "generator": "thesis_sumo.proxy.generate",
        "site_file": site.path.name, "site_sha256": _sha256(site.path), "targets_sha256": hashlib.sha256(
            json.dumps(targets, sort_keys=True, default=str).encode()).hexdigest(),
        "git_commit": _git_commit(), "queue_range_m": range_m, "window_s": window,
        "day_factors": {k: round(f, 6) for k, f in p.factor.items() if f != 1.0},
        "day_factors_normalised": (f"mean 1 over {', '.join(DAY_SEEDS)} (campaign_day_factors)" if normalised
                                   else "no (this day's raw draw)"),
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def load_targets(path: Path = TARGETS_PATH) -> dict:
    with Path(path).open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m thesis_sumo.proxy.generate", description=__doc__.split("\n\n")[0])
    ap.add_argument("--site", type=Path, default=PROXY_SITE, help="site file (default: the literature proxy)")
    ap.add_argument("--targets", type=Path, default=TARGETS_PATH)
    ap.add_argument("--days", nargs="+", default=list(DAY_SEEDS), choices=list(DAY_SEEDS))
    ap.add_argument("--out-root", type=Path, default=OBSERVED_ROOT)
    ap.add_argument("--no-routes", action="store_true", help="skip scenario/demand/routes_<day>.rou.xml (ruling R2)")
    args = ap.parse_args(argv)
    site, targets = load_site(args.site), load_targets(args.targets)
    if site.source != "LITERATURE_PROXY":
        raise ValueError(f"{args.site}: proxy days need a LITERATURE_PROXY site file, got {site.source}")
    factors = campaign_day_factors(targets, DAY_SEEDS)  # always over all five days, whichever are written
    for day in args.days:
        out = args.out_root / day
        generate_day(targets, site, day, DAY_SEEDS[day], out, day_factors=factors[day])
        msg = f"{day}: seed {DAY_SEEDS[day]} -> {out}"
        if not args.no_routes:
            from thesis_sumo.demand.build_demand import build_demand  # needs SUMO_HOME (routeSampler)

            cands = DEMAND_DIR / "candidate_routes.rou.xml"
            if not cands.is_file():
                raise FileNotFoundError(f"{cands} missing: run python -m thesis_sumo.demand.build_demand first")
            routes = build_demand(out / "turn_counts.csv", cands, DEMAND_DIR / f"routes_{day}.rou.xml", DAY_SEEDS[day])
            msg += f", {routes}"
        print(msg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
