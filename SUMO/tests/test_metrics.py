"""Metrics M1-M8, G0 and the distance (PLAN 5.2-5.3, Task 10) on small hand-built tables with answers worked out
by hand in the comments, plus a few checks on the committed proxy days (definitions match the generator)."""

import math

import numpy as np
import pandas as pd
import pytest

from thesis_sumo.config import REPO_ROOT, Site, load_site
from thesis_sumo.metrics import (
    distance,
    g0_geh,
    m1_headway,
    m2_early_start,
    m3_red_running,
    m4_lateral,
    m5_queue,
    m6_traversal,
    m7_illegal_left,
    m8_wrong_lane,
)
from thesis_sumo.metrics.common import MetricContext, MetricValue, read_tables
from thesis_sumo.schema_observed import TABLES

PROXY_SITE = REPO_ROOT / "config" / "site.proxy.yaml"
OBSERVED = REPO_ROOT / "data" / "observed"
CYCLE = 120.0


# ------------------------------------------------------------------ hand-built tables


def _signal(n_cycles: int = 10) -> pd.DataFrame:
    """LVL_W/LVL_E: G [0,64) y [64,68) r [68,120); HDT_N/HDT_S: r [0,70) G [70,114) y [114,118) r [118,120).
    Green onsets (the first record is not one): LVL 120, 240, ...; HDT 70, 190, 310, ..."""
    rows = [(0.0, a, "r") for a in ("HDT_N", "HDT_S")]
    for c in range(n_cycles):
        b = c * CYCLE
        for a in ("LVL_W", "LVL_E"):
            rows += [(b, a, "G"), (b + 64, a, "y"), (b + 68, a, "r")]
        for a in ("HDT_N", "HDT_S"):
            rows += [(b + 70, a, "G"), (b + 114, a, "y"), (b + 118, a, "r")]
    return pd.DataFrame(rows, columns=TABLES["signal_events"]).sort_values(["t", "approach_group"], kind="stable")


def _state(ev: pd.DataFrame, app: str, t: float) -> str:
    e = ev[(ev["approach_group"] == app) & (ev["t"] <= t)].sort_values("t", kind="stable")
    return e["state"].iloc[-1]


def _tables(vehicles=(), lateral=(), queue=(), box=(), counts=(), n_cycles: int = 10) -> dict[str, pd.DataFrame]:
    """vehicles: (track_id, approach, vclass, movement, t_stopline, lat, t_exit, t_range_entry);
    lateral: (cycle_id, approach, track_id, vclass, lat_m, long_m); queue / box / counts: schema rows."""
    ev = _signal(n_cycles)
    tr = pd.DataFrame([(i, vc, a, mv, "X", lat, t_rng, t, t_ex) for i, a, vc, mv, t, lat, t_ex, t_rng in vehicles],
                      columns=TABLES["traversals"])
    tr = tr.sort_values(["t_stopline", "track_id"], kind="stable").reset_index(drop=True)
    cr = pd.DataFrame({"t": tr["t_stopline"], "approach": tr["approach"], "lane_or_lat_m": tr["lat_m_at_stopline"],
                       "vclass": tr["vclass"], "track_id": tr["track_id"],
                       "signal_state_at_t": [_state(ev, a, t) for a, t in zip(tr["approach"], tr["t_stopline"])]},
                      columns=TABLES["stopline_crossings"])
    return {
        "signal_events": ev.reset_index(drop=True),
        "stopline_crossings": cr,
        "traversals": tr,
        "lateral_snapshots": pd.DataFrame(list(lateral), columns=TABLES["lateral_snapshots"]),
        "queue_snapshots": pd.DataFrame(list(queue), columns=TABLES["queue_snapshots"]),
        "box_queue": pd.DataFrame(list(box), columns=TABLES["box_queue"]),
        "turn_counts": pd.DataFrame(list(counts), columns=TABLES["turn_counts"]),
    }


