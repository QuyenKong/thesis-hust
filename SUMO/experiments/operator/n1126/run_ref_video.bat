@echo off
cd /d %~dp0..\..\..
.venv\Scripts\python.exe -u experiments\operator\n1126\eval_ref_video.py > experiments\campaigns\REF_v1126_run.log 2>&1
