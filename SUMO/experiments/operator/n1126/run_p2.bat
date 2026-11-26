@echo off
rem P2_v1126 detached (R10 cap: B0 lane collisions/h of REF_v1126 = 8.0)
cd /d %~dp0..\..\..
"C:\Program Files\Git\bin\bash.exe" experiments/operator/n1126/run_campaigns_video.sh p2 8.0 > experiments\campaigns\P2_v1126_run.log 2>&1
