"""B0 (SUMO defaults) vs B1 (hand-written rule set) on REF_n1104s5, against the proxy target days PROXY_D1-D3.

Two outputs, for the thesis chapter "Cài đặt và thực nghiệm":
  1. results/compare_b0_b1/counts.csv: per run (and per proxy day) the metric values of thesis_sumo.metrics
     (same definitions and window as the scoring), plus stop-line throughput; summary.csv: mean and SD per source.
  2. results/compare_b0_b1/traj_b0_b1.png: vehicle paths near the junction centre over one signal cycle, B0 and
     B1 side by side (same day, seed, time window); red-light crossings marked.
Nothing here is observed data: PROXY_D* are literature-proxy days (LITERATURE_PROXY), not video.

Run from SUMO/: .venv/bin/python (Windows: .venv/Scripts/python) experiments/operator/compare_b0_b1/compare.py
"""
from __future__ import annotations

import gzip
import sys
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sumolib

from thesis_sumo.config import REPO_ROOT, load_experiment, load_site
from thesis_sumo.metrics.common import MetricContext, read_tables
from thesis_sumo.metrics import m8_wrong_lane
from thesis_sumo.metrics.distance import MODULES
from thesis_sumo.metrics.m2_early_start import classified, crossings

CAMPAIGN = REPO_ROOT / "experiments" / "campaigns" / "REF_n1104s5"
OBSERVED = REPO_ROOT / "data" / "observed"
OUT = REPO_ROOT / "results" / "compare_b0_b1"
DAYS = ["PROXY_D1", "PROXY_D2", "PROXY_D3"]
SEEDS = [1, 2, 3, 4, 5]
SPECS = {"B0": "B0", "B1": "B1_manual"}

# metric key -> (column name, unit). Means of dist metrics are taken over the events of one run/day.
KEYS = {
    "M3/share/moto": "red_share_moto",
    "M3/share/car": "red_share_car",
    "M3/per_cycle": "red_per_cycle",
    "M2/early/moto": "early_share_moto",
    "M2/early/car": "early_share_car",
    "M4/overshoot_share": "overshoot_share_moto",
    "M7a/n_waiting": "box_waiting_per_cycle",
    "M9a/per_cycle": "right_lane_block_per_cycle",
    "M10a/per_cycle": "sidewalk_per_cycle",
}

TRAJ_DAY, TRAJ_SEED = "PROXY_D2", 1
TRAJ_RADIUS_M = 70.0
# colours: dataviz reference palette, categorical slots 1-2 (light mode) + neutral for context
C_CAR, C_MOTO, C_VIOL = "#9a9a95", "#2a78d6", "#eb6834"


def run_dir(spec: str, day: str, seed: int) -> Path:
    return CAMPAIGN / "runs" / f"{spec}__{day}" / f"seed_{seed:02d}"


def row_from(tables: dict, ctx: MetricContext) -> dict:
    # M8 is left out: REF_n1104s5 tables predate the 2026-11-08 M8 definition (lane read at the right-turn
    # stretch start) and would have to be regenerated
    vals = {}
    for mod in MODULES:
        if mod is not m8_wrong_lane:
            vals.update(mod.compute(tables, ctx))
    out = {}
    for key, col in KEYS.items():
        out[col] = vals[key].mean() if key in vals else np.nan
    sc = tables["stopline_crossings"]
    n = int(ctx.in_window(sc["t"]).sum())
    out["stopline_crossings_per_h"] = n * 3600.0 / (ctx.window[1] - ctx.window[0])
    return out


def counts(ctx: MetricContext) -> pd.DataFrame:
    rows = []
    for day in DAYS:
        rows.append({"source": "proxy", "day": day, "seed": None, **row_from(read_tables(OBSERVED / day), ctx)})
    for label, spec in SPECS.items():
        for day in DAYS:
            for seed in SEEDS:
                rows.append({"source": label, "day": day, "seed": seed,
                             **row_from(read_tables(run_dir(spec, day, seed)), ctx)})
    return pd.DataFrame(rows)


def junction_centre(net_path: Path) -> tuple[float, float]:
    net = sumolib.net.readNet(str(net_path))
    tls = [n for n in net.getNodes() if n.getType().startswith("traffic_light")]
    node = max(tls, key=lambda n: len(n.getIncoming()))
    return node.getCoord()


def read_fcd(path: Path, t0: float, t1: float, centre, radius: float) -> pd.DataFrame:
    cx, cy = centre
    recs = []
    with gzip.open(path, "rb") as f:
        t = None
        for ev, el in ET.iterparse(f, events=("start", "end")):
            if ev == "start" and el.tag == "timestep":
                t = float(el.get("time"))
            elif ev == "end" and el.tag == "vehicle" and t is not None and t0 <= t < t1:
                x, y = float(el.get("x")), float(el.get("y"))
                if (x - cx) ** 2 + (y - cy) ** 2 <= radius ** 2:
                    recs.append((t, el.get("id"), el.get("type"), x - cx, y - cy))
            elif ev == "end" and el.tag == "timestep":
                el.clear()
                if t is not None and t >= t1:
                    break
    return pd.DataFrame(recs, columns=["t", "id", "type", "x", "y"])


def red_crossings(tables: dict, ctx: MetricContext, t0: float, t1: float) -> pd.DataFrame:
    c = classified(tables, ctx)
    c = c[(c["kind"] == "red") & (c["t"] >= t0) & (c["t"] < t1)]
    # classified() drops track ids; recover them from the crossings it was built from (same approach and time)
    cr = crossings(tables)[["approach", "t", "track_id"]]
    return c.merge(cr, on=["approach", "t"], how="left")[["t", "track_id"]]


