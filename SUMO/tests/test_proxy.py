"""Proxy observed days (Task 6): generator determinism, schema, internal consistency and match to the
literature targets in data/proxy/targets.yaml. Statistics are computed from the written CSVs only, with the
definitions stated in targets.yaml, never with the generator's internals."""

import filecmp
import json
import math
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml
from lxml import etree

from thesis_sumo.config import EVIDENCE, REPO_ROOT, MissingFieldDataError, load_experiment, load_site
from thesis_sumo.proxy import generate
from thesis_sumo.schema_observed import INTERVAL_S, MOVEMENTS, SIGNAL_STATES, TABLES, VCLASSES, cycle_id_at, green_onsets

TARGETS_PATH = REPO_ROOT / "data" / "proxy" / "targets.yaml"
PROXY_SITE = REPO_ROOT / "config" / "site.proxy.yaml"
OBSERVED = REPO_ROOT / "data" / "observed"
DEMAND = REPO_ROOT / "scenario" / "demand"
SEEDS = {f"PROXY_D{k}": 100 + k for k in range(1, 6)}
TOL = 0.15  # brief: raw mean over the 5 days within 15 % of the NOMINAL targets.yaml value
# The CLI normalises the day factors to mean 1 over D1-D5 (generate.campaign_day_factors), so the 5-day mean of
# every target is its nominal value by construction and only within-day sampling noise remains.
FACTORS = generate.campaign_day_factors(yaml.safe_load(TARGETS_PATH.read_text(encoding="utf-8")), SEEDS)
APPROACHES = ("LVL_W", "LVL_E", "HDT_N", "HDT_S")


def _targets() -> dict:
    return yaml.safe_load(TARGETS_PATH.read_text(encoding="utf-8"))


def _t(key: str):
    node = _targets()["targets"]
    for part in key.split("."):
        node = node[part]
    return node["value"]


def _read(day_dir: Path) -> dict[str, pd.DataFrame]:
    tables = {name: pd.read_csv(day_dir / f"{name}.csv") for name in TABLES}
    tables["_day_factors"] = json.loads((day_dir / "manifest.json").read_text(encoding="utf-8"))["day_factors"]
    return tables


@pytest.fixture(scope="module")
def site():
    return load_site(PROXY_SITE)


@pytest.fixture(scope="module")
def five_days(tmp_path_factory, site) -> dict[str, dict[str, pd.DataFrame]]:
    root = tmp_path_factory.mktemp("proxy")
    out = {}
    for day, seed in SEEDS.items():
        generate.generate_day(_targets(), site, day, seed, root / day, day_factors=FACTORS[day])
        out[day] = _read(root / day)
    return out


def _onsets(tables, approach):
    return green_onsets(tables["signal_events"], approach)


def _signalled(tables):
    """The tables without the right turns of continuous_right_lane approaches: not signal controlled (PLAN 0), so
    never early starts, red runners, queued or discharged (proxy_targets.md §2)."""
    cont = {a["id"] for a in load_site(PROXY_SITE)["approaches"] if a["continuous_right_lane"]}
    tr, cr = tables["traversals"], tables["stopline_crossings"]
    free = set(tr.loc[tr["approach"].isin(cont) & (tr["movement"] == "r"), "track_id"])
    return {**tables, "traversals": tr[~tr["track_id"].isin(free)],
            "stopline_crossings": cr[~cr["track_id"].isin(free)]}


def _close(got: float, want: float, what: str, tol: float = TOL):
    assert want != 0
    assert abs(got - want) <= tol * abs(want), f"{what}: generated {got:.4f}, target {want:.4f}"


# ------------------------------------------------------------------ determinism / schema


def test_generator_deterministic(tmp_path, site):
    for sub in ("a", "b"):
        generate.generate_day(_targets(), site, "PROXY_D1", 101, tmp_path / sub, day_factors=FACTORS["PROXY_D1"])
    for name in TABLES:
        assert filecmp.cmp(tmp_path / "a" / f"{name}.csv", tmp_path / "b" / f"{name}.csv", shallow=False), name


def test_days_differ(five_days):
    a, b = five_days["PROXY_D1"], five_days["PROXY_D2"]
    for name in ("stopline_crossings", "turn_counts", "queue_snapshots", "box_queue"):
        assert not a[name].equals(b[name]), name


