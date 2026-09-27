"""
Runners and preregistered analyses for the v7 studies.

    K  feedback vs innovation     which part of the author's prediction error has to be
                                  in step with the network: the part its own state
                                  predicts (a feedback loop) or the rest?
    L  powered causal emergence   72 new networks: does authorship raise Psi?
    M  comparator gain, robust    the v6 Study J question with a bounded persistence
                                  measure and a rank-based test

Interventions act only in the analysis window (cycles burn..steps-1); before it, each
run is identical to its live reference. Runs are stored under random codes with a
separate unblinding key, as in v4-v6.
"""

from __future__ import annotations

import secrets
import time
from pathlib import Path
from typing import Callable, Dict, List, Sequence, Tuple

import numpy as np

from ghost_v4 import infotheory as it
from ghost_v4 import stats as st
from ghost_v4.campaign import _dz, _map, _pool, _test, write_json
from ghost_v4.engine import AgentConfig
from ghost_v5.studies import _col, _family, _load, design
from ghost_v6.studies import SESOI_PERSISTENCE, tost, v6_panel, window_shift

from .engine import V7Config, run_agent_v7

SESOI_PSI = 0.0561                  # one third of the v4 confirmatory H4 mean difference (as in v6's post-hoc re-reading)
RIDGE = 1e-3                        # ridge penalty, relative to the mean eigenvalue of the state covariance
GAINS_M = (0.5, 1.0, 2.0)


# ---------------------------------------------------------------- state-feedback decomposition

def fit_state_feedback(X: np.ndarray, mm: np.ndarray, burn: int) -> Tuple[np.ndarray, np.ndarray, float]:
    """
    Ridge regression of the mismatch at cycle t on the network state entering cycle t
    (X[t-1]) over the analysis window. Returns B (obs_dim, nodes), c (obs_dim,) and the
    share of mismatch variance the state predicts (R^2, pooled over channels).
    """
    Xp = np.asarray(X[burn - 1:-1], dtype=float)
    M = np.asarray(mm[burn:], dtype=float)
    mx, mm_ = Xp.mean(axis=0), M.mean(axis=0)
    Xc, Mc = Xp - mx, M - mm_
    G = Xc.T @ Xc
    lam = RIDGE * np.trace(G) / G.shape[0]
    B = np.linalg.solve(G + lam * np.eye(G.shape[0]), Xc.T @ Mc).T
    c = mm_ - B @ mx
    resid = Mc - Xc @ B.T
    r2 = 1.0 - float(np.sum(resid ** 2)) / float(np.sum(Mc ** 2))
    return B, c, r2


def feedback_streams(X: np.ndarray, mm: np.ndarray, B: np.ndarray, c: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """f_t = c + B X[t-1] (f_0 = c) and i_t = m_t - f_t over the whole run."""
    Xp = np.vstack([np.zeros((1, X.shape[1])), np.asarray(X[:-1], dtype=float)])
    fb = c[None, :] + Xp @ B.T
    fb[0] = c
    return fb, np.asarray(mm, dtype=float) - fb


# ---------------------------------------------------------------- robust statistics

def self_rho(X: np.ndarray, slices) -> float:
    """Bounded persistence: lag-1 autocorrelation of the self population's slowest collective mode."""
    a, b = slices["self"]
    V = it.slow_macro(X[:, a:b])
    return float(np.corrcoef(V[:-1], V[1:])[0, 1])


def signed_rank_test(d: Sequence[float], alternative: str = "greater", n_perm: int = 20000,
                     rng: np.random.Generator | None = None) -> float:
    """Wilcoxon signed-rank test by sign-flipping the ranks of |d| (exact for n <= 16)."""
    d = np.asarray(d, dtype=float)
    d = d[np.isfinite(d) & (d != 0)]
    n = len(d)
    if n == 0:
        return float("nan")
    order = np.argsort(np.abs(d), kind="stable")
    ranks = np.empty(n)
    absd = np.abs(d)[order]
    i = 0
    while i < n:                                           # average ranks for ties
        j = i
        while j + 1 < n and absd[j + 1] == absd[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return st.sign_flip_test(np.sign(d) * ranks, alternative=alternative, n_perm=n_perm, rng=rng)


def hodges_lehmann(d: np.ndarray) -> float:
    d = np.asarray(d, dtype=float)
    i, j = np.triu_indices(len(d))
    return float(np.median((d[i] + d[j]) / 2.0))


def _rtest(d: np.ndarray, alternative: str, rng) -> Dict:
    d = np.asarray(d, dtype=float)
    idx = rng.integers(0, len(d), size=(2000, len(d)))
    boots = np.array([hodges_lehmann(d[k]) for k in idx])
    return {"n": int(len(d)), "hodges_lehmann": hodges_lehmann(d),
            "hl_ci95": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))],
            "median": float(np.median(d)), "positive": int(np.sum(d > 0)),
            "mean_diff": float(np.mean(d)), "d_z": _dz(d),
            "p": signed_rank_test(d, alternative, rng=rng), "p_two_sided": signed_rank_test(d, "two-sided", rng=rng)}


