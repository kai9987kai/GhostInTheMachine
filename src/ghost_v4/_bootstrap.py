"""Zero-setup dependency bootstrap (same behaviour as v1-v3) and thread pinning."""

from __future__ import annotations

import importlib
import os
import subprocess
import sys

# One BLAS thread per process: the campaign parallelizes across processes, and
# oversubscribed BLAS threads make small-matrix work slower, not faster.
for _var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_var, "1")

REQUIREMENTS = (("numpy", "numpy>=1.26"), ("matplotlib", "matplotlib>=3.8"))


def ensure_dependencies() -> None:
    for module, spec in REQUIREMENTS:
        try:
            importlib.import_module(module)
            continue
        except ModuleNotFoundError:
            print(f"[setup] Missing dependency {module}; installing {spec}")
        for cmd in ([sys.executable, "-m", "pip", "install", spec],
                    [sys.executable, "-m", "pip", "install", "--user", spec]):
            if subprocess.call(cmd) == 0:
                importlib.invalidate_caches()
                break
        else:
            raise SystemExit(f"Could not install {spec}. Install it manually: python -m pip install {spec}")
