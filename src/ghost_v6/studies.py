"""
Runners and preregistered analyses for the v6 studies.

    G  prediction-error transplant   swap, desynchronize, phase-randomize and rescale
                                     the comparator's input stream
    I  near-full authorship          p in {0.75, 0.90, 0.95, 0.99, 1}, with the
                                     prediction-error amplitude as a candidate mediator
    J  comparator gain               does the effect scale with the coupling strength?

Every intervention on the prediction-error stream is applied only in the analysis
window (cycles burn..steps-1). Before it, each run is identical to its live
reference, so conditions differ only in what the comparator injects while the
endpoint is measured. Runs are stored under random codes with a separate
unblinding key, as in v4 and v5.
"""

from __future__ import annotations

import secrets
import time
from pathlib import Path
from typing import Callable, Dict, List, Sequence

import numpy as np

from ghost_v4 import metrics as mt
from ghost_v4 import stats as st
from ghost_v4.campaign import _map, _pool, _test, write_json
from ghost_v4.engine import AgentConfig
from ghost_v4.surrogates import mv_phase
from ghost_v5.studies import _col, _family, _load, design

from .engine import V6Config, run_agent_v6

SESOI_PERSISTENCE = 0.04          # nats; about a third of the v4 / v4-replication authorship effect (0.140 / 0.120)
LEVELS_I = (0.75, 0.90, 0.95, 0.99, 1.0)
GAINS_J = (0.5, 1.0, 2.0)


# ---------------------------------------------------------------- stream interventions

