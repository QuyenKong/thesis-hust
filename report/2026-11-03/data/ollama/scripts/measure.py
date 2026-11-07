"""Scratch measurement: POST to Ollama /v1/chat/completions, save raw response + timing.
usage: measure.py short|full_think|full_nothink"""
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

OUT = Path(r"D:/hust-master/Thesis/report/2026-11-03/data/ollama")
LOG = Path(r"D:/hust-master/Thesis/SUMO/experiments/llm_logs/P2_n28b/P2_n28b__it02_s03_a1.json")
URL = "http://localhost:11434/v1/chat/completions"
tag = sys.argv[1]

if tag == "short":
    body = {"model": "qwen3.5:9b", "messages": [{"role": "user", "content": "Reply with OK"}]}
else:
    log = json.loads(LOG.read_text(encoding="utf-8"))
    body = {"model": "qwen3.5:9b", "messages": log["request"]["messages"], "temperature": 0.7, "seed": 42,
            "response_format": {"type": "json_schema",
                                "json_schema": {"name": "rule_spec", "schema": log["request"]["schema"]}}}
    if tag == "full_nothink":
        body["reasoning_effort"] = "none"

req = urllib.request.Request(URL, data=json.dumps(body).encode("utf-8"), headers={"Content-Type": "application/json"})
ps_during = None
t0 = time.perf_counter()
err = None
try:
    with urllib.request.urlopen(req, timeout=3600) as r:
        raw = r.read().decode("utf-8")
except Exception as e:  # record timeout/HTTP errors instead of losing the timing
    raw, err = None, repr(e)
wall = time.perf_counter() - t0
ps_after = subprocess.run(["ollama", "ps"], capture_output=True, text=True).stdout

rec = {"tag": tag, "wall_s": round(wall, 2), "error": err,
       "request_extra": {k: v for k, v in body.items() if k not in ("messages", "response_format")},
       "ollama_ps_after": ps_after}
if raw is not None:
    (OUT / f"{tag}_response.json").write_text(raw, encoding="utf-8")
    resp = json.loads(raw)
    ch = resp["choices"][0]
    msg = ch["message"]
    content = msg.get("content") or ""
    reasoning = msg.get("reasoning") or msg.get("reasoning_content") or ""
    try:
        json.loads(content)
        complete = True
    except ValueError:
        complete = False
    u = resp.get("usage") or {}
    rec.update(usage=u, finish_reason=ch.get("finish_reason"), content_chars=len(content),
               reasoning_chars=len(reasoning), content_is_json=complete,
               completion_tok_per_s_wall=round(u.get("completion_tokens", 0) / wall, 2) if wall else None)
(OUT / f"{tag}_summary.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
print(json.dumps({k: v for k, v in rec.items() if k != "ollama_ps_after"}, ensure_ascii=False))
print(ps_after)
