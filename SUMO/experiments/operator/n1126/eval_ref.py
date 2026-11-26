"""Reference rows on the LVL x HMG x NT net (2026-11-26): B0 and B1_manual scored like a campaign spec on the
LITERATURE_PROXY days PROXY_D1-D3, seeds 1-5. Pipeline check on the new net, not a thesis result (owner 2026-11-26:
"chay thu PROXY song song"). Run from SUMO/: .venv/Scripts/python experiments/operator/n1126/eval_ref.py"""
import json
import pickle
from pathlib import Path

from thesis_sumo.evaluate import CAMPAIGNS_DIR, RunBudget, evaluate_spec

CAMPAIGN = "REF_n1126"

if __name__ == "__main__":  # the run pool spawns processes that re-import this file
    budget = RunBudget(30, CAMPAIGN)
    for name in ["B0", "B1_manual"]:
        spec = json.loads(Path(f"rules/specs/{name}.json").read_text(encoding="utf-8"))
        res = evaluate_spec(spec, ["PROXY_D1", "PROXY_D2", "PROXY_D3"], [1, 2, 3, 4, 5], budget, campaign=CAMPAIGN,
                            site_path=Path("config/site.proxy.yaml"), nproc=10)
        (CAMPAIGNS_DIR / CAMPAIGN / f"{name}.pkl").write_bytes(pickle.dumps(res))
        r = res.to_row()
        print(name, {k: r.get(k) for k in ["eligibility", "collisions_per_hour", "lane_collisions_per_hour",
                                            "jam_yield_teleports_per_hour", "S"]}, flush=True)