def window_shift(M: np.ndarray, burn: int) -> np.ndarray:
    """Same waveform, desynchronized: circularly shift the window segment by half its length."""
    out = M.copy()
    seg = M[burn:]
    out[burn:] = np.roll(seg, len(seg) // 2, axis=0)
    return out


def window_phase(M: np.ndarray, burn: int, rng: np.random.Generator) -> np.ndarray:
    """Same auto- and cross-spectra, new phases: a multivariate Fourier surrogate of the window segment."""
    out = M.copy()
    out[burn:] = mv_phase(M[burn:], rng)
    return out


def window_rescale(Y: np.ndarray, M: np.ndarray, burn: int) -> np.ndarray:
    """Y's temporal structure with M's per-channel mean and standard deviation (window segment)."""
    out = Y.copy()
    y, m = Y[burn:], M[burn:]
    sd = y.std(axis=0)
    sd[sd < 1e-12] = 1.0
    out[burn:] = (y - y.mean(axis=0)) / sd * m.std(axis=0) + m.mean(axis=0)
    return out


# ---------------------------------------------------------------- per-run work

def v6_panel(rec, burn: int) -> Dict[str, float]:
    panel = mt.record_panel(rec, burn)
    own = rec.intended[burn:] == rec.executed[burn:]
    mm = rec.mismatch[burn:].astype(float)
    panel["mismatch_rms"] = float(mm.mean())
    panel["own_step_mismatch_rms"] = float(mm[own].mean()) if own.any() else float("nan")
    panel["foreign_step_mismatch_rms"] = float(mm[~own].mean()) if (~own).any() else float("nan")
    panel["injected_rms"] = float(rec.injected_rms[burn:].astype(float).mean())
    return panel


def _job(job: Dict) -> Dict:
    base = AgentConfig(net_seed=job["seed"], world_seed=job["world"], steps=job["steps"], **job.get("base_kw", {}))
    v6 = V6Config(base=base, **job.get("v6_kw", {}))
    rec = run_agent_v6(v6, yoke=job.get("yoke"), donor_actions=job.get("donor_actions"),
                       cmp_replay=job.get("replay"))
    out = {k: job[k] for k in ("study", "seed", "cond", "role", "world")}
    out["panel"] = v6_panel(rec, job["burn"])
    if job.get("want_stream"):
        out["stream"] = rec.stream()
    if job.get("want_mm"):
        out["mm"] = rec.mismatch_vec
    return out


def _execute(phases: Sequence[Callable[[Dict], List[Dict]]], out_dir: Path, workers: int, log) -> None:
    """Run dependent phases; each phase builder sees the streams and mismatch vectors of earlier phases."""
    out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    pool = _pool(workers)
    done: List[Dict] = []
    carry = {"stream": {}, "mm": {}}
    try:
        for i, make in enumerate(phases):
            jobs = make(carry)
            log(f"  phase {i + 1}: {len(jobs)} runs ({time.time() - t0:.0f}s elapsed)")
            res = _map(pool, _job, jobs) if jobs else []
            for r in res:
                if "stream" in r:
                    carry["stream"][(r["seed"], r["cond"], r["role"])] = r.pop("stream")
                if "mm" in r:
                    carry["mm"][(r["seed"], r["cond"], r["role"])] = r.pop("mm")
            done.extend(res)
    finally:
        if pool is not None:
            pool.close()
            pool.join()
    coded, key = {}, {}
    for r in done:
        code = secrets.token_hex(6)
        key[code] = {k: r[k] for k in ("study", "seed", "cond", "role", "world")}
        coded[code] = r["panel"]
    write_json(out_dir / "runs_coded.json", coded)
    write_json(out_dir / "unblinding_key.json", key)
    log(f"  {len(coded)} runs written in {time.time() - t0:.0f}s")


# ---------------------------------------------------------------- study G: prediction-error transplant

G_MASTER = ("live", "off", "shift", "phase", "twinPE", "twinPE_scaled")
G_TWIN = ("live", "off", "masterPE")


def run_G(spec, out_dir, workers=4, log=print):
    worlds, donors = design(spec)
    burn, T = int(spec["burn"]), int(spec["steps"])
    seeds = list(spec["seeds"])

    def job(s, cond, role, **kw):
        return dict(study="G", seed=s, cond=cond, role=role, world=worlds[s], steps=T, burn=burn, **kw)

    zeros = np.zeros((T, AgentConfig().obs_dim))
    win = {"replay_start": burn}

    def phase1(c):
        return ([job(s, "live", "master", want_stream=True, want_mm=True) for s in seeds]
                + [job(s, "off", "master", v6_kw=win, replay=zeros) for s in seeds])

    def phase2(c):
        jobs = []
        for s in seeds:
            M = c["mm"][(s, "live", "master")]
            y = c["stream"][(donors[s], "live", "master")]
            jobs += [job(s, "live", "twin", yoke=y, want_mm=True),
                     job(s, "off", "twin", yoke=y, v6_kw=win, replay=zeros),
                     job(s, "masterPE", "twin", yoke=y, v6_kw=win, replay=M),
                     job(s, "shift", "master", v6_kw=win, replay=window_shift(M, burn)),
                     job(s, "phase", "master", v6_kw=win,
                         replay=window_phase(M, burn, np.random.default_rng([s, 606])))]
        return jobs

    def phase3(c):
        jobs = []
        for s in seeds:
            M, Y = c["mm"][(s, "live", "master")], c["mm"][(s, "live", "twin")]
            jobs += [job(s, "twinPE", "master", v6_kw=win, replay=Y),
                     job(s, "twinPE_scaled", "master", v6_kw=win, replay=window_rescale(Y, M, burn))]
        return jobs

    _execute([phase1, phase2, phase3], out_dir, workers, log)


# ---------------------------------------------------------------- study I: near-full authorship

def run_I(spec, out_dir, workers=4, log=print):
    worlds, donors = design(spec)
    burn, T = int(spec["burn"]), int(spec["steps"])
    seeds = list(spec["seeds"])
    name = lambda p: f"p{p:g}"

    def phase1(c):
        return [dict(study="I", seed=s, cond=name(1.0), role="graded", world=worlds[s], steps=T, burn=burn,
                     want_stream=True) for s in seeds]

    def phase2(c):
        return [dict(study="I", seed=s, cond=name(p), role="graded", world=worlds[s], steps=T, burn=burn,
                     v6_kw={"authorship": p}, donor_actions=c["stream"][(donors[s], name(1.0), "graded")].executed)
                for s in seeds for p in LEVELS_I if p < 1.0]

    _execute([phase1, phase2], out_dir, workers, log)


# ---------------------------------------------------------------- study J: comparator gain

def run_J(spec, out_dir, workers=4, log=print):
    worlds, donors = design(spec)
    burn, T = int(spec["burn"]), int(spec["steps"])
    seeds = list(spec["seeds"])
    name = lambda k: f"gain{k:g}"

    def phase1(c):
        return [dict(study="J", seed=s, cond=name(k), role="master", world=worlds[s], steps=T, burn=burn,
                     v6_kw={"cmp_gain": k}, want_stream=True) for s in seeds for k in GAINS_J]

    def phase2(c):
        return [dict(study="J", seed=s, cond=name(k), role="twin", world=worlds[s], steps=T, burn=burn,
                     v6_kw={"cmp_gain": k}, yoke=c["stream"][(donors[s], name(k), "master")])
                for s in seeds for k in GAINS_J]

    _execute([phase1, phase2], out_dir, workers, log)


RUNNERS = {"G": run_G, "I": run_I, "J": run_J}


# ---------------------------------------------------------------- statistics

def tost(d: np.ndarray, bound: float, rng, alpha: float = 0.05) -> Dict:
    """Two one-sided sign-flip tests: is the mean difference inside (-bound, +bound)?"""
    d = np.asarray(d, dtype=float)
    p_lower = st.sign_flip_test(d + bound, "greater", rng=rng)
    p_upper = st.sign_flip_test(d - bound, "less", rng=rng)
    p = max(p_lower, p_upper)
    return {"bound": bound, "mean_diff": float(np.mean(d)),
            "ci90": st.bootstrap_ci(d, level=0.90, rng=rng),
            "p_lower": p_lower, "p_upper": p_upper, "p": p, "equivalent": bool(p <= alpha)}


def _fisher_z_within(Y: np.ndarray, Z: np.ndarray) -> np.ndarray:
    """Per-row Pearson r between Y and Z (rows = networks, columns = levels), Fisher-z transformed."""
    out = []
    for y, z in zip(Y, Z):
        if np.std(y) < 1e-15 or np.std(z) < 1e-15:
            out.append(0.0)
            continue
        r = float(np.corrcoef(y, z)[0, 1])
        out.append(float(np.arctanh(np.clip(r, -0.999999, 0.999999))))
    return np.array(out)


# ---------------------------------------------------------------- analyses

def analyze_G(out_dir: Path, alpha=0.05) -> Dict:
    data, seeds = _load(out_dir)
    rng = np.random.default_rng(61)
    P = lambda cond, role, m="self_persistence": _col(data, seeds, cond, role, m)
    live_m, live_y = P("live", "master"), P("live", "twin")
    gate = _test(live_m - live_y, "greater", rng)
    gate["pass"] = bool(gate["p"] <= alpha)
    tests = _family({
        "G1_pe_content_necessary": _test(live_m - P("twinPE", "master"), "greater", rng),
        "G2_pe_content_sufficient": _test(P("masterPE", "twin") - live_y, "greater", rng),
        "G3_contingency_matters": _test(live_m - P("shift", "master"), "greater", rng),
        "G4_amplitude_matters": _test(P("twinPE_scaled", "master") - P("twinPE", "master"), "greater", rng),
    }, alpha)
    equivalence = {
        "G1": tost(live_m - P("twinPE", "master"), SESOI_PERSISTENCE, rng),
        "G2": tost(P("masterPE", "twin") - live_y, SESOI_PERSISTENCE, rng),
        "G3": tost(live_m - P("shift", "master"), SESOI_PERSISTENCE, rng),
        "G4": tost(P("twinPE_scaled", "master") - P("twinPE", "master"), SESOI_PERSISTENCE, rng),
    }
    sig = {k.split("_")[0]: v["significant"] for k, v in tests.items()}
    if sig["G1"] and sig["G2"] and sig["G4"] and not sig["G3"] and equivalence["G3"]["equivalent"]:
        account = "amplitude"
    elif sig["G1"] and sig["G3"]:
        account = "contingency"
    else:
        account = "undetermined"

    conds = [(c, "master") for c in G_MASTER] + [(c, "twin") for c in G_TWIN]
    effect = live_m - live_y
    levels, fraction, injected = {}, {}, {}
    for c, r in conds:
        v = P(c, r)
        k = f"{r}:{c}"
        levels[k] = {"mean": float(v.mean()), "ci95": st.bootstrap_ci(v, rng=rng)}
        rel = v - live_y
        idx = rng.integers(0, len(seeds), size=(4000, len(seeds)))
        boots = rel[idx].mean(axis=1) / effect[idx].mean(axis=1)
        fraction[k] = {"fraction_of_authorship_effect": float(rel.mean() / effect.mean()),
                       "ci95": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))]}
        injected[k] = float(P(c, r, "injected_rms").mean())
    secondary = {
        "phase_vs_live_master": _test(live_m - P("phase", "master"), "two-sided", rng),
        "shift_vs_phase_master": _test(P("shift", "master") - P("phase", "master"), "two-sided", rng),
        "off_master_vs_live_twin": _test(P("off", "master") - live_y, "two-sided", rng),
        "masterPE_twin_vs_live_master": _test(P("masterPE", "twin") - live_m, "two-sided", rng),
        "association_G1": _test(P("live", "master", "atlas_persistence_association")
                                - P("twinPE", "master", "atlas_persistence_association"), "two-sided", rng),
        "psi_live_master_minus_twin": _test(P("live", "master", "self_psi") - P("live", "twin", "self_psi"),
                                            "two-sided", rng),
    }
    return {"n_seeds": len(seeds), "gate_authorship_effect": gate, "primary": tests,
            "equivalence_sesoi_nats": SESOI_PERSISTENCE, "equivalence": equivalence, "account": account,
            "levels": levels, "fraction_of_effect": fraction, "injected_rms": injected, "secondary": secondary}


