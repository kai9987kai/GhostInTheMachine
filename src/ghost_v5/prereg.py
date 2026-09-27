"""v5 preregistration lock: same mechanism as v4, covering v4's frozen code as well."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

from ghost_v4.prereg import HASHED_SOURCES as V4_SOURCES
from ghost_v4.prereg import ROOT, _git_head, sha256_file

PREREG_PATH = ROOT / "prereg" / "PREREGISTRATION_v5.json"
LOCK_PATH = ROOT / "prereg" / "PREREGISTRATION_v5.lock.json"
REPLICATION_PATH = ROOT / "prereg" / "REPLICATION_v4_1.json"

V5_SOURCES = [
    "src/ghost_v5/__init__.py",
    "src/ghost_v5/engine.py",
    "src/ghost_v5/estimators.py",
    "src/ghost_v5/studies.py",
]


def load(path: Path = PREREG_PATH) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def digests() -> Dict[str, str]:
    d = {"prereg_v5": sha256_file(PREREG_PATH), "replication_v4_1": sha256_file(REPLICATION_PATH)}
    for rel in V4_SOURCES + V5_SOURCES:
        d[rel] = sha256_file(ROOT / rel)
    return d


def lock() -> Dict:
    payload = {"locked_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "git_head_at_lock": _git_head(), "digests": digests()}
    LOCK_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def verify() -> Tuple[bool, List[str], Dict]:
    if not LOCK_PATH.exists():
        return False, ["<no lock file>"], {}
    payload = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    now = digests()
    bad = [k for k, v in payload["digests"].items() if now.get(k) != v]
    return not bad, bad, payload
