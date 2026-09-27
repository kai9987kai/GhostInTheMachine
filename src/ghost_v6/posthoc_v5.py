"""
Post-hoc (EXPLORATORY) re-reading of the v5 null results.

v5 reported several non-significant tests as "did not replicate" or "did not move".
Non-significance is absence of evidence; this module asks which of those nulls are
evidence of absence. It was written after the v5 data were seen, so none of it is
confirmatory, and it is kept outside the v6 lock on purpose.

Two tools:
    equivalence (TOST)  is the effect inside (-bound, +bound)? Bounds are one third
                        of the corresponding v4 confirmatory effect.
    small telescopes    (Simonsohn 2015) is the replication effect significantly
                        smaller than d33, the effect the original study (n = 48) had
                        33% power to detect?
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Dict

import numpy as np

from ghost_v4 import stats as st
from ghost_v4.campaign import _dz, _load_runs
from ghost_v5.studies import LEVELS, VARIANTS_D, _authorship, _col, _load

from .studies import SESOI_PERSISTENCE, tost

V4_H4_MEAN_DIFF = 0.1684       # v4 confirmatory H4 (Psi) master - twin, results/v4/results_v4.json
SESOI_PSI = round(V4_H4_MEAN_DIFF / 3.0, 4)


def _inv_norm(p: float) -> float:
    """Inverse standard normal CDF (Acklam's rational approximation, |error| < 1.2e-9 after one Newton step)."""
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02, 1.383577518672690e+02,
         -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02, 6.680131188771972e+01,
         -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00, -2.549732539343734e+00,
         4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00, 3.754408661907416e+00]
    lo = 0.02425
    if p < lo:
        q = math.sqrt(-2 * math.log(p))
        x = (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
            ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    elif p > 1 - lo:
        return -_inv_norm(1 - p)
    else:
        q = p - 0.5
        r = q * q
        x = (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / \
            (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)
    e = 0.5 * math.erfc(-x / math.sqrt(2)) - p
    u = e * math.sqrt(2 * math.pi) * math.exp(x * x / 2)
    return x - u / (1 + x * u / 2)


def d33(n_original: int, alpha: float = 0.05) -> float:
    """Effect size (d_z) a one-sided paired test with n_original had 33% power to detect (normal approximation)."""
    return (_inv_norm(1 - alpha) - _inv_norm(2.0 / 3.0)) / math.sqrt(n_original)


def small_telescopes(d: np.ndarray, n_original: int, rng) -> Dict:
    d = np.asarray(d, dtype=float)
    target = d33(n_original)
    idx = rng.integers(0, len(d), size=(10000, len(d)))
    boots = np.array([_dz(d[i]) for i in idx])
    p = float((np.sum(boots >= target) + 1) / (len(boots) + 1))
    return {"d33": target, "replication_d_z": _dz(d), "p_smaller_than_d33": p,
            "verdict": "replication effect significantly smaller than d33" if p <= 0.05
            else "cannot rule out an effect of size d33"}


def run(root: Path) -> Dict:
    rng = np.random.default_rng(64)
    out = {"status": "POST-HOC, EXPLORATORY: written after the v5 data were seen; not preregistered",
           "bounds": {"persistence_nats": SESOI_PERSISTENCE, "psi": SESOI_PSI,
                      "psi_rule": "one third of the v4 confirmatory H4 mean difference"}}
    v5 = root / "results" / "v5"

    data, seeds = _load_runs(v5 / "A")
    h4 = np.array([data[(s, "full", "master")]["self_psi"] - data[(s, "full", "twin")]["self_psi"] for s in seeds])
    out["A_H4_psi"] = {"test": st.paired_effect(h4), "equivalence": tost(h4, SESOI_PSI, rng),
                       "small_telescopes": small_telescopes(h4, 48, rng),
                       "v4_estimate_outside_replication_ci95": bool(st.bootstrap_ci(h4, rng=rng)[1] < V4_H4_MEAN_DIFF)}

    dataB, seedsB = _load(v5 / "B")
    x = np.array(LEVELS)
    Y = np.stack([_col(dataB, seedsB, f"full@p{p:g}", "graded", "self_psi") for p in LEVELS], axis=1)
    slopes = np.polyfit(x, Y.T, 1)[0]
    out["B3_psi_slope"] = {"test": st.paired_effect(slopes), "equivalence": tost(slopes, SESOI_PSI, rng),
                           "note": "slope per unit authorship, so the bound is the SESOI over the full 0-to-1 range"}

    dataD, seedsD = _load(v5 / "D")
    out["D_psi"] = {v: {"test": st.paired_effect(_authorship(dataD, seedsD, v, "self_psi")),
                        "equivalence": tost(_authorship(dataD, seedsD, v, "self_psi"), SESOI_PSI, rng)}
                    for v in VARIANTS_D}

    dataE, seedsE = _load(v5 / "E")
    off = _authorship(dataE, seedsE, "off_late", "self_persistence")
    out["E_switched_off_persistence"] = {"test": st.paired_effect(off),
                                         "equivalence": tost(off, SESOI_PERSISTENCE, rng)}
    return out