def test_schema_columns(five_days):
    for tables in five_days.values():
        for name, cols in TABLES.items():
            assert list(tables[name].columns) == cols, name
        assert set(tables["signal_events"]["state"]) <= set(SIGNAL_STATES)
        assert set(tables["stopline_crossings"]["signal_state_at_t"]) <= set(SIGNAL_STATES)
        for name in ("stopline_crossings", "lateral_snapshots", "traversals"):
            assert set(tables[name]["vclass"]) <= set(VCLASSES), name
        assert set(tables["traversals"]["movement"]) <= set(MOVEMENTS)
        tc = tables["turn_counts"]
        assert set(tc["movement"]) <= set(MOVEMENTS) and set(tc["vclass"]) <= set(VCLASSES)
        assert ((tc["interval_end"] - tc["interval_start"]) == INTERVAL_S).all()
        assert sorted(set(tc["interval_start"])) == [0, 900, 1800, 2700]
        assert not tc.duplicated(["interval_start", "approach", "movement", "vclass"]).any()
        assert not ((tc["vclass"] == "car") & (tc["movement"] == "illegal_l")).any()
        cr = tables["stopline_crossings"]
        assert cr["t"].between(0, 3600, inclusive="left").all()
        assert cr["track_id"].is_unique


# ------------------------------------------------------------------ internal consistency (same vehicles everywhere)


def test_tables_consistent(five_days, site):
    range_m = load_experiment()["observation"]["queue_range_m"]
    width = {a["id"]: sum(a["lane_widths_m"]) for a in site["approaches"]}
    for tables in five_days.values():
        cr, tr, tc = tables["stopline_crossings"], tables["traversals"], tables["turn_counts"]
        assert list(cr["track_id"]) == list(tr["track_id"])
        assert (cr["t"].to_numpy() == tr["t_stopline"].to_numpy()).all()
        assert np.allclose(cr["lane_or_lat_m"], tr["lat_m_at_stopline"])
        # turn counts = crossings binned by crossing time
        b = tr.assign(interval_start=(np.floor(tr["t_stopline"] / INTERVAL_S) * INTERVAL_S).astype(int))
        got = b.groupby(["interval_start", "approach", "movement", "vclass"]).size()
        nz = tc[tc["count"] > 0].set_index(["interval_start", "approach", "movement", "vclass"])["count"]
        assert got.sort_index().to_dict() == nz.sort_index().to_dict()
        # signal state at crossing = signal_events state at t
        ev = tables["signal_events"]
        for app in APPROACHES:
            e = ev[ev["approach_group"] == app].sort_values("t")
            c = cr[cr["approach"] == app]
            idx = np.searchsorted(e["t"].to_numpy(), c["t"].to_numpy(), side="right") - 1
            assert (e["state"].to_numpy()[idx] == c["signal_state_at_t"].to_numpy()).all()
        # queue: behind-line vehicles of the lateral snapshot; length capped at the range
        q, lat = tables["queue_snapshots"], tables["lateral_snapshots"]
        behind = lat[lat["long_m_from_stopline"] >= 0].groupby(["cycle_id", "approach", "vclass"]).size()
        for r in q.itertuples():
            assert r.n_car == behind.get((r.cycle_id, r.approach, "car"), 0)
            assert r.n_moto == behind.get((r.cycle_id, r.approach, "moto"), 0)
            assert 0 <= r.queue_length_m <= range_m
            assert math.isclose(r.area_m2, r.queue_length_m * width[r.approach], rel_tol=1e-6, abs_tol=0.01)
        assert (lat["long_m_from_stopline"] <= range_m).all()
        # traversal times are positive and ordered
        assert (tr["t_exit"].dropna() > tr.loc[tr["t_exit"].notna(), "t_stopline"]).all()
        assert (tr["t_range_entry"].dropna() < tr.loc[tr["t_range_entry"].notna(), "t_stopline"]).all()


def _box_expected(tables, approach="LVL_W", opposing="LVL_E", halt_lead=generate.HALT_LEAD_S):
    """box_queue recomputed from traversals with the binding definition (schema_observed, ruling R11)."""
    ev, tr = tables["signal_events"], tables["traversals"]
    onsets = _onsets(tables, approach)
    e = ev[ev["approach_group"] == opposing].sort_values("t")
    prev = e["state"].shift()
    ends = e.loc[(prev == "G") & (e["state"] != "G"), "t"].to_numpy()
    v = tr[(tr["approach"] == approach) & (tr["movement"] == "illegal_l")]
    cyc = cycle_id_at(onsets, v["t_stopline"])
    rows = []
    for t in ends:
        k = int(cycle_id_at(onsets, [t])[0])
        inside = v[(v["t_stopline"] <= t - halt_lead) & ~(v["t_exit"] <= t)]
        ent = v[cyc == k]
        ex = ent["t_exit"].dropna()
        start = ex.min() if len(ex) else np.nan
        end = np.nan if (ent["t_exit"].isna().any() or not len(ex)) else ex.max()
        rows.append((k, t, approach, len(inside), start, end))
    return pd.DataFrame(rows, columns=TABLES["box_queue"])


def test_box_queue_follows_binding_definition(five_days):
    for tables in five_days.values():
        exp = _box_expected(tables)
        got = tables["box_queue"]
        assert len(got) == len(exp) == 30
        pd.testing.assert_frame_equal(got.reset_index(drop=True), exp, check_dtype=False)


