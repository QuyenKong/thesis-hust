#!/usr/bin/env bash
# Campaigns of 2026-11-08 on the net of 2026-11-04 (report/2026-11-08): B2 (Optuna), P1 (LLM params_only), P2 (LLM full),
# 36 SUMO runs each (R44: PROXY_D1-D3 x seed 1), LLM = qwen3.5:9b on the local Ollama server (llm.yaml block `ollama`,
# OLLAMA_CONTEXT_LENGTH=32768, report/2026-11-08/data/ollama/scripts/start_ollama_32k.ps1), prompt v004.
# R10 cap: B0 lane collisions/h of REF_n1104s5 (15 runs) = 1.8667.
# usage, from SUMO/:  bash experiments/operator/n1108/run_campaigns.sh b2|p1|p2
set -euo pipefail
cd "$(dirname "$0")/../../.."
PY=.venv/Scripts/python; [ -x "$PY" ] || PY=.venv/bin/python
B0=1.8667
case "${1:?b2|p1|p2}" in
  b2) "$PY" -m thesis_sumo.baselines.optuna_search --structure rules/specs/B1_manual.json --campaign B2_n1108 \
        --budget 36 --nproc 3 --site config/site.proxy.yaml --b0-lane-collisions "$B0" \
        --write-best rules/specs/B2_n1108_best.json ;;
  p1) "$PY" -m thesis_sumo.llm.loop --campaign P1_n1108 --mode params_only --base rules/specs/B1_manual.json \
        --budget 36 --nproc 12 --site config/site.proxy.yaml --b0-lane-collisions "$B0" --llm ollama \
        --write-best rules/specs/P1_n1108_best.json ;;
  p2) "$PY" -m thesis_sumo.llm.loop --campaign P2_n1108 --mode full \
        --budget 36 --nproc 12 --site config/site.proxy.yaml --b0-lane-collisions "$B0" --llm ollama \
        --write-best rules/specs/P2_n1108_best.json ;;
  *) echo "unknown campaign $1" >&2; exit 2 ;;
esac
