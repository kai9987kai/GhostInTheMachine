"""
Post-hoc (NOT preregistered) analyses, kept out of the hashed confirmatory code.

Everything here was specified after the locked confirmatory pipeline had run,
in response to what it showed. Results from this module are labelled
POST-HOC wherever they are reported.

1. `sesoi_calibration`: the preregistered calibration found that linear lag
   statistics tested against multivariate phase-randomized (L2) surrogates are
   "detected" in ~22% of ground-truth systems where the rung preserves the
   property (expected: 5%). The diagnosed cause is the circular (FFT) end
   effect. This re-runs those ceiling rows, plus their power/FPR companions,
   scoring a detection only when p <= alpha AND the relative deviation from the
   null mean is >= 1% (the SESOI already used by the preregistered fingerprint).
2. `end_effect_demo`: shows the size of the end effect directly: real vs L2
   difference of a lag-1 statistic, and its dependence on series length T.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict

import numpy as np

from . import controls
from . import stats as st
from . import surrogates as sg
from .campaign import CALIBRATION_METRICS, _map, _pool, write_json

SESOI = 0.01

POSTHOC_ROWS = [
    ("linear_nonnormal_var", "lagged_asymmetry", "L2_mvphase", None),
    ("shared_mode", "persistence_maf", "L2_mvphase", None),
    ("linear_nonnormal_var", "lagged_asymmetry", "L1_iaaft", True),
    ("shared_mode", "persistence_maf", "L1_iaaft", True),
    ("independent_ar", "lagged_asymmetry", "L1_iaaft", False),
    ("independent_ar", "persistence_maf", "L1_iaaft", False),
]


def _job(args):
    row, rep, n_surr, T = args
    system, metric, rung, _ = POSTHOC_ROWS[row]
    rng = np.random.default_rng([row, rep, 707])
    X = controls.CONTROLS[system](rng, T=T, n=12)
    fn, alt = CALIBRATION_METRICS[metric]
    real = fn(X)
    gen = sg.NullLadder(X, rng)
    null = np.array([fn(gen.draw(rung)) for _ in range(n_surr)])
    p = st.empirical_p(real, null, alt)
    rel = (real - float(null.mean())) / max(abs(float(null.mean())), 1e-12)
    return row, p, rel


def sesoi_calibration(out_dir: Path, replicates: int = 100, n_surr: int = 19, T: int = 4000,
                      workers: int = 4, alpha: float = 0.05) -> Dict:
    jobs = [(i, r, n_surr, T) for i in range(len(POSTHOC_ROWS)) for r in range(replicates)]
    pool = _pool(workers)
    try:
        res = _map(pool, _job, jobs)
    finally:
        if pool is not None:
            pool.close()
            pool.join()
    rows = []
    for i, (system, metric, rung, truth) in enumerate(POSTHOC_ROWS):
        ps = np.array([p for (row, p, _) in res if row == i])
        rel = np.array([r for (row, _, r) in res if row == i])
        raw = int(np.sum(ps <= alpha))
        with_sesoi = int(np.sum((ps <= alpha) & (np.abs(rel) >= SESOI)))
        rows.append({
            "system": system, "metric": metric, "rung": rung, "ground_truth": truth,
            "raw_detection_rate": raw / len(ps), "raw_ci95": st.wilson_interval(raw, len(ps)),
            "sesoi_detection_rate": with_sesoi / len(ps), "sesoi_ci95": st.wilson_interval(with_sesoi, len(ps)),
            "median_abs_relative_deviation": float(np.median(np.abs(rel))),
        })
    result = {"label": "POST-HOC (not preregistered)", "sesoi_relative": SESOI, "alpha": alpha, "rows": rows}
    write_json(out_dir / "posthoc_sesoi_calibration.json", result)
    return result


def end_effect_demo(lengths=(500, 1000, 2000, 4000, 8000), reps: int = 40, seed: int = 0) -> Dict:
    """Median |real - L2 surrogate| relative difference of lag-1 persistence, by series length."""
    from .campaign import _persistence_metric
    rng = np.random.default_rng(seed)
    out = {}
    for T in lengths:
        rel, z = [], []
        for _ in range(reps):
            X = controls.shared_mode(rng, T=T, n=12)
            real = _persistence_metric(X)
            null = np.array([_persistence_metric(sg.mv_phase(X, rng)) for _ in range(19)])
            rel.append(abs(real - null.mean()) / abs(null.mean()))
            z.append(abs(st.null_z(real, null)))
        out[str(T)] = {"median_abs_relative_difference": float(np.median(rel)), "median_abs_z": float(np.median(z))}
    return out


def psi_anatomy(campaign_dir: Path) -> Dict:
    """
    What the confirmatory H4 effect is made of (POST-HOC): Psi = macro self-information
    minus the summed part information; absolute levels; fraction of seeds with Psi > 0;
    the authorship effect on Psi within each lesion; robustness by world; and whether
    the per-seed authorship effect on self persistence tracks the per-seed reduction
    in prediction error (a mediation-style association, not a causal estimate).
    """
    import json
    from .campaign import _load_runs, _test
    data, _ = _load_runs(campaign_dir)
    seeds = sorted({k[0] for k in data})
    key = json.loads((campaign_dir / "unblinding_key.json").read_text())
    world = {v["seed"]: v["world"] for v in key.values()}
    rng = np.random.default_rng(11)

    def arr(c, r, m):
        return np.array([data[(s, c, r)][m] for s in seeds], dtype=float)

    out: Dict = {"label": "POST-HOC (not preregistered)", "n_seeds": len(seeds)}
    comp = {}
    for m in ("self_psi", "self_macro_self_information", "self_parts_information", "self_psi_r",
              "self_delta", "self_gamma"):
        a, b, p = arr("full", "master", m), arr("full", "twin", m), arr("full", "placebo", m)
        comp[m] = {"master_mean": float(a.mean()), "twin_mean": float(b.mean()), "placebo_mean": float(p.mean()),
                   "master_minus_twin": _test(a - b, "two-sided", rng)}
    out["psi_components"] = comp
    a, b = arr("full", "master", "self_psi"), arr("full", "twin", "self_psi")
    out["fraction_seeds_psi_positive"] = {"master": float(np.mean(a > 0)), "twin": float(np.mean(b > 0))}
    out["seeds_master_psi_above_twin"] = int(np.sum(a > b))
    out["psi_authorship_within_lesion"] = {
        c: _test(arr(c, "master", "self_psi") - arr(c, "twin", "self_psi"), "two-sided", rng)
        for c in ("no_comparator", "no_efference", "no_selffeedback", "frozen")}
    by_world = {}
    for w in sorted(set(world.values())):
        idx = [i for i, s in enumerate(seeds) if world[s] == w]
        d1 = (arr("full", "master", "self_persistence") - arr("full", "twin", "self_persistence"))[idx]
        d4 = (a - b)[idx]
        by_world[str(w)] = {"n": len(idx), "H1_d_z": st.paired_effect(d1)["d_z"], "H4_d_z": st.paired_effect(d4)["d_z"],
                            "H1_mean_diff": float(d1.mean()), "H4_mean_diff": float(d4.mean())}
    out["by_world"] = by_world
    dp = arr("full", "master", "self_persistence") - arr("full", "twin", "self_persistence")
    de = arr("full", "master", "prediction_error") - arr("full", "twin", "prediction_error")
    r = float(np.corrcoef(dp, de)[0, 1])
    perm = np.array([np.corrcoef(dp, rng.permutation(de))[0, 1] for _ in range(20000)])
    out["mediation_association"] = {
        "corr(delta_persistence, delta_prediction_error)": r,
        "p_two_sided_permutation": float((1 + np.sum(np.abs(perm) >= abs(r))) / (1 + len(perm))),
        "note": "Across seeds: do networks whose twin suffers more extra prediction error show a larger persistence cost?",
    }
    return out


def run_all(results_dir: Path, workers: int = 4) -> Dict:
    out_dir = results_dir / "posthoc"
    out_dir.mkdir(parents=True, exist_ok=True)
    res = {"label": "POST-HOC (not preregistered)"}
    res["psi_anatomy"] = psi_anatomy(results_dir / "campaign")
    res["sesoi_calibration"] = sesoi_calibration(out_dir, workers=workers)
    res["end_effect_demo"] = end_effect_demo()
    write_json(out_dir / "posthoc_results.json", res)
    return res