# ---------------------------------------------------------------- per-run work

def v7_panel(rec, burn: int) -> Dict[str, float]:
    panel = v6_panel(rec, burn)
    X = rec.X[burn:].astype(float)
    panel["self_rho"] = self_rho(X, rec.slices)
    panel["pe_state_r2"] = fit_state_feedback(rec.X, rec.mismatch_vec, burn)[2]
    return panel


def _job(job: Dict) -> Dict:
    base = AgentConfig(net_seed=job["seed"], world_seed=job["world"], steps=job["steps"], **job.get("base_kw", {}))
    v7 = V7Config(base=base, **job.get("v7_kw", {}))
    rec = run_agent_v7(v7, yoke=job.get("yoke"), donor_actions=job.get("donor_actions"),
                       cmp_replay=job.get("replay"), fb_B=job.get("fb_B"), fb_c=job.get("fb_c"),
                       fb_replay=job.get("fb_replay"), inn_replay=job.get("inn_replay"))
    out = {k: job[k] for k in ("study", "seed", "cond", "role", "world")}
    out["panel"] = v7_panel(rec, job["burn"])
    if job.get("want_stream"):
        out["stream"] = rec.stream()
    if job.get("want_mm"):
        out["mm"] = rec.mismatch_vec
    if job.get("want_fb"):
        B, c, r2 = fit_state_feedback(rec.X, rec.mismatch_vec, job["burn"])
        fb, inn = feedback_streams(rec.X, rec.mismatch_vec, B, c)
        out["fb"] = {"B": B, "c": c, "fb": fb, "inn": inn}
    return out


def _execute(phases: Sequence[Callable[[Dict], List[Dict]]], out_dir: Path, workers: int, log) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    pool = _pool(workers)
    done: List[Dict] = []
    carry = {"stream": {}, "mm": {}, "fb": {}}
    try:
        for i, make in enumerate(phases):
            jobs = make(carry)
            log(f"  phase {i + 1}: {len(jobs)} runs ({time.time() - t0:.0f}s elapsed)")
            res = _map(pool, _job, jobs) if jobs else []
            for r in res:
                key = (r["seed"], r["cond"], r["role"])
                for k in ("stream", "mm", "fb"):
                    if k in r:
                        carry[k][key] = r.pop(k)
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


# ---------------------------------------------------------------- study K: feedback vs innovation

K_MASTER = ("live", "shift", "fbLive_innShift", "fbShift_innLive")
K_TWIN = ("live", "shift")


def run_K(spec, out_dir, workers=4, log=print):
    worlds, donors = design(spec)
    burn, T = int(spec["burn"]), int(spec["steps"])
    seeds = list(spec["seeds"])
    win = {"replay_start": burn}

    def job(s, cond, role, **kw):
        return dict(study="K", seed=s, cond=cond, role=role, world=worlds[s], steps=T, burn=burn, **kw)

    def phase1(c):
        return [job(s, "live", "master", want_stream=True, want_mm=True, want_fb=True) for s in seeds]

    def phase2(c):
        jobs = []
        for s in seeds:
            M = c["mm"][(s, "live", "master")]
            f = c["fb"][(s, "live", "master")]
            jobs += [job(s, "live", "twin", yoke=c["stream"][(donors[s], "live", "master")], want_mm=True),
                     job(s, "shift", "master", v7_kw=win, replay=window_shift(M, burn)),
                     job(s, "fbLive_innShift", "master", v7_kw=win, fb_B=f["B"], fb_c=f["c"],
                         inn_replay=window_shift(f["inn"], burn)),
                     job(s, "fbShift_innLive", "master", v7_kw=win, fb_B=f["B"], fb_c=f["c"],
                         fb_replay=window_shift(f["fb"], burn))]
        return jobs

    def phase3(c):
        return [job(s, "shift", "twin", yoke=c["stream"][(donors[s], "live", "master")], v7_kw=win,
                    replay=window_shift(c["mm"][(s, "live", "twin")], burn)) for s in seeds]

    _execute([phase1, phase2, phase3], out_dir, workers, log)


