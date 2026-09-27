"""
Campaign orchestration: instrument calibration, the v4 authorship campaign with
its null ladder, the v3 forensic re-adjudication, and the preregistered
analysis.

Blinding: every simulated run is stored under a random opaque code in
`runs_coded.json`; the mapping from code to (seed, condition, role) lives only
in `unblinding_key.json`. Metrics are computed before any label is joined, and
hypothesis tests run only in `analyze`, which requires both files.
"""

from __future__ import annotations

import json
import math
import os
import secrets
import time
from dataclasses import asdict
from multiprocessing import get_context
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from . import DISCLAIMER, __version__
from . import classifier as clf
from . import controls
from . import infotheory as it
from . import metrics as mt
from . import stats as st
from . import surrogates as sg
from . import temporal as tp
from .engine import POPULATIONS, AgentConfig, Stream, run_agent

CONDITIONS: Dict[str, Dict] = {
    "full": {},
    "no_comparator": {"comparator": False},
    "no_efference": {"efference": False},
    "no_selffeedback": {"self_feedback": False},
    "frozen": {"learning": False},
}


def _jsonable(obj):
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, np.ndarray):
        return _jsonable(obj.tolist())
    if isinstance(obj, float) and not math.isfinite(obj):
        return None
    return obj


def write_json(path: Path, obj) -> None:
    path.write_text(json.dumps(_jsonable(obj), indent=2) + "\n", encoding="utf-8")


def _pool(workers: int):
    return get_context("spawn").Pool(workers) if workers > 1 else None


def _map(pool, fn, items):
    return pool.map(fn, items, chunksize=1) if pool is not None else [fn(i) for i in items]


# ---------------------------------------------------------------------------
# Design helpers
# ---------------------------------------------------------------------------

def blocks(spec: Dict) -> List[List[int]]:
    seeds = list(spec["seeds"])
    k = int(spec.get("world_blocks", 1))
    size = len(seeds) // k
    return [seeds[i * size:(i + 1) * size] for i in range(k)]


def world_of(spec: Dict) -> Dict[int, int]:
    out = {}
    for b, members in enumerate(blocks(spec)):
        for s in members:
            out[s] = int(spec["world_seed_base"]) + b
    return out


def donor_of(spec: Dict) -> Dict[int, int]:
    """Cross-yoking: each network is yoked to the next network in its world block."""
    out = {}
    for members in blocks(spec):
        for i, s in enumerate(members):
            out[s] = members[(i + 1) % len(members)]
    return out


def _cfg(spec: Dict, seed: int, cond: str, world: int, replicate: int = 0) -> AgentConfig:
    return AgentConfig(net_seed=seed, world_seed=world, steps=int(spec["steps"]),
                       replicate=replicate, **CONDITIONS[cond])


# ---------------------------------------------------------------------------
# Null ladder on one trajectory
# ---------------------------------------------------------------------------

def ladder(X: np.ndarray, slices, n_surrogates: int, seed: int, rungs=sg.RUNGS) -> Dict:
    rng = np.random.default_rng([seed, 404])
    real = mt.fingerprint_panel(X, slices)
    names = list(real)
    gen = sg.NullLadder(X, rng)
    null = {}
    for rung in rungs:
        rows = []
        for _ in range(n_surrogates):
            S = gen.draw(rung)
            panel = mt.fingerprint_panel(S, slices)
            rows.append([panel[n] for n in names])
        null[rung] = np.asarray(rows)
    return {"metrics": names, "real": [real[n] for n in names], "null": null}


# ---------------------------------------------------------------------------
# v4 authorship campaign
# ---------------------------------------------------------------------------

def _master_job(args) -> Dict:
    spec, seed, cond, world, replicate, do_ladder = args
    rec = run_agent(_cfg(spec, seed, cond, world, replicate))
    burn = int(spec["burn"])
    out = {"seed": seed, "cond": cond, "role": "master" if replicate == 0 else "placebo",
           "world": world, "panel": mt.record_panel(rec, burn), "stream": rec.stream()}
    if do_ladder:
        out["ladder"] = ladder(rec.X[burn:].astype(float), rec.slices, int(spec["n_surrogates"]), seed)
    return out


