"""Numbers for the thesis from the 2026-11-26 campaigns (net N7, VIDEO_V2 / VIDEO_V1).

    .venv/Scripts/python experiments/operator/n1126/summarise.py ref      # REF_v1126: B0, B1_manual per run
    .venv/Scripts/python experiments/operator/n1126/summarise.py camp     # B2/P1/P2_v1126: one row per spec
    .venv/Scripts/python experiments/operator/n1126/summarise.py llm      # P1/P2_v1126 LLM logs: validity, errors

Writes results/v1126/<what>.csv and prints a readable table. Reads only campaign files.
"""
from __future__ import annotations

import collections
import json
import pickle
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from thesis_sumo.config import REPO_ROOT

CAMP = REPO_ROOT / "experiments" / "campaigns"
OUT = REPO_ROOT / "results" / "v1126"


def backlog(run_dir: str) -> int | None:
    m = Path(run_dir) / "manifest.json"
    if not m.is_file():
        return None
    return json.loads(m.read_text(encoding="utf-8")).get("insertion_backlog")


def manifest(run_dir: str) -> dict:
    m = Path(run_dir) / "manifest.json"
    return json.loads(m.read_text(encoding="utf-8")) if m.is_file() else {}


def eval_rows(res, label: str) -> list[dict]:
    rows = []
    for r in res.runs:
        man = manifest(r["run_dir"])
        rows.append({"spec": label, "day": r["day"], "seed": r["seed"], "eligibility": r["eligibility"],
                     "g0_pass": r["g0_pass"], "geh_share": r["geh_share"],
                     "collisions_per_hour": r["collisions_per_hour"],
                     "lane_collisions_per_hour": r["lane_collisions_per_hour"],
                     "jam_teleports_per_hour": r["jam_yield_teleports_per_hour"],
                     "backlog": man.get("insertion_backlog"), "n_teleports_noncollision": man.get("n_teleports_noncollision"),
                     "reasons": "; ".join(r["reasons"])})
    return rows


def S_of(res) -> float:
    return float(res.S)
    for name in ("S", "score", "total"):
        if hasattr(rep, name):
            return float(getattr(rep, name))
    raise AttributeError("no S on report")


def ref():
    rows, specs = [], []
    for s in ("B0", "B1_manual"):
        res = pickle.load(open(CAMP / "REF_v1126" / f"{s}.pkl", "rb"))
        rows += eval_rows(res, s)
        specs.append({"spec": s, "S": S_of(res), "interventions": json.dumps(res.interventions_summary)})
    df = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "ref_runs.csv", index=False)
    pd.DataFrame(specs).to_csv(OUT / "ref_specs.csv", index=False)
    num = ["collisions_per_hour", "lane_collisions_per_hour", "jam_teleports_per_hour", "backlog", "geh_share"]
    print(df.groupby("spec")[num].agg(["mean", "min", "max"]).T.round(3).to_string())
    print(df.groupby("spec")["eligibility"].value_counts().to_string())
    for s in specs:
        print(s["spec"], "S", round(s["S"], 4))
        print(" ", s["interventions"][:900])
    for spec, g in df.groupby("spec"):
        print(spec, "reasons:", collections.Counter(x.split(":")[0] for r in g["reasons"] for x in r.split("; ") if x))