def _site(continuous: bool = False) -> Site:
    lanes = [["r", "s"], ["s"], ["s", "l", "u"]]
    return Site({"site_source": "LITERATURE_PROXY", "approaches": [
        {"id": a, "lane_widths_m": [3.5, 3.5, 3.5], "lane_movements": lanes, "continuous_right_lane": continuous}
        for a in ("LVL_W", "LVL_E", "HDT_N", "HDT_S")]}, PROXY_SITE)


def _ctx(window=(0.0, 1000.0), continuous: bool = False) -> MetricContext:
    return MetricContext(window=window, queue_range_m=80.0, site=_site(continuous))


def V(i, a, vc, mv, t, lat=1.0, t_exit=np.nan, t_range=np.nan):
    return (i, a, vc, mv, t, lat, t_exit, t_range)


# ------------------------------------------------------------------ M1


def test_m1_headway_known():
    veh = [
        V("x", "LVL_W", "moto", "illegal_l", 50.0),       # box waiter: crossed before the onset, not queued
        V("a", "LVL_W", "moto", "s", 121.2), V("b", "LVL_W", "moto", "s", 121.5), V("c", "LVL_W", "car", "s", 122.4),
        V("d", "LVL_W", "moto", "s", 123.0),              # arrived in green: beyond the queue of 3
        V("e", "LVL_E", "moto", "s", 121.3),              # other approach
        V("f", "LVL_W", "moto", "s", 241.0), V("g", "LVL_W", "moto", "s", 241.4),
        V("h", "LVL_W", "moto", "s", 361.0), V("i", "LVL_W", "moto", "s", 362.0),
        V("j", "LVL_W", "moto", "s", 430.0),              # after the red onset 428: not discharge
        V("k", "LVL_W", "moto", "s", 1081.0), V("m", "LVL_W", "moto", "s", 1081.5),  # onset 1080 outside window
    ]
    lat = [(0, "LVL_W", t, vc, 1.0, d) for t, vc, d in [("x", "moto", -20.0), ("a", "moto", -1.0),
                                                        ("b", "moto", 0.5), ("c", "car", 3.0)]]
    lat += [(1, "LVL_W", "f", "moto", 1.0, 0.0), (1, "LVL_W", "g", "moto", 1.0, 2.0)]
    lat += [(2, "LVL_W", t, "moto", 1.0, 2.0 * n) for n, t in enumerate("hij")]
    lat += [(8, "LVL_W", t, "moto", 1.0, 1.0) for t in "km"]
    out = m1_headway.compute(_tables(veh, lat, n_cycles=12), _ctx())
    # cycle 0: queue a, b, c -> b - a = 0.3 (moto, position 2), c - b = 0.9 (car, position 3)
    # cycle 1: g - f = 0.4; cycle 2: i - h = 1.0 (j crosses after the red onset 428)
    assert sorted(out["M1/moto"].values) == pytest.approx([0.3, 0.4, 1.0])
    assert list(out["M1/car"].values) == pytest.approx([0.9])
    assert out["M1/moto"].kind == "dist"


# ------------------------------------------------------------------ M2 / M3


def _red_tables():
    # HDT_N red: [118 + 120c, 190 + 120c); onsets 70, 190, 310, 430, 550 (< 600)
    veh = [V(f"r{n}", "HDT_N", "moto", "s", t) for n, t in enumerate([120, 185, 240, 241, 250, 500, 545, 599])]
    veh += [V(f"g{n}", "HDT_N", "moto", "s", t) for n, t in enumerate([80, 90, 200, 320, 440])]
    veh += [V("c0", "HDT_N", "car", "s", 85.0)]
    return _tables(veh)


