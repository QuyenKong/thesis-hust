#!/bin/bash
source "$(dirname "$0")/../env.sh"
P=$PY; G=experiments/operator/task4/gui_snap.py
$P $G overview 1 0 338 272 1500 100 128 150 190 300
$P $G A_seed2 2 2651.7 332.6 263 3500 -8
$P $G A_seed2b 2 2651.7 332.6 263 3500 -1.0
$P $G B_seed1 1 438.6 323.3 293.5 3500 -8
$P $G B_seed1b 1 438.6 323.3 293.5 3500 -1.0
