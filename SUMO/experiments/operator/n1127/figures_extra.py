"""Extra comparison figures of 2026-11-27 (decision D37): B0 (SUMO default, before calibration) against the final rule
set ("RS", best benchmark spec) on the validation day VIDEO_V1; observed day where a target exists.

  fig_D3_redpercycle_<s>.png  red-light crossings per cycle per approach: histogram B0 / RS / observed, var/mean noted
                              (20 seeds pooled)
  fig_D4_lateral_<s>.png      2-D density of stopped motorcycles at green onset (lateral position x distance to the
                              stop line), B0 | RS, one seed
  fig_D5_traj_<s>.png         vehicle paths within 70 m of the centre over one signal cycle, B0 | RS, one seed;
                              x = red-light crossing
  fig_D6_box_<s>.png          number of vehicles standing in the junction box (illegal-left waiters) over time,
                              B0 vs RS, one seed
  fig_D7_stability_<s>.png    collisions/h, lane collisions/h, jam teleports/h, end backlog (20 seeds, mean +- sd)

Run from SUMO/: .venv/Scripts/python experiments/operator/n1127/figures_extra.py --rs P2 [--campaign BENCH_v1127]
                [--suffix v1127] [--seed 1] [--out-dir ../Latex_SOICT/Figure]
"""
from __future__ import annotations

import argparse
import gzip
import json
import pickle
import xml.etree.ElementTree as ET
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import sumolib  # noqa: E402

from thesis_sumo.config import REPO_ROOT, load_experiment, load_site  # noqa: E402
from thesis_sumo.metrics.common import MetricContext  # noqa: E402
from thesis_sumo.metrics.m2_early_start import classified  # noqa: E402
from thesis_sumo.metrics.m3_red_running import _var_to_mean, per_cycle_counts  # noqa: E402
from thesis_sumo.metrics.common import read_tables  # noqa: E402
from thesis_sumo.sim.outputs import junction_geometry, scan_fcd  # noqa: E402

CAMP_DIR = REPO_ROOT / "experiments" / "campaigns"
OBS = REPO_ROOT / "data" / "observed"
DAY = "VIDEO_V1"
SEEDS = list(range(1, 21))
CYCLE = 160.0
WINDOW = (240.0, 2040.0)  # metric window of the runs (warm-up 240 s, 1800 s); VIDEO days start at 0
LABELS = {"B0": "B0", "B2": "B2_{s}_best", "P1": "P1_{s}_best", "P2": "P2_{s}_best"}
COL = {"B0": "#999999", "RS": "#0072B2", "obs": "#000000"}
B0_LONG = "B0: SUMO mặc định (trước hiệu chỉnh)"


def run_dir(campaign: str, stem: str, seed: int) -> Path:
    return CAMP_DIR / campaign / "runs" / f"{stem}__bench__{DAY}" / f"seed_{seed:02d}"


def rs_long(lb: str) -> str:
    return {"B2": "Bộ luật tốt nhất (B2, Optuna)", "P1": "Bộ luật tốt nhất (P1, LLM chỉ tham số)",
            "P2": "Bộ luật tốt nhất (P2, LLM tham số và luật)"}.get(lb, f"Bộ luật tốt nhất ({lb})")


def classified_ids(tables: dict, ctx) -> "pd.DataFrame":
    """m2_early_start.classified (M2/M3 kinds) with the vehicle id, joined back from stopline_crossings on
    (approach, vclass, t): classified keeps the crossing times as they are, so the join is exact."""
    c = classified(tables, ctx)
    cr = tables["stopline_crossings"][["approach", "vclass", "t", "track_id"]]
    return c.merge(cr, on=["approach", "vclass", "t"], how="left")


def red_per_cycle(tables: dict, ctx) -> np.ndarray:
    """Red runners per (approach, complete cycle) with the M3 definition (m3_red_running.per_cycle_counts: own-head
    and continuous right-turn movements left out), so the histogram matches the M3/per_cycle metric."""
    counts = per_cycle_counts(tables, ctx)
    return np.concatenate(list(counts.values())) if counts else np.array([])


