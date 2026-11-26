"""Print version of the B0/B1 trajectory figure for the thesis (Latex_SOICT/Figure/traj_b0_b1.png).

Same data and cycle choice as compare.py's traj_figure (REF_n1104s5, PROXY_D2, seed 1, the B1 cycle with the
most red-light crossings); only the styling differs: Vietnamese labels, decimal comma on ticks, 15 cm wide at
9 pt, and the three vehicle classes told apart by line width / dash pattern and lightness as well as colour so
the figure reads in black and white. Needs the raw fcd.xml.gz of both runs (git-ignored, not re-simulated here).

Run from SUMO/: .venv/Scripts/python (Linux: .venv/bin/python) experiments/operator/compare_b0_b1/plot_traj_vi.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.ticker import ScalarFormatter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compare import (OUT, SPECS, TRAJ_DAY, TRAJ_RADIUS_M, TRAJ_SEED, junction_centre,  # noqa: E402
                     read_fcd, red_crossings, run_dir)

from thesis_sumo.config import REPO_ROOT, load_experiment, load_site  # noqa: E402
from thesis_sumo.metrics.common import MetricContext, read_tables  # noqa: E402
from thesis_sumo.metrics.m2_early_start import classified  # noqa: E402

FIG_OUT = REPO_ROOT.parent / "Latex_SOICT" / "Figure" / "traj_b0_b1.png"
WIDTH_IN = 5.9  # \textwidth ~ 15 cm

# (colour, line width, dash pattern, z-order). Lightness differs (grey L~74%, blue ~50%, orange drawn dashed and
# thicker on top) so the classes stay apart in greyscale; the colours match the caption (grey / blue / orange).
STYLE = {
    "car": ("#b4b4ae", 1.1, None, 1),
    "moto": ("#2a6fc4", 0.45, None, 2),
    "viol": ("#e2641c", 1.2, (0, (3.5, 1.5)), 3),
}
INK, MUTED, FRAME = "#1a1a19", "#4a4944", "#9c9b94"


class CommaFormatter(ScalarFormatter):
    """Default tick text with a decimal comma (independent of the OS locale)."""

    def __call__(self, x, pos=None):
        return super().__call__(x, pos).replace(".", ",")


def main() -> None:
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.unicode_minus": True})
    ctx = MetricContext.from_config(load_experiment(), site=load_site(REPO_ROOT / "config" / "site.proxy.yaml"))
    man = json.loads((run_dir("B0", TRAJ_DAY, TRAJ_SEED) / "manifest.json").read_text(encoding="utf-8"))
    centre = junction_centre(REPO_ROOT / man["net"])
    # cycle choice: identical to compare.traj_figure
    sig = read_tables(run_dir("B0", TRAJ_DAY, TRAJ_SEED))["signal_events"]
    on = sig[(sig["approach_group"] == "HDT_S") & (sig["state"].str.upper() == "G")]["t"].to_numpy()
    on = on[(on >= ctx.window[0]) & (on < ctx.window[1])]
    red_b1 = classified(read_tables(run_dir("B1_manual", TRAJ_DAY, TRAJ_SEED)), ctx)
    red_b1 = red_b1.loc[red_b1["kind"] == "red", "t"].to_numpy()
    n_red = [int(((red_b1 >= a) & (red_b1 < b)).sum()) for a, b in zip(on[:-1], on[1:])]
    k = int(np.argmax(n_red))
    t0, t1 = float(on[k]), float(on[k + 1])

    fig, axes = plt.subplots(1, 2, figsize=(WIDTH_IN, 3.55), sharex=True, sharey=True)
    info = {"window_s": [t0, t1], "centre": list(centre)}
    for ax, (label, spec) in zip(axes, SPECS.items()):
        rd = run_dir(spec, TRAJ_DAY, TRAJ_SEED)
        df = read_fcd(rd / "fcd.xml.gz", t0, t1, centre, TRAJ_RADIUS_M)
        df["cls"] = np.where(df["type"].str.startswith("car"), "car",
                             np.where(df["id"].str.contains("violator"), "viol", "moto"))
        for cls, (col, lw, ls, z) in STYLE.items():
            for _, g in df[df["cls"] == cls].groupby("id"):
                ax.plot(g["x"], g["y"], color=col, lw=lw, linestyle=ls if ls else "-", alpha=0.8, zorder=z)
        rc = red_crossings(read_tables(rd), ctx, t0, t1)
        pts = []
        for _, r in rc.iterrows():
            g = df[(df["id"] == r["track_id"])]
            if len(g):
                j = (g["t"] - r["t"]).abs().idxmin()
                pts.append((g.at[j, "x"], g.at[j, "y"]))
        if pts:
            p = np.array(pts)
            ax.scatter(p[:, 0], p[:, 1], marker="x", s=30, color=INK, lw=1.3, zorder=5)
        n_veh = df["id"].nunique()
        ax.set_title(f"{label}: {n_veh} xe, {len(pts)} lượt vượt đèn đỏ", fontsize=9.5, color=INK)
        ax.set_aspect("equal")
        ax.set_xlim(-TRAJ_RADIUS_M, TRAJ_RADIUS_M)
        ax.set_ylim(-TRAJ_RADIUS_M, TRAJ_RADIUS_M)
        ax.set_xticks(np.arange(-60, 61, 30))
        ax.set_yticks(np.arange(-60, 61, 30))
        for a in (ax.xaxis, ax.yaxis):
            a.set_major_formatter(CommaFormatter())
        ax.tick_params(labelsize=9, colors=MUTED)
        for s in ax.spines.values():
            s.set_color(FRAME)
        ax.set_xlabel("x so với tâm nút (m)", fontsize=9, color=INK)
        info[label] = {"vehicles": int(n_veh), "red_crossings_drawn": len(pts), "red_crossings": int(len(rc))}
    axes[0].set_ylabel("y so với tâm nút (m)", fontsize=9, color=INK)
    handles = [Line2D([], [], color=STYLE["car"][0], lw=2.2, label="ô tô"),
               Line2D([], [], color=STYLE["moto"][0], lw=1.4, label="xe máy"),
               Line2D([], [], color=STYLE["viol"][0], lw=2.0, linestyle=(0, (3.5, 1.5)), label="xe máy lớp vi phạm"),
               Line2D([], [], color=INK, marker="x", lw=0, markersize=6, label="vượt đèn đỏ")]
    fig.legend(handles=handles, loc="lower center", ncol=4, frameon=False, fontsize=9, handlelength=2.4,
               columnspacing=1.4)
    fig.tight_layout(rect=(0, 0.075, 1, 1), w_pad=1.2)
    fig.savefig(FIG_OUT, dpi=200)
    plt.close(fig)

    ref = OUT / "traj_info.json"  # written by compare.py; the print figure must show the same cycle and counts
    if ref.is_file():
        old = json.loads(ref.read_text(encoding="utf-8"))
        same = (old["window_s"] == info["window_s"]
                and all(old[s] == info[s] for s in SPECS))
        print("matches traj_info.json:", same)
    print(json.dumps(info, indent=2))
    print("wrote", FIG_OUT)


if __name__ == "__main__":
    main()
