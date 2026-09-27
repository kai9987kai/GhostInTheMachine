"""
The null ladder.

Each rung is a surrogate-generating procedure defined by what it PRESERVES and
what it DESTROYS. A metric can only ever be specific against a rung that
destroys the structure the metric reads. Choosing the null is therefore part of
the hypothesis, not an afterthought.

    rung            preserves                              destroys
    ------------    -------------------------------------  ----------------------------------
    L0_shuffle      marginals, zero-lag covariance          all temporal order
    L1_iaaft        each channel's spectrum + amplitudes    cross-channel coordination,
                                                            nonlinear structure
    L2_mvphase      all auto- AND cross-spectra             nonlinear / higher-order temporal
                    (= every lagged linear covariance)      structure
    L3_var          linear dynamics of a fitted VAR(p)      nonlinear, non-Gaussian structure

L4 (the cross-yoked twin) is not a transformation of data: it is a different
generative mechanism and lives in `engine.py`.

References: Theiler et al. (1992) Physica D 58:77; Schreiber & Schmitz (1996)
PRL 77:635 (IAAFT); Prichard & Theiler (1994) PRL 73:951 (multivariate phase
randomization).
"""

from __future__ import annotations

from typing import Callable, Dict

import numpy as np

RUNGS = ("L0_shuffle", "L1_iaaft", "L2_mvphase", "L3_var")

RUNG_DESCRIPTIONS: Dict[str, str] = {
    "L0_shuffle": "temporal shuffle (keeps marginals + zero-lag covariance)",
    "L1_iaaft": "channel-wise IAAFT (keeps each channel's spectrum + amplitudes; breaks coordination)",
    "L2_mvphase": "multivariate phase randomization (keeps all linear auto/cross structure)",
    "L3_var": "fitted Gaussian VAR(2) simulation (keeps linear dynamics)",
}


def shuffle(X: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    return X[rng.permutation(len(X))]


def iaaft(X: np.ndarray, rng: np.random.Generator, n_iter: int = 25) -> np.ndarray:
    """
    Independent IAAFT surrogate for every column of X (T, n): alternately impose
    the original amplitude spectrum and the original value distribution.
    Iteration stops early once the rank ordering no longer changes.
    """
    X = np.asarray(X, dtype=float)
    T, n = X.shape
    sorted_vals = np.sort(X, axis=0)
    amp = np.abs(np.fft.rfft(X, axis=0))
    cols = np.arange(n)
    y = X[rng.permuted(np.tile(np.arange(T)[:, None], (1, n)), axis=0), cols]
    prev = None
    for _ in range(n_iter):
        F = np.fft.rfft(y, axis=0)
        z = np.fft.irfft(amp * np.exp(1j * np.angle(F)), n=T, axis=0)
        order = np.argsort(z, axis=0)
        y = np.empty_like(z)
        y[order, cols] = sorted_vals
        if prev is not None and np.array_equal(order, prev):
            break
        prev = order
    return y


def mv_phase(X: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Multivariate Fourier surrogate: one random phase per frequency, shared by all columns."""
    X = np.asarray(X, dtype=float)
    T = len(X)
    F = np.fft.rfft(X, axis=0)
    phases = rng.uniform(0.0, 2.0 * np.pi, size=F.shape[0])
    phases[0] = 0.0
    if T % 2 == 0:
        phases[-1] = 0.0
    return np.fft.irfft(F * np.exp(1j * phases)[:, None], n=T, axis=0)


def fit_var(X: np.ndarray, order: int = 2, ridge: float = 1e-3):
    """Least-squares VAR(order) with ridge; returns (coef list, residual chol, mean)."""
    X = np.asarray(X, dtype=float)
    mu = X.mean(axis=0)
    Xc = X - mu
    T, n = Xc.shape
    Y = Xc[order:]
    Z = np.hstack([Xc[order - k:T - k] for k in range(1, order + 1)])
    G = Z.T @ Z
    lam = ridge * float(np.trace(G)) / G.shape[0]
    B = np.linalg.solve(G + lam * np.eye(G.shape[0]), Z.T @ Y)  # (order*n, n)
    E = Y - Z @ B
    S = np.cov(E, rowvar=False) + 1e-10 * np.eye(n)
    L = np.linalg.cholesky(S)
    coefs = [B[k * n:(k + 1) * n].T for k in range(order)]  # x_t = sum_k A_k x_{t-k}
    # Enforce stability of the companion matrix.
    comp = np.zeros((order * n, order * n))
    comp[:n] = np.hstack(coefs)
    if order > 1:
        comp[n:, :-n] = np.eye((order - 1) * n)
    radius = float(np.max(np.abs(np.linalg.eigvals(comp))))
    if radius >= 0.999:
        shrink = 0.995 / radius
        coefs = [A * shrink ** (k + 1) for k, A in enumerate(coefs)]
    return coefs, L, mu


def var_surrogate(X: np.ndarray, rng: np.random.Generator, order: int = 2, burn: int = 200, fitted=None) -> np.ndarray:
    coefs, L, mu = fitted if fitted is not None else fit_var(X, order)
    X = np.asarray(X, dtype=float)
    T, n = X.shape
    p = len(coefs)
    A = np.hstack(coefs)  # (n, p*n)
    noise = rng.standard_normal((T + burn, n)) @ L.T
    hist = [(X[p - 1 - k] - mu) for k in range(p)]  # most recent first
    out = np.empty((T + burn, n))
    state = np.concatenate(hist)
    for t in range(T + burn):
        x = A @ state + noise[t]
        out[t] = x
        state = np.concatenate([x, state[:-n]]) if p > 1 else x
    return out[burn:] + mu


class NullLadder:
    """Generates surrogates for one data matrix, caching any fitted model."""

    def __init__(self, X: np.ndarray, rng: np.random.Generator, var_order: int = 2):
        self.X = np.asarray(X, dtype=float)
        self.rng = rng
        self.var_order = var_order
        self._var = None

    def draw(self, rung: str) -> np.ndarray:
        if rung == "L0_shuffle":
            return shuffle(self.X, self.rng)
        if rung == "L1_iaaft":
            return iaaft(self.X, self.rng)
        if rung == "L2_mvphase":
            return mv_phase(self.X, self.rng)
        if rung == "L3_var":
            if self._var is None:
                self._var = fit_var(self.X, self.var_order)
            return var_surrogate(self.X, self.rng, fitted=self._var)
        raise ValueError(f"unknown rung {rung!r}")


SURROGATE_FUNCS: Dict[str, Callable] = {
    "L0_shuffle": shuffle,
    "L1_iaaft": iaaft,
    "L2_mvphase": mv_phase,
    "L3_var": var_surrogate,
}
