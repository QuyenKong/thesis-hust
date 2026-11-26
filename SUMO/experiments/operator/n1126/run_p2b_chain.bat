@echo off
rem Decision D29: P2b_v1126 (prompt v007) after P2_v1126, then benchmark rerun; see run_p2b_chain.sh
cd /d %~dp0..\..\..
"C:\Program Files\Git\bin\bash.exe" experiments/operator/n1126/run_p2b_chain.sh