def test_m3_violations_per_cycle():
    out = m3_red_running.compute(_red_tables(), _ctx(window=(0.0, 600.0)))
    # complete cycles in [0, 600) with the next onset < 600: HDT 70, 190, 310, 430 (4 each), LVL 120, 240, 360 (3 each)
    # HDT_N red runners (not within 10 s of the next onset): 120 | 240, 241, 250 | - | 500  -> [1, 3, 0, 1]
    # 185 and 545 are early starts; 599 cannot be classified (next onset 670 is outside the window)
    assert sorted(out["M3/per_cycle"].values) == [0] * 11 + [1, 1, 3]   # 14 approach-cycles
    # var/mean per approach with a non-zero mean: HDT_N mean 1.25, var 4.75/3 -> 1.26667
    assert out["M3/var_to_mean"].values == pytest.approx(4.75 / 3 / 1.25)
    # share: classifiable crossings t < 550 (last onset): 12 moto (7 red + 5 green), 1 car; 5 red runners
    assert out["M3/share/moto"].values == pytest.approx(5 / 12)
    assert out["M3/share/car"].values == 0.0
    assert out["M3/share/moto"].kind == "scalar"


def test_m2_early_start_and_first_delay():
    tables = _red_tables()
    out = m2_early_start.compute(tables, _ctx(window=(0.0, 600.0)))
    assert out["M2/early/moto"].values == pytest.approx(2 / 12)  # 185 and 545
    assert out["M2/early/car"].values == 0.0
    # first crossing at/after each onset in the window, before that cycle's red onset, any approach:
    # HDT_N onsets 70 -> 80 (10), 190 -> 200 (10), 310 -> 320 (10), 430 -> 440 (10), 550 -> none before 598
    assert sorted(out["M2/first_delay"].values) == pytest.approx([10.0] * 4)


@pytest.mark.parametrize("continuous", [True, False])
def test_continuous_right_turns_not_violations(continuous):
    """PLAN 0: with continuous_right_lane true a right turn on red is no violation. HDT_N (onsets 70, 190):
    s in red at 20 (red runner), r in red at 25 and in the last 10 s of red at 65, r at 80 and s at 85 in green."""
    veh = [V("s1", "HDT_N", "moto", "s", 20.0), V("r1", "HDT_N", "moto", "r", 25.0),
           V("r2", "HDT_N", "moto", "r", 65.0), V("r3", "HDT_N", "moto", "r", 80.0),
           V("s2", "HDT_N", "moto", "s", 85.0)]
    tables, ctx = _tables(veh, n_cycles=2), _ctx(window=(0.0, 240.0), continuous=continuous)
    m2, m3 = m2_early_start.compute(tables, ctx), m3_red_running.compute(tables, ctx)
    if continuous:  # only s1, s2 are classifiable; first crossing after 70 is s2
        assert m3["M3/share/moto"].values == pytest.approx(1 / 2)
        assert m2["M2/early/moto"].values == 0.0
        assert list(m2["M2/first_delay"].values) == pytest.approx([15.0])
    else:  # r1 red runner, r2 early start, r3 first crossing
        assert m3["M3/share/moto"].values == pytest.approx(2 / 5)
        assert m2["M2/early/moto"].values == pytest.approx(1 / 5)
        assert list(m2["M2/first_delay"].values) == pytest.approx([10.0])


def test_continuous_right_lane_flag_required():
    """No silent default: a site without the flag raises."""
    site = _site()
    for a in site["approaches"]:
        del a["continuous_right_lane"]
    with pytest.raises(KeyError, match="continuous_right_lane"):
        m3_red_running.compute(_tables([V("s1", "HDT_N", "moto", "s", 20.0)], n_cycles=2),
                               MetricContext(window=(0.0, 240.0), queue_range_m=80.0, site=site))


# ------------------------------------------------------------------ M4 / M5 / M6 / M8