def fig_d3(campaign, b0, rs, rs_lb, out):
    """Histogram pools every (approach, cycle) count; the legend's variance/mean is M3/var_to_mean (per run: mean over
    approaches with a non-zero mean of the per-cycle variance/mean; simulation: mean over the 20 runs), the value in
    profile.md."""
    ctx = MetricContext.from_config(load_experiment(), site=load_site(REPO_ROOT / "config" / "site.yaml"))
    data, vtm = {}, {}
    for key, stem in (("B0", b0), ("RS", rs)):
        per = [per_cycle_counts(read_tables(run_dir(campaign, stem, s)), ctx) for s in SEEDS
               if (run_dir(campaign, stem, s) / "observed_schema").is_dir()]
        data[key] = np.concatenate([np.concatenate(list(c.values())) for c in per if c])
        vtm[key] = float(np.nanmean([_var_to_mean(c) for c in per if c]))
    obs = per_cycle_counts(read_tables(OBS / DAY), ctx)
    data["obs"], vtm["obs"] = np.concatenate(list(obs.values())), _var_to_mean(obs)
    fig, ax = plt.subplots(figsize=(7.5, 3.8), layout="constrained")
    hi = int(max(v.max() for v in data.values())) + 1
    bins = np.arange(-0.5, hi + 1.5, 1)
    names = {"B0": B0_LONG, "RS": rs_long(rs_lb), "obs": "Ngày quan sát VIDEO_V1 (dữ liệu sinh)"}
    for i, (key, v) in enumerate(data.items()):
        h, _ = np.histogram(v, bins=bins)
        x = np.arange(len(h)) + (i - 1) * 0.28
        ax.bar(x, h / h.sum(), width=0.28, color=COL[key], edgecolor="black", linewidth=0.3,
               label=f"{names[key]}: TB {v.mean():.2f}, phương sai/TB {vtm[key]:.2f}")
    ax.set_xlabel("Số xe vượt đèn đỏ trong một chu kỳ ở một nhánh (định nghĩa M3)", fontsize=9)
    ax.set_ylabel("Tỷ lệ (chu kỳ × nhánh)", fontsize=9)
    ax.legend(fontsize=7.5, frameon=False)
    ax.tick_params(labelsize=8)
    fig.savefig(out, dpi=200)
    plt.close(fig)
    pooled = {k: float(v.var(ddof=1) / v.mean()) if v.mean() > 0 else float("nan") for k, v in data.items()}
    print("D3 var/mean (M3) ", vtm, " pooled over approaches (caption only):", pooled, flush=True)


def fig_d4(campaign, b0, rs, rs_lb, seed, out):
    fig, axes = plt.subplots(1, 2, figsize=(9, 4), sharex=True, sharey=True, layout="constrained")
    for ax, (key, stem) in zip(axes, (("B0", b0), ("RS", rs))):
        ls = read_tables(run_dir(campaign, stem, seed))["lateral_snapshots"]
        m = ls[ls["vclass"] == "moto"]
        hb = ax.hexbin(m["lat_m"], m["long_m_from_stopline"], gridsize=(28, 22), extent=(0, 16, -10, 60),
                       cmap="viridis", mincnt=1)
        ax.axhline(0, color="#D55E00", lw=1)
        ax.set_title(B0_LONG if key == "B0" else rs_long(rs_lb), fontsize=9)
        ax.set_xlabel("Vị trí ngang tính từ mép phải đường (m)", fontsize=8)
        ax.tick_params(labelsize=7)
    axes[0].set_ylabel("Khoảng cách tới vạch dừng (m; âm: đã qua vạch)", fontsize=8)
    fig.colorbar(hb, ax=axes, label="Số xe máy dừng lúc đầu pha xanh")
    fig.savefig(out, dpi=200)
    plt.close(fig)


def junction_centre(net: Path):
    n = sumolib.net.readNet(str(net))
    tls = [x for x in n.getNodes() if x.getType().startswith("traffic_light")]
    return max(tls, key=lambda x: len(x.getIncoming())).getCoord()


