"""Reference rows for the interim report: B0 and B1_manual scored like a campaign spec (PROXY_D1-D3, seeds 1-5, R44).
Campaign REF_n1104s5 (budget 30, 5 seeds, net of 2026-11-04: lane-0 stretch 30 m without the violator left and U-turn links; swarm_red_running enters only a clear junction (D1); B1_manual with uturn_bypass (D2)). Run from SUMO/: .venv/bin/python (Windows: .venv/Scripts/python) experiments/operator/ref/eval_ref_n1104_s5.py"""
import json
import pickle
from pathlib import Path

from thesis_sumo.evaluate import CAMPAIGNS_DIR, RunBudget, evaluate_spec

if __name__ == "__main__":  # the run pool spawns processes that re-import this file
    budget = RunBudget(30, "REF_n1104s5")
    for name in ["B0", "B1_manual"]:
        spec = json.loads(Path(f"rules/specs/{name}.json").read_text(encoding="utf-8"))
        res = evaluate_spec(spec, ["PROXY_D1", "PROXY_D2", "PROXY_D3"], [1, 2, 3, 4, 5], budget, campaign="REF_n1104s5",
                            site_path=Path("config/site.proxy.yaml"), nproc=6)
        (CAMPAIGNS_DIR / "REF_n1104s5" / f"{name}.pkl").write_bytes(pickle.dumps(res))
        r = res.to_row()
        print(name, {k: r.get(k) for k in ["eligibility", "collisions_per_hour", "lane_collisions_per_hour",
                                            "jam_yield_teleports_per_hour", "S"]}, flush=True)
