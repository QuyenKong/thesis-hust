#!/usr/bin/env bash
# Unattended compute chain of 2026-11-27 (docs/HANDOFF_2026-11-27.md): REF_v1127 -> B2_v1127 in the background,
# P1_v1127 then P2_v1127 in the foreground (shared GPU) -> wait for B2 -> benchmark BENCH_v1127 -> figures.
# Every step is skipped when its output already exists, and the campaigns resume from their own state, so after a
# reboot or a crash the same command continues where it stopped. Progress: experiments/campaigns/chain_v1127.log
# (one line per step; "chain done" at the end).
# usage, from SUMO/:  bash experiments/operator/n1127/chain.sh      (or run_chain.bat, detached)
set -uo pipefail
cd "$(dirname "$0")/../../.."
PY=.venv/Scripts/python; [ -x "$PY" ] || PY=.venv/bin/python
OP=experiments/operator/n1127
CAMP=experiments/campaigns
LOG=$CAMP/chain_v1127.log
say() { echo "$(date '+%F %T') $*" >> "$LOG"; }
done_campaign() { grep -qE "stopped on |no valid (spec|trial)" "$CAMP/$1_v1127_run.log" 2>/dev/null; }
failed_campaign() { grep -q "Traceback" "$CAMP/$1_v1127_run.log" 2>/dev/null; }
ollama_up() { curl -s --max-time 5 localhost:11434/api/tags | grep -q 'qwen3.5:9b'; }

say "chain started (pid $$)"

# 1. REF_v1127: B0 and B1_manual on VIDEO_V2 x seeds 1-5
if [ -f "$CAMP/REF_v1127/B0.pkl" ] && [ -f "$CAMP/REF_v1127/B1_manual.pkl" ]; then
  say "REF exists, skipped"
else
  say "REF start"
  "$PY" -u $OP/eval_ref_video.py > "$CAMP/REF_v1127_run.log" 2>&1
  say "REF exit $?"
fi
B0_LANE=$("$PY" -c "import pickle;print(round(pickle.load(open('$CAMP/REF_v1127/B0.pkl','rb')).to_row()['lane_collisions_per_hour'],1))")
if [ -z "$B0_LANE" ]; then say "REF failed: no B0 lane collisions; stop"; exit 1; fi
say "R10 cap (B0 lane collisions/h) = $B0_LANE"

# 2. B2 in the background (CPU only)
if done_campaign B2; then say "B2 already done"; B2_PID=""
else
  say "B2 start"
  bash $OP/run_campaigns_video.sh b2 "$B0_LANE" >> "$CAMP/B2_v1127_run.log" 2>&1 &
  B2_PID=$!
fi

# 3. P1 then P2 (local LLM)
for c in P1 P2; do
  if done_campaign $c; then say "$c already done"; continue; fi
  for i in 1 2 3; do ollama_up && break
    say "ollama down, starting it (try $i)"
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File ../report/2026-11-08/data/ollama/scripts/start_ollama_32k.ps1 >/dev/null 2>&1
    sleep 30
  done
  ollama_up || { say "ollama not reachable; $c skipped"; continue; }
  say "$c start"
  bash $OP/run_campaigns_video.sh "$(echo $c | tr 'P' 'p')" "$B0_LANE" >> "$CAMP/${c}_v1127_run.log" 2>&1
  say "$c exit $? ($(failed_campaign $c && echo FAILED || echo ok))"
done

# 4. wait for B2
if [ -n "${B2_PID:-}" ]; then wait "$B2_PID"; say "B2 exit $? ($(failed_campaign B2 && echo FAILED || echo ok))"; fi
until done_campaign B2 || failed_campaign B2; do sleep 60; done

# 5. benchmark (reuses existing .pkl)
say "benchmark start"
"$PY" -u $OP/eval_benchmark_video.py >> "$CAMP/BENCH_v1127_run.log" 2>&1
say "benchmark exit $?"

# 6. figures (written while the chain runs; skipped when the script does not exist yet)
if [ -f $OP/figures.py ]; then
  "$PY" -u $OP/figures.py >> "$CAMP/FIG_v1127_run.log" 2>&1
  say "figures exit $?"
else
  say "figures.py missing, skipped"
fi
say "chain done"
