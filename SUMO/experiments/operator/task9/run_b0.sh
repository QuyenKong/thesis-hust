#!/bin/bash
# R28: B0 x PROXY_D1..D3 x seeds 1-3, SSM off, default end (calib_end_s 1800), check-junctions on (runner default)
cd /d/hust-master/Thesis/SUMO
for d in PROXY_D1 PROXY_D2 PROXY_D3; do
  s=$(date +%s)
  .venv/Scripts/python -m thesis_sumo.sim.runner --spec B0 --day $d --seeds 1 2 3 --site config/site.proxy.yaml --nproc 3 --ssm off > experiments/operator/task9/run_$d.txt 2>&1
  echo $d exit $? batch_wall $(( $(date +%s)-s ))
done
