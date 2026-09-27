#!/usr/bin/env python3
"""
GHOST IN THE MACHINE v4.0 — THE SPECIFICITY LABORATORY
======================================================

Entry point. The implementation lives in the `ghost_v4` package next to this file.

v4 asks whether a synthetic self/world-modelling agent contains a macroscopic
self-variable that is (E) causally emergent, (A) dependent on the agent
authoring its own actions — tested against a cross-yoked twin that receives an
equivalent stream it did not author — and (S) specific, surviving a calibrated
ladder of null models. It also re-adjudicates v3 with metric-identical nulls.

It does NOT create, detect, measure or prove phenomenal consciousness.

Quick start:
    python src/ghost_in_the_machine_v4.py demo
    python src/ghost_in_the_machine_v4.py all          # full preregistered pipeline

See README.md and paper/Ghost_in_the_Machine_v4_Paper.md.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ghost_v4._bootstrap import ensure_dependencies  # noqa: E402

ensure_dependencies()

from ghost_v4.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