# ------------------------------------------------------------------ generated statistics vs targets


def _per_day(five_days, fn) -> float:
    return float(np.mean([fn(t) for t in five_days.values()]))


def test_counts_match_targets(five_days):
    vol = _t("G0_counts.approach_volume_veh_h")
    for app, want in vol.items():
        _close(_per_day(five_days, lambda t: t["turn_counts"].loc[t["turn_counts"]["approach"] == app, "count"].sum()),
               want, f"volume {app}")
    _close(_per_day(five_days, lambda t: (t["turn_counts"].query("vclass == 'moto'")["count"].sum()
                                          / t["turn_counts"]["count"].sum())),
           _t("G0_counts.moto_share"), "moto share")


def _queue_headways(tables, app):
    """(position, vclass, headway) of queued vehicles discharged after each green onset (cycles >= 0);
    the queue = vehicles of the lateral snapshot at that onset that have not crossed yet (early starters have left;
    box waiters, which crossed earlier, are not part of the discharge)."""
    cr = tables["stopline_crossings"]
    cr = cr[cr["approach"] == app].sort_values("t")
    lat = tables["lateral_snapshots"]
    lat = lat[lat["approach"] == app].merge(cr[["track_id", "t"]], on="track_id", how="left")
    on = _onsets(tables, app)
    lat = lat[~(lat["t"] < on[lat["cycle_id"].to_numpy()])]
    n_q = lat.groupby("cycle_id").size()
    out = []
    for k, g in enumerate(on):
        after = cr[cr["t"] >= g].head(int(n_q.get(k, 0)))
        h = np.diff(after["t"].to_numpy())
        out += [(n + 2, vc, x) for n, (vc, x) in enumerate(zip(after["vclass"].to_numpy()[1:], h))]
    return pd.DataFrame(out, columns=["pos", "vclass", "h"])


def test_m1_headways_match_targets(five_days):
    h = pd.concat([_queue_headways(_signalled(t), a) for t in five_days.values() for a in APPROACHES])
    sat = h[h["pos"] >= 15]
    hm = sat.loc[sat["vclass"] == "moto", "h"].mean()
    _close(hm, _t("M1_headway.moto_saturation_headway_s"), "moto saturation headway")
    _close(sat.loc[sat["vclass"] == "car", "h"].mean() / hm, _t("M1_headway.car_headway_factor"), "car factor")


def _rates(tables, kind):
    """Share of each approach x vclass volume crossing on red as early starter (last N s before green) or
    red runner (earlier in red); N = early_start_exclusion_s. Only crossings before the last observed green onset
    (a red crossing after it cannot be classified: the next onset is outside the window)."""
    excl = _t("M3_red_running.early_start_exclusion_s")
    cr, tr = tables["stopline_crossings"], tables["traversals"]
    out = {}
    for app in APPROACHES:
        on = _onsets(tables, app)
        mv = cr["track_id"].map(tr.set_index("track_id")["movement"])
        c = cr[(cr["approach"] == app) & (mv != "illegal_l") & (cr["t"] < on[-1])]
        nxt = on[np.searchsorted(on, c["t"].to_numpy(), side="left")]
        lead = nxt - c["t"].to_numpy()
        red = c["signal_state_at_t"].to_numpy() == "r"
        sel = red & ((lead > 0) & (lead <= excl) if kind == "early" else ~((lead > 0) & (lead <= excl)))
        for vc in VCLASSES:
            n = (c["vclass"] == vc).sum()
            out[(app, vc)] = (sel & (c["vclass"] == vc).to_numpy()).sum() / n
    return out


# Task F2-net: right turns of continuous-right approaches left the M2/M3 denominator, which changed the random stream
# of the generator. The D1-D5 realisation of two shares is then off by more than 15 % from noise alone (checked:
# LVL_W moto red over 20 seeds with unit day factors 0.0641 +- 0.0018 vs 0.0649; 8 other 5-day campaigns -5 ... +9 %;
# car early start over the same 8 campaigns -36 ... +39 %). Strict xfail, as for car red running.
_NOISE_LVL_W_RED = pytest.mark.xfail(strict=True, reason="D1-D5 realisation +17.6 % (noise, see comment above)")


@pytest.mark.parametrize("kind,key,app", [
    pytest.param(kind, key, app, marks=_NOISE_LVL_W_RED if (kind, app) == ("red", "LVL_W") else ())
    for kind, key in (("early", "M2_early_start.early_start_share"), ("red", "M3_red_running.red_run_share"))
    for app in APPROACHES])
def test_m2_m3_shares_match_targets(five_days, kind, key, app):
    want = _t(key)
    got = [_rates(_signalled(t), kind) for t in five_days.values()]
    _close(np.mean([g[(app, "moto")] for g in got]), want[app]["moto"], f"{kind} {app} moto")