def _twin_job(args) -> Dict:
    spec, seed, cond, world, stream = args
    rec = run_agent(_cfg(spec, seed, cond, world), yoke=stream)
    return {"seed": seed, "cond": cond, "role": "twin", "world": world, "donor": stream.source_net_seed,
            "panel": mt.record_panel(rec, int(spec["burn"]))}


def run_v4(spec: Dict, out_dir: Path, workers: int = 4, log=print) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    worlds, donors = world_of(spec), donor_of(spec)
    conds = list(spec["conditions"])
    jobs = []
    for s in spec["seeds"]:
        for c in conds:
            jobs.append((spec, s, c, worlds[s], 0, c == "full"))
        if spec.get("placebo", True):
            jobs.append((spec, s, "full", worlds[s], 1, False))
    t0 = time.time()
    pool = _pool(workers)
    try:
        log(f"[v4] phase A: {len(jobs)} closed-loop runs (+ null ladder on every full master)")
        masters = _map(pool, _master_job, jobs)
        streams = {(m["seed"], m["cond"]): m.pop("stream") for m in masters if m["role"] == "master"}
        for m in masters:
            m.pop("stream", None)
        twin_jobs = [(spec, s, c, worlds[s], streams[(donors[s], c)]) for s in spec["seeds"] for c in conds]
        log(f"[v4] phase B: {len(twin_jobs)} cross-yoked twin runs  ({time.time() - t0:.0f}s elapsed)")
        twins = _map(pool, _twin_job, twin_jobs)
    finally:
        if pool is not None:
            pool.close()
            pool.join()

    coded, key = {}, {}
    for r in masters + twins:
        code = secrets.token_hex(6)
        key[code] = {k: r.get(k) for k in ("seed", "cond", "role", "world", "donor")}
        coded[code] = {"panel": r["panel"], "ladder": r.get("ladder")}
    write_json(out_dir / "runs_coded.json", coded)
    write_json(out_dir / "unblinding_key.json", key)
    log(f"[v4] {len(coded)} runs written (coded) in {time.time() - t0:.0f}s")


# ---------------------------------------------------------------------------
# Instrument calibration on ground-truth systems
# ---------------------------------------------------------------------------

def _persistence_metric(X):
    V = it.slow_macro(X)
    return it.gaussian_mi(V[:-1], V[1:])


CALIBRATION_METRICS = {
    "irr_ordinal": (lambda X: tp.ordinal_irreversibility(X), "greater"),
    "lagged_asymmetry": (lambda X: tp.lagged_asymmetry(X), "greater"),
    "persistence_maf": (_persistence_metric, "greater"),
    "phi_r_mean": (lambda X: float(it.phi_r_pairwise(X)[np.triu_indices(X.shape[1], 1)].mean()), "greater"),
    "psi_mean_macro": (lambda X: it.emergence_criteria(X, X.mean(axis=1))["psi"], "two-sided"),
}

# (system, metric, rung, truth): truth is True where the property the rung tests
# for is present by construction, False where it is absent, None where the rung
# preserves the property by construction (expected detection rate = alpha).
CALIBRATION_PLAN = [
    ("independent_ar", "irr_ordinal", "L2_mvphase", False),
    ("linear_nonnormal_var", "irr_ordinal", "L2_mvphase", False),
    ("relaxation_oscillators", "irr_ordinal", "L2_mvphase", True),
    ("independent_ar", "lagged_asymmetry", "L1_iaaft", False),
    ("linear_nonnormal_var", "lagged_asymmetry", "L1_iaaft", True),
    ("linear_nonnormal_var", "lagged_asymmetry", "L2_mvphase", None),
    ("independent_ar", "persistence_maf", "L1_iaaft", False),
    ("shared_mode", "persistence_maf", "L1_iaaft", True),
    ("shared_mode", "persistence_maf", "L2_mvphase", None),
    ("independent_ar", "phi_r_mean", "L1_iaaft", False),
    ("linear_nonnormal_var", "phi_r_mean", "L1_iaaft", True),
    ("independent_ar", "psi_mean_macro", "L1_iaaft", False),
    ("shared_mode", "psi_mean_macro", "L1_iaaft", True),
]


