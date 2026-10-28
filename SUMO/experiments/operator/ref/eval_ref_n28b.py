"""Reference rows for the interim report: B0 and B1_manual scored like a campaign spec (PROXY_D1-D3, seed 1, R44).
Campaign REF_n28b (budget 6, network of 2026-10-28 (round 2: open lane 0)). Run from SUMO/: .venv/bin/python experiments/operator/ref/eval_ref_n28b.py"""
import json
import pickle
from pathlib import Path

from thesis_sumo.evaluate import CAMPAIGNS_DIR, RunBudget, evaluate_spec

if __name__ == "__main__":  # the run pool spawns processes that re-import this file
    budget = RunBudget(6, "REF_n28b")
    for name in ["B0", "B1_manual"]:
        spec = json.loads(Path(f"rules/specs/{name}.json").read_text(encoding="utf-8"))
        res = evaluate_spec(spec, ["PROXY_D1", "PROXY_D2", "PROXY_D3"], [1], budget, campaign="REF_n28b",
                            site_path=Path("config/site.proxy.yaml"), nproc=3)
        (CAMPAIGNS_DIR / "REF_n28b" / f"{name}.pkl").write_bytes(pickle.dumps(res))
        r = res.to_row()
        print(name, {k: r.get(k) for k in ["eligibility", "collisions_per_hour", "lane_collisions_per_hour",
                                            "jam_yield_teleports_per_hour", "S"]}, flush=True)
