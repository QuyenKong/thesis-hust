@echo off
rem REF_n1126 (B0, B1_manual on PROXY_D1-D3 x seeds 1-5, new net LVL x HMG x NT), detached run with a log
cd /d %~dp0..\..\..
.venv\Scripts\python.exe -u experiments\operator\n1126\eval_ref.py > experiments\campaigns\REF_n1126_run.log 2>&1
