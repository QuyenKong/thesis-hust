#!/bin/bash
# Relaunch P1/P2 LLM loops (detached) once every pending request of a campaign has its response file; exit (to wake
# the controller) when some request still needs an answer and its loop is idle, or when both campaigns are finished.
cd "$(dirname "${BASH_SOURCE[0]}")/../.." || exit 1
PY=.venv/bin/python; [ -x "$PY" ] || PY=.venv/Scripts/python
declare -A ARGS=(
  [P1]="--mode params_only --base rules/specs/B1_manual.json --nproc 9"
  [P2]="--mode full --nproc 3"
)
common="--budget 36 --site config/site.proxy.yaml --b0-lane-collisions 1.333"
while true; do
  need=0; finished=0
  for c in P1 P2; do
    log=experiments/campaigns/${c}_run.log
    if pgrep -f "thesis_sumo.llm.loop --campaign $c " >/dev/null; then continue; fi
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
    for c in P1 P2; do echo "== $c $(cat experiments/campaigns/$c/budget.json)"; tail -6 experiments/campaigns/${c}_run.log; done
    exit 0
  fi
  sleep 30
done
