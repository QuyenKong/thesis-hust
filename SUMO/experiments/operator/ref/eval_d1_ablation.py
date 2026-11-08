"""Which part of B1 leaves vehicles waiting for insertion on PROXY_D1 (owner decision 1A, 2026-11-08)?
B0 has none on PROXY_D1 (REF_n1104s5, 5/5 runs eligible), B1_manual has 241-457 vehicles waiting at the end there.
B1_manual with TraCI rules removed one at a time (early_start and queue_space_seeking have every p = 0 in B1 and
never intervene, so only swarm_red_running and uturn_bypass are switched off), plus B1 with no rule at all (its vType
params only). PROXY_D1 x seed 1-3, campaign AB_d1. Prints per run the vehicles waiting for insertion at the end, the
maximum backlog during the run, teleports and collisions, and the TraCI intervention counts per variant.
Run from SUMO/: .venv/Scripts/python experiments/operator/ref/eval_d1_ablation.py (Linux: .venv/bin/python)"""
import copy
import json
import pickle
from pathlib import Path

from thesis_sumo.evaluate import CAMPAIGNS_DIR, RunBudget, evaluate_spec

CAMPAIGN = "AB_d1"
DAYS, SEEDS = ["PROXY_D1"], [1, 2, 3]
DROP = {"full": set(), "no_swarm": {"swarm_red_running"}, "no_uturn": {"uturn_bypass"},
        "no_rules": {"swarm_red_running", "uturn_bypass", "early_start", "queue_space_seeking"}}


def variant(base: dict, name: str) -> dict:
    spec = copy.deepcopy(base)
    spec["spec_id"] = f"B1_d1_{name}"
    spec["traci_rules"] = [r for r in spec["traci_rules"] if r["rule_type"] not in DROP[name]]
    spec["description"] = f"B1_manual without TraCI rules {sorted(DROP[name])} (eval_d1_ablation.py)"
    return spec


if __name__ == "__main__":  # the run pool spawns processes that re-import this file
    base = json.loads(Path("rules/specs/B1_manual.json").read_text(encoding="utf-8"))
    budget = RunBudget(len(DROP) * len(DAYS) * len(SEEDS), CAMPAIGN)
    for name in DROP:
        res = evaluate_spec(variant(base, name), DAYS, SEEDS, budget, campaign=CAMPAIGN,
                            site_path=Path("config/site.proxy.yaml"), nproc=len(SEEDS))
        (CAMPAIGNS_DIR / CAMPAIGN / f"{res.spec_id}.pkl").write_bytes(pickle.dumps(res))
        for run in res.runs:
            m = json.loads((Path(run["run_dir"]) / "manifest.json").read_text(encoding="utf-8"))
            print(f"{res.spec_id} seed {run['seed']}: waiting at end {m['insertion_backlog']}, max backlog "
                  f"{m['insertion_backlog_max']}, teleports {m.get('teleports')}, collisions/h "
                  f"{run['collisions_per_hour']:.1f} (lane {run['lane_collisions_per_hour']:.1f}), "
                  f"eligibility {run['eligibility']} {run['reasons']}", flush=True)
        print(f"{res.spec_id}: S {res.S:.4f}; interventions {res.interventions_summary}", flush=True)
