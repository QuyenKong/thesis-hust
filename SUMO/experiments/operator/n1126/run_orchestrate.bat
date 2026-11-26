@echo off
rem Unattended rest of the 2026-11-26 compute chain (P2 after P1, benchmark after B2 and P2); see orchestrate.sh
cd /d %~dp0..\..\..
"C:\Program Files\Git\bin\bash.exe" experiments/operator/n1126/orchestrate.sh
