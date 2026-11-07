"""Feasibility of the cut-back wrong lane (2026-11-08): B1_cut_back (B1_manual + queue_space_seeking p_wrong_lane 0.5 on
moto_seeker and car_seeker) on PROXY_D1-D3 x seed 1, campaign AB_cut; compare with REF_n1104s5 B1_manual seed 1.
Run from SUMO/: .venv/Scripts/python experiments/operator/ref/eval_cut_back.py (Linux: .venv/bin/python)"""
import json
import pickle
from pathlib import Path

from thesis_sumo.evaluate import CAMPAIGNS_DIR, RunBudget, evaluate_spec

if __name__ == "__main__":  # the run pool spawns processes that re-import this file
    budget = RunBudget(3, "AB_cut")
    spec = json.loads(Path("rules/specs/B1_cut_back.json").read_text(encoding="utf-8"))
    res = evaluate_spec(spec, ["PROXY_D1", "PROXY_D2", "PROXY_D3"], [1], budget, campaign="AB_cut",
                        site_path=Path("config/site.proxy.yaml"), nproc=3)
    (CAMPAIGNS_DIR / "AB_cut" / "B1_cut_back.pkl").write_bytes(pickle.dumps(res))
    r = res.to_row()
    print("B1_cut_back", {k: r.get(k) for k in ["eligibility", "collisions_per_hour", "lane_collisions_per_hour",
                                                "jam_yield_teleports_per_hour", "S"]}, flush=True)
    print(res.interventions_summary, flush=True)