def analyze_I(out_dir: Path, alpha=0.05) -> Dict:
    data, seeds = _load(out_dir)
    rng = np.random.default_rng(62)
    col = lambda p, m: _col(data, seeds, f"p{p:g}", "graded", m)
    Y = np.stack([col(p, "self_persistence") for p in LEVELS_I], axis=1)
    Z = np.stack([col(p, "mismatch_rms") for p in LEVELS_I], axis=1)
    tests = _family({
        "I1_five_percent_foreign_reduces_persistence": _test(col(1.0, "self_persistence") - col(0.95, "self_persistence"),
                                                             "greater", rng),
        "I2_one_percent_foreign_reduces_persistence": _test(col(1.0, "self_persistence") - col(0.99, "self_persistence"),
                                                            "greater", rng),
        "I3_foreign_actions_raise_own_step_error": _test(col(0.95, "own_step_mismatch_rms") - col(1.0, "own_step_mismatch_rms"),
                                                         "greater", rng),
        "I4_persistence_tracks_prediction_error": _test(_fisher_z_within(Y, Z), "less", rng),
    }, alpha)
    lv = {}
    for m in ("self_persistence", "mismatch_rms", "own_step_mismatch_rms", "foreign_step_mismatch_rms",
              "intention_outcome_match", "self_psi"):
        lv[m] = {}
        for p in LEVELS_I:
            v = col(p, m)
            v = v[np.isfinite(v)]
            lv[m][f"{p:g}"] = {"mean": float(v.mean()) if len(v) else None,
                               "ci95": st.bootstrap_ci(v, rng=rng) if len(v) > 1 else [None, None]}
    rel = {f"{p:g}": {"mean": float((Y[:, i] - Y[:, -1]).mean()), "ci95": st.bootstrap_ci(Y[:, i] - Y[:, -1], rng=rng)}
           for i, p in enumerate(LEVELS_I)}
    steps = {f"{LEVELS_I[i]:g}->{LEVELS_I[i + 1]:g}": _test(Y[:, i + 1] - Y[:, i], "two-sided", rng)
             for i in range(len(LEVELS_I) - 1)}
    return {"n_seeds": len(seeds), "primary": tests, "levels": lv, "relative_to_full_authorship": rel,
            "adjacent_steps": steps}