def _calibration_job(args) -> Tuple[int, int, float]:
    row, rep, n_surr, T = args
    system, metric, rung, _ = CALIBRATION_PLAN[row]
    rng = np.random.default_rng([row, rep, 505])
    X = controls.CONTROLS[system](rng, T=T, n=12)
    fn, alt = CALIBRATION_METRICS[metric]
    real = fn(X)
    gen = sg.NullLadder(X, rng)
    null = [fn(gen.draw(rung)) for _ in range(n_surr)]
    return row, rep, st.empirical_p(real, null, alt)


def run_calibration(spec: Dict, out_dir: Path, workers: int = 4, log=print) -> Dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    reps = int(spec["replicates"])
    n_surr = int(spec["n_surrogates"])
    T = int(spec.get("T", 4000))
    alpha = float(spec.get("alpha", 0.05))
    jobs = [(i, r, n_surr, T) for i in range(len(CALIBRATION_PLAN)) for r in range(reps)]
    log(f"[calibration] {len(jobs)} ground-truth replicates x {n_surr} surrogates")
    pool = _pool(workers)
    try:
        res = _map(pool, _calibration_job, jobs)
    finally:
        if pool is not None:
            pool.close()
            pool.join()
    rows = []
    for i, (system, metric, rung, truth) in enumerate(CALIBRATION_PLAN):
        ps = np.array([p for (row, _, p) in res if row == i])
        k = int(np.sum(ps <= alpha))
        rate = k / len(ps)
        lo, hi = st.wilson_interval(k, len(ps))
        if truth is True:
            role, ok = "power", rate >= 0.80
        elif truth is False:
            role, ok = "false_positive_rate", lo <= alpha
        else:
            role, ok = "ceiling (property preserved by rung)", lo <= alpha
        rows.append({"system": system, "metric": metric, "rung": rung, "ground_truth": truth,
                     "role": role, "detection_rate": rate, "ci95": [lo, hi], "n": len(ps), "pass": bool(ok)})
    result = {"alpha": alpha, "rows": rows, "all_pass": all(r["pass"] for r in rows)}
    write_json(out_dir / "calibration.json", result)
    return result


# ---------------------------------------------------------------------------
# v3 forensic re-adjudication
# ---------------------------------------------------------------------------

V3_CONDITIONS = {
    "master": {},
    "clamp_low": {"clamp_gain": 0.91},     # v3's initial gain, ramp disabled
    "clamp_high": {"clamp_gain": 1.18},    # v3's ceiling gain from cycle 1
    "frozen": {"freeze_learning": True},
}


def _v3_job(args) -> Dict:
    spec, seed, cond, yoke_obs, donor = args
    from . import v3_bridge as vb
    kw = dict(V3_CONDITIONS.get(cond, {}))
    rec = vb.run_v3(seed, steps=int(spec["steps"]), yoke_obs=yoke_obs, **kw)
    audit = vb.detector_audit(rec)
    rows = rec["rows"]
    cal = rec["calibration_steps"]
    post = [r for r in rows if r["step"] > cal]
    out = {
        "seed": seed, "cond": cond if yoke_obs is None else "twin", "donor": donor,
        "first_event_step": rec["first_event_step"], "events": rec["events"],
        "active_fraction": float(np.mean([r["ghost_active"] for r in rows])),
        "mean_convergence": float(np.mean([r["cross_theory_convergence"] for r in post])),
        "mean_ghost_index": float(np.mean([r["ghost_index"] for r in post])),
        "audit": audit,
        "trace_step": [r["step"] for r in rows],
        "trace_gain": [float(rec["gain"][r["step"] - 1]) for r in rows],
        "trace_ghost_index": [r["ghost_index"] for r in rows],
        "trace_baseline_z": [r["baseline_z"] for r in rows],
        "trace_active": [int(r["ghost_active"]) for r in rows],
    }
    if yoke_obs is None and cond == "master":
        out["obs"] = rec["obs"]
        out["ladder"] = _v3_ladder(rec, spec)
    return out


