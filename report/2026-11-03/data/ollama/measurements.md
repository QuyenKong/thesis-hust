# qwen3.5:9b on local Ollama: timing of one real P2 request

Machine: Windows, RTX 4060 8 GB (6.9 GiB free before load), 16 logical CPUs, 31.8 GiB RAM. Ollama 0.40.13, llama.cpp runner, 8 CPU threads.
Model: qwen3.5:9b, Q4_K_M, 9.0B parameters, 32 blocks (33 offloadable layers incl. output), vision projector loaded too (`--mmproj`).
Request: messages and schema of `SUMO/experiments/llm_logs/P2_n28b/P2_n28b__it02_s03_a1.json` (prompt v002, mode full),
`response_format` json_schema, temperature 0.7, seed 42, POST `/v1/chat/completions`. Scripts in `scripts/`:
`measure.py <tag>` sends the request, `load_snapshot.ps1 -Tag <tag>_start` records the load, `start_ollama*.ps1` start the server.
Validation: `validate_resp.py <tag>` parses the content like `LLMClient.generate_spec` (`client._parse`), inserts
`spec_id`/`source`/`provenance` and calls `validator.validate` with `config/site.proxy.yaml` (the site the P2 loops used).

| tag | OLLAMA_CONTEXT_LENGTH | thinking | GPU layers | prompt tok | prompt tok/s | completion tok | gen tok/s | wall s | JSON valid | validator | concurrent load at start |
|---|---|---|---|---|---|---|---|---|---|---|---|
| full_think | 65536 | on | 21/33 | 25,633 evaluated (512 cached) | 20.4 | 2,127 | 1.25 | 2968 | yes | 3 issues | not recorded; system RAM free 14.6 GiB at model load (22:59) vs 20-21 GiB at later loads |
| full_nothink | 65536 | off (`reasoning_effort: "none"`, reasoning 0 chars) | 21/33 | 26,147 | 1174 | 2,260 | 4.22 | 574 | yes | 2 issues | CPU 10 %, no sumo process |
| full_think_ctx65536_rerun | 65536 | on | 21/33 | 2 evaluated (26,143 cached) | n/a (cache hit) | 1,596 | 4.52 | 356 | yes | 2 issues | CPU 42 %, 3 sumo processes |
| full_think_ctx32768 | 32768 | on | 26/33 | 26,145 | 1395 | 1,954 | 9.67 | 230 | yes | 3 issues | CPU 24 %, 1 sumo process |

Prompt and generation rates come from llama-server `print_timing` lines (`server.log` for 65536, `server_ctx32768.log` for 32768).
Wall time includes model load (about 12 s) where the model was not loaded yet (full_nothink, full_think_ctx32768).
`ollama ps` after the run: 8.7 GB, 36 %/64 % CPU/GPU at 65536; 7.3 GB, 24 %/76 % CPU/GPU at 32768.
KV cache: 2048 MiB (1280 GPU + 768 CPU) at 65536; 1024 MiB (896 GPU + 128 CPU) at 32768.
Load snapshots: `load_<tag>_start.txt` (Get-Process sumo/python/ollama, CPU load, nvidia-smi).

The first full_think run was slow throughout, not only in the thinking phase: prompt processing ran at 13-20 tok/s
from the first 512-token batch to the last, against 1174 tok/s for the same prompt and setup in full_nothink.
Thinking does not change prompt processing, so the 2968 s come from load on the machine during that run, not from
thinking or from the context length. The load was not recorded.

Validator issues (all runs, same kind):
- `share_sum`: shares of `moto` sum to 0.7-0.8 and of `moto_violator` to 1.2-1.3; the model gives the violator
  archetype share 1 and splits the rest wrongly.
- `logic` (full_think, full_think_ctx32768): archetype id `moto_violator` clashes with the reserved distribution id.
No run produced a valid spec on attempt 1. The retry chains are in the next section.

Seed 42 does not make runs repeatable across server states: the three think runs above returned 2127, 1596 and
1954 completion tokens and different specs (3 to 7 rules). With the same server (32768) and seed, attempt 1 of the
seed-42 chain below repeated full_think_ctx32768 exactly (1954 tokens, same 3 issues).

Models under `D:\ollama\models` (manifests; nothing pulled):

| model | blob | size bytes |
|---|---|---|
| qwen3.5:9b (`ollama list`: 6.6 GB, id 56671c2ab938) | model.gguf sha256-02d45dc1... | 5,629,109,120 |
| | mmproj.gguf (vision projector) sha256-f836f08f... | 921,704,832 |
| | template, params, license, config | < 12 kB |

Server state when this file was written: `ollama serve` PID 31904 running with OLLAMA_CONTEXT_LENGTH=32768,
OLLAMA_MODELS=D:\ollama\models, started by `start_ollama_32k.ps1`, log `server_ctx32768.log`.