def camp():
    out = []
    for c in ("B2_v1126", "P1_v1126", "P2_v1126", "P2b_v1126"):
        d = CAMP / c
        if not d.is_dir():
            continue
        pkls = sorted((d / "optuna_results").glob("*.pkl")) if (d / "optuna_results").is_dir() else []
        pkls += sorted((d / "loop" / "results").glob("*.pkl")) if (d / "loop" / "results").is_dir() else []
        for p in pkls:
            try:
                res = pickle.load(open(p, "rb"))
            except Exception as e:  # a result being written
                print("skip", p.name, e)
                continue
            runs = eval_rows(res, res.spec_id) if res.valid else []
            el = [r["eligibility"] for r in runs]
            out.append({"campaign": c, "spec": res.spec_id, "valid": res.valid,
                        "S": S_of(res) if res.valid else np.nan,
                        "n_runs": len(runs), "n_eligible": sum(e == "eligible" for e in el),
                        "collisions_per_hour": np.mean([r["collisions_per_hour"] for r in runs]) if runs else np.nan,
                        "lane_collisions_per_hour": np.mean([r["lane_collisions_per_hour"] for r in runs]) if runs else np.nan,
                        "jam_teleports_per_hour": np.mean([r["jam_teleports_per_hour"] for r in runs]) if runs else np.nan,
                        "backlog_mean": np.mean([r["backlog"] for r in runs if r["backlog"] is not None]) if runs else np.nan,
                        "backlog_min": min([r["backlog"] for r in runs if r["backlog"] is not None], default=np.nan),
                        "backlog_max": max([r["backlog"] for r in runs if r["backlog"] is not None], default=np.nan),
                        "g0_pass": sum(bool(r["g0_pass"]) for r in runs), "wall_time_s": res.wall_time_s,
                        "reasons": " | ".join(sorted({x.split(":")[0] for r in runs for x in r["reasons"].split("; ") if x}))})
    df = pd.DataFrame(out)
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "campaign_specs.csv", index=False)
    pd.set_option("display.width", 250)
    print(df.drop(columns=["reasons"]).round(3).to_string())
    for c, g in df.groupby("campaign"):
        print(c, "reasons:", collections.Counter(x for r in g["reasons"] for x in r.split(" | ") if x))


def llm():
    rows, errs = [], collections.defaultdict(collections.Counter)
    for c in ("P1_v1126", "P2_v1126", "P2b_v1126"):
        d = REPO_ROOT / "experiments" / "llm_logs" / c
        if not d.is_dir():
            continue
        for p in sorted(d.glob(f"{c}__*.json")):
            j = json.loads(p.read_text(encoding="utf-8"))
            m = re.search(r"__it(\d+)_s(\d+)_a(\d+)", p.name)
            raw = (j.get("response") or {}).get("raw") or {}
            usage = raw.get("usage") or j.get("usage") or {}
            issues = j.get("issues") or (j.get("validation") or {}).get("issues") or []
            codes = [i.get("code") for i in issues if isinstance(i, dict)]
            for i in issues:
                if isinstance(i, dict):
                    errs[c][f"{i.get('code')}: {str(i.get('message', ''))[:90]}"] += 1
            rows.append({"campaign": c, "it": int(m.group(1)), "sample": int(m.group(2)), "attempt": int(m.group(3)),
                         "valid": not issues if "issues" in j or "validation" in j else j.get("valid"),
                         "prompt_tokens": usage.get("prompt_tokens"), "completion_tokens": usage.get("completion_tokens"),
                         "finish": ((raw.get("choices") or [{}])[0]).get("finish_reason"),
                         "elapsed_s": j.get("elapsed_s") or j.get("latency_s"), "codes": ",".join(map(str, codes))})
    df = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "llm_attempts.csv", index=False)
    print(df.to_string())
    for c, cnt in errs.items():
        print(c)
        for k, v in cnt.most_common(25):
            print(f"  {v:3d}  {k}")


def bench():
    """BENCH_v1126 (VIDEO_V1 x seeds 1-20): one row per run, then mean / min / max per spec."""
    rows, specs = [], []
    for p in sorted((CAMP / "BENCH_v1126").glob("*.pkl")):
        res = pickle.load(open(p, "rb"))
        rows += eval_rows(res, p.stem)
        specs.append({"spec": p.stem, "S": S_of(res), "interventions": json.dumps(res.interventions_summary)})
    df = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "bench_runs.csv", index=False)
    pd.DataFrame(specs).to_csv(OUT / "bench_specs.csv", index=False)
    num = ["collisions_per_hour", "lane_collisions_per_hour", "jam_teleports_per_hour", "backlog", "geh_share"]
    pd.set_option("display.width", 250)
    print(df.groupby("spec")[num].agg(["mean", "std", "min", "max"]).T.round(3).to_string())
    print(df.groupby("spec")["eligibility"].value_counts().to_string())
    print(df.groupby("spec")["g0_pass"].sum().to_string())
    for s in specs:
        print(s["spec"], "S", round(s["S"], 4))
    for spec, g in df.groupby("spec"):
        print(spec, "reasons:", collections.Counter(x.split(":")[0] for r in g["reasons"] for x in r.split("; ") if x))


if __name__ == "__main__":
    {"ref": ref, "camp": camp, "llm": llm, "bench": bench}[sys.argv[1]]()