def _v3_ladder(rec: Dict, spec: Dict) -> Dict:
    from . import v3_bridge as vb
    X = rec["X"].astype(float)
    gains = rec["gain"].astype(float)
    n_surr = int(spec["n_surrogates"])
    rng = np.random.default_rng([rec["seed"], 606])
    cal = rec["calibration_steps"]
    var_fit = sg.fit_var(X[cal:], order=1)
    out = {}
    for tpoint in spec["timepoints"]:
        Xw = X[tpoint - vb.WINDOW:tpoint]
        gw = gains[tpoint - vb.WINDOW:tpoint]
        real = vb.v3_window_metrics(Xw, rec["slices"], rec["W"], gw, rec["base_spectral_radius"])
        names = list(real)
        per_rung = {}
        gen = sg.NullLadder(Xw, rng)
        gen._var = var_fit
        for rung in sg.RUNGS:
            vals = []
            for _ in range(n_surr):
                S = gen.draw(rung)
                m = vb.v3_window_metrics(S, rec["slices"], rec["W"], gw, rec["base_spectral_radius"])
                vals.append([m[n] for n in names])
            per_rung[rung] = np.asarray(vals)
        out[str(tpoint)] = {"metrics": names, "real": [real[n] for n in names], "null": per_rung}
    return out


def run_v3_forensics(spec: Dict, out_dir: Path, workers: int = 4, log=print) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    seeds = list(spec["seeds"])
    t0 = time.time()
    pool = _pool(workers)
    try:
        jobs = [(spec, s, c, None, None) for s in seeds for c in V3_CONDITIONS]
        log(f"[v3] phase A: {len(jobs)} v3 runs (master / clamp_low / clamp_high / frozen)")
        first = _map(pool, _v3_job, jobs)
        obs = {r["seed"]: r.pop("obs") for r in first if "obs" in r}
        twin_jobs = [(spec, s, "twin", obs[seeds[(i + 1) % len(seeds)]], seeds[(i + 1) % len(seeds)])
                     for i, s in enumerate(seeds)]
        log(f"[v3] phase B: {len(twin_jobs)} cross-yoked v3 twins ({time.time() - t0:.0f}s elapsed)")
        second = _map(pool, _v3_job, twin_jobs)
    finally:
        if pool is not None:
            pool.close()
            pool.join()
    write_json(out_dir / "v3_forensics_runs.json", first + second)
    log(f"[v3] done in {time.time() - t0:.0f}s")


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

def _load_runs(out_dir: Path):
    coded = json.loads((out_dir / "runs_coded.json").read_text())
    key = json.loads((out_dir / "unblinding_key.json").read_text())
    data, ladders = {}, {}
    for code, entry in coded.items():
        k = key[code]
        data[(k["seed"], k["cond"], k["role"])] = entry["panel"]
        if entry.get("ladder"):
            ladders[k["seed"]] = entry["ladder"]
    return data, ladders


def _paired(data, seeds, metric, a: Tuple[str, str], b: Tuple[str, str]) -> np.ndarray:
    return np.array([
        (data[(s, *a)].get(metric) if data[(s, *a)].get(metric) is not None else np.nan)
        - (data[(s, *b)].get(metric) if data[(s, *b)].get(metric) is not None else np.nan)
        for s in seeds
    ], dtype=float)