def read_xy(path: Path, t0: float, t1: float, centre, radius: float) -> pd.DataFrame:
    cx, cy = centre
    rec = []
    with gzip.open(path, "rb") as f:
        t = None
        for ev, el in ET.iterparse(f, events=("start", "end")):
            if ev == "start" and el.tag == "timestep":
                t = float(el.get("time"))
            elif ev == "end" and el.tag == "vehicle" and t is not None and t0 <= t < t1:
                x, y = float(el.get("x")) - cx, float(el.get("y")) - cy
                if x * x + y * y <= radius * radius:
                    rec.append((t, el.get("id"), el.get("type"), x, y))
                el.clear()
            elif ev == "end" and el.tag == "timestep":
                el.clear()
                if t is not None and t >= t1:
                    break
    return pd.DataFrame(rec, columns=["t", "id", "type", "x", "y"])


def fig_d5(campaign, b0, rs, rs_lb, seed, t0, out):
    net = REPO_ROOT / "scenario" / "net" / "site.net.xml"
    centre = junction_centre(net)
    t1 = t0 + CYCLE
    fig, axes = plt.subplots(1, 2, figsize=(10, 5.2), sharex=True, sharey=True, layout="constrained")
    for ax, (key, stem) in zip(axes, (("B0", b0), ("RS", rs))):
        d = run_dir(campaign, stem, seed)
        df = read_xy(d / "fcd.xml.gz", t0, t1, centre, 70.0)
        cls = np.where(df["type"].str.startswith("car"), "car", np.where(df["id"].str.contains("violator"), "viol", "moto"))
        df = df.assign(cls=cls)
        for c, col, lw in (("car", "#555555", 1.0), ("moto", "#0072B2", 0.5), ("viol", "#D55E00", 0.9)):
            for _, g in df[df.cls == c].groupby("id"):
                ax.plot(g.x, g.y, color=col, lw=lw, alpha=0.5)
        ctx = MetricContext.from_config(load_experiment(), site=load_site(REPO_ROOT / "config" / "site.yaml"))
        c = classified_ids(read_tables(d), ctx)  # M3 definition: red runners, not early starts / uncontrolled turns
        red = c[(c["kind"] == "red") & (c["t"] >= t0) & (c["t"] < t1)]
        pts = []
        for _, r in red.iterrows():
            g = df[df.id == r["track_id"]]
            if len(g):
                k = (g.t - r["t"]).abs().idxmin()
                pts.append((g.at[k, "x"], g.at[k, "y"]))
        if pts:
            p = np.array(pts)
            ax.scatter(p[:, 0], p[:, 1], marker="x", s=30, color="black", lw=1.3, zorder=5)
        ax.set_title(f"{B0_LONG if key == 'B0' else rs_long(rs_lb)}\n{df.id.nunique()} xe, {len(pts)} lượt vượt đèn đỏ",
                     fontsize=9)
        ax.set_aspect("equal")
        ax.set_xlim(-70, 70)
        ax.set_ylim(-70, 70)
        ax.tick_params(labelsize=7)
        ax.set_xlabel("x (m, gốc tại tâm nút)", fontsize=8)
    axes[0].set_ylabel("y (m)", fontsize=8)
    h = [plt.Line2D([], [], color=c, lw=1.5) for c in ("#0072B2", "#555555", "#D55E00")]
    h.append(plt.Line2D([], [], marker="x", ls="", color="black"))
    fig.legend(h, ["Xe máy", "Ô tô", "Xe máy lớp vi phạm", "Vị trí lúc vượt đèn đỏ (định nghĩa M3)"],
               loc="outside lower center", ncol=4, fontsize=8, frameon=False)
    fig.savefig(out, dpi=200)
    plt.close(fig)
    return t0, t1


def box_series(d: Path) -> pd.Series:
    """Vehicles standing (speed < 0.5 m/s) on the box lanes (illegal-left internal lanes) per second."""
    geo = junction_geometry(REPO_ROOT / "scenario" / "net" / "site.net.xml")
    scan = scan_fcd(d / "fcd.xml.gz", geo, set(), 80.0)
    b = scan.box_rows
    b = b[b.speed < 0.5]
    s = b.assign(sec=np.floor(b.t)).groupby("sec")["track_id"].nunique()
    return s.reindex(np.arange(0, 2040), fill_value=0)


