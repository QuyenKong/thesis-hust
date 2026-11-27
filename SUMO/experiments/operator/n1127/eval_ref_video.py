"""REF_v1127: B0 and B1_manual on the video calibration day VIDEO_V2 (seeds 1-5), net LVL x HMG x NT, measured site
(decisions D17-D23, signal plan D30, moto insertion D31). Gives the B0 lane-collision rate for the R10 cap of the B2 / P1 / P2 campaigns.
Run from SUMO/: .venv/Scripts/python experiments/operator/n1126/eval_ref_video.py"""
import json
import pickle
from pathlib import Path

from thesis_sumo.evaluate import CAMPAIGNS_DIR, RunBudget, evaluate_spec

CAMPAIGN = "REF_v1127"

if __name__ == "__main__":
    budget = RunBudget(10, CAMPAIGN)
    for name in ["B0", "B1_manual"]:
        spec = json.loads(Path(f"rules/specs/{name}.json").read_text(encoding="utf-8"))
        res = evaluate_spec(spec, ["VIDEO_V2"], [1, 2, 3, 4, 5], budget, campaign=CAMPAIGN,
                            site_path=Path("config/site.yaml"), nproc=10)
        (CAMPAIGNS_DIR / CAMPAIGN / f"{name}.pkl").write_bytes(pickle.dumps(res))
        r = res.to_row()
        print(name, {k: r.get(k) for k in ["eligibility", "collisions_per_hour", "lane_collisions_per_hour",
                                            "jam_yield_teleports_per_hour", "S"]}, flush=True)