## Retry chains (repo client, 32768 server)

`scripts/retry_chain.py 42 43 44` runs `LLMClient.generate_spec(messages, "full", iteration=2, sample_idx=seed-42)`
with the `ollama` block of `config/llm.yaml` (max_attempts 3, temperature 0.7, seed 42 + sample_idx) and in-memory
overrides only: `active: ollama`, `prompt_version: v002` (as logged), `timeout_s: 3600`, and `llm_schema` returning the
logged schema (the current code adds rule `uturn_bypass`; nothing else differs). The client validates with
`config/site.proxy.yaml` and the working-tree validator, then appends its answer and `build_retry(issues)` and asks
again. Thinking on (the client sends no `reasoning_effort`). Attempt logs: `retry/qwen_retry_seedNN/`; per-attempt
table with server timings: `retry/chain_seedNN.json`; load: `retry/load_seedNN_start.txt`.

| seed | attempt | prompt tok | completion tok | prompt+completion | reasoning chars | finish | truncated | wall s | validator |
|---|---|---|---|---|---|---|---|---|---|
| 42 | 1 | 26,145 | 1,954 | 28,099 | 2,511 | stop | 0 | 211 | share_sum moto 0.7, share_sum moto_violator 1.2, logic id `moto_violator` reserved |
| 42 | 2 | 27,670 | 4,393 | 32,063 | 12,276 | stop | 0 | 518 | share_sum moto_violator 1.2 |
| 42 | 3 | 29,101 | 3,398 | 32,499 | 10,735 | stop | 0 | 424 | valid |
| 43 | 1 | 26,145 | 2,642 | 28,787 | 4,753 | stop | 0 | 279 | share_sum moto 0.75, share_sum moto_violator 1.25, logic id reserved |
| 43 | 2 | 27,605 | 3,542 | 31,147 | 8,391 | stop | 0 | 380 | share_sum moto 0.75, share_sum moto_violator 1.25 |
| 43 | 3 | 29,014 | 1,912 | 30,926 | 2,363 | stop | 0 | 199 | 2 x logic: queue_space_seeking on a motorcycle archetype (needs custom1/custom2; no usable option on site) |
| 44 | 1 | 26,145 | 6,623 | 32,768 | 22,866 | length | 1 | 695 | schema: empty answer, not JSON |
| 44 | 2 | 26,227 | 2,801 | 29,028 | 3,104 | stop | 0 | 293 | share_sum moto 0.7, share_sum moto_violator 1.25, logic id reserved |
| 44 | 3 | 28,475 | 3,441 | 31,916 | 5,190 | stop | 0 | 370 | 2 x logic: queue_space_seeking on a motorcycle archetype |

| seed | valid within 3 | chain wall s | load at chain start |
|---|---|---|---|
| 42 | yes (attempt 3) | 1153 | CPU 31 %, 3 sumo + 3 busy python |
| 43 | no | 858 | CPU 39 %, 3 busy python (no sumo process) |
| 44 | no | 1358 | CPU 31 %, 3 busy python (no sumo process) |

Valid within 3 attempts: 1 of 3 chains. Total 3369 s for 3 chains (avg 374 s per attempt).
Generation ran at 8.0-9.7 tok/s in every attempt. Attempt 1 reused the cached prompt (4 tokens evaluated);
the retries evaluated 86-2,252 new prompt tokens at 235-1,123 tok/s.

Context: the client sets no `max_tokens`, so the model can think until the 32,768-token context is full. Seed 44
attempt 1 did that: 6,623 completion tokens of reasoning, finish_reason `length`, llama-server `truncated = 1`,
empty content. Its retry then started from the original prompt plus an empty answer. Seed 42 attempt 3 ended
269 tokens short of the limit, seed 42 attempt 2 705 tokens short. Reasoning per attempt ranged from 2.4k to
12.3k chars (22.9k in the overflowed attempt).

How the share error arises: no archetype sets `distribution`, so each joins the default one for its base vclass.
The seeker (share 0.2-0.25) and the violator (share 1) are both `custom1` and land in `moto_violator`, whose shares
then sum to 1.2-1.25; the two `motorcycle` archetypes in `moto` sum to 0.7-0.75.
After the retry message the model renames the violator (clearing the
reserved-id issue) but keeps its share at 1 (seeds 42, 43 attempt 2). It cleared the share issues in two ways:
- seed 42 attempt 3 (valid): dropped the seeker archetype and its queue_space_seeking rule (6 rules left);
- seeds 43 and 44 attempt 3: changed the seeker to base_vclass motorcycle, so it joins `moto`, and the
  queue_space_seeking rule on it becomes invalid (it needs custom1/custom2).
