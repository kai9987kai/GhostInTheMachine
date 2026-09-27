"""
Linear-Gaussian information-theoretic estimators.

Every estimator here treats the data as jointly Gaussian, so it measures only
second-order (linear, lagged-covariance) information. That is a deliberate,
declared limitation: all of these quantities are functions of the lag-0 and
lag-1 covariance matrices, and are therefore preserved (up to sampling noise)
by any surrogate that preserves the auto- and cross-spectra (null rung L2).
They can beat a null only when the null destroys lagged covariance structure.

Units are nats throughout.

References
----------
Rosas, F. E., Mediano, P. A. M., Jensen, H. J., Seth, A. K., Barrett, A. B.,
    Carhart-Harris, R. L., & Bor, D. (2020). Reconciling emergences: an
    information-theoretic approach to identify causal emergence in multivariate
    data. PLoS Computational Biology 16(12): e1008289.
Mediano, P. A. M., Rosas, F. E., Farah, J. C., Shanahan, M., Bor, D., &
    Barrett, A. B. (2022). Integrated information as a common signature of
    dynamical and information-processing complexity. Chaos 32: 013115.
Barnett, L., Barrett, A. B., & Seth, A. K. (2009). Granger causality and
    transfer entropy are equivalent for Gaussian variables. PRL 103: 238701.
"""

from __future__ import annotations

import math
from typing import Dict

import numpy as np

_RIDGE = 1e-9