def _dz(x: np.ndarray) -> float:
    sd = float(np.std(x, ddof=1))
    return float(np.mean(x)) / sd if sd > 1e-15 else 0.0


def _test(d: np.ndarray, alternative: str, rng) -> Dict:
    e = st.paired_effect(d)
    return {
        "n": e["n"], "mean_diff": e["mean"], "sd": e["sd"], "d_z": e["d_z"], "g_z": e["g_z"],
        "ci95": st.bootstrap_ci(d, rng=rng),
        "d_z_ci95": st.bootstrap_ci(d, stat=_dz, n_boot=4000, rng=rng),
        "p": st.sign_flip_test(d, alternative=alternative, rng=rng),
        "p_two_sided": st.sign_flip_test(d, alternative="two-sided", rng=rng),
    }


def analyze_v4(out_dir: Path, prereg: Dict, alpha: float = 0.05) -> Dict:
    data, ladders = _load_runs(out_dir)
    seeds = sorted({k[0] for k in data})
    rng = np.random.default_rng(2026)
    M_, T_ = ("full", "master"), ("full", "twin")
    res: Dict = {"n_seeds": len(seeds), "seeds": seeds}

    # Gate: manipulation check.
    gate = _test(_paired(data, seeds, "te_net_to_obs", M_, T_), "greater", rng)
    gate["pass"] = gate["p"] <= alpha
    res["gate_manipulation_check"] = gate

    # Primary family.
    prim = {}
    prim["H1_authorship_self_persistence"] = _test(_paired(data, seeds, "self_persistence", M_, T_), "greater", rng)
    d_self = _paired(data, seeds, "atlas_persistence_self", M_, T_)
    d_other = np.mean([_paired(data, seeds, f"atlas_persistence_{p}", M_, T_) for p in POPULATIONS if p != "self"], axis=0)
    prim["H2_self_specificity"] = _test(d_self - d_other, "greater", rng)
    inter = (_paired(data, seeds, "self_persistence", M_, T_)
             - _paired(data, seeds, "self_persistence", ("no_comparator", "master"), ("no_comparator", "twin")))
    prim["H3_comparator_mechanism"] = _test(inter, "greater", rng)
    prim["H4_authorship_causal_emergence"] = _test(_paired(data, seeds, "self_psi", M_, T_), "greater", rng)
    prim["H5_authorship_integration"] = _test(_paired(data, seeds, "phi_r_mean", M_, T_), "greater", rng)
    z = []
    for s in seeds:
        L = ladders[s]
        j = L["metrics"].index("irr_nodes")
        z.append(st.null_z(L["real"][j], np.asarray(L["null"]["L2_mvphase"])[:, j]))
    h6 = _test(np.asarray(z), "greater", rng)
    h6["note"] = "effect is the per-seed z of irr_nodes against its own 49 L2 surrogates"
    prim["H6_nonlinear_arrow_of_time"] = h6
    prim["H7_authorship_arrow_of_time"] = _test(_paired(data, seeds, "irr_nodes", M_, T_), "greater", rng)
    names = list(prim)
    adj = st.holm([prim[n]["p"] for n in names])
    for n, a in zip(names, adj):
        prim[n]["p_holm"] = a
        prim[n]["significant"] = bool(a <= alpha)
    res["primary"] = prim

    # Placebo A/A contrasts on the same endpoints (should be null).
    pl = {}
    for metric in ("self_persistence", "self_psi", "phi_r_mean", "irr_nodes", "te_net_to_obs"):
        pl[metric] = _test(_paired(data, seeds, metric, M_, ("full", "placebo")), "two-sided", rng)
    res["placebo_AA"] = pl

    # Verdict ladder (preregistered).
    sig = {n.split("_")[0]: prim[n]["significant"] for n in names}
    level = 0
    if gate["pass"] and sig["H1"]:
        level = 1
        if sig["H2"]:
            level = 2
            if sig["H3"]:
                level = 3
                if sig["H4"]:
                    level = 4
    res["verdict"] = {"level": level, "label": prereg["verdict_levels"][str(level)],
                      "ghost_v4": level == 4}

    # Secondary / exploratory (BH-FDR within family).
    sec = {}
    for cond in ("no_efference", "no_selffeedback", "frozen"):
        d = (_paired(data, seeds, "self_persistence", M_, T_)
             - _paired(data, seeds, "self_persistence", (cond, "master"), (cond, "twin")))
        sec[f"interaction_{cond}"] = _test(d, "two-sided", rng)
    for cond in ("no_comparator", "no_efference", "no_selffeedback", "frozen"):
        sec[f"authorship_effect_within_{cond}"] = _test(
            _paired(data, seeds, "self_persistence", (cond, "master"), (cond, "twin")), "two-sided", rng)
    for metric in ("self_ntic", "self_micro_dependence", "self_env_dependence", "self_delta", "self_psi_r",
                   "irr_modules_q3", "lagged_asymmetry", "pr_dimension", "fc_mean_abs_corr", "mse_global",
                   "pci_lz_mean", "ignition", "activity", "prediction_error", "self_model_error", "te_obs_to_net"):
        sec[f"authorship_{metric}"] = _test(_paired(data, seeds, metric, M_, T_), "two-sided", rng)
    sn = list(sec)
    for n, a in zip(sn, st.benjamini_hochberg([sec[n]["p_two_sided"] for n in sn])):
        sec[n]["q_bh"] = a
    res["secondary"] = sec

    atlas = {}
    for p in POPULATIONS:
        atlas[p] = {
            "persistence": _test(_paired(data, seeds, f"atlas_persistence_{p}", M_, T_), "two-sided", rng),
            "psi": _test(_paired(data, seeds, f"atlas_psi_{p}", M_, T_), "two-sided", rng),
            "pci_lz": _test(_paired(data, seeds, f"pci_lz_{p}", M_, T_), "two-sided", rng),
        }
    qs = st.benjamini_hochberg([atlas[p]["persistence"]["p_two_sided"] for p in POPULATIONS])
    for p, q in zip(POPULATIONS, qs):
        atlas[p]["persistence"]["q_bh"] = q
    res["atlas"] = atlas

    # Specificity fingerprints.
    res["fingerprint"] = fingerprint_summary(ladders, seeds, alpha)

    # Blind discrimination.
    res["discrimination"] = discrimination(data, ladders, seeds, rng)

    res["condition_means"] = {
        f"{c}/{r}": {m: float(np.nanmean([data[(s, c, r)].get(m, np.nan) if data[(s, c, r)].get(m) is not None else np.nan
                                          for s in seeds]))
                     for m in ("self_persistence", "self_psi", "phi_r_mean", "irr_nodes", "te_net_to_obs",
                               "cf_agency", "intention_outcome_match", "prediction_error", "ignition")}
        for (c, r) in sorted({(k[1], k[2]) for k in data})
    }
    return res


