@echo off
rem Detached launcher of the 2026-11-27 compute chain (chain.sh); progress in experiments\campaigns\chain_v1127.log
cd /d %~dp0..\..\..
"C:\Program Files\Git\bin\bash.exe" experiments/operator/n1127/chain.sh
