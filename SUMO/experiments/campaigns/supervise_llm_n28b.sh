#!/bin/bash
# Network of 2026-10-28: relaunch the P1_n28b / P2_n28b LLM loops (detached) once every pending request of a campaign has
# its response file; exit (to wake the controller) when some request still needs an answer and its loop is idle, or when
# both campaigns are finished. Usage: B0=<b0 lane collisions per hour> bash supervise_llm_n28b.sh
cd "$(dirname "${BASH_SOURCE[0]}")/../.." || exit 1
PY=.venv/bin/python; [ -x "$PY" ] || PY=.venv/Scripts/python
: "${B0:?set B0 to the B0 lane collisions per hour of REF_n28b}"
declare -A ARGS=(
  [P1_n28b]="--mode params_only --base rules/specs/B1_manual.json --nproc 5 --write-best rules/specs/P1_n28b_best.json"
  [P2_n28b]="--mode full --nproc 3 --write-best rules/specs/P2_n28b_best.json"
)
common="--budget 24 --iters 2 --site config/site.proxy.yaml --b0-lane-collisions $B0 --prompt-version v002"
while true; do
  need=0; finished=0
  for c in P1_n28b P2_n28b; do
    log=experiments/campaigns/${c}_run.log
    if pgrep -f "thesis_sumo.llm.loop --campaign $c " >/dev/null; then continue; fi
    if [ ! -f "$log" ]; then  # first launch
      setsid nohup $PY -m thesis_sumo.llm.loop --campaign $c ${ARGS[$c]} $common > "$log" 2>&1 < /dev/null &
      echo "$(date +%T) launched $c"; sleep 20; continue
    fi
    if grep -q "pending" "$log"; then
      missing=$(grep -o -- '-> .*\.json' "$log" | cut -c4- | while read -r f; do [ -f "$f" ] || echo "$f"; done)
      if [ -z "$missing" ]; then
        setsid nohup $PY -m thesis_sumo.llm.loop --campaign $c ${ARGS[$c]} $common > "$log" 2>&1 < /dev/null &
        echo "$(date +%T) relaunched $c"; sleep 20
      else
        need=1
      fi
    else
      finished=$((finished + 1))
    fi
  done
  if [ $need -eq 1 ] || [ $finished -eq 2 ]; then
    for c in P1_n28b P2_n28b; do echo "== $c $(cat experiments/campaigns/$c/budget.json 2>/dev/null)"; tail -6 experiments/campaigns/${c}_run.log; done
    exit 0
  fi
  sleep 30
done
