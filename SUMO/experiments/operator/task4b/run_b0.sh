#!/bin/bash
# B0 x PROXY_D1..D3 x seeds 1-3, SSM off, --end 1800 (3600 s took >10 min for 1750 s sim)
source "$(dirname "$0")/../env.sh"
for d in PROXY_D1 PROXY_D2 PROXY_D3; do
  s=$(date +%s)
  $PY -m thesis_sumo.sim.runner --spec B0 --day $d --seeds 1 2 3 --site config/site.proxy.yaml --nproc 3 --ssm off --end 1800 > experiments/operator/task4b/run_$d.txt 2>&1
  echo $d exit $? batch_wall $(( $(date +%s)-s ))
done
