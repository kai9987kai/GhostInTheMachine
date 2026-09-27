import math

import numpy as np
import pytest

from ghost_v4 import controls, infotheory as it, stats, surrogates as sg, temporal as tp


def rng(seed=0):
    return np.random.default_rng(seed)


# ---------------------------------------------------------------- information theory

def test_gaussian_mi_matches_analytic():
    r = rng(1)
    rho = 0.6
    z = r.standard_normal((20000, 2))
    x = z[:, 0]
    y = rho * x + math.sqrt(1 - rho ** 2) * z[:, 1]
    assert it.gaussian_mi(x, y) == pytest.approx(-0.5 * math.log(1 - rho ** 2), abs=0.01)


def test_cmi_zero_for_conditionally_independent():
    r = rng(2)
    z = r.standard_normal(20000)
    x = z + r.standard_normal(20000)
    y = z + r.standard_normal(20000)
    assert it.gaussian_mi(x, y) > 0.1
    assert it.gaussian_cmi(x, y, z) < 0.002


def test_transfer_entropy_is_directional():
    r = rng(3)
    T = 8000
    x = np.zeros(T)
    y = np.zeros(T)
    for t in range(1, T):
        x[t] = 0.7 * x[t - 1] + r.standard_normal()
        y[t] = 0.5 * y[t - 1] + 0.6 * x[t - 1] + r.standard_normal()
    assert it.transfer_entropy(x, y) > 0.1
    assert it.transfer_entropy(y, x) < 0.003


def test_psi_sign_tracks_redundancy_not_coordination():
    """
    Calibration finding used throughout v4: with Gaussian estimation, independent
    autocorrelated parts give psi > 0 ('emergence' by the naive zero threshold),
    while a coordinated flock whose parts redundantly carry a shared slow mode
    gives psi < 0. Psi is therefore only interpretable in matched contrasts.
    """
    r = rng(4)
    indep = controls.independent_ar(r, T=4000, n=12, phi=0.9)
    flock = controls.shared_mode(r, T=4000, n=12)
    psi_indep = it.emergence_criteria(indep, indep.mean(axis=1))
    psi_flock = it.emergence_criteria(flock, flock.mean(axis=1))
    assert psi_indep["psi"] > 0.2
    assert psi_flock["psi"] < -0.2
    assert psi_flock["psi_r"] > 0.0
    # Independent-parts surrogates reproduce the independent system's psi ...
    null = [it.emergence_criteria(S, S.mean(axis=1))["psi"] for S in (sg.iaaft(indep, r) for _ in range(19))]
    assert stats.empirical_p(psi_indep["psi"], null, "two-sided") > 0.05
    # ... and sit ABOVE the coordinated flock: coordination lowers Gaussian psi.
    null = [it.emergence_criteria(S, S.mean(axis=1))["psi"] for S in (sg.iaaft(flock, r) for _ in range(19))]
    assert stats.empirical_p(psi_flock["psi"], null, "less") <= 0.05


def test_closure_dynamical_independence_and_ntic():
    r = rng(16)
    T = 6000
    # Environment e drives a coordinated population; the population mean V tracks e.
    e = np.zeros(T)
    for t in range(1, T):
        e[t] = 0.95 * e[t - 1] + r.standard_normal()
    X = np.zeros((T, 8))
    for t in range(1, T):
        X[t] = 0.6 * X[t - 1] + 0.3 * e[t - 1] + 0.5 * r.standard_normal(8)
    V = X.mean(axis=1)
    c = it.closure_metrics(V, X, e)
    assert c["ntic"] > 0.3               # V carries in its own past much of e's information about V'
    assert c["micro_dependence"] < 0.01  # homogeneous parts: V is dynamically independent of them
    # A macro that ignores the environment has no non-trivial closure.
    Y = controls.independent_ar(r, T=T, n=8, phi=0.6)
    c0 = it.closure_metrics(Y.mean(axis=1), Y, e)
    assert abs(c0["ntic"]) < 0.01


def test_phi_r_higher_for_coupled_pair():
    r = rng(6)
    T = 6000
    a = np.zeros(T)
    b = np.zeros(T)
    for t in range(1, T):
        a[t] = 0.3 * a[t - 1] + 0.6 * b[t - 1] + r.standard_normal()
        b[t] = 0.3 * b[t - 1] + 0.6 * a[t - 1] + r.standard_normal()
    coupled = it.phi_r_pairwise(np.column_stack([a, b]))[0, 1]
    indep = it.phi_r_pairwise(controls.independent_ar(r, T=T, n=2, phi=0.5))[0, 1]
    assert coupled > 0.1
    assert abs(indep) < 0.01


# ---------------------------------------------------------------- arrow of time

