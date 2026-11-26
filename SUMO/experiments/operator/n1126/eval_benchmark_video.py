"""Benchmark of 2026-11-26 (PLAN Phase 7): B0, B1_manual and the best spec of each campaign (B2_v1126, P1_v1126,
P2_v1126) on the validation day VIDEO_V1, seeds 1-20, net LVL x HMG x NT, measured site. LLM / Optuna never saw
VIDEO_V1 (decision D19: same G0 targets as VIDEO_V2, new seed and day factor). Writes BENCH_v1126/<spec>.pkl and
results/benchmark_v1126.csv. Run from SUMO/: .venv/Scripts/python experiments/operator/n1126/eval_benchmark_video.py"""
import json
import pickle
from pathlib import Path

import pandas as pd

from thesis_sumo.evaluate import CAMPAIGNS_DIR, RunBudget, evaluate_spec

CAMPAIGN = "BENCH_v1126"
SPECS = ["B0", "B1_manual", "B2_v1126_best", "P1_v1126_best", "P2_v1126_best", "P2b_v1126_best"]  # P2b: D29
SEEDS = list(range(1, 21))

if __name__ == "__main__":
    specs = [s for s in SPECS if Path(f"rules/specs/{s}.json").is_file()]
    budget = RunBudget(len(specs) * len(SEEDS), CAMPAIGN)
    rows = []
    for name in specs:
        pkl = CAMPAIGNS_DIR / CAMPAIGN / f"{name}.pkl"
        if pkl.is_file():
            res = pickle.loads(pkl.read_bytes())
        else:
            spec = json.loads(Path(f"rules/specs/{name}.json").read_text(encoding="utf-8"))
            spec = {**spec, "spec_id": f"{name}__bench"}
            res = evaluate_spec(spec, ["VIDEO_V1"], SEEDS, budget, campaign=CAMPAIGN,
                                site_path=Path("config/site.yaml"), nproc=12, allow_validation=True)
            pkl.write_bytes(pickle.dumps(res))
        row = {"spec": name, **res.to_row()}
        rows.append(row)
        print(name, {k: row.get(k) for k in ("eligibility", "S", "collisions_per_hour", "lane_collisions_per_hour",
                                              "jam_yield_teleports_per_hour")}, flush=True)
    out = Path("results/benchmark_v1126.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out, index=False)
    print("wrote", out)