def test_m4_lateral_and_overshoot():
    veh = [V("bx", "LVL_W", "moto", "illegal_l", 50.0),   # box waiter (crossed in green before the onset): excluded
           V("ov", "LVL_W", "moto", "s", 110.0),          # crossed in red, halted past the line at the onset: kept
           V("q1", "LVL_W", "moto", "s", 121.0), V("q2", "LVL_W", "moto", "s", 121.4), V("c", "LVL_W", "car", "s", 122)]
    lat = [(0, "LVL_W", "bx", "moto", 9.0, -20.0), (0, "LVL_W", "ov", "moto", 2.0, -1.5),
           (0, "LVL_W", "q1", "moto", 4.0, -2.0), (0, "LVL_W", "q2", "moto", 6.0, 3.0), (0, "LVL_W", "c", "car", 5.0, 5.0)]
    out = m4_lateral.compute(_tables(veh, lat), _ctx())
    assert sorted(out["M4/lat_moto"].values) == pytest.approx([2.0, 4.0, 6.0])
    assert out["M4/overshoot_share"].values == pytest.approx(2 / 3)
    assert sorted(out["M4/overshoot_depth"].values) == pytest.approx([1.5, 2.0])


def test_m5_queue_and_censoring():
    q = [(0, 120.0, "LVL_W", 10.0, 1, 5, 105.0), (1, 240.0, "LVL_W", 80.0, 4, 40, 840.0),
         (0, 190.0, "HDT_N", 0.0, 0, 0, 0.0), (9, 1200.0, "HDT_N", 50.0, 1, 1, 525.0)]  # last: outside window
    out = m5_queue.compute(_tables(queue=q), _ctx())
    assert sorted(out["M5/length"].values) == pytest.approx([0.0, 10.0, 80.0])
    assert sorted(out["M5/moto_density"].values) == pytest.approx([5 / 105, 40 / 840])  # area 0 has no density
    assert out["M5/share_censored"].values == pytest.approx(1 / 3)      # 80 m >= queue_range_m
    assert out["M5/share_censored"].scored is False


def test_m6_traversal_times():
    veh = [V("a", "LVL_W", "moto", "s", 100.0, t_exit=105.0, t_range=80.0),
           V("b", "LVL_W", "moto", "s", 200.0, t_exit=208.0, t_range=np.nan),
           V("c", "HDT_N", "car", "r", 300.0, t_exit=302.5, t_range=270.0),
           V("d", "LVL_W", "moto", "illegal_l", 400.0, t_exit=np.nan, t_range=390.0),
           V("e", "LVL_W", "moto", "s", 1200.0, t_exit=1205.0, t_range=1180.0)]  # outside window
    out = m6_traversal.compute(_tables(veh), _ctx())
    assert sorted(out["M6/junction/s/moto"].values) == pytest.approx([5.0, 8.0])
    assert list(out["M6/approach/s/moto"].values) == pytest.approx([20.0])
    assert list(out["M6/junction/r/car"].values) == pytest.approx([2.5])
    assert list(out["M6/approach/illegal_l/moto"].values) == pytest.approx([10.0])
    assert out["M6/junction/illegal_l/moto"].n == 0
    assert "M6/junction/illegal_l/car" not in out


def test_m8_wrong_lane_share():
    # lanes [0, 3.5) r,s | [3.5, 7) s | [7, 10.5) s,l,u ; lat beyond the roadway falls in the outer lane
    veh = [V("a", "HDT_N", "moto", "r", 100.0, lat=1.0), V("b", "HDT_N", "moto", "r", 101.0, lat=5.0),
           V("c", "HDT_N", "moto", "l", 102.0, lat=2.0), V("d", "HDT_N", "moto", "u", 103.0, lat=12.0),
           V("e", "HDT_N", "moto", "s", 104.0, lat=5.0), V("f", "LVL_W", "moto", "illegal_l", 105.0, lat=1.0),
           V("g", "HDT_N", "car", "l", 106.0, lat=9.0), V("h", "HDT_N", "moto", "l", 107.0, lat=np.nan)]
    out = m8_wrong_lane.compute(_tables(veh), _ctx())
    assert out["M8/moto"].values == pytest.approx(2 / 4)  # b (r in lane 1), c (l in lane 0)
    assert out["M8/car"].values == 0.0


