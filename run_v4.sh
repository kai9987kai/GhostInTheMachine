#!/usr/bin/env bash
# Full preregistered v4 pipeline: calibration, v3 forensics, confirmatory campaign, analysis, figures.
set -euo pipefail
python3 src/ghost_in_the_machine_v4.py all --out results/v4 --workers "${WORKERS:-4}"