def analyze_J(out_dir: Path, alpha=0.05) -> Dict:
    data, seeds = _load(out_dir)
    rng = np.random.default_rng(63)
    P = lambda k, role, m="self_persistence": _col(data, seeds, f"gain{k:g}", role, m)
    eff = {k: P(k, "master") - P(k, "twin") for k in GAINS_J}
    tests = _family({
        "J1_effect_present_at_half_gain": _test(eff[0.5], "greater", rng),
        "J2_effect_grows_with_gain": _test(eff[2.0] - eff[0.5], "greater", rng),
    }, alpha)
    sec = {f"authorship_effect_gain{k:g}": _test(eff[k], "two-sided", rng) for k in GAINS_J}
    sec["master_gain2_minus_gain0.5"] = _test(P(2.0, "master") - P(0.5, "master"), "two-sided", rng)
    sec["twin_gain2_minus_gain0.5"] = _test(P(2.0, "twin") - P(0.5, "twin"), "two-sided", rng)
    levels = {f"{r}:gain{k:g}": {"mean": float(P(k, r).mean()), "ci95": st.bootstrap_ci(P(k, r), rng=rng),
                                  "injected_rms": float(P(k, r, "injected_rms").mean())}
              for k in GAINS_J for r in ("master", "twin")}
    return {"n_seeds": len(seeds), "primary": tests, "secondary": sec, "levels": levels}


def across_study_holm(results: Dict, alpha=0.05) -> Dict:
    rows = [(s, n, r["p"]) for s, res in results.items() for n, r in (res.get("primary") or {}).items()]
    adj = st.holm([p for _, _, p in rows])
    return {f"{s}:{n}": {"p": p, "p_holm_all_v6": a, "significant": bool(a <= alpha)}
            for (s, n, p), a in zip(rows, adj)}
