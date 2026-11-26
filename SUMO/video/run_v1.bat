@echo off
rem Track IMG_4800 in two segments (camera pans at ~72-80 s), one reference frame each.
cd /d %~dp0models
set PY=..\..\.venv-video\Scripts\python.exe
set COMMON=--video ..\..\data\IMG_4800.MOV --fps 15 --model yolo11x.pt --imgsz 1920 --match-scale 0.4 --preview
%PY% -u ..\track.py %COMMON% --out ..\runs\V1_IMG_4800_a --ref-time 30 --start 0 --end 76 > ..\runs\V1_IMG_4800_a\log.txt 2> ..\runs\V1_IMG_4800_a\err.txt
%PY% -u ..\track.py %COMMON% --out ..\runs\V1_IMG_4800_b --ref-time 120 --start 76 > ..\runs\V1_IMG_4800_b\log.txt 2> ..\runs\V1_IMG_4800_b\err.txt