def fig_d6(campaign, b0, rs, rs_lb, seed, out):
    fig, ax = plt.subplots(figsize=(9, 3.2), layout="constrained")
    for key, stem in (("B0", b0), ("RS", rs)):
        s = box_series(run_dir(campaign, stem, seed)).loc[WINDOW[0]:WINDOW[1]]
        ax.plot(s.index, s.values, color=COL[key], lw=0.9, label=B0_LONG if key == "B0" else rs_long(rs_lb))
    ax.set_xlabel("Thời gian mô phỏng (s)", fontsize=8)
    ax.set_ylabel("Xe rẽ trái cấm đứng chờ giữa nút", fontsize=8)
    ax.legend(fontsize=8, frameon=False)
    ax.tick_params(labelsize=7)
    fig.savefig(out, dpi=200)
    plt.close(fig)


def stability(campaign: str, stem: str) -> pd.DataFrame:
    res = pickle.loads((CAMP_DIR / campaign / f"{stem}.pkl").read_bytes())
    rows = []
    for r in res.runs:
        man = Path(r["run_dir"]) / "manifest.json"
        bl = json.loads(man.read_text(encoding="utf-8")).get("insertion_backlog") if man.is_file() else np.nan
        rows.append({"collisions_per_hour": r["collisions_per_hour"],
                     "lane_collisions_per_hour": r["lane_collisions_per_hour"],
                     "jam_yield_teleports_per_hour": r["jam_yield_teleports_per_hour"], "backlog": bl})
    return pd.DataFrame(rows)


def fig_d7(campaign, b0, rs, rs_lb, out):
    cols = [("collisions_per_hour", "Va chạm/h"), ("lane_collisions_per_hour", "Va chạm trên làn/h"),
            ("jam_yield_teleports_per_hour", "Teleport kẹt/h"), ("backlog", "Xe chờ vào mạng cuối lượt")]
    dfs = {"B0": stability(campaign, b0), "RS": stability(campaign, rs)}
    fig, axes = plt.subplots(1, 4, figsize=(10, 3), layout="constrained")
    for ax, (c, title) in zip(axes, cols):
        m = [dfs[k][c].mean() for k in ("B0", "RS")]
        s = [dfs[k][c].std() for k in ("B0", "RS")]
        ax.bar([0, 1], m, yerr=s, color=[COL["B0"], COL["RS"]], capsize=3, edgecolor="black", linewidth=0.4)
        ax.set_xticks([0, 1], ["B0", rs_lb], fontsize=8)
        ax.set_title(title, fontsize=9)
        ax.tick_params(axis="y", labelsize=7)
    fig.legend([plt.Rectangle((0, 0), 1, 1, color=COL[k]) for k in ("B0", "RS")], [B0_LONG, rs_long(rs_lb)],
               loc="outside lower center", ncol=2, fontsize=8, frameon=False)
    fig.savefig(out, dpi=200)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--campaign", default="BENCH_v1127")
    ap.add_argument("--suffix", default="v1127")
    ap.add_argument("--rs", required=True, help="label of the final rule set: B2 | P1 | P2")
    ap.add_argument("--rs-stem", default=None, help="spec file stem, default LABELS[rs] with the suffix")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--t0", type=float, default=None, help="start of the D5 cycle (default: 3rd cycle start, 480 s)")
    ap.add_argument("--out-dir", type=Path, default=REPO_ROOT.parent / "Latex_SOICT" / "Figure")
    a = ap.parse_args()
    b0 = "B0"
    rs = a.rs_stem or LABELS[a.rs].format(s=a.suffix)
    o, s = a.out_dir, a.suffix
    o.mkdir(parents=True, exist_ok=True)
    fig_d3(a.campaign, b0, rs, a.rs, o / f"fig_D3_redpercycle_{s}.png")
    fig_d4(a.campaign, b0, rs, a.rs, a.seed, o / f"fig_D4_lateral_{s}.png")
    win = fig_d5(a.campaign, b0, rs, a.rs, a.seed, a.t0 if a.t0 is not None else 480.0, o / f"fig_D5_traj_{s}.png")
    fig_d6(a.campaign, b0, rs, a.rs, a.seed, o / f"fig_D6_box_{s}.png")
    fig_d7(a.campaign, b0, rs, a.rs, o / f"fig_D7_stability_{s}.png")
    print("wrote D3-D7 to", o, "D5 window", win, flush=True)


if __name__ == "__main__":
    main()