@pytest.mark.parametrize("kind,key", [
    pytest.param("early", "M2_early_start.early_start_share", marks=pytest.mark.xfail(
        strict=True, reason="5 days too few: a handful of car early starts per day; D1-D5 raw mean -19 % vs nominal, "
                            "8 other campaigns -36 ... +39 % (noise, Task F2-net)")),
    pytest.param("red", "M3_red_running.red_run_share", marks=pytest.mark.xfail(
        strict=True, reason="5 days too few: ~20 car red-running events over D1-D5 (Poisson SE ~21 %); raw 5-day "
                            "mean -45 % vs nominal after Task F2-net (was +18.3 %); too few car events to test for bias "
                            "even over 36000 s; experiments/proxy_bias/bias_check.py: no bias over 200 campaigns")),
])
def test_m2_m3_car_shares_match_targets(five_days, kind, key):
    """Cars: a handful of events per day, pooled over approaches and days."""
    want = _t(key)
    pooled = np.mean([_rates(_signalled(t), kind)[(a, "car")] for t in five_days.values() for a in APPROACHES])
    _close(pooled, np.mean([want[a]["car"] for a in APPROACHES]), f"{kind} car")


def test_m3_per_cycle_dispersion(five_days):
    excl = _t("M3_red_running.early_start_exclusion_s")
    ratios = []
    for tables in five_days.values():
        cr = _signalled(tables)["stopline_crossings"]
        for app in APPROACHES:
            on = _onsets(tables, app)
            c = cr[(cr["approach"] == app) & (cr["signal_state_at_t"] == "r")]
            nxt = on[np.searchsorted(on, c["t"].to_numpy(), side="left").clip(max=len(on) - 1)]
            c = c[~((nxt - c["t"] > 0) & (nxt - c["t"] <= excl))]
            k = cycle_id_at(on, c["t"])
            counts = np.bincount(k[k >= 0], minlength=len(on))[:len(on) - 1]
            ratios.append(counts.var(ddof=1) / counts.mean())
    _close(float(np.mean(ratios)), _t("M3_red_running.per_cycle_var_to_mean"), "red runners var/mean")


def test_m2_first_crossing_delay(five_days):
    def delay(tables):
        cr = _signalled(tables)["stopline_crossings"]
        d = []
        for app in ("LVL_W", "LVL_E"):  # HDT has the M7c box effect on top
            t = np.sort(cr.loc[cr["approach"] == app, "t"].to_numpy())
            for g in _onsets(tables, app):
                d.append(t[np.searchsorted(t, g)] - g)
        return np.mean(d)
    _close(_per_day(five_days, delay), _t("M2_early_start.first_crossing_delay_s"), "first-crossing delay")


def test_m4_overshoot_share(five_days):
    def share(tables):
        """Halting motorcycles that have not crossed yet (box waiters crossed before the onset: not queued)."""
        lat = tables["lateral_snapshots"]
        crossed = lat["track_id"].map(tables["stopline_crossings"].set_index("track_id")["t"])
        onset = pd.Series({(a, k): g for a in APPROACHES for k, g in enumerate(_onsets(tables, a))})
        at = [onset[(a, k)] for a, k in zip(lat["approach"], lat["cycle_id"])]
        m = lat[(lat["vclass"] == "moto") & ~(crossed < np.array(at)).to_numpy()]
        return (m["long_m_from_stopline"] < 0).mean()
    _close(_per_day(five_days, share), _t("M4_lateral.overshoot_share_moto"), "overshoot share")


def test_m6_speeds(five_days, site):
    path = _targets()["geometry"]["path_length_m"]
    range_m = load_experiment()["observation"]["queue_range_m"]
    tr = pd.concat([t["traversals"] for t in five_days.values()])
    legal = tr[(tr["movement"] != "illegal_l") & tr["t_exit"].notna()]
    v = legal["movement"].map(path) / (legal["t_exit"] - legal["t_stopline"]) * 3.6
    want = _t("M6_traversal.crossing_speed_kmh")
    for vc in VCLASSES:
        _close(v[legal["vclass"] == vc].mean(), want[vc], f"crossing speed {vc}")
    # unimpeded approach: crossings in green, >= 30 s after green onset (queue cleared)
    rows = []
    for tables in five_days.values():
        t = tables["traversals"].merge(tables["stopline_crossings"][["track_id", "signal_state_at_t"]], on="track_id")
        for app in APPROACHES:
            on = _onsets(tables, app)
            a = t[(t["approach"] == app) & (t["signal_state_at_t"] == "G") & t["t_range_entry"].notna()]
            since = a["t_stopline"].to_numpy() - on[(cycle_id_at(on, a["t_stopline"])).clip(min=0)]
            rows.append(a[since >= 30])
    free = pd.concat(rows)
    va = range_m / (free["t_stopline"] - free["t_range_entry"]) * 3.6
    want = _t("M6_traversal.approach_speed_kmh")
    for vc in VCLASSES:
        _close(va[free["vclass"] == vc].mean(), want[vc], f"approach speed {vc}")


