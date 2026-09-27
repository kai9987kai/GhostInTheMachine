"""
Cryptographic preregistration.

`lock` hashes the preregistration document together with every source file
that can influence a confirmatory result, and writes the digests to a lock
file. The confirmatory runner refuses to produce confirmatory output unless
the current files hash to the locked values; anything else is labelled
EXPLORATORY. Committing the lock file to git before the confirmatory run gives
an externally timestamped, tamper-evident record of what was planned.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[2]
PREREG_PATH = ROOT / "prereg" / "PREREGISTRATION_v4.json"
LOCK_PATH = ROOT / "prereg" / "PREREGISTRATION_v4.lock.json"

# Files whose content can change a confirmatory number.
HASHED_SOURCES = [
    "src/ghost_in_the_machine_v3.py",
    "src/ghost_v4/__init__.py",
    "src/ghost_v4/campaign.py",
    "src/ghost_v4/classifier.py",
    "src/ghost_v4/controls.py",
    "src/ghost_v4/engine.py",
    "src/ghost_v4/infotheory.py",
    "src/ghost_v4/metrics.py",
    "src/ghost_v4/stats.py",
    "src/ghost_v4/surrogates.py",
    "src/ghost_v4/temporal.py",
    "src/ghost_v4/v3_bridge.py",
]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_prereg(path: Path = PREREG_PATH) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def current_digests(prereg_path: Path = PREREG_PATH) -> Dict[str, str]:
    d = {"prereg": sha256_file(prereg_path)}
    for rel in HASHED_SOURCES:
        d[rel] = sha256_file(ROOT / rel)
    return d


def _git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True,
                                       stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "unavailable"


def lock(prereg_path: Path = PREREG_PATH, lock_path: Path = LOCK_PATH) -> Dict:
    payload = {
        "locked_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_head_at_lock": _git_head(),
        "digests": current_digests(prereg_path),
    }
    lock_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def verify(prereg_path: Path = PREREG_PATH, lock_path: Path = LOCK_PATH) -> Tuple[bool, List[str], Dict]:
    """Return (ok, list of mismatching files, lock payload)."""
    if not lock_path.exists():
        return False, ["<no lock file>"], {}
    payload = json.loads(lock_path.read_text(encoding="utf-8"))
    now = current_digests(prereg_path)
    bad = [k for k, v in payload["digests"].items() if now.get(k) != v]
    return not bad, bad, payload
