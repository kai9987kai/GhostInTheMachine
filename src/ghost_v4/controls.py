"""
Ground-truth systems for instrument calibration.

A test that cannot fail is useless; so is a test that cannot pass. Before any
claim about the agent, v4 measures, for each metric/rung pair it relies on,

    false-positive rate  on systems where the property is absent by construction
    power                on systems where the property is present by construction.

Each generator returns an array (T, n) of "micro" variables.
"""

from __future__ import annotations

import numpy as np


def independent_ar(rng: np.random.Generator, T: int = 4000, n: int = 12, phi: float = 0.9) -> np.ndarray:
    """n independent AR(1) processes. No coordination, fully reversible, linear."""
    X = np.zeros((T + 200, n))
    e = rng.standard_normal((T + 200, n))
    for t in range(1, T + 200):
        X[t] = phi * X[t - 1] + e[t]
    return X[200:]


def shared_mode(rng: np.random.Generator, T: int = 4000, n: int = 12, phi: float = 0.95,
                private_noise: float = 2.0) -> np.ndarray:
    """
    Parts driven by one shared slow latent (a 'flock'): x_i = s + noise_i.
    The collective mode predicts its own future better than independent parts
    with identical individual autocorrelation would: emergence beyond aggregation.
    """
    s = np.zeros(T + 200)
    e = rng.standard_normal(T + 200)
    for t in range(1, T + 200):
        s[t] = phi * s[t - 1] + e[t]
    s = s[200:] / s[200:].std()
    return s[:, None] + private_noise * rng.standard_normal((T, n))


def linear_nonnormal_var(rng: np.random.Generator, T: int = 4000, n: int = 12) -> np.ndarray:
    """
    Stable linear Gaussian VAR(1) with a non-symmetric (feed-forward) coupling
    matrix: irreversible in its lagged cross-covariance, but with no nonlinear
    structure. Negative control for nonlinear irreversibility.
    """
    A = 0.55 * np.eye(n)
    for i in range(n - 1):
        A[i + 1, i] = 0.6  # chain i -> i+1
    radius = float(np.max(np.abs(np.linalg.eigvals(A))))
    A *= min(1.0, 0.9 / radius)
    X = np.zeros((T + 200, n))
    e = rng.standard_normal((T + 200, n))
    for t in range(1, T + 200):
        X[t] = A @ X[t - 1] + e[t]
    return X[200:]


def relaxation_oscillators(rng: np.random.Generator, T: int = 4000, n: int = 12) -> np.ndarray:
    """
    Noisy integrate-and-reset units (slow rise, abrupt reset): strongly
    time-irreversible through nonlinear dynamics. Positive control.
    """
    X = np.zeros((T, n))
    x = rng.uniform(0, 1, n)
    rate = rng.uniform(0.03, 0.06, n)
    for t in range(T):
        x = x + rate + 0.02 * rng.standard_normal(n)
        fired = x > 1.0
        x[fired] = 0.0
        X[t] = x
    return X + 0.02 * rng.standard_normal((T, n))


CONTROLS = {
    "independent_ar": independent_ar,
    "shared_mode": shared_mode,
    "linear_nonnormal_var": linear_nonnormal_var,
    "relaxation_oscillators": relaxation_oscillators,
}