def test_m8_needs_site_lanes(tmp_path):
    p = tmp_path / "site.yaml"
    p.write_text("site_source: MEASURED\napproaches:\n  - id: HDT_N\n    lane_widths_m: null\n"
                 "    lane_movements: null\n", encoding="utf-8")
    veh = [V("a", "HDT_N", "moto", "r", 100.0)]
    from thesis_sumo.config import MissingFieldDataError
    with pytest.raises(MissingFieldDataError, match="lane_widths_m"):
        m8_wrong_lane.compute(_tables(veh), MetricContext(window=(0, 1000), queue_range_m=80, site=load_site(p)))


# ------------------------------------------------------------------ M7


def _box_tables():
    veh = [
        # cycle 0 of LVL_W (t_stopline in [120, 240)); box_queue row t = 184 (LVL_E green end)
        V("v1", "LVL_W", "moto", "illegal_l", 130.0, t_exit=150.0),   # early leaver
        V("v2", "LVL_W", "moto", "illegal_l", 140.0, t_exit=190.0),
        V("v3", "LVL_W", "moto", "illegal_l", 150.0, t_exit=190.6),
        # cycle 1; row t = 304
        V("v4", "LVL_W", "moto", "illegal_l", 250.0, t_exit=310.0),
        # opposing straight crossings
        V("o1", "LVL_E", "moto", "s", 183.0), V("o2", "LVL_E", "moto", "s", 186.5), V("o3", "LVL_E", "moto", "s", 195.0),
        V("o4", "LVL_E", "moto", "s", 300.0), V("o5", "LVL_E", "moto", "r", 303.0),  # o5 not straight
        # crossing road: first crossing after its onsets 190 / 310
        V("n1", "HDT_N", "moto", "s", 192.0), V("n2", "HDT_N", "moto", "s", 311.5),
        V("s1", "HDT_S", "moto", "s", 192.3), V("s2", "HDT_S", "moto", "s", 311.4),
    ]
    box = [(-1, 64.0, "LVL_W", 4, 30.0, 70.0), (0, 184.0, "LVL_W", 2, 150.0, 190.6), (1, 304.0, "LVL_W", 1, 310.0, 310.0)]
    return _tables(veh, box=box)


def test_m7_box_count():
    out = m7_illegal_left.compute(_box_tables(), _ctx(window=(100.0, 1000.0)))
    assert sorted(out["M7a/n_waiting"].values) == [1, 2]          # row t = 64 is before the window
    # exits minus the cycle's opposing green end: v1 150-184, v2 190-184, v3 190.6-184, v4 310-304
    assert sorted(out["M7a/release_time"].values) == pytest.approx([-34.0, 6.0, 6.0, 6.6])
    # first exit >= t minus max(t, last opposing straight crossing before it): 190 - 186.5; 310 - max(304, 300)
    assert sorted(out["M7b/clear_lag"].values) == pytest.approx([3.5, 6.0])
    # crossing road onsets 190 (box row 184: n 2) and 310 (row 304: n 1); delays 2.0, 2.3 | 1.5, 1.4 -> slope 0.7
    assert out["M7c/slope"].values == pytest.approx(0.7)
    assert out["M7c/slope"].kind == "scalar"


def test_m7_day_past_window_same_as_truncated():
    """An observed day that goes on past w1 gives the same M7a as the same day cut at w1 (entrants after the last
    in-window onset must not be filed under that onset's cycle)."""
    t = read_tables(OBSERVED / "PROXY_D2")
    ctx = MetricContext.from_config(site=load_site(PROXY_SITE))
    w1 = ctx.window[1]
    cut = dict(t)
    cut["signal_events"] = t["signal_events"][t["signal_events"]["t"] < w1]
    cut["traversals"] = t["traversals"][t["traversals"]["t_stopline"] < w1]
    full, short = m7_illegal_left.compute(t, ctx), m7_illegal_left.compute(cut, ctx)
    assert np.max(full["M7a/release_time"].values) < 300
    assert sorted(full["M7a/release_time"].values) == pytest.approx(sorted(short["M7a/release_time"].values))