# ---------------------------------------------------------------- study L: powered causal emergence

def run_L(spec, out_dir, workers=4, log=print):
    worlds, donors = design(spec)
    burn, T = int(spec["burn"]), int(spec["steps"])
    seeds = list(spec["seeds"])

    def phase1(c):
        return [dict(study="L", seed=s, cond="live", role="master", world=worlds[s], steps=T, burn=burn,
                     want_stream=True) for s in seeds]

    def phase2(c):
        return [dict(study="L", seed=s, cond="live", role="twin", world=worlds[s], steps=T, burn=burn,
                     yoke=c["stream"][(donors[s], "live", "master")]) for s in seeds]

    _execute([phase1, phase2], out_dir, workers, log)


# ---------------------------------------------------------------- study M: comparator gain, robust

def run_M(spec, out_dir, workers=4, log=print):
    worlds, donors = design(spec)
    burn, T = int(spec["burn"]), int(spec["steps"])
    seeds = list(spec["seeds"])
    name = lambda k: f"gain{k:g}"

    def phase1(c):
        return [dict(study="M", seed=s, cond=name(k), role="master", world=worlds[s], steps=T, burn=burn,
                     v7_kw={"cmp_gain": k}, want_stream=True) for s in seeds for k in GAINS_M]

    def phase2(c):
        return [dict(study="M", seed=s, cond=name(k), role="twin", world=worlds[s], steps=T, burn=burn,
                     v7_kw={"cmp_gain": k}, yoke=c["stream"][(donors[s], name(k), "master")])
                for s in seeds for k in GAINS_M]

    _execute([phase1, phase2], out_dir, workers, log)


RUNNERS = {"K": run_K, "L": run_L, "M": run_M}


# ---------------------------------------------------------------- analyses

def analyze_K(out_dir: Path, alpha=0.05) -> Dict:
    data, seeds = _load(out_dir)
    rng = np.random.default_rng(71)
    P = lambda cond, role, m="self_persistence": _col(data, seeds, cond, role, m)
    live, shift = P("live", "master"), P("shift", "master")
    fbL, innL = P("fbLive_innShift", "master"), P("fbShift_innLive", "master")
    tests = _family({
        "K1_desynchronization_costs_the_author": _test(live - shift, "greater", rng),
        "K2_live_state_feedback_restores": _test(fbL - shift, "greater", rng),
        "K3_live_innovation_restores": _test(innL - shift, "greater", rng),
        "K4_synchrony_matters_more_for_the_author": _test((live - shift) - (P("live", "twin") - P("shift", "twin")),
                                                          "greater", rng),
    }, alpha)
    equivalence = {"K2": tost(fbL - shift, SESOI_PERSISTENCE, rng), "K3": tost(innL - shift, SESOI_PERSISTENCE, rng)}
    k2, k3 = tests["K2_live_state_feedback_restores"]["significant"], tests["K3_live_innovation_restores"]["significant"]
    if k2 and k3:
        account = "both"
    elif k2 and equivalence["K3"]["equivalent"]:
        account = "feedback"
    elif k3 and equivalence["K2"]["equivalent"]:
        account = "innovation"
    else:
        account = "undetermined"

    loss = live - shift
    idx = rng.integers(0, len(seeds), size=(4000, len(seeds)))
    recovered = {}
    for name, v in (("fbLive_innShift", fbL), ("fbShift_innLive", innL)):
        gain = v - shift
        boots = gain[idx].mean(axis=1) / loss[idx].mean(axis=1)
        recovered[name] = {"fraction_of_desync_loss_recovered": float(gain.mean() / loss.mean()),
                           "ci95": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))]}
    conds = [(c, "master") for c in K_MASTER] + [(c, "twin") for c in K_TWIN]
    levels = {f"{r}:{c}": {"mean": float(P(c, r).mean()), "ci95": st.bootstrap_ci(P(c, r), rng=rng),
                           "rho": float(P(c, r, "self_rho").mean()),
                           "injected_rms": float(P(c, r, "injected_rms").mean())} for c, r in conds}
    R = lambda cond, role: P(cond, role, "self_rho")
    robust = {
        "K1": _rtest(R("live", "master") - R("shift", "master"), "greater", rng),
        "K2": _rtest(R("fbLive_innShift", "master") - R("shift", "master"), "greater", rng),
        "K3": _rtest(R("fbShift_innLive", "master") - R("shift", "master"), "greater", rng),
        "K4": _rtest((R("live", "master") - R("shift", "master")) - (R("live", "twin") - R("shift", "twin")),
                     "greater", rng),
    }
    r2m, r2y = P("live", "master", "pe_state_r2"), P("live", "twin", "pe_state_r2")
    secondary = {
        "authorship_effect_live": _test(live - P("live", "twin"), "two-sided", rng),
        "twin_desync_cost": _test(P("live", "twin") - P("shift", "twin"), "two-sided", rng),
        "state_predictable_share_master_minus_twin": _test(r2m - r2y, "two-sided", rng),
        "fbLive_vs_innLive": _test(fbL - innL, "two-sided", rng),
    }
    return {"n_seeds": len(seeds), "primary": tests, "equivalence_sesoi_nats": SESOI_PERSISTENCE,
            "equivalence": equivalence, "account": account, "recovered": recovered, "levels": levels,
            "robust_rho_signed_rank": robust,
            "state_predictable_share": {"master": float(r2m.mean()), "twin": float(r2y.mean()),
                                        "master_ci95": st.bootstrap_ci(r2m, rng=rng),
                                        "twin_ci95": st.bootstrap_ci(r2y, rng=rng)},
            "secondary": secondary}