def test_m7_box_targets(five_days):
    box = pd.concat([t["box_queue"] for t in five_days.values()])
    _close(box["n_waiting_in_box"].mean(), _t("M7_illegal_left.n_waiting_in_box"), "n_waiting_in_box")
    lags, early, n_ent, exit_h = [], 0, 0, []
    for tables in five_days.values():
        tr = tables["traversals"]
        opp = np.sort(tr.loc[(tr["approach"] == "LVL_E") & (tr["movement"] == "s"), "t_stopline"].to_numpy())
        v = tr[tr["movement"] == "illegal_l"]
        cyc = cycle_id_at(_onsets(tables, "LVL_W"), v["t_stopline"])
        for r in tables["box_queue"].itertuples():
            ex = np.sort(v.loc[cyc == r.cycle_id, "t_exit"].dropna().to_numpy())
            n_ent += int((cyc == r.cycle_id).sum())
            early += int((ex < r.t).sum())
            late = ex[ex >= r.t]
            if len(late):
                before = opp[opp < late[0]]
                lags.append(late[0] - max(r.t, before[-1] if len(before) else -np.inf))
                exit_h += list(np.diff(late))
    _close(float(np.mean(lags)), _t("M7_illegal_left.clear_lag_s"), "clear lag (M7b)")
    _close(early / n_ent, _t("M7_illegal_left.early_leave_share"), "early leave share")
    _close(float(np.mean(exit_h)), _t("M7_illegal_left.box_exit_headway_s"), "box exit headway")


def test_m7c_crossing_start_delay_slope(five_days):
    x, y = [], []
    for tables in five_days.values():
        cr, box = _signalled(tables)["stopline_crossings"], tables["box_queue"]
        for app in ("HDT_N", "HDT_S"):
            t = np.sort(cr.loc[cr["approach"] == app, "t"].to_numpy())
            for g in _onsets(tables, app):
                prev = box[box["t"] <= g]
                if len(prev) and g - prev["t"].iloc[-1] < 60:
                    x.append(prev["n_waiting_in_box"].iloc[-1])
                    y.append(t[np.searchsorted(t, g)] - g)
    slope, intercept = np.polyfit(x, y, 1)
    _close(slope, _t("M7_illegal_left.crossing_start_delay_per_waiter_s"), "M7c slope")
    _close(intercept, _t("M2_early_start.first_crossing_delay_s"), "M7c intercept")


def test_m8_wrong_lane_share(five_days, site):
    lanes = {a["id"]: (np.cumsum(a["lane_widths_m"]), a["lane_movements"]) for a in site["approaches"]}
    want = _t("M8_wrong_lane.wrong_lane_share")
    tr = pd.concat([t["traversals"] for t in five_days.values()])
    turning = tr[tr["movement"].isin(["r", "l", "u"])]
    wrong = []
    for r in turning.itertuples():
        edges, mv = lanes[r.approach]
        lane = min(int(np.searchsorted(edges, r.lat_m_at_stopline, side="right")), len(mv) - 1)
        wrong.append(r.movement not in mv[lane])
    wrong = np.array(wrong)
    for vc in VCLASSES:
        _close(wrong[(turning["vclass"] == vc).to_numpy()].mean(), want[vc], f"wrong lane {vc}",
               )


# ------------------------------------------------------------------ F2 tables (Task F2-metrics)


def test_f2_stream_leaves_other_tables(tmp_path, site):
    """The F2 draws use their own stream (child 2 of the day's seed): with both choice probabilities 0 the
    pre-F2 tables are identical, except the range entry of the right-turners the riders blocked (moved earlier)."""
    tg = _targets()
    tg["targets"]["M9_right_lane"]["right_lane_choice_prob"]["value"] = {"moto": 0.0, "car": 0.0}
    tg["targets"]["M10_sidewalk"]["sidewalk_choice_prob"]["value"] = 0.0
    generate.generate_day(_targets(), site, "PROXY_D1", 101, tmp_path / "f2", day_factors=FACTORS["PROXY_D1"])
    generate.generate_day(tg, site, "PROXY_D1", 101, tmp_path / "none", day_factors=FACTORS["PROXY_D1"])
    a, b = _read(tmp_path / "f2"), _read(tmp_path / "none")
    for name in ("turn_counts", "signal_events", "stopline_crossings", "queue_snapshots", "lateral_snapshots",
                 "box_queue", "queue_timeseries"):
        assert a[name].equals(b[name]), name
    blocked = set(a["right_turn_delay"].loc[a["right_turn_delay"]["blocked"], "track_id"])
    assert blocked and not b["right_turn_delay"]["blocked"].any()
    same = ~a["traversals"]["track_id"].isin(blocked)
    assert a["traversals"][same].equals(b["traversals"][same])
    ta, tb = (t["traversals"].set_index("track_id").loc[sorted(blocked), "t_range_entry"] for t in (a, b))
    assert ((ta < tb) | ta.isna()).all()
    assert set(b["space_seeking_events"]["space"]) == {"wrong_lane"}