def _as2d(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    return x[:, None] if x.ndim == 1 else x


def logdet_cov(C: np.ndarray, ridge: float = _RIDGE) -> float:
    """log-determinant of a covariance matrix with a scale-relative ridge."""
    C = np.atleast_2d(np.asarray(C, dtype=float))
    d = C.shape[0]
    scale = float(np.trace(C)) / d if d else 1.0
    _, ld = np.linalg.slogdet(C + ridge * max(scale, 1e-12) * np.eye(d))
    return float(ld)


def gaussian_entropy(X: np.ndarray) -> float:
    X = _as2d(X)
    d = X.shape[1]
    return 0.5 * (d * math.log(2.0 * math.pi * math.e) + logdet_cov(np.cov(X, rowvar=False)))


def gaussian_mi(X: np.ndarray, Y: np.ndarray) -> float:
    """I(X;Y) for jointly Gaussian X (T,dx) and Y (T,dy)."""
    X, Y = _as2d(X), _as2d(Y)
    dx = X.shape[1]
    C = np.atleast_2d(np.cov(np.hstack([X, Y]), rowvar=False))
    mi = 0.5 * (logdet_cov(C[:dx, :dx]) + logdet_cov(C[dx:, dx:]) - logdet_cov(C))
    return max(0.0, mi)


def gaussian_cmi(X: np.ndarray, Y: np.ndarray, Z: np.ndarray) -> float:
    """I(X;Y|Z) = H(X,Z) + H(Y,Z) - H(Z) - H(X,Y,Z) for jointly Gaussian data."""
    X, Y, Z = _as2d(X), _as2d(Y), _as2d(Z)
    dx, dy = X.shape[1], Y.shape[1]
    C = np.cov(np.hstack([X, Y, Z]), rowvar=False)
    ix = np.arange(dx)
    iy = np.arange(dx, dx + dy)
    iz = np.arange(dx + dy, C.shape[0])

    def sub(idx):
        return C[np.ix_(idx, idx)]

    cmi = 0.5 * (
        logdet_cov(sub(np.r_[ix, iz]))
        + logdet_cov(sub(np.r_[iy, iz]))
        - logdet_cov(sub(iz))
        - logdet_cov(C)
    )
    return max(0.0, cmi)


def _embed(X: np.ndarray, lags: int, start: int, stop: int) -> np.ndarray:
    """Stack X[t], X[t-1], ..., X[t-lags+1] for t in [start, stop)."""
    return np.hstack([X[start - k:stop - k] for k in range(lags)])


def transfer_entropy(source: np.ndarray, target: np.ndarray, k: int = 2, l: int = 1) -> float:
    """
    Gaussian transfer entropy TE(source -> target) = I(target_{t+1}; source^(l)_t | target^(k)_t).
    Equals half the Granger log-variance ratio for Gaussian data (Barnett et al. 2009).
    """
    S, Tg = _as2d(source), _as2d(target)
    p = max(k, l)
    n = len(Tg)
    future = Tg[p:n]
    past_t = _embed(Tg, k, p - 1, n - 1)
    past_s = _embed(S, l, p - 1, n - 1)
    return gaussian_cmi(future, past_s, past_t)


# ---------------------------------------------------------------------------
# Causal emergence (Rosas et al. 2020)
# ---------------------------------------------------------------------------

def _standardize(X: np.ndarray) -> np.ndarray:
    X = _as2d(X)
    sd = X.std(axis=0)
    sd[sd < 1e-12] = 1.0
    return (X - X.mean(axis=0)) / sd


def _mi_from_r(r: np.ndarray) -> np.ndarray:
    r2 = np.clip(np.asarray(r, dtype=float) ** 2, 0.0, 1.0 - 1e-12)
    return -0.5 * np.log1p(-r2)


def emergence_criteria(micro: np.ndarray, macro: np.ndarray, lag: int = 1) -> Dict[str, float]:
    """
    Rosas et al. (2020) practical criteria for a 1-D macro feature V = f(X).

    psi   = I(V_t; V_t') - sum_j I(X^j_t; V_t')
            Psi > 0 is sufficient for causal emergence of V.
    delta = max_j [ I(V_t; X^j_t') - sum_i I(X^i_t; X^j_t') ]
            Delta > 0 is sufficient for downward causation from V.
    gamma = max_j I(V_t; X^j_t')
            Causal decoupling is indicated when psi > 0 and gamma ~ 0.
    psi_r = psi + (n-1) * min_j I(X^j_t; V_t')
            Adds back the minimum-mutual-information redundancy that the plain
            sum subtracts n times instead of once (lattice-style correction).

    Calibration caveat (demonstrated in tests/test_estimators.py and in the v4
    instrument-calibration block): with linear-Gaussian estimation the sign of
    psi tracks redundancy, not coordination. The mean of *independent*
    autocorrelated parts gives psi > 0, while a genuinely coordinated "flock"
    whose parts all carry the shared signal gives psi < 0. v4 therefore never
    interprets psi against zero, nor against a coordination-destroying null;
    psi is only used in matched contrasts (master vs yoked twin, population vs
    population) where the aggregation structure is held fixed.
    """
    X = _standardize(micro)
    V = _standardize(macro)
    if V.shape[1] != 1:
        raise ValueError("emergence_criteria expects a 1-D macro variable")
    n = X.shape[1]
    N = len(X) - lag
    Xt, Xf = X[:-lag], X[lag:]
    Vt, Vf = V[:-lag, 0], V[lag:, 0]

    def corr_cols(A: np.ndarray, b: np.ndarray) -> np.ndarray:
        A = (A - A.mean(0)) / (A.std(0) + 1e-12)
        b = (b - b.mean()) / (b.std() + 1e-12)
        return A.T @ b / len(b)

    i_vv = float(_mi_from_r(np.corrcoef(Vt, Vf)[0, 1]))
    i_xv = _mi_from_r(corr_cols(Xt, Vf))           # I(X^j_t; V_t')
    i_vx = _mi_from_r(corr_cols(Xf, Vt))           # I(V_t; X^j_t')

    At = (Xt - Xt.mean(0)) / (Xt.std(0) + 1e-12)
    Af = (Xf - Xf.mean(0)) / (Xf.std(0) + 1e-12)
    i_xx = _mi_from_r(At.T @ Af / N)               # [i, j] = I(X^i_t; X^j_t')

    psi = i_vv - float(i_xv.sum())
    delta = float(np.max(i_vx - i_xx.sum(axis=0)))
    gamma = float(np.max(i_vx))
    psi_r = psi + (n - 1) * float(np.min(i_xv))
    return {
        "psi": psi,
        "psi_r": psi_r,
        "delta": delta,
        "gamma": gamma,
        "macro_self_information": i_vv,
        "parts_information": float(i_xv.sum()),
    }


def closure_metrics(macro: np.ndarray, micro: np.ndarray, env: np.ndarray, lag: int = 1) -> Dict[str, float]:
    """
    Informational closure of a macro process V with respect to its own parts X
    and to an environment E.

    self_information   I(V_t'; V_t)
    micro_dependence   I(V_t'; X_t | V_t)
                       "dynamical dependence" (Barnett & Seth 2023, PRE 108:014304):
                       how much the micro-state still adds once the macro past is
                       known. Zero means V is dynamically independent of its parts.
    env_dependence     I(V_t'; E_t | V_t)   (lack of closure w.r.t. environment)
    ntic               I(V_t'; E_t) - I(V_t'; E_t | V_t)
                       Non-trivial informational closure (Bertschinger et al. 2006;
                       Chang, Biehl, Yu & Kanai 2020, Front. Psychol. 11:1504): the
                       environmental information about V's future that V already
                       carries in its own past, i.e. how much V models E.
    """
    V = _as2d(macro)
    X = _as2d(micro)
    E = _as2d(env)
    Vt, Vf = V[:-lag], V[lag:]
    Xt, Et = X[:-lag], E[:-lag]
    self_info = gaussian_mi(Vt, Vf)
    i_ve = gaussian_mi(Vf, Et)
    env_dep = gaussian_cmi(Vf, Et, Vt)
    return {
        "self_information": self_info,
        "micro_dependence": gaussian_cmi(Vf, Xt, Vt),
        "env_dependence": env_dep,
        "ntic": i_ve - env_dep,
    }


def slow_macro(micro: np.ndarray, lag: int = 1, ridge: float = 1e-6) -> np.ndarray:
    """
    Maximum-autocorrelation linear feature of a population (Min/Max Autocorrelation
    Factors, Switzer & Green 1984; equivalently the slowest feature of linear Slow
    Feature Analysis). This is the population's most self-predictive linear macro,
    in the spirit of searching for dynamically independent macroscopic variables
    (Barnett & Seth 2023). Being fitted to the data, it must be (and in v4 is)
    re-fitted identically on every surrogate and every comparison condition.
    """
    X = _as2d(micro)
    Xc = X - X.mean(axis=0)
    if X.shape[1] == 1:
        return Xc[:, 0]
    C0 = Xc.T @ Xc / len(Xc)
    C1 = Xc[:-lag].T @ Xc[lag:] / (len(Xc) - lag)
    C1 = 0.5 * (C1 + C1.T)
    C0 = C0 + ridge * np.trace(C0) / len(C0) * np.eye(len(C0))
    L = np.linalg.cholesky(C0)
    Li = np.linalg.inv(L)
    M = Li @ C1 @ Li.T
    vals, vecs = np.linalg.eigh(0.5 * (M + M.T))
    w = Li.T @ vecs[:, -1]
    return Xc @ w


def principal_macro(micro: np.ndarray) -> np.ndarray:
    """First principal component score of a population (a fixed linear V = f(X))."""
    X = _as2d(micro)
    Xc = X - X.mean(axis=0)
    if X.shape[1] == 1:
        return Xc[:, 0]
    _, _, vt = np.linalg.svd(Xc, full_matrices=False)
    return Xc @ vt[0]


# ---------------------------------------------------------------------------
# Integrated information, revised (Mediano et al. 2022), pairwise
# ---------------------------------------------------------------------------

def phi_r_pairwise(Y: np.ndarray, lag: int = 1) -> np.ndarray:
    """
    Pairwise Phi_R for every pair of columns of Y (T, m).

        Phi_WMS = I([a,b]_t; [a,b]_t') - I(a_t; a_t') - I(b_t; b_t')
        Phi_R   = Phi_WMS + min{I(a_t;a_t'), I(a_t;b_t'), I(b_t;a_t'), I(b_t;b_t')}

    Returns an (m, m) symmetric matrix with zeros on the diagonal.
    """
    Z = _standardize(Y)
    m = Z.shape[1]
    A, B = Z[:-lag], Z[lag:]
    N = len(A)
    A = (A - A.mean(0)) / (A.std(0) + 1e-12)
    B = (B - B.mean(0)) / (B.std(0) + 1e-12)
    C_aa = A.T @ A / N
    C_bb = B.T @ B / N
    C_ab = A.T @ B / N  # [i, j] = corr(a_i(t), a_j(t+lag))

    ii, jj = np.triu_indices(m, 1)
    P = len(ii)
    cov = np.empty((P, 4, 4))
    cov[:, 0, 0] = 1.0; cov[:, 1, 1] = 1.0; cov[:, 2, 2] = 1.0; cov[:, 3, 3] = 1.0
    cov[:, 0, 1] = cov[:, 1, 0] = C_aa[ii, jj]
    cov[:, 2, 3] = cov[:, 3, 2] = C_bb[ii, jj]
    cov[:, 0, 2] = cov[:, 2, 0] = C_ab[ii, ii]
    cov[:, 0, 3] = cov[:, 3, 0] = C_ab[ii, jj]
    cov[:, 1, 2] = cov[:, 2, 1] = C_ab[jj, ii]
    cov[:, 1, 3] = cov[:, 3, 1] = C_ab[jj, jj]
    cov += 1e-9 * np.eye(4)[None]

    _, ld_joint = np.linalg.slogdet(cov)
    _, ld_past = np.linalg.slogdet(cov[:, :2, :2])
    _, ld_fut = np.linalg.slogdet(cov[:, 2:, 2:])
    i_joint = 0.5 * (ld_past + ld_fut - ld_joint)

    i_aa = _mi_from_r(C_ab[ii, ii])
    i_bb = _mi_from_r(C_ab[jj, jj])
    i_ab = _mi_from_r(C_ab[ii, jj])
    i_ba = _mi_from_r(C_ab[jj, ii])
    red = np.minimum(np.minimum(i_aa, i_bb), np.minimum(i_ab, i_ba))
    phi = i_joint - i_aa - i_bb + red

    out = np.zeros((m, m))
    out[ii, jj] = phi
    out[jj, ii] = phi
    return out
