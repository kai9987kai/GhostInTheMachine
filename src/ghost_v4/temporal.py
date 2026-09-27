"""
Arrow-of-time (temporal irreversibility) statistics.

A stationary process is time-reversible when its statistics are unchanged by
playing it backwards. Two facts make irreversibility a sharp tool here:

* A temporal shuffle (rung L0) is exchangeable, hence exactly reversible.
* A stationary univariate linear Gaussian process is reversible (Weiss 1975),
  so per-channel irreversibility that survives rung L2/L3 surrogates must come
  from nonlinear or non-Gaussian dynamics. Multivariate linear processes can be
  irreversible through asymmetric lagged cross-covariance; that part is captured
  separately by `lagged_asymmetry` and is preserved by rungs L2/L3.

Non-equilibrium, time-irreversible dynamics have been proposed as a signature of
conscious brain states (Sanz Perl et al. 2021, Phys Rev E 104: 014411;
de la Fuente et al. 2023, Cerebral Cortex 33: 1856-1865). Here they are used
only as synthetic dynamical observables.

Ordinal reversibility test after Zanin, Rodriguez-Gonzalez, Menasalvas Ruiz &
Papo (2018), Entropy 20: 665.
"""

from __future__ import annotations

import math
from itertools import permutations
from typing import Tuple

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view


def _as2d(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    return x[:, None] if x.ndim == 1 else x


def _pattern_codes(X: np.ndarray, order: int, lag: int) -> Tuple[np.ndarray, np.ndarray]:
    """Forward and time-reversed ordinal-pattern codes, shape (windows, channels)."""
    span = (order - 1) * lag + 1
    W = sliding_window_view(X, span, axis=0)[..., ::lag]  # (T-span+1, ch, order)
    pi = np.argsort(W, axis=-1, kind="stable")
    powers = order ** np.arange(order)
    fwd = pi @ powers
    rev = (order - 1 - pi) @ powers
    return fwd, rev


def ordinal_irreversibility(X: np.ndarray, order: int = 3, lag: int = 1, per_channel: bool = False):
    """
    KL divergence between the ordinal-pattern distribution of each channel and
    that of the same channel played backwards (symmetric by construction).
    Returns the channel mean (or the per-channel vector).
    """
    X = _as2d(X)
    fwd, rev = _pattern_codes(X, order, lag)
    ncodes = order ** order
    valid = np.zeros(ncodes, dtype=bool)
    for p in permutations(range(order)):
        valid[int(np.dot(p, order ** np.arange(order)))] = True
    out = np.empty(X.shape[1])
    for c in range(X.shape[1]):
        pf = np.bincount(fwd[:, c], minlength=ncodes)[valid] + 0.5
        pr = np.bincount(rev[:, c], minlength=ncodes)[valid] + 0.5
        pf = pf / pf.sum()
        pr = pr / pr.sum()
        out[c] = float(np.sum(pf * np.log(pf / pr)))
    return out if per_channel else float(out.mean())


def time_asymmetry_q3(X: np.ndarray, lag: int = 1) -> float:
    """
    Mean absolute third-order time-reversal asymmetry across channels:
        Q(lag) = E[(x_{t+lag} - x_t)^3] / E[(x_{t+lag} - x_t)^2]^{3/2}
    Q = 0 for any time-reversible process (Theiler et al. 1992 surrogate statistic).
    """
    X = _as2d(X)
    d = X[lag:] - X[:-lag]
    m2 = np.mean(d ** 2, axis=0)
    m3 = np.mean(d ** 3, axis=0)
    q = m3 / np.maximum(m2, 1e-15) ** 1.5
    return float(np.mean(np.abs(q)))


def lagged_asymmetry(Y: np.ndarray, lag: int = 1) -> float:
    """
    Normalized asymmetry of the lagged cross-correlation matrix,
        ||C(lag) - C(lag)^T||_F / ||C(lag)||_F,  C_ij = corr(y_i(t), y_j(t+lag)).
    Zero for any reversible process; a linear (second-order) irreversibility.
    """
    Z = _as2d(Y)
    Z = (Z - Z.mean(0)) / (Z.std(0) + 1e-12)
    A, B = Z[:-lag], Z[lag:]
    C = A.T @ B / len(A)
    denom = float(np.linalg.norm(C)) + 1e-12
    return float(np.linalg.norm(C - C.T) / denom)


def lz76_complexity(bits: np.ndarray) -> int:
    """Lempel-Ziv (1976) phrase count, Kaspar-Schuster algorithm."""
    s = np.asarray(bits, dtype=np.uint8).ravel()
    n = len(s)
    if n < 2:
        return n
    c, l, i, k, k_max = 1, 1, 0, 1, 1
    while True:
        if s[i + k - 1] == s[l + k - 1]:
            k += 1
            if l + k > n:
                c += 1
                break
        else:
            k_max = max(k, k_max)
            i += 1
            if i == l:
                c += 1
                l += k_max
                if l + 1 > n:
                    break
                i, k, k_max = 0, 1, 1
            else:
                k = 1
    return c


def normalized_lz76(bits: np.ndarray) -> float:
    n = len(np.asarray(bits).ravel())
    if n < 8:
        return 0.0
    return lz76_complexity(bits) * math.log2(n) / n
