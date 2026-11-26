#!/usr/bin/env bash
# Campaigns of 2026-11-26 on the LVL x HMG x NT net, video calibration day VIDEO_V2 x seeds 1-3 (decision D23):
# B2 (Optuna), P1 (LLM params_only), P2 (LLM full), 36 SUMO runs each; LLM = qwen3.5:9b on the local Ollama server
# (OLLAMA_CONTEXT_LENGTH=32768), prompt v006. R10 cap: B0 lane collisions/h of REF_v1126 (passed as $2).
# usage, from SUMO/:  bash experiments/operator/n1126/run_campaigns_video.sh b2|p1|p2|p2b <b0_lane_collisions_per_h>
set -euo pipefail
cd "$(dirname "$0")/../../.."
PY=.venv/Scripts/python; [ -x "$PY" ] || PY=.venv/bin/python
B0="${2:?B0 lane collisions per hour from REF_v1126}"
COMMON=(--budget 36 --site config/site.yaml --days VIDEO_V2 --seeds 1 2 3 --b0-lane-collisions "$B0")
case "${1:?b2|p1|p2|p2b}" in
  b2) "$PY" -u -m thesis_sumo.baselines.optuna_search --structure rules/specs/B1_manual.json --campaign B2_v1126 \
        --nproc 6 "${COMMON[@]}" --write-best rules/specs/B2_v1126_best.json ;;
  p1) "$PY" -u -m thesis_sumo.llm.loop --campaign P1_v1126 --mode params_only --base rules/specs/B1_manual.json \
        --nproc 12 "${COMMON[@]}" --llm ollama --write-best rules/specs/P1_v1126_best.json ;;
  p2) "$PY" -u -m thesis_sumo.llm.loop --campaign P2_v1126 --mode full \
        --nproc 12 "${COMMON[@]}" --llm ollama --write-best rules/specs/P2_v1126_best.json ;;
  p2b) "$PY" -u -m thesis_sumo.llm.loop --campaign P2b_v1126 --mode full --prompt-version v007         --nproc 12 "${COMMON[@]}" --llm ollama --write-best rules/specs/P2b_v1126_best.json ;;  # decision D29
  *) echo "unknown campaign $1" >&2; exit 2 ;;
esac