SESOI_RELATIVE = 0.01  # smallest relative deviation from the null mean treated as a real difference


def fingerprint_summary(ladders: Dict, seeds: List[int], alpha: float) -> Dict:
    """
    For every metric x rung: how far real data sit from their own surrogates.

    A cell counts as 'differs' only when a seed's surrogate test is significant AND
    the real value deviates from the null mean by >= 1% (SESOI). The SESOI matters:
    FFT surrogates preserve circular, not linear, covariance, so a lag statistic
    under L2 differs by an O(1/T) end effect that is statistically detectable (the
    null has almost no spread) but substantively nil.
    """
    names = ladders[seeds[0]]["metrics"]
    out = {}
    for j, name in enumerate(names):
        kind = mt.FINGERPRINT[name][0]
        per = {}
        for rung in sg.RUNGS:
            zs, ps, rel, exact, differs = [], [], [], [], []
            for s in seeds:
                L = ladders[s]
                null = np.asarray(L["null"][rung])[:, j]
                real = L["real"][j]
                z = st.null_z(real, null)
                p = st.empirical_p(real, null, "two-sided")
                r = (real - float(np.mean(null))) / max(abs(float(np.mean(null))), 1e-12)
                zs.append(z)
                ps.append(p)
                rel.append(r)
                exact.append(bool(np.allclose(null, real, rtol=1e-9, atol=1e-12)))
                differs.append(p <= alpha and abs(r) >= SESOI_RELATIVE)
            zs = np.asarray(zs)
            per[rung] = {
                "mean_z": float(np.mean(np.clip(zs, -99, 99))),
                "median_z": float(np.median(zs)),
                "median_relative_deviation": float(np.median(rel)),
                "fraction_seeds_p<=alpha": float(np.mean(np.asarray(ps) <= alpha)),
                "fraction_seeds_differ": float(np.mean(differs)),
                "exactly_invariant": bool(all(exact)),
                "predicted_can_differ": mt.PREDICTED_CEILING[kind][rung],
                "observed_differs": bool(np.mean(differs) >= 0.5),
            }
        out[name] = {"kind": kind, "rungs": per}
    return out