def test_f2_queue_timeseries_matches_snapshots(five_days):
    """queue_timeseries uses the snapshot packing: at green onsets on the 2 s grid the two agree up to the vehicles
    carried over from an earlier cycle (overshoot flag of their last queue), i.e. within a car length."""
    gaps = []
    for tables in five_days.values():
        q = tables["queue_timeseries"].set_index(["approach", "t"])["queue_length_m"]
        for r in tables["queue_snapshots"].itertuples():
            if (r.approach, r.t_green_onset) in q.index:
                gaps.append(abs(q[(r.approach, r.t_green_onset)] - r.queue_length_m))
    assert len(gaps) > 100
    assert np.median(gaps) == 0.0 and max(gaps) <= _targets()["geometry"]["car_length_m"] + 1e-6
    for tables in five_days.values():
        q = tables["queue_timeseries"]
        assert list(q["t"].unique()) == [2.0 * k for k in range(1800)]
        assert (q.groupby("t").size() == 4).all()


def _ramp(tables, approach, t):
    q = tables["queue_timeseries"]
    q = q[q["approach"] == approach].set_index("t")["queue_length_m"]
    grid = np.ceil(np.asarray(t, dtype=float) / 2.0) * 2.0
    ramp = _t("M9_right_lane.choice_ramp_queue_m")
    return np.minimum(q.reindex(np.round(grid, 2)).to_numpy() / ramp, 1.0)


def _f2_rates(five_days, site) -> tuple[Counter, Counter]:
    """(events, expected events) per (space, vclass): expected = sum over candidates of target x day factor x
    ramp(queue at the first grid time after the range entry); candidates = straight crossings with a range entry
    (traversals), day factors from the manifests."""
    sidewalk = set(site["f2_measured_approaches"])
    got, want = Counter(), Counter()
    for tables in five_days.values():
        f = tables["_day_factors"]
        tr = tables["traversals"]
        tr = tr[(tr["movement"] == "s") & tr["t_range_entry"].notna()]
        ev = tables["space_seeking_events"]
        for app, g in tr.groupby("approach"):
            ramp = _ramp(tables, app, g["t_range_entry"])
            for space, vc, key in [("right_lane", "moto", "M9_right_lane.right_lane_choice_prob"),
                                   ("right_lane", "car", "M9_right_lane.right_lane_choice_prob"),
                                   ("sidewalk", "moto", "M10_sidewalk.sidewalk_choice_prob")]:
                if space == "sidewalk" and app not in sidewalk:
                    continue
                sel = (g["vclass"] == vc).to_numpy()
                target = _t(key)[vc] if space == "right_lane" else _t(key)
                want[space, vc] += target * f.get(key, 1.0) * ramp[sel].sum()
                got[space, vc] += int(((ev["space"] == space) & ev["track_id"].isin(g.loc[sel, "track_id"])).sum())
    return got, want


@pytest.mark.parametrize("space,vc", [("right_lane", "moto"), ("right_lane", "car"), ("sidewalk", "moto")])
def test_f2_choice_rates_match_targets(five_days, site, space, vc):
    """Event counts are small (5 days: ~240 moto / ~16 car right-lane, ~60 sidewalk expected), so the check is
    Poisson: within 3 SD of the expected count. D1-D5 give moto right-lane 200 vs 239.5 (-2.6 SD), car 23 vs 15.5;
    not a bias: 30 independent one-day draws (seeds 201-230, day factor 1) give moto 1421 / 1459 (-2.6 %, SE ~2.6 %),
    car 85 / 94.5. Seeds are not re-rolled (ruling R40)."""
    got, want = _f2_rates(five_days, site)
    assert want[space, vc] > 10
    assert abs(got[space, vc] - want[space, vc]) <= 3 * math.sqrt(want[space, vc]), (space, vc, got, want)


def test_f2_wrong_lane_events_are_m8(five_days, site):
    """wrong_lane events = the turning crossings in a lane whose markings do not permit the movement (M8 rule), at
    the range entry (or the crossing if first seen inside the range)."""
    lanes = {a["id"]: (np.cumsum(a["lane_widths_m"]), a["lane_movements"]) for a in site["approaches"]}
    for tables in five_days.values():
        tr = tables["traversals"]
        want = {}
        for r in tr[tr["movement"].isin(["r", "l", "u"])].itertuples():
            edges, mv = lanes[r.approach]
            if r.movement not in mv[min(int(np.searchsorted(edges, r.lat_m_at_stopline, side="right")), len(mv) - 1)]:
                want[r.track_id] = r.t_stopline if np.isnan(r.t_range_entry) else r.t_range_entry
        ev = tables["space_seeking_events"]
        ev = ev[ev["space"] == "wrong_lane"]
        assert dict(zip(ev["track_id"], ev["t"])) == pytest.approx(want)


