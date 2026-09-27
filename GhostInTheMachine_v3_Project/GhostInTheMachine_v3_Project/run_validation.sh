#!/usr/bin/env bash
set -euo pipefail
python3 src/ghost_in_the_machine_v3.py --steps 5000 --calibration-steps 1000 --diagnostic-interval 50 --perturb-interval 500 --print-every 500 --skip-ablations --skip-recovery --output results/validation_run