def traj_figure(ctx: MetricContext, path_png: Path) -> dict:
    exp = load_experiment()
    man = json.loads((run_dir("B0", TRAJ_DAY, TRAJ_SEED) / "manifest.json").read_text(encoding="utf-8"))
    centre = junction_centre(REPO_ROOT / man["net"])
    # one full signal cycle after warm-up: from the 2nd green onset of HDT_S inside the metric window
    sig = read_tables(run_dir("B0", TRAJ_DAY, TRAJ_SEED))["signal_events"]
    on = sig[(sig["approach_group"] == "HDT_S") & (sig["state"].str.upper() == "G")]["t"].to_numpy()
    on = on[(on >= ctx.window[0]) & (on < ctx.window[1])]
    # the B1 cycle with the most red-light crossings (red running comes in bursts; most cycles have none).
    # The choice is stated in the figure caption; the per-run means are in counts.csv.
    red_b1 = classified(read_tables(run_dir("B1_manual", TRAJ_DAY, TRAJ_SEED)), ctx)
    red_b1 = red_b1.loc[red_b1["kind"] == "red", "t"].to_numpy()
    n_red = [int(((red_b1 >= a) & (red_b1 < b)).sum()) for a, b in zip(on[:-1], on[1:])]
    k = int(np.argmax(n_red))
    t0, t1 = float(on[k]), float(on[k + 1])
    fig, axes = plt.subplots(1, 2, figsize=(10, 5.2), sharex=True, sharey=True)
    info = {"window_s": [t0, t1], "centre": list(centre)}
    for ax, (label, spec) in zip(axes, SPECS.items()):
        rd = run_dir(spec, TRAJ_DAY, TRAJ_SEED)
        df = read_fcd(rd / "fcd.xml.gz", t0, t1, centre, TRAJ_RADIUS_M)
        df["cls"] = np.where(df["type"].str.startswith("car"), "car",
                             np.where(df["id"].str.contains("violator"), "viol", "moto"))
        for cls, col, lw, z in (("car", C_CAR, 1.0, 1), ("moto", C_MOTO, 0.6, 2), ("viol", C_VIOL, 0.9, 3)):
            for _, g in df[df["cls"] == cls].groupby("id"):
                ax.plot(g["x"], g["y"], color=col, lw=lw, alpha=0.55, zorder=z)
        rc = red_crossings(read_tables(rd), ctx, t0, t1)
        pts = []
        for _, r in rc.iterrows():
            g = df[(df["id"] == r["track_id"])]
            if len(g):
                k = (g["t"] - r["t"]).abs().idxmin()
                pts.append((g.at[k, "x"], g.at[k, "y"]))
        if pts:
            p = np.array(pts)
            ax.scatter(p[:, 0], p[:, 1], marker="x", s=36, color="#1a1a19", lw=1.4, zorder=5)
        n_veh = df["id"].nunique()
        ax.set_title(f"{label}: {n_veh} xe, {len(pts)} lượt vượt đèn đỏ", fontsize=11)
        ax.set_aspect("equal")
        ax.set_xlim(-TRAJ_RADIUS_M, TRAJ_RADIUS_M)
        ax.set_ylim(-TRAJ_RADIUS_M, TRAJ_RADIUS_M)
        ax.tick_params(labelsize=8, colors="#6b6a63")
        for s in ax.spines.values():
            s.set_color("#c3c2b7")
        ax.set_xlabel("x so với tâm nút (m)", fontsize=9)
        info[label] = {"vehicles": int(n_veh), "red_crossings_drawn": len(pts), "red_crossings": int(len(rc))}
    axes[0].set_ylabel("y so với tâm nút (m)", fontsize=9)
    from matplotlib.lines import Line2D
    handles = [Line2D([], [], color=C_CAR, lw=2, label="ô tô"),
               Line2D([], [], color=C_MOTO, lw=2, label="xe máy"),
               Line2D([], [], color=C_VIOL, lw=2, label="xe máy nhóm vi phạm"),
               Line2D([], [], color="#1a1a19", marker="x", lw=0, label="vị trí lúc vượt vạch khi đèn đỏ")]
    fig.legend(handles=handles, loc="lower center", ncol=4, frameon=False, fontsize=9)
    fig.tight_layout(rect=(0, 0.07, 1, 0.95))
    fig.savefig(path_png, dpi=200)
    plt.close(fig)
    return info


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ctx = MetricContext.from_config(load_experiment(), site=load_site(REPO_ROOT / "config" / "site.proxy.yaml"))
    if (OUT / "counts.csv").is_file() and "--recount" not in sys.argv:
        df = pd.read_csv(OUT / "counts.csv")
    else:
        df = counts(ctx)
        df.to_csv(OUT / "counts.csv", index=False)
    cols = [c for c in df.columns if c not in ("source", "day", "seed")]
    summ = df.groupby("source")[cols].agg(["mean", "std", "count"])
    summ.to_csv(OUT / "summary.csv")
    print(df.groupby("source")[cols].mean().T.round(4).to_string())
    info = traj_figure(ctx, OUT / "traj_b0_b1.png")
    (OUT / "traj_info.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
    print(json.dumps(info, indent=2))


if __name__ == "__main__":
    main()