def test_f2_right_turn_delay_and_blocking(five_days, site):
    """right_turn_delay = the right-turn traversals (t_enter / t_exit = t_range_entry / t_stopline); blocked ones
    are in lane 0's band and come after a right-lane event of their approach."""
    w0 = {a["id"]: a["lane_widths_m"][0] for a in site["approaches"]}
    n_blocked = 0
    for tables in five_days.values():
        tr, rt, ev = tables["traversals"], tables["right_turn_delay"], tables["space_seeking_events"]
        r = tr[tr["movement"] == "r"]
        assert list(rt["track_id"]) == list(r["track_id"])
        assert np.allclose(rt["t_exit"], r["t_stopline"]) and np.allclose(rt["t_enter"], r["t_range_entry"], equal_nan=True)
        b = rt[rt["blocked"]].merge(tr[["track_id", "lat_m_at_stopline"]], on="track_id")
        assert (b["lat_m_at_stopline"] < b["approach"].map(w0)).all()
        first = ev[ev["space"] == "right_lane"].groupby("approach")["t"].min()
        assert (b["t_exit"].to_numpy() > b["approach"].map(first).to_numpy()).all()
        n_blocked += len(b)
    assert n_blocked > 50


def test_continuous_right_turns_never_wait(five_days, site):
    """Right-turners of continuous_right_lane approaches are not signal controlled: never in a queue snapshot,
    unimpeded from the range entry to the stop line (approach speed >= 10 km/h), so they cross in red as often
    as anyone arriving then; the metrics never classify them (M2/M3 classified set has none)."""
    from thesis_sumo.metrics.common import MetricContext
    from thesis_sumo.metrics.m2_early_start import classified
    cont = {a["id"] for a in site["approaches"] if a["continuous_right_lane"]}
    range_m = load_experiment()["observation"]["queue_range_m"]
    ctx = MetricContext.from_config(site=site)
    n_red = 0
    for tables in five_days.values():
        tr, cr = tables["traversals"], tables["stopline_crossings"]
        free = tr[tr["approach"].isin(cont) & (tr["movement"] == "r")]
        assert len(free)
        assert not set(free["track_id"]) & set(tables["lateral_snapshots"]["track_id"])
        blocked = tables["right_turn_delay"].loc[tables["right_turn_delay"]["blocked"], "track_id"]
        ok = free["t_range_entry"].notna() & ~free["track_id"].isin(blocked)  # F2: blocked behind a right-lane rider
        assert ((free.loc[ok, "t_stopline"] - free.loc[ok, "t_range_entry"]) <= range_m / (10 / 3.6) + 1e-6).all()
        n_red += int(cr[cr["track_id"].isin(free["track_id"])]["signal_state_at_t"].eq("r").sum())
        assert classified(tables, ctx).equals(classified(_signalled(tables), ctx))  # free right turns never classified
    assert n_red > 0  # they do cross in red, as allowed


def test_straight_only_in_lanes_marked_straight(five_days, site):
    """Straight vehicles cross the stop line only in lanes whose markings permit `s` (continuous right-turn lane 0
    is right only, Task F2-net); the committed days too."""
    lanes = {a["id"]: (np.cumsum(a["lane_widths_m"]), a["lane_movements"]) for a in site["approaches"]}
    days = [t["traversals"] for t in five_days.values()]
    days += [pd.read_csv(OBSERVED / day / "traversals.csv") for day in SEEDS]
    for tr in days:
        s = tr[(tr["movement"] == "s") & tr["lat_m_at_stopline"].notna()]
        assert len(s)
        for app, g in s.groupby("approach"):
            edges, mv = lanes[app]
            idx = np.minimum(np.searchsorted(edges, g["lat_m_at_stopline"].to_numpy(dtype=float), side="right"),
                             len(mv) - 1)
            assert all("s" in mv[i] for i in idx), app


# ------------------------------------------------------------------ targets file, committed days, routes, split


def _evidence_issues(node: dict, where: str) -> list[str]:
    """Every `[<prefix>]evidence` key is one of EVIDENCE; `literature_transferred` iff a `[<prefix>]transfer_note`."""
    bad = []
    for key, ev in node.items():
        if not key.endswith("evidence"):
            continue
        prefix = key[:-len("evidence")]
        note = node.get(f"{prefix}transfer_note")
        if ev not in EVIDENCE or (ev == "literature_transferred") != (isinstance(note, str) and bool(note.strip())):
            bad.append(f"{where}.{key}={ev}")
    return bad


