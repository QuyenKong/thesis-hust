"""Follow-up of eval_d1_ablation.py (2026-11-08): B1 without any TraCI rule still leaves 203-387 vehicles waiting for
insertion on PROXY_D1, B0 none, so B1's vType params cause it. Two variants of B1 without rules, PROXY_D1 x seed 1-3,
campaign AB_d1v: `car_b0` = car archetypes with B0's params (SUMO defaults; B1 has accel 1.2, decel 4.8, tau 2.5,
minGap 1.1), `moto_accel_b0` = motorcycle archetypes without accel (SUMO default; B1 has 1.1 m/s^2), rest of B1 kept.
Run from SUMO/: .venv/Scripts/python experiments/operator/ref/eval_d1_vtype.py (Linux: .venv/bin/python)"""
import copy
import json
import pickle
from pathlib import Path

from thesis_sumo.evaluate import CAMPAIGNS_DIR, RunBudget, evaluate_spec

CAMPAIGN = "AB_d1v"
DAYS, SEEDS = ["PROXY_D1"], [1, 2, 3]
CARS, MOTOS = ("passenger", "custom2"), ("motorcycle", "custom1")


def variant(base: dict, name: str) -> dict:
    spec = copy.deepcopy(base)
    spec["spec_id"], spec["traci_rules"] = f"B1_d1v_{name}", []
    for a in spec["driver_archetypes"]:
        if name == "car_b0" and a["base_vclass"] in CARS:
            a["params"] = {}
        if name == "moto_accel_b0" and a["base_vclass"] in MOTOS:
            a["params"].pop("accel")
    spec["description"] = f"B1_manual without TraCI rules, variant {name} (eval_d1_vtype.py)"
    return spec


if __name__ == "__main__":  # the run pool spawns processes that re-import this file
    base = json.loads(Path("rules/specs/B1_manual.json").read_text(encoding="utf-8"))
    names = ["car_b0", "moto_accel_b0"]
    budget = RunBudget(len(names) * len(DAYS) * len(SEEDS), CAMPAIGN)
    for name in names:
        res = evaluate_spec(variant(base, name), DAYS, SEEDS, budget, campaign=CAMPAIGN,
                            site_path=Path("config/site.proxy.yaml"), nproc=len(SEEDS))
        (CAMPAIGNS_DIR / CAMPAIGN / f"{res.spec_id}.pkl").write_bytes(pickle.dumps(res))
        for run in res.runs:
            m = json.loads((Path(run["run_dir"]) / "manifest.json").read_text(encoding="utf-8"))
            print(f"{res.spec_id} seed {run['seed']}: waiting at end {m['insertion_backlog']}, max backlog "
                  f"{m['insertion_backlog_max']}, teleports {m.get('teleports')}, collisions/h "
                  f"{run['collisions_per_hour']:.1f} (lane {run['lane_collisions_per_hour']:.1f}), "
                  f"eligibility {run['eligibility']} {run['reasons']}", flush=True)
        print(f"{res.spec_id}: S {res.S:.4f}", flush=True)
