#!/usr/bin/env python3
"""
GHOST IN THE MACHINE v6.0 — WHAT DOES THE COMPARATOR'S PREDICTION ERROR CARRY?
==============================================================================

Entry point for the preregistered v6 studies: prediction-error transplant (G),
near-full authorship with the prediction error as a candidate mediator (I) and
comparator gain (J). The implementation lives in `ghost_v6`, which builds on the
frozen `ghost_v4` and `ghost_v5` packages.

It does NOT create, detect, measure or prove phenomenal consciousness.

    python src/ghost_in_the_machine_v6.py verify
    python src/ghost_in_the_machine_v6.py run --study all
    python src/ghost_in_the_machine_v6.py analyze
    python src/ghost_in_the_machine_v6.py report
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ghost_v4._bootstrap import ensure_dependencies  # noqa: E402

ensure_dependencies()

from ghost_v6.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
