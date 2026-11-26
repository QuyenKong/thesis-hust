"""B0 vs B1 on REF_v1126 (net N7, junction LVL x HMG x NT) against the observed day VIDEO_V2.

Same tables and figure as experiments/operator/compare_b0_b1/compare.py (REF_n1104s5, proxy days), with the
constants of that script pointed at the 2026-11-26 campaign:
  results/compare_b0_b1_v1126/counts.csv, summary.csv: metric values per run (and for the observed day)
  ../Latex_SOICT/Figure/traj_b0_b1_v1126.png: vehicle paths near the centre over one signal cycle, B0 | B1.
VIDEO_V2 is generated from video targets (G0) and literature targets (other metrics), decisions D17-D19.

Run from SUMO/: .venv/Scripts/python experiments/operator/n1126/compare_video.py [--recount]
"""
from __future__ import annotations

import json
import sys

import pandas as pd

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1] / "compare_b0_b1"))
import compare as C  # noqa: E402

from thesis_sumo.config import REPO_ROOT, load_experiment, load_site  # noqa: E402
from thesis_sumo.metrics.common import MetricContext, read_tables  # noqa: E402
from thesis_sumo.metrics.distance import MODULES  # noqa: E402

C.CAMPAIGN = REPO_ROOT / "experiments" / "campaigns" / "REF_v1126"
C.OUT = REPO_ROOT / "results" / "compare_b0_b1_v1126"
C.DAYS = ["VIDEO_V2"]
C.SEEDS = [1, 2, 3, 4, 5]
C.TRAJ_DAY, C.TRAJ_SEED = "VIDEO_V2", 1
C.KEYS = {k: v for k, v in C.KEYS.items() if not k.startswith("M10")}  # no sidewalk on N7 (D25)
C.KEYS.update({"M8/moto": "wrong_lane_share_moto", "M8/car": "wrong_lane_share_car"})
FIG = REPO_ROOT.parent / "Latex_SOICT" / "Figure" / "traj_b0_b1_v1126.png"


def row_from(tables: dict, ctx: MetricContext) -> dict:
    """compare.row_from with M8 included: the REF_v1126 tables use the current M8 definition."""
    vals = {}
    for mod in MODULES:
        vals.update(mod.compute(tables, ctx))
    out = {col: (vals[key].mean() if key in vals else float("nan")) for key, col in C.KEYS.items()}
    sc = tables["stopline_crossings"]
    out["stopline_crossings_per_h"] = int(ctx.in_window(sc["t"]).sum()) * 3600.0 / (ctx.window[1] - ctx.window[0])
    return out


C.row_from = row_from
_traj = C.traj_figure


def traj_figure(ctx, path_png):
    """compare.traj_figure, but the cycle is taken from the green onsets of NT (HDT_S on the old nets)."""
    real_read = C.read_tables

    def read_renamed(path):
        t = real_read(path)
        t["signal_events"] = t["signal_events"].replace({"approach_group": {"NT": "HDT_S"}})
        return t

    C.read_tables = read_renamed
    try:
        return _traj(ctx, path_png)
    finally:
        C.read_tables = real_read


def main():
    C.OUT.mkdir(parents=True, exist_ok=True)
    ctx = MetricContext.from_config(load_experiment(), site=load_site(REPO_ROOT / "config" / "site.yaml"))
    if (C.OUT / "counts.csv").is_file() and "--recount" not in sys.argv:
        df = pd.read_csv(C.OUT / "counts.csv")
    else:
        df = C.counts(ctx)
        df["source"] = df["source"].replace({"proxy": "VIDEO_V2"})
        df.to_csv(C.OUT / "counts.csv", index=False)
    cols = [c for c in df.columns if c not in ("source", "day", "seed")]
    df.groupby("source")[cols].agg(["mean", "std", "count"]).to_csv(C.OUT / "summary.csv")
    print(df.groupby("source")[cols].mean().T.round(4).to_string())
    print(df.groupby("source")[cols].std().T.round(4).to_string())
    info = traj_figure(ctx, FIG)
    (C.OUT / "traj_info.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
    print(json.dumps(info, indent=2))


if __name__ == "__main__":
    main()
