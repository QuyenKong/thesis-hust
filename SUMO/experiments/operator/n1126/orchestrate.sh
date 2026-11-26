#!/usr/bin/env bash
# Runs the rest of the 2026-11-26 compute chain unattended (docs/HANDOFF_2026-11-26.md):
#   wait for P1_v1126 to finish -> run P2_v1126 -> wait for B2_v1126 -> run the benchmark BENCH_v1126.
# B2 and P1 are started separately (run_b2.bat, run_p1.bat). Progress goes to experiments/campaigns/orchestrate_v1126.log.
# usage, from SUMO/:  bash experiments/operator/n1126/orchestrate.sh
set -uo pipefail
cd "$(dirname "$0")/../../.."
PY=.venv/Scripts/python; [ -x "$PY" ] || PY=.venv/bin/python
LOG=experiments/campaigns/orchestrate_v1126.log
say() { echo "$(date '+%F %T') $*" >> "$LOG"; }
done_campaign() {  # 0 when the campaign log shows its final line (best spec written or budget exhausted)
  grep -qE "stopped on |no valid (spec|trial)" "experiments/campaigns/$1_v1126_run.log" 2>/dev/null
}
failed_campaign() { grep -q "Traceback" "experiments/campaigns/$1_v1126_run.log" 2>/dev/null; }

say "orchestrator started"
until done_campaign P1 || failed_campaign P1; do sleep 60; done
say "P1 finished ($(failed_campaign P1 && echo FAILED || echo ok)); starting P2"
bash experiments/operator/n1126/run_campaigns_video.sh p2 8.0 > experiments/campaigns/P2_v1126_run.log 2>&1
say "P2 exit $?"
until done_campaign B2 || failed_campaign B2; do sleep 60; done
say "B2 finished ($(failed_campaign B2 && echo FAILED || echo ok)); starting benchmark"
"$PY" -u experiments/operator/n1126/eval_benchmark_video.py > experiments/campaigns/BENCH_v1126_run.log 2>&1
say "benchmark exit $?"
say "orchestrator done"
