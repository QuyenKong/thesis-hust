"""Benchmark of 2026-11-27 (PLAN Phase 7): B0, B1_manual and the best spec of each campaign (B2_v1127, P1_v1127,
P2_v1127) on the validation day VIDEO_V1, seeds 1-20, net LVL x HMG x NT with the split LVL signal plan (D30) and
side-by-side motorcycle insertion (D31). LLM / Optuna never saw VIDEO_V1 (D19). Writes BENCH_v1127/<spec>.pkl and
results/benchmark_v1127.csv; reuses a spec's .pkl when it exists, skips a spec whose file is missing.
Run from SUMO/: .venv/Scripts/python experiments/operator/n1127/eval_benchmark_video.py"""
import json
import pickle
from pathlib import Path

import pandas as pd

from thesis_sumo.evaluate import CAMPAIGNS_DIR, RunBudget, evaluate_spec

CAMPAIGN = "BENCH_v1127"
SPECS = ["B0", "B1_manual", "B2_v1127_best", "P1_v1127_best", "P2_v1127_best"]
SEEDS = list(range(1, 21))

if __name__ == "__main__":
    specs = [s for s in SPECS if Path(f"rules/specs/{s}.json").is_file()]
    budget = RunBudget(len(SPECS) * len(SEEDS), CAMPAIGN)
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
    out = Path("results/benchmark_v1127.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out, index=False)
    print("wrote", out)
