"""Rerun of report/2026-11-03/data/ollama/scripts/retry_chain.py with prompt v003 and the output cap
(config/llm.yaml ollama.max_tokens). LLMClient.generate_spec (validate -> retry loop, max_attempts from llm.yaml)
against the running Ollama server (OLLAMA_CONTEXT_LENGTH=32768).
Request: rebuilt as the loop builds it for campaign P2_n28b (mode full, days of its loop.json, site.proxy.yaml):
system = v003 system_prompt, context = v003 build_context with the current llm_schema; the third message (feedback
on iteration 1) is taken verbatim from the logged it02_s03 request (v002 and v003 feedback.md are identical; its
inputs are the iteration-1 results). In-memory overrides only: active=ollama, prompt_version=v003.
usage: retry_chain.py 42 43 44     (cfg seed 42, sample_idx = seed - 42, so the client sends seed + sample_idx)"""
import json
import re
import subprocess
import sys
import time
from pathlib import Path

import thesis_sumo.llm.client as client
from thesis_sumo.config import load_llm, load_site
from thesis_sumo.llm.feedback import build_context, calibration_targets, system_prompt
from thesis_sumo.rules.schema import load_bounds

REPO = Path(r"D:/hust-master/Thesis/SUMO")
LOG = REPO / "experiments/llm_logs/P2_n28b/P2_n28b__it02_s03_a1.json"
LOOP = REPO / "experiments/campaigns/P2_n28b/loop/loop.json"
SCRATCH = REPO / "experiments/llm_logs/_scratch_qwen_retry_v003"
OUT = Path(r"D:/hust-master/Thesis/report/2026-11-04/data/ollama/retry")
SERVER_LOG = Path(r"D:/hust-master/Thesis/report/2026-11-03/data/ollama/server_ctx32768.log")  # read only
SNAP = Path(r"C:/Users/qdcon/AppData/Local/Temp/thesis_ollama/load_snapshot.ps1")
SITE = REPO / "config/site.proxy.yaml"

doc = load_llm()
doc["active"] = "ollama"
doc["prompt_version"] = "v003"
cfg = client.llm_config(doc)
site = load_site(SITE)
bounds = load_bounds()
logged = json.loads(LOG.read_text(encoding="utf-8"))
days = json.loads(LOOP.read_text(encoding="utf-8"))["days"]
schema = client.llm_schema("full", None, bounds)
messages = [{"role": "system", "content": system_prompt("v003")},
            {"role": "user", "content": build_context("full", None, site, bounds, calibration_targets(days, site=site),
                                                      schema=schema, prompt_version="v003")},
            logged["request"]["messages"][2]]
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "request_messages.json").write_text(json.dumps(messages, indent=1, ensure_ascii=False), encoding="utf-8")


def server_lines(start: int) -> list[str]:
    with SERVER_LOG.open("rb") as f:
        f.seek(start)
        return f.read().decode("utf-8", "replace").splitlines()


def timing(lines: list[str]) -> dict:
    t = {}
    for ln in lines:
        if m := re.search(r"new prompt, n_ctx_slot = (\d+), .*task\.n_tokens = (\d+)", ln):
            t.update(n_ctx_slot=int(m[1]), task_n_tokens=int(m[2]))
        elif m := re.search(r"prompt eval time = +([\d.]+) ms / +(\d+) tokens .* ([\d.]+) tokens per second", ln):
            t.update(prompt_eval_ms=float(m[1]), prompt_eval_tokens=int(m[2]), prompt_tok_s=float(m[3]))
        elif m := re.search(r"\| +eval time = +([\d.]+) ms / +(\d+) tokens .* ([\d.]+) tokens per second", ln):
            t.update(eval_ms=float(m[1]), eval_tokens=int(m[2]), gen_tok_s=float(m[3]))
        elif m := re.search(r"stop processing: n_tokens = (\d+), truncated = (\d+)", ln):
            t.update(final_n_tokens=int(m[1]), truncated=int(m[2]))
        elif re.search(r"(?i)context|exceed|error", ln) and "slot" in ln and "checkpoint" not in ln:
            t.setdefault("notes", []).append(ln.strip()[:300])
    return t


rows = []
for seed in map(int, sys.argv[1:]):
    tag = f"seed{seed}"
    snap = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(SNAP),
                           "-Tag", f"retry_{tag}_start"], capture_output=True, text=True).stdout
    (OUT / f"load_{tag}_start.txt").write_text(snap, encoding="utf-8")
    c = client.LLMClient(cfg, site=site, campaign=f"qwen_retry_{tag}", log_root=SCRATCH)
    per_attempt = []
    orig = c._call_openai

    def timed(msgs, sch, sample_idx, _orig=orig, _acc=per_attempt):
        pos = SERVER_LOG.stat().st_size
        t0 = time.perf_counter()
        err = None
        try:
            return _orig(msgs, sch, sample_idx)
        except Exception as e:
            err = repr(e)
            raise
        finally:
            _acc.append({"wall_s": round(time.perf_counter() - t0, 2), "error": err,
                         "server": timing(server_lines(pos))})

    c._call_openai = timed
    t0 = time.perf_counter()
    err = None
    try:
        spec, record = c.generate_spec(list(messages), "full", iteration=2, sample_idx=seed - int(cfg["seed"]))
    except Exception as e:
        spec, record, err = None, {"attempts": []}, repr(e)
    chain = {"seed": seed, "chain_wall_s": round(time.perf_counter() - t0, 2), "error": err,
             "valid": bool(record.get("valid")), "n_attempts": len(per_attempt), "attempts": []}
    for i, a in enumerate(per_attempt):
        rec = record["attempts"][i] if i < len(record["attempts"]) else {}
        log = json.loads(Path(rec["log"]).read_text(encoding="utf-8")) if rec.get("log") else {}
        raw = (log.get("response") or {}).get("raw") or {}
        ch = (raw.get("choices") or [{}])[0]
        u = raw.get("usage") or {}
        chain["attempts"].append({
            "attempt": i + 1, "wall_s": a["wall_s"], "error": a["error"],
            "prompt_tokens": u.get("prompt_tokens"), "completion_tokens": u.get("completion_tokens"),
            "total_tokens": u.get("total_tokens"), "finish_reason": ch.get("finish_reason"),
            "seed_sent": (log.get("request") or {}).get("seed"),
            "max_tokens": (log.get("request") or {}).get("max_tokens"),
            "response_format": (log.get("request") or {}).get("response_format"),
            "reasoning_chars": len((log.get("response") or {}).get("reasoning") or ""),
            "valid": rec.get("valid"), "issues": rec.get("issues"), "server": a["server"]})
    rows.append(chain)
    (OUT / f"chain_{tag}.json").write_text(json.dumps(chain, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in chain.items() if k != "attempts"}), flush=True)
    for a in chain["attempts"]:
        print("  ", {k: a[k] for k in ("attempt", "wall_s", "prompt_tokens", "completion_tokens", "finish_reason",
                                      "valid", "error")}, a["server"].get("truncated"),
              [f"{i['code']}:{i['message'][:90]}" for i in a["issues"] or []], flush=True)
(OUT / "chains_summary.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False), encoding="utf-8")
