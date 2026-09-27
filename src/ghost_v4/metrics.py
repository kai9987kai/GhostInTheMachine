"""
The v4 observational metric panel.

Every metric is a pure function of a recorded trajectory window, so real data,
surrogate data, yoked twins and lesioned agents all pass through exactly the
same code. Each metric is tagged with the kind of structure it can read, which
determines, before any data are seen, which null rungs it could possibly beat
(its "specificity ceiling"):

    zero-lag             reads only the distribution of single time points.
                         Exactly invariant to a temporal shuffle (L0).
    univariate-temporal  reads each channel's own temporal order.
                         Largely preserved by channel-wise IAAFT (L1).
    lagged-linear        reads lagged (cross-)covariance.
                         Preserved by multivariate phase randomization (L2) and VAR (L3).
    nonlinear-temporal   reads higher-order temporal structure.
                         Can in principle beat every rung.
"""

from __future__ import annotations

from typing import Callable, Dict, Tuple

import numpy as np

from . import infotheory as it
from . import temporal as tp
from .engine import POPULATIONS, Record, perturbational_response


def module_means(X: np.ndarray, slices: Dict[str, Tuple[int, int]]) -> np.ndarray:
    return np.stack([X[:, a:b].mean(axis=1) for a, b in (slices[p] for p in POPULATIONS)], axis=1)


def _pcs(A: np.ndarray, k: int) -> np.ndarray:
    A = A - A.mean(axis=0)
    _, _, vt = np.linalg.svd(A, full_matrices=False)
    return A @ vt[:k].T


def participation_ratio(X: np.ndarray) -> float:
    Y = X - X.mean(axis=0)
    s = np.linalg.svd(Y, compute_uv=False) ** 2
    return float(s.sum() ** 2 / (np.sum(s * s) + 1e-12))


def mean_abs_fc(M: np.ndarray) -> float:
    C = np.corrcoef(M, rowvar=False)
    return float(np.mean(np.abs(C[np.triu_indices_from(C, 1)])))


def multiscale_pe(x: np.ndarray, scales=(1, 2, 4, 8), order: int = 3) -> float:
    """Multiscale permutation entropy (vectorized; same construction as v3)."""
    vals = []
    for s in scales:
        n = (len(x) // s) * s
        c = x[-n:].reshape(-1, s).mean(axis=1)
        if len(c) < 12 * order:
            continue
        from numpy.lib.stride_tricks import sliding_window_view
        pi = np.argsort(sliding_window_view(c, order), axis=-1, kind="stable")
        codes = pi @ (order ** np.arange(order))
        p = np.bincount(codes)
        p = p[p > 0] / p.sum()
        vals.append(float(-(p * np.log(p)).sum() / np.log(float(np.prod(np.arange(1, order + 1))))))
    return float(np.mean(vals)) if vals else 0.0


def self_persistence(X: np.ndarray, slices, population: str = "self") -> float:
    a, b = slices[population]
    V = it.slow_macro(X[:, a:b])
    return it.gaussian_mi(V[:-1], V[1:])


# Metrics evaluated on every null-ladder surrogate (functions of the node matrix X).
FINGERPRINT: Dict[str, Tuple[str, Callable]] = {
    "pr_dimension": ("zero-lag", lambda X, sl: participation_ratio(X)),
    "fc_mean_abs_corr": ("zero-lag", lambda X, sl: mean_abs_fc(module_means(X, sl))),
    "mse_global": ("univariate-temporal", lambda X, sl: multiscale_pe(X.mean(axis=1))),
    "self_persistence": ("lagged-linear", lambda X, sl: self_persistence(X, sl)),
    "self_psi": ("lagged-linear", lambda X, sl: it.emergence_criteria(
        X[:, sl["self"][0]:sl["self"][1]], it.slow_macro(X[:, sl["self"][0]:sl["self"][1]]))["psi"]),
    "phi_r_mean": ("lagged-linear", lambda X, sl: float(
        it.phi_r_pairwise(module_means(X, sl))[np.triu_indices(len(POPULATIONS), 1)].mean())),
    "lagged_asymmetry": ("lagged-linear", lambda X, sl: tp.lagged_asymmetry(module_means(X, sl))),
    "irr_nodes": ("nonlinear-temporal", lambda X, sl: tp.ordinal_irreversibility(X)),
    "irr_modules_q3": ("nonlinear-temporal", lambda X, sl: tp.time_asymmetry_q3(module_means(X, sl))),
}

# Which rungs each kind of metric can, in principle, differ from (True) or must match (False).
PREDICTED_CEILING = {
    "zero-lag": {"L0_shuffle": False, "L1_iaaft": True, "L2_mvphase": False, "L3_var": False},
    "univariate-temporal": {"L0_shuffle": True, "L1_iaaft": False, "L2_mvphase": False, "L3_var": False},
    "lagged-linear": {"L0_shuffle": True, "L1_iaaft": True, "L2_mvphase": False, "L3_var": False},
    "nonlinear-temporal": {"L0_shuffle": True, "L1_iaaft": True, "L2_mvphase": True, "L3_var": True},
}


def fingerprint_panel(X: np.ndarray, slices) -> Dict[str, float]:
    return {name: float(fn(X, slices)) for name, (_, fn) in FINGERPRINT.items()}


def record_panel(rec: Record, burn: int, probe_seed: int = 0) -> Dict[str, float]:
    """All observational + behavioural + interventional metrics for one run."""
    X = rec.X[burn:].astype(float)
    sl = rec.slices
    out = fingerprint_panel(X, sl)

    a, b = sl["self"]
    S = X[:, a:b]
    V = it.slow_macro(S)
    em = it.emergence_criteria(S, V)
    out.update({f"self_{k}": v for k, v in em.items() if k != "psi"})
    E = _pcs(rec.obs[burn + 1:].astype(float), 4)
    cl = it.closure_metrics(V, S, E)
    out.update({f"self_{k}": v for k, v in cl.items() if k != "self_information"})

    for p in POPULATIONS:
        pa, pb = sl[p]
        P = X[:, pa:pb]
        Vp = it.slow_macro(P)
        out[f"atlas_persistence_{p}"] = it.gaussian_mi(Vp[:-1], Vp[1:])
        out[f"atlas_psi_{p}"] = it.emergence_criteria(P, Vp)["psi"]

    Z = _pcs(X, 5)
    out["te_net_to_obs"] = it.transfer_entropy(Z, E, k=10, l=1)
    out["te_obs_to_net"] = it.transfer_entropy(E, Z, k=10, l=1)

    out["cf_agency"] = float(rec.cf_agency[burn:].mean())
    out["ignition"] = float(rec.ignition[burn:].mean())
    out["prediction_error"] = float(rec.pred_error[burn:].mean())
    out["self_model_error"] = float(rec.self_error[burn:].mean())
    out["activity"] = float(np.abs(X).mean())
    out["intention_outcome_match"] = float(np.mean(rec.intended[burn:] == rec.executed[burn:]))

    rng = np.random.default_rng([rec.config.net_seed, 303, probe_seed])
    pci = []
    for p in POPULATIONS:
        pa, pb = sl[p]
        r = perturbational_response(rec.W, rec.gain, rec.final_state, np.arange(pa, pb), rng, leak=rec.config.leak)
        out[f"pci_lz_{p}"] = r["lz"]
        pci.append(r["lz"])
    out["pci_lz_mean"] = float(np.mean(pci))
    return out
