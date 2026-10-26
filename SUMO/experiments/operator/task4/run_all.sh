#!/bin/bash
# one-factor scratch experiments (3600 s, seeds 1 2 3); run from the repo root
source "$(dirname "$0")/../env.sh"
P=$PY; S=experiments/operator/task4
$P $S/run_variant.py outw --net $S/net_outw/site.outw.net.xml
$P $S/run_variant.py lc2013cars --vtypes $S/vtypes_cars_lc2013.add.xml
$P $S/run_variant.py latres02 --latres 0.2
$P $S/run_variant.py latres08 --latres 0.8
$P $S/run_variant.py checkjunc --collision.check-junctions
