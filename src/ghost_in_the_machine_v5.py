#!/usr/bin/env python3
"""
GHOST IN THE MACHINE v5.0 — FOLLOW-UP STUDIES ON THE v4 AUTHORSHIP EFFECT
=========================================================================

Entry point for the preregistered v5 studies: direct replication (A), graded
authorship (B), nonlinear-estimator robustness (C), architecture robustness (D),
comparator timing (E) and comparator rerouting (F). The implementation lives in
`ghost_v5`, which builds on the frozen `ghost_v4` package.

It does NOT create, detect, measure or prove phenomenal consciousness.

    python src/ghost_in_the_machine_v5.py verify
    python src/ghost_in_the_machine_v5.py run --study all
    python src/ghost_in_the_machine_v5.py analyze
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ghost_v4._bootstrap import ensure_dependencies  # noqa: E402

ensure_dependencies()

from ghost_v5.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
