"""One-off: resend the logged request P2_n28b__it02_s03_a1 to the local qwen3.5:9b, same call as llm.client._call_openai.
Writes only to the scratchpad; touches no campaign, budget or llm_logs file."""
import json
import sys
import time
from pathlib import Path

import openai

sys.path.insert(0, "src")
SCRATCH = Path(sys.argv[1])
BASE_URL = sys.argv[2]
SEED = int(sys.argv[3])
TAG = sys.argv[4]

log = json.loads(Path("experiments/llm_logs/P2_n28b/P2_n28b__it02_s03_a1.json").read_text(encoding="utf-8"))
messages, schema = log["request"]["messages"], log["request"]["schema"]

client = openai.OpenAI(base_url=BASE_URL, api_key="unused", timeout=3000, max_retries=0)
fmt = {"type": "json_schema", "json_schema": {"name": "rule_spec", "schema": schema}}
t0 = time.time()
resp = client.chat.completions.create(model="qwen3.5:9b", messages=messages, temperature=0.7, seed=SEED,
                                      response_format=fmt)
dt = time.time() - t0
msg = resp.choices[0].message
extra = msg.model_extra or {}
out = {"wall_s": round(dt, 1), "usage": resp.usage.model_dump() if resp.usage else None,
       "finish_reason": resp.choices[0].finish_reason, "model": resp.model,
       "content": msg.content, "reasoning": extra.get("reasoning") or extra.get("reasoning_content")}
(SCRATCH / f"qwen_{TAG}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print({k: out[k] for k in ("wall_s", "usage", "finish_reason", "model")})
print("content chars", len(msg.content or ""), "reasoning chars", len(out["reasoning"] or ""))
