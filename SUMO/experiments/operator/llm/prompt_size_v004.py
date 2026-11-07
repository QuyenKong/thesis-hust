"""Size of the P2 prompt (mode full) for iterations 2 and 3, prompt v002 vs v004, built from the results of campaign
P2_n28b (2 iterations, stand-in specs; used here only as realistic feedback content). Tokens are estimated with the
ratio measured on 2026-11-03 for qwen3.5:9b (26,145 prompt tokens for 71,346 characters of the v002 request,
report/2026-11-03/data/ollama/measurements.md). Writes the v004 messages of iteration 2 to --out (JSON) if given.
usage (from SUMO/): .venv/Scripts/python experiments/operator/llm/prompt_size_v004.py [--out file.json]"""
import argparse
import json
import pickle
import sys
from pathlib import Path

if sys.platform == "win32":
    import libsumo  # noqa: F401  (before anything that loads sqlite3, as in baselines.optuna_search)

from thesis_sumo.config import load_site
from thesis_sumo.evaluate import CAMPAIGNS_DIR
from thesis_sumo.llm.client import llm_schema
from thesis_sumo.llm.feedback import build_context, calibration_targets, system_prompt
from thesis_sumo.llm.loop import _history_message, _summary_message
from thesis_sumo.rules.schema import load_bounds

CHARS_PER_TOKEN = 71346 / 26145
CAMP = CAMPAIGNS_DIR / "P2_n28b"


def load_iter(it: int):
    res = [pickle.loads(p.read_bytes()) for p in sorted((CAMP / "loop" / "results").glob(f"P2_n28b_it{it:02d}_*.pkl"))]
    specs = {}
    for r in res:
        p = CAMP / "specs" / f"{r.spec_id}.json"
        if p.is_file():
            specs[r.spec_id] = json.loads(p.read_text(encoding="utf-8"))
    return specs, res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    a = ap.parse_args()
    site, bounds = load_site(Path("config/site.proxy.yaml")), load_bounds()
    days = json.loads((CAMP / "loop" / "loop.json").read_text(encoding="utf-8"))["days"]
    targets = calibration_targets(days, site=site)
    it1, it2 = load_iter(1), load_iter(2)
    for pv in ("v002", "v004"):
        base = [{"role": "system", "content": system_prompt(pv)},
                {"role": "user", "content": build_context("full", None, site, bounds, targets,
                                                          schema=llm_schema("full", None, bounds), prompt_version=pv)}]
        h1 = _history_message(1, *it1, pv)
        h2 = _history_message(2, *it2, pv)
        rows = {"iteration 2": base + [h1],
                "iteration 3": base + ([_summary_message(1, *it1), h2] if pv >= "v004" else [h1, h2])}
        for name, msgs in rows.items():
            n = sum(len(m["content"]) for m in msgs)
            parts = ", ".join(str(len(m["content"])) for m in msgs)
            print(f"{pv} {name}: {n} chars (~{n / CHARS_PER_TOKEN:,.0f} tokens); per message {parts}")
        if pv == "v004" and a.out:
            Path(a.out).write_text(json.dumps(rows["iteration 2"], indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
