"""Behaviour counts of the benchmark BENCH_v1126 (VIDEO_V1 x seeds 1-20, net N7) next to the observed day VIDEO_V1.

Same metric columns as compare_video.py (compare_b0_b1/compare.py with M8 and without M10), for every spec that the
benchmark ran. Writes results/benchmark_v1126/counts.csv and summary.csv (mean, std, count per source).
Run from SUMO/: .venv/Scripts/python experiments/operator/n1126/bench_counts.py [--recount]
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compare_video as V  # noqa: E402  (sets the compare.py constants and row_from for N7)

C = V.C
from thesis_sumo.config import REPO_ROOT, load_experiment, load_site  # noqa: E402
from thesis_sumo.metrics.common import MetricContext  # noqa: E402

C.CAMPAIGN = REPO_ROOT / "experiments" / "campaigns" / "BENCH_v1126"
C.OUT = REPO_ROOT / "results" / "benchmark_v1126"
C.DAYS = ["VIDEO_V1"]
C.SEEDS = list(range(1, 21))
SPECS = ["B0", "B1_manual", "B2_v1126_best", "P1_v1126_best", "P2_v1126_best", "P2b_v1126_best"]
C.SPECS = {s: f"{s}__bench" for s in SPECS if (C.CAMPAIGN / "runs" / f"{s}__bench__VIDEO_V1").is_dir()}


def main():
    C.OUT.mkdir(parents=True, exist_ok=True)
    ctx = MetricContext.from_config(load_experiment(), site=load_site(REPO_ROOT / "config" / "site.yaml"))
    path = C.OUT / "counts.csv"
    if path.is_file() and "--recount" not in sys.argv:
        df = pd.read_csv(path)
    else:
        df = C.counts(ctx)
        df["source"] = df["source"].replace({"proxy": "VIDEO_V1"})
        df.to_csv(path, index=False)
    cols = [c for c in df.columns if c not in ("source", "day", "seed")]
    df.groupby("source")[cols].agg(["mean", "std", "count"]).to_csv(C.OUT / "summary.csv")
    pd.set_option("display.width", 250)
    print(df.groupby("source")[cols].mean().T.round(4).to_string())
    print(df.groupby("source")[cols].std().T.round(4).to_string())


if __name__ == "__main__":
    main()