def test_empty_never_beats_wrong():
    """R35: no events on the sim side is never cheaper than events that are far off."""
    obs = MetricValue(kind="dist", values=np.array([5.0, 5.5, 6.0, 7.0]), label="x", unit="s")
    far = MetricValue(kind="dist", values=np.array([60.0, 70.0]), label="x", unit="s")
    empty = MetricValue(kind="dist", values=np.array([]), label="x", unit="s")
    assert distance.metric_distance(far, obs) <= distance.metric_distance(empty, obs) == distance.D_EMPTY
    assert distance.metric_distance(_sv(0.05), _sv(0.0087)) <= distance.D_EMPTY


def test_m7_no_box_events():
    out = m7_illegal_left.compute(_tables([V("a", "LVL_E", "moto", "s", 150.0)]), _ctx())
    assert out["M7a/n_waiting"].n == 0 and out["M7b/clear_lag"].n == 0
    assert math.isnan(out["M7c/slope"].values)


# ------------------------------------------------------------------ G0


def _counts(rows):
    return pd.DataFrame([(s, s + 900, a, m, vc, n) for s, a, m, vc, n in rows], columns=TABLES["turn_counts"])


def test_geh_gate():
    assert g0_geh.geh(150, 100) == pytest.approx(math.sqrt(20))
    assert g0_geh.geh(0, 0) == 0.0
    sim = _counts([(0, "LVL_W", "s", "moto", 100), (0, "LVL_W", "r", "moto", 150), (900, "LVL_W", "s", "moto", 160),
                   (1800, "LVL_W", "s", "moto", 1000)])  # 1800: outside [0, 1800)
    obs = _counts([(0, "LVL_W", "s", "moto", 100), (0, "LVL_W", "r", "moto", 100), (900, "LVL_W", "s", "moto", 100),
                   (900, "HDT_N", "s", "car", 0), (1800, "LVL_W", "s", "moto", 10)])
    # cells: GEH 0, 4.47, 5.26 (fail), 0 (0 vs 0; HDT_N missing on the sim side = 0) -> 3/4 below 5
    ok, share = g0_geh.gate({"turn_counts": sim}, {"turn_counts": obs}, threshold=5, min_share=0.85, window=(0, 1800))
    assert share == pytest.approx(0.75) and ok is False
    ok, share = g0_geh.gate({"turn_counts": sim}, {"turn_counts": obs}, threshold=5, min_share=0.75, window=(0, 1800))
    assert ok is True
    with pytest.raises(ValueError, match="no turn-count cells"):
        g0_geh.gate({"turn_counts": sim}, {"turn_counts": obs}, threshold=5, min_share=0.85, window=(3600, 4500))


def test_geh_gate_defaults_from_config():
    obs = _counts([(0, "LVL_W", "s", "moto", 100), (900, "LVL_W", "s", "moto", 100)])
    ok, share = g0_geh.gate({"turn_counts": obs}, {"turn_counts": obs})
    assert ok and share == 1.0


# ------------------------------------------------------------------ distance


def test_w1_iqr_normalised():
    obs = np.arange(0.0, 101.0)                     # IQR 75 - 25 = 50
    assert distance.w1_normalised(obs + 10.0, obs) == pytest.approx(10.0 / 50.0)
    assert distance.w1_normalised(obs, obs) == 0.0
    # W1 of {0, 0} vs {1, 3} = 2; obs IQR (linear) = 1; scale = IQR
    assert distance.w1_normalised(np.array([0.0, 0.0]), np.array([1.0, 3.0])) == pytest.approx(2.0 / 1.0)
    # constant obs sample: IQR 0, sd 0 -> scale |mean| = 2
    assert distance.w1_normalised(np.array([1.0]), np.array([2.0, 2.0])) == pytest.approx(1.0 / 2.0)
    # all-zero obs sample: scale 1
    assert distance.w1_normalised(np.array([0.5]), np.array([0.0, 0.0])) == pytest.approx(0.5)


def test_rel_error():
    assert distance.rel_error(1.5, 1.0) == pytest.approx(0.5)
    assert distance.rel_error(0.0, 0.2) == pytest.approx(1.0)
    assert distance.rel_error(0.0, 0.0) == 0.0
    assert distance.rel_error(0.1, 0.0) == distance.D_EMPTY