def test_reversible_processes_have_small_irreversibility():
    r = rng(7)
    X = controls.independent_ar(r, T=4000, n=6, phi=0.8)
    assert tp.ordinal_irreversibility(X) < 0.005
    assert tp.time_asymmetry_q3(X) < 0.08
    assert tp.lagged_asymmetry(X) < 0.15


def test_relaxation_oscillators_irreversible_beyond_l2():
    r = rng(8)
    X = controls.relaxation_oscillators(r, T=4000, n=6)
    real = tp.ordinal_irreversibility(X)
    null = [tp.ordinal_irreversibility(sg.mv_phase(X, r)) for _ in range(19)]
    assert stats.empirical_p(real, null) <= 0.05


def test_linear_var_irreversibility_is_linear_only():
    r = rng(9)
    X = controls.linear_nonnormal_var(r, T=4000, n=8)
    lin = tp.lagged_asymmetry(X)
    null_l1 = [tp.lagged_asymmetry(sg.iaaft(X, r)) for _ in range(19)]
    null_l2 = [tp.lagged_asymmetry(sg.mv_phase(X, r)) for _ in range(19)]
    assert stats.empirical_p(lin, null_l1) <= 0.05          # beats independent-channel null
    assert stats.empirical_p(lin, null_l2) > 0.05           # but is linear: L2 preserves it


def test_lz76_known_values():
    assert tp.lz76_complexity(np.zeros(64, dtype=int)) == 2
    alt = np.tile([0, 1], 32)
    assert tp.lz76_complexity(alt) == 3


# ---------------------------------------------------------------- surrogates

def test_shuffle_preserves_zero_lag_covariance_exactly():
    r = rng(10)
    X = controls.linear_nonnormal_var(r, T=2000, n=5)
    S = sg.shuffle(X, r)
    assert np.allclose(np.cov(X, rowvar=False), np.cov(S, rowvar=False))


def test_mvphase_preserves_cross_spectrum():
    r = rng(11)
    X = controls.linear_nonnormal_var(r, T=2048, n=4)
    S = sg.mv_phase(X, r)
    FX, FS = np.fft.rfft(X, axis=0), np.fft.rfft(S, axis=0)
    cross_x = FX[:, :, None] * np.conj(FX[:, None, :])
    cross_s = FS[:, :, None] * np.conj(FS[:, None, :])
    assert np.allclose(cross_x, cross_s, atol=1e-6 * np.abs(cross_x).max())


def test_iaaft_preserves_values_and_approximately_spectrum():
    r = rng(12)
    X = controls.relaxation_oscillators(r, T=2048, n=3)
    S = sg.iaaft(X, r)
    assert np.allclose(np.sort(X, axis=0), np.sort(S, axis=0))
    ax = np.abs(np.fft.rfft(X - X.mean(0), axis=0))
    as_ = np.abs(np.fft.rfft(S - S.mean(0), axis=0))
    assert np.corrcoef(ax.ravel(), as_.ravel())[0, 1] > 0.95
    # coordination across channels is destroyed
    Y = controls.shared_mode(r, T=2048, n=4)
    C = np.corrcoef(sg.iaaft(Y, r), rowvar=False)
    assert np.max(np.abs(C[np.triu_indices(4, 1)])) < 0.15


def test_var_surrogate_reproduces_lag1_structure():
    r = rng(13)
    X = controls.linear_nonnormal_var(r, T=4000, n=4)
    S = sg.var_surrogate(X, r, order=1)
    lag = lambda A: (A[:-1] - A.mean(0)).T @ (A[1:] - A.mean(0)) / len(A)
    assert np.allclose(lag(X), lag(S), atol=0.35)


# ---------------------------------------------------------------- stats

def test_empirical_p_bounds():
    assert stats.empirical_p(10.0, np.zeros(99)) == pytest.approx(0.01)
    assert stats.empirical_p(-10.0, np.zeros(99)) == pytest.approx(1.0)


def test_sign_flip_calibrated_under_null():
    r = rng(14)
    ps = [stats.sign_flip_test(r.standard_normal(12)) for _ in range(400)]
    assert 0.02 < np.mean(np.array(ps) <= 0.05) < 0.10


def test_sign_flip_detects_shift():
    r = rng(15)
    assert stats.sign_flip_test(r.standard_normal(24) + 1.0, rng=r) < 0.001


def test_holm_and_bh():
    assert stats.holm([0.01, 0.04, 0.03]) == pytest.approx([0.03, 0.06, 0.06])
    assert stats.benjamini_hochberg([0.01, 0.04, 0.03]) == pytest.approx([0.03, 0.04, 0.04])


def test_stouffer_combines():
    assert stats.stouffer([0.5, 0.5]) == pytest.approx(0.5)
    assert stats.stouffer([0.01] * 5) < 0.001
