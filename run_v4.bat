@echo off
REM Full preregistered v4 pipeline: calibration, v3 forensics, confirmatory campaign, analysis, figures.
python src\ghost_in_the_machine_v4.py all --out results\v4 --workers 4
pause