def _sv(x):
    return MetricValue(kind="scalar", values=x, label="x", unit="")


def test_R_ratio():
    obs = [_sv(1.0), _sv(1.2), _sv(0.8)]
    d, ddd = distance.pair_stats([_sv(1.5)], obs)
    assert d == pytest.approx((0.5 + 0.3 / 1.2 + 0.7 / 0.8) / 3)
    # ordered pairs (a vs b, normalised by b): .2/1.2, .2/.8, .2/1, .4/.8, .2/1, .4/1.2
    assert ddd == pytest.approx((0.2 / 1.2 + 0.25 + 0.2 + 0.5 + 0.2 + 0.4 / 1.2) / 6)
    assert distance.ratio(d, ddd) == pytest.approx(d / ddd)
    # guard: identical observed days -> noise floor 0 -> R against R_FLOOR, finite
    d0, ddd0 = distance.pair_stats([_sv(1.5)], [_sv(1.0), _sv(1.0)])
    assert ddd0 == 0.0 and distance.ratio(d0, ddd0) == pytest.approx(0.5 / distance.R_FLOOR)
    assert distance.ratio(0.0, 0.0) == 0.0
    # one observed day: no noise floor
    _, ddd1 = distance.pair_stats([_sv(1.5)], [_sv(1.0)])
    assert math.isnan(ddd1) and math.isnan(distance.ratio(0.5, ddd1))


def test_split_weights_hierarchical():
    keys = ["M1/moto", "M1/car", "M7a/n_waiting", "M7a/release_time", "M7b/clear_lag", "M7c/slope"]
    w = distance.split_weights(keys, {"M1": 0.5, "M7": 0.5})
    assert w["M1/moto"] == pytest.approx(0.25)
    assert w["M7a/n_waiting"] == pytest.approx(0.5 / 3 / 2)
    assert w["M7b/clear_lag"] == pytest.approx(0.5 / 3)
    assert sum(w.values()) == pytest.approx(1.0)
    with pytest.raises(ValueError, match="M7"):
        distance.split_weights(keys, {"M1": 1.0})


def _rich_obs(shift: float = 0.0):
    """Tables with events for every metric (red runner, early start, box waiters, queue)."""
    veh = [V("r1", "HDT_N", "moto", "s", 130.0 + shift), V("e1", "HDT_N", "moto", "s", 185.0),
           V("g1", "HDT_N", "moto", "r", 200.0, lat=5.0, t_exit=203.0, t_range=180.0),
           V("g2", "HDT_N", "car", "l", 201.0, lat=9.0, t_exit=208.0, t_range=170.0)]
    t = _box_tables()
    extra = _tables(veh)
    for name in ("traversals", "stopline_crossings"):
        t[name] = pd.concat([t[name], extra[name]], ignore_index=True).sort_values("t" if name != "traversals"
                                                                                    else "t_stopline")
    t["queue_snapshots"] = pd.DataFrame([(0, 120.0, "LVL_W", 10.0 + shift, 1, 5, 105.0)], columns=TABLES["queue_snapshots"])
    t["lateral_snapshots"] = pd.DataFrame([(0, "LVL_W", "v2", "moto", 9.0, 2.0)], columns=TABLES["lateral_snapshots"])
    return t


def test_empty_events_defined_distance():
    """Rule: a distribution with no events on exactly one side is D_EMPTY away; with none on either side 0 (and the
    key is not scored when no observed day has events); a share of 0 against a positive share is relative error 1;
    an undefined scalar (e.g. a slope without box waiters) on one side is D_EMPTY."""
    obs = [_rich_obs(0.0), _rich_obs(2.0)]
    sim = [_tables([V("a", "LVL_E", "moto", "s", 150.0)])]     # nothing happens: no red runner, no box, no queue
    rep = distance.compare(sim, obs, weights={f"M{k}": 1.0 for k in range(1, 9)}, ctx=_ctx())
    for key, m in rep.metrics.items():
        assert math.isfinite(m.d), key
    assert rep.metrics["M7b/clear_lag"].d == distance.D_EMPTY
    assert rep.metrics["M7c/slope"].d == distance.D_EMPTY
    assert rep.metrics["M3/share/moto"].d == pytest.approx(1.0)
    assert rep.metrics["M7a/n_waiting"].direction == "sim<obs"
    none = rep.metrics["M6/junction/u/car"]                     # no events anywhere
    assert none.d == 0.0 and not none.scored and none.weight == 0.0
    assert math.isfinite(rep.S) and rep.S > 0