def test_every_target_cites_source_and_evidence():
    targets, bad = _targets(), []
    for group, items in targets["targets"].items():
        for name, t in items.items():
            assert isinstance(t.get("source"), str) and t["source"].strip(), f"{group}.{name}"
            assert "evidence" in t, f"{group}.{name}"
            assert "family" in t and "between_day_cv" in t or t.get("derived"), f"{group}.{name}"
            bad += _evidence_issues(t, f"{group}.{name}")
    bad += _evidence_issues(targets, "<top>") + _evidence_issues(targets["geometry"], "geometry")
    assert bad == []
    for key in ("M2_early_start.early_start_share", "M3_red_running.red_run_share", "M4_lateral.overshoot_share_moto",
                "M1_headway.moto_saturation_headway_s", "G0_counts.moto_share"):  # ruling R13
        group, name = key.split(".")
        assert targets["targets"][group][name]["evidence"] == "literature_transferred", key


def test_day_factors_normalised(five_days):
    """Day factors (manifest) average to 1 over D1-D5 for every target, and still vary between days."""
    keys = {k for t in five_days.values() for k in t["_day_factors"]}
    for k in keys:
        f = [t["_day_factors"].get(k, 1.0) for t in five_days.values()]
        assert math.isclose(np.mean(f), 1.0, abs_tol=1e-5), k
        assert np.std(f) > 0, k
    cv = _targets()["targets"]["G0_counts"]["approach_volume_veh_h"]["between_day_cv"]
    assert "G0_counts.approach_volume_veh_h" in keys and cv > 0


def test_lateral_snapshots_include_box_waiters(tmp_path, site):
    """As in sim.outputs: halting illegal lefts still in the box at a green onset of their approach are in that
    onset's lateral snapshot (past the stop line). Clearing is delayed past the next onset to create some."""
    tg = _targets()
    tg["targets"]["M7_illegal_left"]["clear_lag_s"]["value"] = 70.0  # opposing green ends at 64 s, next onset 120 s
    generate.generate_day(tg, site, "X", 101, tmp_path, day_factors=FACTORS["PROXY_D1"])
    tables = _read(tmp_path)
    tr, lat = tables["traversals"], tables["lateral_snapshots"]
    v = tr[tr["movement"] == "illegal_l"]
    on = _onsets(tables, "LVL_W")
    want = {(k, r.track_id) for k, g in enumerate(on) for r in v.itertuples()
            if r.t_stopline <= g - generate.HALT_LEAD_S and not r.t_exit <= g}
    rows = lat[lat["track_id"].isin(set(v["track_id"])) & (lat["approach"] == "LVL_W")]
    in_box = rows.merge(v[["track_id", "t_stopline"]], on="track_id")
    in_box = in_box[in_box["t_stopline"] < on[in_box["cycle_id"].to_numpy()]]
    assert len(want) > 20
    assert set(zip(in_box["cycle_id"], in_box["track_id"])) == want
    assert (in_box["long_m_from_stopline"] < 0).all()
    path = tg["geometry"]["path_length_m"]["illegal_l"]
    assert (in_box["long_m_from_stopline"] >= -path).all()


def test_committed_days_reproducible(tmp_path, site):
    """The committed D1-D5 are what the generator writes for seeds 101-105 (lines compared, so a CRLF checkout
    with core.autocrlf still passes)."""
    for day, seed in SEEDS.items():
        generate.generate_day(_targets(), site, day, seed, tmp_path / day, day_factors=FACTORS[day])
        for name in TABLES:
            got = (tmp_path / day / f"{name}.csv").read_text(encoding="utf-8").splitlines()
            assert got == (OBSERVED / day / f"{name}.csv").read_text(encoding="utf-8").splitlines(), (day, name)


@pytest.mark.parametrize("day", list(SEEDS))
def test_routes_match_turn_counts(day):
    tc = pd.read_csv(OBSERVED / day / "turn_counts.csv")
    want = Counter()
    for r in tc.itertuples():
        want["moto_violator" if r.movement == "illegal_l" else r.vclass] += r.count
    got = Counter(v.get("type") for v in etree.parse(str(DEMAND / f"routes_{day}.rou.xml")).getroot().iter("vehicle"))
    assert got == +want


def test_measured_site_nulls_raise(tmp_path):
    """The generator reads the site through `require`: the measured site.yaml (nulls) raises, no fallback."""
    with pytest.raises(MissingFieldDataError):
        generate.generate_day(_targets(), load_site(), "X", 1, tmp_path)


def test_data_split():
    split = load_experiment()["data_split"]
    assert split["calibration_days"] == ["PROXY_D1", "PROXY_D2", "PROXY_D3"]
    assert split["validation_days"] == ["PROXY_D4", "PROXY_D5"]