def discrimination(data, ladders, seeds, rng) -> Dict:
    out = {}
    names = ladders[seeds[0]]["metrics"]
    for rung in sg.RUNGS:
        A = np.array([ladders[s]["real"] for s in seeds])
        B = np.array([np.asarray(ladders[s]["null"][rung])[0] for s in seeds])
        out[f"real_vs_{rung}"] = clf.paired_discrimination(A, B, names, rng=rng)
    x_only = list(names) + [f"atlas_persistence_{p}" for p in POPULATIONS]
    A = np.array([[data[(s, "full", "master")][m] for m in x_only] for s in seeds], dtype=float)
    B = np.array([[data[(s, "full", "twin")][m] for m in x_only] for s in seeds], dtype=float)
    out["master_vs_twin_from_dynamics_alone"] = clf.paired_discrimination(A, B, x_only, rng=rng)
    A = np.array([[data[(s, "full", "master")][m] for m in x_only] for s in seeds], dtype=float)
    B = np.array([[data[(s, "full", "placebo")][m] for m in x_only] for s in seeds], dtype=float)
    out["placebo_master_vs_master"] = clf.paired_discrimination(A, B, x_only, rng=rng)
    return out


def analyze_v3(out_dir: Path, alpha: float = 0.05) -> Dict:
    runs = json.loads((out_dir / "v3_forensics_runs.json").read_text())
    by = {(r["seed"], r["cond"]): r for r in runs}
    seeds = sorted({r["seed"] for r in runs})
    conds = ["master", "twin", "clamp_low", "clamp_high", "frozen"]
    res = {"n_seeds": len(seeds), "conditions": {}}
    rng = np.random.default_rng(3)
    for c in conds:
        rs = [by[(s, c)] for s in seeds]
        fired = [r["events"] > 0 for r in rs]
        onsets = [r["first_event_step"] for r in rs if r["first_event_step"] is not None]
        k = int(sum(fired))
        res["conditions"][c] = {
            "event_rate": k / len(rs), "event_rate_ci95": st.wilson_interval(k, len(rs)),
            "median_onset": float(np.median(onsets)) if onsets else None,
            "onsets": onsets,
            "mean_active_fraction": float(np.mean([r["active_fraction"] for r in rs])),
            "mean_convergence": float(np.mean([r["mean_convergence"] for r in rs])),
            "mean_free_votes": float(np.mean([r["audit"]["n_free_votes"] for r in rs])),
            "persistence_equals_hysteresis_rate": float(np.mean([bool(r["audit"]["persistence_equals_hysteresis"])
                                                                 for r in rs if r["events"] > 0])) if k else None,
            "switch_off_condition_rate": float(np.mean([r["audit"]["switch_off_condition_rate_post_calibration"] for r in rs])),
        }
    comps = {}
    for c in ("twin", "clamp_low", "clamp_high", "frozen"):
        a = np.array([by[(s, "master")]["events"] > 0 for s in seeds])
        b = np.array([by[(s, c)]["events"] > 0 for s in seeds])
        n10, n01 = int(np.sum(a & ~b)), int(np.sum(~a & b))
        n = n10 + n01
        p = min(1.0, 2.0 * st.binomial_sf(max(n10, n01), n, 0.5)) if n else 1.0
        d = np.array([by[(s, "master")]["active_fraction"] - by[(s, c)]["active_fraction"] for s in seeds])
        comps[f"master_vs_{c}"] = {"discordant_master_only": n10, "discordant_other_only": n01,
                                   "mcnemar_exact_p": p, "active_fraction": _test(d, "two-sided", rng)}
    res["comparisons"] = comps
    pooled = {}
    for c in conds:
        for name in runs[0]["audit"]["pass_rate"]:
            pooled.setdefault(c, {})[name] = float(np.mean([by[(s, c)]["audit"]["pass_rate"][name] for s in seeds]))
    res["channel_pass_rates"] = pooled
    res["traces"] = {c: {"step": by[(seeds[0], c)]["trace_step"],
                         "gain": [by[(s, c)]["trace_gain"] for s in seeds],
                         "ghost_index": [by[(s, c)]["trace_ghost_index"] for s in seeds],
                         "baseline_z": [by[(s, c)]["trace_baseline_z"] for s in seeds],
                         "active": [by[(s, c)]["trace_active"] for s in seeds]} for c in conds}
    gains = [by[(s, "master")]["audit"] for s in seeds]
    res["gain_audit"] = {
        "cap_reached_rate": float(np.mean([g["gain_cap_reached_step"] is not None for g in gains])),
        "median_cap_step": float(np.median([g["gain_cap_reached_step"] for g in gains if g["gain_cap_reached_step"]])) if any(g["gain_cap_reached_step"] for g in gains) else None,
        "mean_gain_at_first_event": float(np.mean([g["gain_at_first_event"] for g in gains if g["gain_at_first_event"]])) if any(g["gain_at_first_event"] for g in gains) else None,
        "mean_activity": float(np.mean([g["activity_mean"] for g in gains])),
        "homeostatic_target": 0.31,
    }
    # Metric-identical null ladder of v3's own metrics.
    lad = [by[(s, "master")]["ladder"] for s in seeds]
    tps = list(lad[0])
    names = lad[0][tps[0]]["metrics"]
    from .v3_bridge import V3_METRIC_KIND
    fp = {}
    for j, name in enumerate(names):
        per = {}
        for rung in sg.RUNGS:
            zs, ps, sign, differs = [], [], [], []
            for L in lad:
                for tpt in tps:
                    real = L[tpt]["real"][j]
                    null = np.asarray(L[tpt]["null"][rung])[:, j]
                    p = st.empirical_p(real, null, "two-sided")
                    r = (real - float(np.mean(null))) / max(abs(float(np.mean(null))), 1e-12)
                    zs.append(st.null_z(real, null))
                    ps.append(p)
                    sign.append(real > np.median(null))
                    differs.append(p <= alpha and abs(r) >= SESOI_RELATIVE)
            per[rung] = {"mean_z": float(np.mean(np.clip(zs, -99, 99))), "median_z": float(np.median(zs)),
                         "fraction_windows_p<=alpha": float(np.mean(np.asarray(ps) <= alpha)),
                         "fraction_windows_differ": float(np.mean(differs)),
                         "fraction_real_above_null_median": float(np.mean(sign))}
        fp[name] = {"kind": V3_METRIC_KIND.get(name, "?"), "rungs": per}
    res["v3_metric_fingerprint"] = fp
    return res
