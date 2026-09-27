"""
Living meta-analysis of the core master - twin contrasts (EXPLORATORY, post hoc).

Single-sample verdicts are noisy: v4's causal-emergence (Psi) effect was significant
in the v4 sample, not in the v5 replication, and significant again (as a secondary
test) in the v6 Study G sample. The honest summary is the pooled estimate across
every independent sample that ran the default master vs cross-yoked-twin contrast,
with its heterogeneity.

Included samples (default architecture and comparator, analysis window 2001-6000,
networks never reused):
    v4 confirmatory            48 networks  (2000-2047)
    v5 A replication           48 networks  (5000-5047)
    v5 F standard wiring       24 networks  (9000-9023)
    v6 G live                  48 networks  (10000-10047)
    v6 J gain 1                24 networks  (12000-12023)
Excluded: v5 C (re-simulates the v4 networks), v5 D (other architectures),
v5 E (different window), v5 B and v6 I (no twin).

Random-effects (DerSimonian-Laird) pooling of mean differences in nats, with tau^2,
I^2 and a 95% prediction interval for a new sample.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, List

import numpy as np

from ghost_v4.campaign import _load_runs
from ghost_v5.studies import _load


def _diffs_v4style(run_dir: Path, metric: str) -> np.ndarray:
    data, seeds = _load_runs(run_dir)
    return np.array([data[(s, "full", "master")][metric] - data[(s, "full", "twin")][metric] for s in seeds])


def _diffs_coded(run_dir: Path, cond: str, metric: str) -> np.ndarray:
    data, seeds = _load(run_dir)
    key = lambda s, role: (s, cond, role)
    return np.array([data[key(s, "master")][metric] - data[key(s, "twin")][metric] for s in seeds])


def samples(root: Path, metric: str) -> Dict[str, np.ndarray]:
    return {
        "v4 confirmatory": _diffs_v4style(root / "results" / "v4" / "campaign", metric),
        "v5 A replication": _diffs_v4style(root / "results" / "v5" / "A", metric),
        "v5 F standard wiring": _diffs_coded(root / "results" / "v5" / "F", "standard", metric),
        "v6 G live": _diffs_coded(root / "results" / "v6" / "G", "live", metric),
        "v6 J gain 1": _diffs_coded(root / "results" / "v6" / "J", "gain1", metric),
    }


def _t975(df: int) -> float:
    """97.5% quantile of Student's t (Cornish-Fisher expansion; ample for df >= 2)."""
    z = 1.959963984540054
    g1 = (z ** 3 + z) / 4
    g2 = (5 * z ** 5 + 16 * z ** 3 + 3 * z) / 96
    g3 = (3 * z ** 7 + 19 * z ** 5 + 17 * z ** 3 - 15 * z) / 384
    return z + g1 / df + g2 / df ** 2 + g3 / df ** 3


def random_effects(groups: Dict[str, np.ndarray]) -> Dict:
    names = list(groups)
    y = np.array([float(np.mean(groups[n])) for n in names])
    v = np.array([float(np.var(groups[n], ddof=1)) / len(groups[n]) for n in names])
    w = 1.0 / v
    fixed = float(np.sum(w * y) / np.sum(w))
    q = float(np.sum(w * (y - fixed) ** 2))
    k = len(y)
    c = float(np.sum(w) - np.sum(w ** 2) / np.sum(w))
    tau2 = max(0.0, (q - (k - 1)) / c) if c > 0 else 0.0
    ws = 1.0 / (v + tau2)
    mu = float(np.sum(ws * y) / np.sum(ws))
    se = math.sqrt(1.0 / float(np.sum(ws)))
    z = mu / se
    p_two = math.erfc(abs(z) / math.sqrt(2))
    i2 = max(0.0, (q - (k - 1)) / q) if q > 0 else 0.0
    t = _t975(k - 2) if k > 2 else float("nan")
    pi = [mu - t * math.sqrt(tau2 + se ** 2), mu + t * math.sqrt(tau2 + se ** 2)]
    per = [{"sample": n, "n": int(len(groups[n])), "mean_diff": float(y[i]), "se": math.sqrt(v[i]),
            "d_z": float(np.mean(groups[n]) / np.std(groups[n], ddof=1)),
            "ci95": [float(y[i] - 1.96 * math.sqrt(v[i])), float(y[i] + 1.96 * math.sqrt(v[i]))],
            "weight": float(ws[i] / np.sum(ws))} for i, n in enumerate(names)]
    pooled_d = float(np.mean(np.concatenate([g for g in groups.values()]))
                     / np.std(np.concatenate([g for g in groups.values()]), ddof=1))
    return {"samples": per, "k": k, "n_networks": int(sum(len(g) for g in groups.values())),
            "pooled_mean_diff": mu, "se": se, "ci95": [mu - 1.96 * se, mu + 1.96 * se], "z": z,
            "p_two_sided": p_two, "tau2": tau2, "Q": q, "Q_df": k - 1, "I2": i2,
            "prediction_interval95": pi, "pooled_d_z_all_networks": pooled_d}


def run(root: Path) -> Dict:
    return {"status": "POST-HOC, EXPLORATORY: not preregistered; the preregistered per-sample verdicts stand as reported",
            "self_persistence": random_effects(samples(root, "self_persistence")),
            "self_psi": random_effects(samples(root, "self_psi"))}