def analyze_L(out_dir: Path, alpha=0.05) -> Dict:
    data, seeds = _load(out_dir)
    rng = np.random.default_rng(72)
    D = lambda m: _col(data, seeds, "live", "master", m) - _col(data, seeds, "live", "twin", m)
    psi, rho = D("self_psi"), D("self_rho")
    tests = _family({
        "L1_authorship_raises_psi": _test(psi, "greater", rng),
        "L2_authorship_raises_bounded_persistence": _rtest(rho, "greater", rng),
    }, alpha)
    secondary = {
        "psi_equivalence": tost(psi, SESOI_PSI, rng),
        "gaussian_persistence": _test(D("self_persistence"), "greater", rng),
        "psi_signed_rank": _rtest(psi, "greater", rng),
        "psi_macro_term": _test(D("self_macro_self_information"), "two-sided", rng),
        "psi_parts_term": _test(D("self_parts_information"), "two-sided", rng),
        "state_predictable_share_master_minus_twin": _test(D("pe_state_r2"), "two-sided", rng),
    }
    return {"n_seeds": len(seeds), "primary": tests, "secondary": secondary,
            "psi_positive": int(np.sum(psi > 0)), "rho_positive": int(np.sum(rho > 0))}


def analyze_M(out_dir: Path, alpha=0.05) -> Dict:
    data, seeds = _load(out_dir)
    rng = np.random.default_rng(73)
    P = lambda k, role, m: _col(data, seeds, f"gain{k:g}", role, m)
    eff = {k: P(k, "master", "self_rho") - P(k, "twin", "self_rho") for k in GAINS_M}
    tests = _family({
        "M1_effect_present_at_half_gain": _rtest(eff[0.5], "greater", rng),
        "M2_effect_grows_with_gain": _rtest(eff[2.0] - eff[0.5], "greater", rng),
    }, alpha)
    sec = {f"robust_effect_gain{k:g}": _rtest(eff[k], "two-sided", rng) for k in GAINS_M}
    for k in GAINS_M:
        sec[f"gaussian_effect_gain{k:g}"] = _test(P(k, "master", "self_persistence") - P(k, "twin", "self_persistence"),
                                                  "two-sided", rng)
    sec["master_rho_gain2_minus_gain0.5"] = _rtest(P(2.0, "master", "self_rho") - P(0.5, "master", "self_rho"),
                                                   "two-sided", rng)
    sec["twin_rho_gain2_minus_gain0.5"] = _rtest(P(2.0, "twin", "self_rho") - P(0.5, "twin", "self_rho"),
                                                 "two-sided", rng)
    levels = {f"{r}:gain{k:g}": {"rho": float(P(k, r, "self_rho").mean()),
                                  "rho_ci95": st.bootstrap_ci(P(k, r, "self_rho"), rng=rng),
                                  "persistence": float(P(k, r, "self_persistence").mean()),
                                  "injected_rms": float(P(k, r, "injected_rms").mean())}
              for k in GAINS_M for r in ("master", "twin")}
    return {"n_seeds": len(seeds), "primary": tests, "secondary": sec, "levels": levels}


def across_study_holm(results: Dict, alpha=0.05) -> Dict:
    rows = [(s, n, r["p"]) for s, res in results.items() for n, r in (res.get("primary") or {}).items()]
    adj = st.holm([p for _, _, p in rows])
    return {f"{s}:{n}": {"p": p, "p_holm_all_v7": a, "significant": bool(a <= alpha)}
            for (s, n, p), a in zip(rows, adj)}
