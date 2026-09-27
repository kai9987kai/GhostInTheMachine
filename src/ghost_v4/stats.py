"""
Inference utilities: surrogate p-values, paired randomization tests, effect
sizes, bootstrap intervals and family-wise error control. NumPy + stdlib only.
"""

from __future__ import annotations

import math
from statistics import NormalDist
from typing import Dict, Iterable, List, Sequence

import numpy as np

_NORMAL = NormalDist()


def empirical_p(real: float, null: Sequence[float], alternative: str = "greater") -> float:
    """
    Surrogate-test p-value with the +1 correction, p = (1 + #{null as extreme}) / (1 + m),
    which is exact (never anti-conservative) under exchangeability.
    """
    null = np.asarray(null, dtype=float)
    m = len(null)
    if m == 0:
        return float("nan")
    if alternative == "greater":
        b = int(np.sum(null >= real))
    elif alternative == "less":
        b = int(np.sum(null <= real))
    elif alternative == "two-sided":
        centre = float(np.median(null))
        b = int(np.sum(np.abs(null - centre) >= abs(real - centre)))
    else:
        raise ValueError(alternative)
    return (1 + b) / (1 + m)


def null_z(real: float, null: Sequence[float]) -> float:
    """Standardized distance of the real value from its surrogate distribution."""
    null = np.asarray(null, dtype=float)
    sd = float(np.std(null, ddof=1)) if len(null) > 1 else 0.0
    if sd < 1e-12:
        return 0.0 if abs(real - float(np.mean(null))) < 1e-12 else math.copysign(99.0, real - float(np.mean(null)))
    return float((real - np.mean(null)) / sd)


def sign_flip_test(d: Sequence[float], alternative: str = "greater", n_perm: int = 20000,
                   rng: np.random.Generator | None = None) -> float:
    """
    Paired randomization test on the mean difference (sign-flip). Exact
    enumeration for n <= 16, Monte Carlo (+1 corrected) otherwise.
    """
    d = np.asarray(d, dtype=float)
    d = d[np.isfinite(d)]
    n = len(d)
    if n == 0:
        return float("nan")
    obs = float(np.mean(d))
    if n <= 16:
        signs = ((np.arange(2 ** n)[:, None] >> np.arange(n)) & 1) * 2 - 1
        dist = signs @ d / n
        denom = len(dist)
        extra = 0
    else:
        rng = rng or np.random.default_rng(0)
        signs = rng.choice([-1.0, 1.0], size=(n_perm, n))
        dist = signs @ d / n
        denom = n_perm + 1
        extra = 1
    eps = 1e-12
    if alternative == "greater":
        b = int(np.sum(dist >= obs - eps))
    elif alternative == "less":
        b = int(np.sum(dist <= obs + eps))
    else:
        b = int(np.sum(np.abs(dist) >= abs(obs) - eps))
    return (b + extra) / denom


def paired_effect(d: Sequence[float]) -> Dict[str, float]:
    """Mean difference, Cohen's d_z and Hedges-corrected g_z for paired data."""
    d = np.asarray(d, dtype=float)
    d = d[np.isfinite(d)]
    n = len(d)
    mean = float(np.mean(d)) if n else float("nan")
    sd = float(np.std(d, ddof=1)) if n > 1 else float("nan")
    dz = mean / sd if n > 1 and sd > 1e-15 else float("nan")
    j = 1.0 - 3.0 / (4.0 * (n - 1) - 1.0) if n > 2 else float("nan")
    return {"n": n, "mean": mean, "sd": sd, "d_z": dz, "g_z": dz * j if np.isfinite(dz) else float("nan")}


def bootstrap_ci(x: Sequence[float], stat=np.mean, n_boot: int = 10000, level: float = 0.95,
                 rng: np.random.Generator | None = None) -> List[float]:
    """Percentile bootstrap confidence interval."""
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) < 2:
        return [float("nan"), float("nan")]
    rng = rng or np.random.default_rng(0)
    idx = rng.integers(0, len(x), size=(n_boot, len(x)))
    boots = np.apply_along_axis(stat, 1, x[idx]) if stat is not np.mean else x[idx].mean(axis=1)
    a = (1.0 - level) / 2.0
    return [float(np.quantile(boots, a)), float(np.quantile(boots, 1.0 - a))]


def holm(pvals: Sequence[float]) -> List[float]:
    """Holm-Bonferroni step-down adjusted p-values (strong FWER control)."""
    p = np.asarray(pvals, dtype=float)
    m = len(p)
    order = np.argsort(p)
    adj = np.empty(m)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * p[i]))
        adj[i] = running
    return adj.tolist()


def benjamini_hochberg(pvals: Sequence[float]) -> List[float]:
    """Benjamini-Hochberg FDR-adjusted p-values."""
    p = np.asarray(pvals, dtype=float)
    m = len(p)
    order = np.argsort(p)
    adj = np.empty(m)
    running = 1.0
    for rank in range(m - 1, -1, -1):
        i = order[rank]
        running = min(running, p[i] * m / (rank + 1))
        adj[i] = running
    return adj.tolist()


def stouffer(pvals: Iterable[float]) -> float:
    """Combine one-sided p-values by Stouffer's Z (unweighted)."""
    p = np.clip(np.asarray(list(pvals), dtype=float), 1e-12, 1 - 1e-12)
    if len(p) == 0:
        return float("nan")
    z = np.array([_NORMAL.inv_cdf(1.0 - pi) for pi in p])
    zc = float(z.sum() / math.sqrt(len(z)))
    return 1.0 - _NORMAL.cdf(zc)


def binomial_sf(k: int, n: int, p: float) -> float:
    """P(X >= k) for X ~ Binomial(n, p)."""
    return float(sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1)))


def wilson_interval(k: int, n: int, level: float = 0.95) -> List[float]:
    if n == 0:
        return [float("nan"), float("nan")]
    z = _NORMAL.inv_cdf(0.5 + level / 2.0)
    phat = k / n
    denom = 1 + z * z / n
    centre = (phat + z * z / (2 * n)) / denom
    half = z * math.sqrt(phat * (1 - phat) / n + z * z / (4 * n * n)) / denom
    return [max(0.0, centre - half), min(1.0, centre + half)]
