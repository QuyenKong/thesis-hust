"""Print versions of the Phase 3 waiting-area figures for the thesis (Latex_SOICT/Figure/).

    .venv/Scripts/python experiments/phase3/plot_box_vi.py [--only lateral occupancy]

- box_lateral_32m.png: halted illegal left-turners at each opposing-green end, pooled seeds, scenarios sat,
  sat_mg18, sat_tight of the `native` tag (3.2 m internal lane). Same data as box_capacity.figure_lateral.
- box_occupancy_f2.png: occupancy of the 3.5 m waiting area over time, seed 1, target / target_modopp of the
  `f2` tag. Same data as box_capacity.figure_occupancy.

Only the styling differs from box_capacity.py: Vietnamese labels, decimal comma, 15 cm wide at 9 pt, series
told apart by marker / line style and lightness so the figures read in black and white. Reads the saved run
files (waiters.csv, cycles.csv, box_steps.csv, tls_steps.csv); never re-simulates. A figure whose run files are
missing is skipped with an error message naming them.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import MultipleLocator, ScalarFormatter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from box_capacity import (LATERAL_FIGURE_SCENARIOS, RESULTS_DIR, SCENARIOS, _net_of,  # noqa: E402
                          link_indices, opposing_green, target_stats)

from thesis_sumo.config import REPO_ROOT  # noqa: E402
from thesis_sumo.sim.outputs import HALT_SPEED_MPS  # noqa: E402

FIG_DIR = REPO_ROOT.parent / "Latex_SOICT" / "Figure"
WIDTH_IN = 5.9  # \textwidth ~ 15 cm
INK, MUTED, GRID, SHADE = "#1a1a19", "#4a4944", "#dedcd6", "#e6e6e3"

# Width of the first box lane in the `native` runs. Their net (manifest net_hash 2d0eda46...) was built from a
# dirty tree and is neither in git nor in the LFS store, so the width cannot be read back with sumolib as
# box_capacity.figure_lateral did; 3.2 m is the width that figure drew (edges at +-1.6 m from lane.getWidth())
# and the netconvert default lane width the thesis cites for that net. The waiting point is not assumed: it is
# recovered from each run's cycles.csv (see waiting_point()).
NATIVE_BOX_LANE_WIDTH_M = 3.2

# lateral figure: scenario -> (label, colour, marker, filled). Dark / mid / light so greyscale keeps them apart.
LATERAL = {
    "sat": ("bão hòa, minGap 2,5 m (B0)", "#1d4f91", "o", True),
    "sat_mg18": ("bão hòa, minGap 1,8 m", "#e2641c", "s", False),
    "sat_tight": ("bão hòa, minGap 1,0 m, minGapLat 0,3 m", "#7cc4a0", "^", True),
}


class CommaFormatter(ScalarFormatter):
    """Default tick text with a decimal comma (independent of the OS locale)."""

    def __call__(self, x, pos=None):
        return super().__call__(x, pos).replace(".", ",")


def num(x: float, nd: int = 0) -> str:
    return f"{x:.{nd}f}".replace(".", ",").replace("-", "−")


def _style(ax) -> None:
    ax.grid(axis="y", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(MUTED)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.xaxis.set_major_formatter(CommaFormatter())
    ax.yaxis.set_major_formatter(CommaFormatter())


def _rows(tag: str) -> pd.DataFrame:
    return pd.read_csv(RESULTS_DIR / f"results_{tag}.csv")


def _missing(run_dirs, names) -> list[str]:
    return [f"{r}/{n}" for r in run_dirs for n in names if not (REPO_ROOT / r / n).is_file()]


def waiting_point(run_dirs) -> float:
    """End of the first box lane (front distance from the stop line), recovered per cycle as leader front +
    leader_gap_to_wait_point_m (box_capacity.analyse); must be one value across all runs."""
    vals = set()
    for r in run_dirs:
        w = pd.read_csv(REPO_ROOT / r / "waiters.csv")
        c = pd.read_csv(REPO_ROOT / r / "cycles.csv").set_index("cycle")
        wp = (w.groupby("cycle")["s"].max() + c["leader_gap_to_wait_point_m"]).dropna()
        vals |= set(np.round(wp.to_numpy(), 3))
    if len(vals) != 1:
        raise ValueError(f"waiting point differs between runs/cycles: {sorted(vals)}")
    return float(vals.pop())


def figure_lateral(out: Path) -> bool:
    rows = _rows("native")
    rows = rows[rows["scenario"].isin(LATERAL_FIGURE_SCENARIOS)]
    missing = _missing(rows["run_dir"], ("waiters.csv", "cycles.csv"))
    if missing:
        print("box_lateral: missing run files, figure not written:\n  " + "\n  ".join(missing))
        return False
    wp = waiting_point(rows["run_dir"])
    half = NATIVE_BOX_LANE_WIDTH_M / 2
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})
    fig, ax = plt.subplots(figsize=(WIDTH_IN, 3.4))
    for y in (-half, half):
        ax.axhline(y, color=MUTED, linewidth=0.9, zorder=1)
    ax.axvline(wp, color=INK, linewidth=1.0, linestyle="--", zorder=1)
    for sc in LATERAL_FIGURE_SCENARIOS:
        label, col, mk, filled = LATERAL[sc]
        w = pd.concat([pd.read_csv(REPO_ROOT / r / "waiters.csv") for r in rows[rows["scenario"] == sc]["run_dir"]])
        ax.scatter(w["s"], w["posLat"], s=26, marker=mk, linewidths=1.0, zorder=3,
                   facecolors=col if filled else "white", edgecolors=INK if filled else col,
                   label=f"{label}; {len(w)} điểm")
    ax.text(wp - 0.15, half + 0.08, "điểm chờ nội bộ", fontsize=9, color=INK, ha="right", va="bottom")
    ax.text(0.4, half + 0.08, "mép làn nội bộ (rộng 3,2 m)", fontsize=9, color=MUTED, ha="left", va="bottom")
    ax.set_xlim(0, 20)
    ax.set_ylim(-half - 0.35, half + 0.55)
    ax.xaxis.set_major_locator(MultipleLocator(2))
    ax.yaxis.set_major_locator(MultipleLocator(0.5))
    _style(ax)
    ax.set_xlabel("vị trí đầu xe tính từ vạch dừng nhánh Lê Văn Lương phía tây, dọc đường rẽ trái (m)",
                  fontsize=9, color=INK)
    ax.set_ylabel("vị trí ngang (m)", fontsize=9, color=INK)
    fig.legend(*ax.get_legend_handles_labels(), fontsize=9, frameon=False, loc="upper center", ncol=1,
               handletextpad=0.3, columnspacing=1.5)
    fig.tight_layout(rect=(0, 0, 1, 0.8))
    fig.savefig(out, dpi=200)
    plt.close(fig)
    print(f"box_lateral: waiting point {wp} m; wrote {out}")
    return True


def figure_occupancy(out: Path) -> bool:
    rows = _rows("f2")
    firsts = [rows[rows["scenario"] == sc].iloc[0] for sc in ("target", "target_modopp")]
    missing = _missing([f["run_dir"] for f in firsts], ("box_steps.csv", "tls_steps.csv", "run.sumocfg"))
    if missing:
        print("box_occupancy: missing run files, figure not written:\n  " + "\n  ".join(missing))
        return False
    tgt = target_stats()
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})
    fig, axes = plt.subplots(2, 1, figsize=(WIDTH_IN, 4.4), sharex=True, sharey=True)
    for ax, first in zip(axes, firsts):
        sc, rd = first["scenario"], REPO_ROOT / first["run_dir"]
        box = pd.read_csv(rd / "box_steps.csv")
        tls = pd.read_csv(rd / "tls_steps.csv", dtype={"state": str})
        on, off = opposing_green(tls, link_indices(_net_of(rd)).opposing_s)
        for a in on:
            ax.axvspan(a, off[off > a].min() if (off > a).any() else box["t"].max(), color=SHADE, linewidth=0)
        box["halt"] = box["speed"] < HALT_SPEED_MPS
        ts = box.groupby("t").agg(n=("veh", "nunique"), h=("halt", "sum"))
        ts = ts.reindex(np.round(np.arange(0, box["t"].max() + 0.05, 0.1), 2), fill_value=0)
        ax.plot(ts.index, ts["n"], color="#2a6fc4", linewidth=1.3, label="xe trên làn nội bộ")
        ax.plot(ts.index, ts["h"], color="#e2641c", linewidth=1.1, linestyle=(0, (4, 1.5)), label="xe đang dừng")
        for y, ls in ((tgt["waiting_mean"], "--"), (tgt["waiting_p90"], ":")):
            ax.axhline(y, color=INK, linewidth=0.9, linestyle=ls)
        opp = sum(SCENARIOS[sc].opposing_vph.values())
        ax.set_title(f"dòng đối diện {num(opp)} xe/h", fontsize=9.5, color=INK, loc="left")
        ax.set_ylabel("số xe", fontsize=9, color=INK)
        ax.yaxis.set_major_locator(MultipleLocator(5))
        _style(ax)
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    handles = [Line2D([], [], color="#2a6fc4", lw=1.5, label="xe trên làn nội bộ"),
               Line2D([], [], color="#e2641c", lw=1.3, linestyle=(0, (4, 1.5)), label="xe đang dừng"),
               Patch(facecolor=SHADE, edgecolor="none", label="xanh đi thẳng của dòng đối diện"),
               Line2D([], [], color=INK, lw=0.9, linestyle="--",
                      label=f"trung bình mục tiêu ({num(tgt['waiting_mean'])} xe)"),
               Line2D([], [], color=INK, lw=0.9, linestyle=":",
                      label=f"phân vị 90 ({num(tgt['waiting_p90'])} xe)")]
    fig.legend(handles=handles, loc="lower center", ncol=3, frameon=False, fontsize=9, columnspacing=1.2)
    axes[-1].set_xlabel("thời gian mô phỏng (s)", fontsize=9, color=INK)
    fig.tight_layout(rect=(0, 0.11, 1, 1))
    fig.savefig(out, dpi=200)
    plt.close(fig)
    print(f"box_occupancy: wrote {out}")
    return True


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--only", nargs="+", choices=["lateral", "occupancy"], default=["lateral", "occupancy"])
    args = ap.parse_args(argv)
    ok = True
    if "lateral" in args.only:
        ok &= figure_lateral(FIG_DIR / "box_lateral_32m.png")
    if "occupancy" in args.only:
        ok &= figure_occupancy(FIG_DIR / "box_occupancy_f2.png")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