def test_compare_report_row_summary_and_evidence():
    obs = [read_tables(OBSERVED / f"PROXY_D{k}") for k in (1, 2, 3)]
    ctx = MetricContext.from_config(site=load_site(PROXY_SITE))
    rep = distance.compare(obs[:1], obs, ctx=ctx)      # weights from experiment.yaml score.weights
    assert rep.n_sim == 1 and rep.n_obs_days == 3
    assert rep.metrics["M1/moto"].evidence == "literature_transferred"
    assert rep.metrics["M7b/clear_lag"].evidence == "assumed"
    assert rep.metrics["M7b/clear_lag"].label.startswith("PET proxy (box clear lag)")
    assert set(rep.direction.values()) <= {"sim>obs", "sim<obs", "sim=obs", "undefined"}
    row = rep.to_row()
    assert row["S"] == pytest.approx(rep.S) and "M7b/clear_lag.R" in row and "S_assumed" in row
    assert sum(m.weight for m in rep.metrics.values()) == pytest.approx(1.0)
    lines = rep.summary_lines()
    assert any(line.startswith("M3/per_cycle") and "sim " in line and " vs obs " in line for line in lines)
    assert not any("PROXY_D" in line for line in lines)


def test_same_generator_gives_R_near_one():
    """Validation days against calibration days come from the same generator: R should scatter around 1."""
    ctx = MetricContext.from_config(site=load_site(PROXY_SITE))
    calib = [read_tables(OBSERVED / f"PROXY_D{k}") for k in (1, 2, 3)]
    valid = [read_tables(OBSERVED / f"PROXY_D{k}") for k in (4, 5)]
    rep = distance.compare(valid, calib, ctx=ctx)
    R = np.array([m.R for m in rep.metrics.values() if m.scored])
    assert 0.6 <= float(np.median(R)) <= 1.6


# ------------------------------------------------------------------ window, config, proxy days


def test_context_from_config():
    ctx = MetricContext.from_config()
    assert ctx.window == (300.0, 1800.0)
    assert ctx.queue_range_m == 80.0


def test_metrics_on_proxy_days_match_targets():
    """The metric code reproduces the generator's definitions: pooled over D1-D5 in the window, the values are near
    the targets.yaml means (wide tolerance: 1500 s per day)."""
    ctx = MetricContext.from_config(site=load_site(PROXY_SITE))
    days = [distance.compute_all(read_tables(OBSERVED / f"PROXY_D{k}"), ctx) for k in range(1, 6)]

    def pooled(key):
        return np.concatenate([np.atleast_1d(d[key].values) for d in days])

    assert np.mean(pooled("M7a/n_waiting")) == pytest.approx(6.0, rel=0.25)
    assert np.mean(pooled("M7b/clear_lag")) == pytest.approx(5.65, rel=0.25)
    assert np.mean(pooled("M7c/slope")) == pytest.approx(0.3, rel=0.4)
    assert np.mean(pooled("M8/moto")) == pytest.approx(0.25, rel=0.2)
    assert np.mean(pooled("M4/overshoot_share")) == pytest.approx(0.63, rel=0.1)
    assert np.mean(pooled("M5/share_censored")) == 0.0
    # early start moto: share of the approach total, LVL 9.45 %, HDT 15.82 % -> pooled in between
    assert 0.09 < np.mean(pooled("M2/early/moto")) < 0.16
