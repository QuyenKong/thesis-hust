#!/usr/bin/env bash
# Decision D29 (docs/DECISIONS_2026-11-26.md): after P2_v1126 (prompt v006) ends, rerun P2 as P2b_v1126 with prompt
# v007, then rerun the benchmark script, which reuses the cached results of the other specs and adds P2b's best.
# usage, from SUMO/:  bash experiments/operator/n1126/run_p2b_chain.sh
set -uo pipefail
cd "$(dirname "$0")/../../.."
PY=.venv/Scripts/python; [ -x "$PY" ] || PY=.venv/bin/python
LOG=experiments/campaigns/orchestrate_v1126.log
say() { echo "$(date '+%F %T') [p2b] $*" >> "$LOG"; }
until grep -qE "stopped on |no valid (spec|trial)|Traceback" experiments/campaigns/P2_v1126_run.log 2>/dev/null; do sleep 60; done
say "P2 ended; starting P2b_v1126 (prompt v007)"
bash experiments/operator/n1126/run_campaigns_video.sh p2b 8.0 > experiments/campaigns/P2b_v1126_run.log 2>&1
say "P2b exit $?"
until grep -q "orchestrator done" "$LOG"; do sleep 60; done
say "benchmark rerun for P2b"
"$PY" -u experiments/operator/n1126/eval_benchmark_video.py > experiments/campaigns/BENCH2_v1126_run.log 2>&1
say "benchmark rerun exit $?"
say "p2b chain done"
