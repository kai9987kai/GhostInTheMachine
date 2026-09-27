"""
Estimators that relax v4's linear-Gaussian assumption.

Gaussian copula (GC) MI (Ince et al. 2017, Human Brain Mapping 38:1541)
    Rank-transform each variable to standard normal marginals, then use the
    Gaussian estimator. Invariant to monotone transforms of each variable; a lower
    bound on MI that is robust to non-Gaussian marginals.

Kraskov-Stoegbauer-Grassberger (KSG) MI, algorithm 1 (Kraskov et al. 2004,
    PRE 69:066138)
    k-nearest-neighbour estimator; consistent for arbitrary (including nonlinear)
    dependence. Implemented here for pairs of 1-D variables in O(N^2) time with
    chunked memory, which is all Psi and persistence need.
"""

from __future__ import annotations

import math
from typing import Dict

import numpy as np

from ghost_v4 import infotheory as it

_EULER_GAMMA = 0.5772156649015329


# ---------------------------------------------------------------- Gaussian copula

def _norm_ppf(p: np.ndarray) -> np.ndarray:
    """Inverse standard normal CDF (Acklam's rational approximation, |error| < 1.2e-9)."""
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00, 3.754408661907416e+00]
    p = np.asarray(p, dtype=float)
    out = np.empty_like(p)
    lo, hi = 0.02425, 1 - 0.02425
    m = p < lo
    q = np.sqrt(-2 * np.log(p[m]))
    out[m] = (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
             ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    m = (p >= lo) & (p <= hi)
    q = p[m] - 0.5
    r = q * q
    out[m] = (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / \
             (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)
    m = p > hi
    q = np.sqrt(-2 * np.log(1 - p[m]))
    out[m] = -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
             ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    return out


def copula_normalize(X: np.ndarray) -> np.ndarray:
    """Map every column to standard-normal marginals through its empirical ranks."""
    X = np.asarray(X, dtype=float)
    squeeze = X.ndim == 1
    X = X[:, None] if squeeze else X
    ranks = np.argsort(np.argsort(X, axis=0, kind="stable"), axis=0, kind="stable") + 1.0
    Z = _norm_ppf(ranks / (len(X) + 1.0))
    return Z[:, 0] if squeeze else Z


def gc_persistence(V: np.ndarray) -> float:
    Z = copula_normalize(V)
    return it.gaussian_mi(Z[:-1], Z[1:])


def gc_emergence(micro: np.ndarray, macro: np.ndarray) -> Dict[str, float]:
    return it.emergence_criteria(copula_normalize(micro), copula_normalize(macro))


# ---------------------------------------------------------------- KSG

def _digamma_int(n: np.ndarray) -> np.ndarray:
    """Digamma at positive integers: psi(n) = -gamma + H_{n-1}."""
    n = np.asarray(n, dtype=np.int64)
    top = int(n.max()) if n.size else 1
    harmonic = np.concatenate([[0.0], np.cumsum(1.0 / np.arange(1, top + 1))])
    return -_EULER_GAMMA + harmonic[n - 1]


def ksg_mi(x: np.ndarray, y: np.ndarray, k: int = 4, chunk: int = 512, jitter: float = 1e-10,
           rng: np.random.Generator | None = None) -> float:
    """KSG algorithm-1 mutual information (nats) between two 1-D samples."""
    rng = rng or np.random.default_rng(0)
    x = np.asarray(x, dtype=float).ravel()
    y = np.asarray(y, dtype=float).ravel()
    x = (x - x.mean()) / (x.std() + 1e-15) + jitter * rng.standard_normal(len(x))
    y = (y - y.mean()) / (y.std() + 1e-15) + jitter * rng.standard_normal(len(y))
    N = len(x)
    eps = np.empty(N)
    for s in range(0, N, chunk):
        e = min(N, s + chunk)
        d = np.maximum(np.abs(x[s:e, None] - x[None, :]), np.abs(y[s:e, None] - y[None, :]))
        d[np.arange(e - s), np.arange(s, e)] = np.inf           # exclude self
        eps[s:e] = np.partition(d, k - 1, axis=1)[:, k - 1]
    xs, ys = np.sort(x), np.sort(y)
    nx = np.searchsorted(xs, x + eps, side="left") - np.searchsorted(xs, x - eps, side="right") - 1
    ny = np.searchsorted(ys, y + eps, side="left") - np.searchsorted(ys, y - eps, side="right") - 1
    nx = np.maximum(nx, 0)
    ny = np.maximum(ny, 0)
    return float(_digamma_int(np.array([k]))[0] + _digamma_int(np.array([N]))[0]
                 - np.mean(_digamma_int(nx + 1) + _digamma_int(ny + 1)))


def ksg_persistence(V: np.ndarray, k: int = 4) -> float:
    V = np.asarray(V, dtype=float).ravel()
    return ksg_mi(V[:-1], V[1:], k=k)


def ksg_emergence(micro: np.ndarray, macro: np.ndarray, k: int = 4) -> Dict[str, float]:
    """Rosas Psi with every mutual information estimated by KSG."""
    X = np.asarray(micro, dtype=float)
    V = np.asarray(macro, dtype=float).ravel()
    Vt, Vf = V[:-1], V[1:]
    i_vv = ksg_mi(Vt, Vf, k=k)
    parts = np.array([ksg_mi(X[:-1, j], Vf, k=k) for j in range(X.shape[1])])
    return {"psi": i_vv - float(parts.sum()), "macro_self_information": i_vv,
            "parts_information": float(parts.sum())}
