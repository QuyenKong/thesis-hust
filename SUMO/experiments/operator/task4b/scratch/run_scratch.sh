#!/bin/bash
cd /d/hust-master/Thesis/SUMO/experiments/operator/task4b/scratch
PY=/d/hust-master/Thesis/SUMO/.venv/Scripts/python
V=../../task4/run_variant.py
R=/d/hust-master/Thesis/SUMO/scenario/demand/routes_PROXY_D1.rou.xml
$PY $V d1_base --routes $R --end 1800
$PY $V d1_mg15 --routes $R --end 1800 --vtypes vtypes_mg15.add.xml
$PY $V d1_noviol --routes routes_D1_noviol.rou.xml --end 1800
$PY $V d1_noleft --routes routes_D1_noleft.rou.xml --end 1800
