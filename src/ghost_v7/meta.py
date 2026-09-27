"""
Cumulative meta-analysis of the master - twin contrast (prespecified in the v7
preregistration as an exploratory analysis; the sample list was fixed before any v7 data).

Samples: every independent set of networks run with the default architecture and
comparator, the analysis window 2001-6000 and the master vs cross-yoked-twin contrast:

    v4 confirmatory (48) · v5 A replication (48) · v5 F standard wiring (24) ·
    v6 G live (48) · v6 J gain 1 (24) · v7 K live (48) · v7 L (72) · v7 M gain 1 (48)

Pooling: DerSimonian-Laird random effects, with the Hartung-Knapp-Sidik-Jonkman
(HKSJ) confidence interval (t with k-1 df, variance rescaled by the weighted
residual spread), which keeps nominal coverage with few samples where DL does not;
leave-one-out estimates; and a 95% prediction interval for a new sample.

Metrics: Gaussian self persistence (nats), its bounded form rho (the lag-1
autocorrelation of the same slow mode; for samples before v7, where only the nats
were stored, rho = sqrt(1 - exp(-2 I)), an exact identity for the Gaussian
estimator), and Psi.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Dict

import numpy as np

from ghost_v6.meta import _diffs_coded, _diffs_v4style, _t975, random_effects

from .studies import _rtest


def _rho_from_nats(I: np.ndarray) -> np.ndarray:
    return np.sqrt(1.0 - np.exp(-2.0 * np.asarray(I, dtype=float)))


def _pairs_v4style(run_dir: Path, metric: str):
    from ghost_v4.campaign import _load_runs
    data, seeds = _load_runs(run_dir)
    return (np.array([data[(s, "full", "master")][metric] for s in seeds]),
            np.array([data[(s, "full", "twin")][metric] for s in seeds]))


def _pairs_coded(run_dir: Path, cond: str, metric: str):
    from ghost_v5.studies import _load
    data, seeds = _load(run_dir)
    return (np.array([data[(s, cond, "master")][metric] for s in seeds]),
            np.array([data[(s, cond, "twin")][metric] for s in seeds]))


SAMPLES = [
    ("v4 confirmatory", "v4", ("results", "v4", "campaign"), None),
    ("v5 A replication", "v4", ("results", "v5", "A"), None),
    ("v5 F standard wiring", "coded", ("results", "v5", "F"), "standard"),
    ("v6 G live", "coded", ("results", "v6", "G"), "live"),
    ("v6 J gain 1", "coded", ("results", "v6", "J"), "gain1"),
    ("v7 K live", "coded", ("results", "v7", "K"), "live"),
    ("v7 L", "coded", ("results", "v7", "L"), "live"),
    ("v7 M gain 1", "coded", ("results", "v7", "M"), "gain1"),
]


def samples(root: Path, metric: str) -> Dict[str, np.ndarray]:
    out = {}
    for name, kind, parts, cond in SAMPLES:
        d = root.joinpath(*parts)
        if metric == "self_rho":
            if kind == "v4":
                m, t = _pairs_v4style(d, "self_persistence")
            else:
                m, t = _pairs_coded(d, cond, "self_persistence")
            out[name] = _rho_from_nats(m) - _rho_from_nats(t)
        else:
            out[name] = _diffs_v4style(d, metric) if kind == "v4" else _diffs_coded(d, cond, metric)
    return out


def hksj(groups: Dict[str, np.ndarray]) -> Dict:
    re = random_effects(groups)
    y = np.array([s["mean_diff"] for s in re["samples"]])
    v = np.array([s["se"] ** 2 for s in re["samples"]])
    w = 1.0 / (v + re["tau2"])
    mu = re["pooled_mean_diff"]
    k = len(y)
    q = float(np.sum(w * (y - mu) ** 2) / (k - 1))
    se = math.sqrt(q / float(np.sum(w)))
    t = _t975(k - 1)
    return {"ci95": [mu - t * se, mu + t * se], "se": se, "t_crit": t}


def leave_one_out(groups: Dict[str, np.ndarray]) -> Dict[str, Dict]:
    out = {}
    for name in groups:
        rest = {k: v for k, v in groups.items() if k != name}
        r = random_effects(rest)
        out[name] = {"pooled_mean_diff": r["pooled_mean_diff"], "ci95": r["ci95"], "p_two_sided": r["p_two_sided"]}
    return out


def _analyse(groups: Dict[str, np.ndarray], rng) -> Dict:
    r = random_effects(groups)
    r["hksj"] = hksj(groups)
    r["leave_one_out"] = leave_one_out(groups)
    r["per_sample_signed_rank"] = {n: {k: v for k, v in _rtest(d, "greater", rng).items()
                                       if k in ("hodges_lehmann", "positive", "n", "p")} for n, d in groups.items()}
    allnets = np.concatenate(list(groups.values()))
    r["all_networks_signed_rank"] = _rtest(allnets, "greater", rng)
    return r


def run(root: Path) -> Dict:
    rng = np.random.default_rng(74)
    out = {"status": "PRESPECIFIED EXPLORATORY (sample list and methods fixed in the v7 preregistration before any v7 data)"}
    for metric in ("self_persistence", "self_rho", "self_psi"):
        out[metric] = _analyse(samples(root, metric), rng)
    # the exact identity rho = sqrt(1 - exp(-2 I)) used for pre-v7 samples, checked on v7 data
    m, t = _pairs_coded(root / "results" / "v7" / "L", "live", "self_persistence")
    mr, tr = _pairs_coded(root / "results" / "v7" / "L", "live", "self_rho")
    out["rho_identity_max_abs_error"] = float(max(np.max(np.abs(_rho_from_nats(m) - mr)),
                                                  np.max(np.abs(_rho_from_nats(t) - tr))))
    return out
