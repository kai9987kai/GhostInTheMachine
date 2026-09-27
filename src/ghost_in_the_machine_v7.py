#!/usr/bin/env python3
"""
GHOST IN THE MACHINE v7.0 — FEEDBACK VS INNOVATION, POWERED PSI, ROBUST GAIN
===========================================================================

Entry point for the preregistered v7 studies: which part of the author's
prediction error must be in step with the network (K), a powered test of
authorship-dependent causal emergence (L) and the comparator-gain question with a
robust measure (M). The implementation lives in `ghost_v7`, which builds on the
frozen `ghost_v4`, `ghost_v5` and `ghost_v6` packages.

It does NOT create, detect, measure or prove phenomenal consciousness.

    python src/ghost_in_the_machine_v7.py verify
    python src/ghost_in_the_machine_v7.py run --study all
    python src/ghost_in_the_machine_v7.py analyze
    python src/ghost_in_the_machine_v7.py report
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ghost_v4._bootstrap import ensure_dependencies  # noqa: E402

ensure_dependencies()

from ghost_v7.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
