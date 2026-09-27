"""
Runners and preregistered analyses for the v5 follow-up studies (B-F).
Study A (direct replication) reuses the frozen v4 campaign code unchanged.

Every run is stored under a random code with a separate unblinding key, as in v4.
"""

from __future__ import annotations

import json
import secrets
import time
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

from ghost_v4 import infotheory as it
from ghost_v4 import metrics as mt
from ghost_v4 import stats as st
from ghost_v4.campaign import _jsonable, _map, _pool, _test, write_json
from ghost_v4.engine import POPULATIONS, AgentConfig, Stream

from . import estimators as est
from .engine import V5Config, run_agent_v5

LEVELS = (0.0, 0.25, 0.5, 0.75, 1.0)


def blocks(seeds: List[int], k: int) -> List[List[int]]:
    size = len(seeds) // k
    return [seeds[i * size:(i + 1) * size] for i in range(k)]


def design(spec: Dict) -> Tuple[Dict[int, int], Dict[int, int]]:
    """world and donor (next network in the same world block) for every seed."""
    worlds, donors = {}, {}
    for b, members in enumerate(blocks(list(spec["seeds"]), int(spec["world_blocks"]))):
        for i, s in enumerate(members):
            worlds[s] = int(spec["world_seed_base"]) + b
            donors[s] = members[(i + 1) % len(members)]
    return worlds, donors


# ---------------------------------------------------------------- per-run work

def nonlinear_panel(X: np.ndarray, slices) -> Dict[str, float]:
    a, b = slices["self"]
    S = X[:, a:b]
    V = it.slow_macro(S)
    k = est.ksg_emergence(S, V)
    g = est.gc_emergence(S, V)
    return {"ksg_persistence": k["macro_self_information"], "ksg_psi": k["psi"],
            "ksg_parts_information": k["parts_information"],
            "gc_persistence": est.gc_persistence(V), "gc_psi": g["psi"]}


def _job(job: Dict) -> Dict:
    base = AgentConfig(net_seed=job["seed"], world_seed=job["world"], steps=job["steps"], **job.get("base_kw", {}))
    v5 = V5Config(base=base, **job.get("v5_kw", {}))
    rec = run_agent_v5(v5, yoke=job.get("yoke"), donor_actions=job.get("donor_actions"))
    panel = mt.record_panel(rec, job["burn"])
    if job.get("nonlinear"):
        panel.update(nonlinear_panel(rec.X[job["burn"]:].astype(float), rec.slices))
    out = {k: job[k] for k in ("study", "seed", "cond", "role", "world")}
    out["panel"] = panel
    if job.get("want_stream"):
        out["stream"] = rec.stream()
    return out


def _execute(phase_a: List[Dict], make_phase_b, out_dir: Path, workers: int, log) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    pool = _pool(workers)
    try:
        log(f"  phase A: {len(phase_a)} runs")
        first = _map(pool, _job, phase_a)
        streams = {(r["seed"], r["cond"]): r.pop("stream") for r in first if "stream" in r}
        phase_b = make_phase_b(streams)
        log(f"  phase B: {len(phase_b)} runs ({time.time() - t0:.0f}s elapsed)")
        second = _map(pool, _job, phase_b) if phase_b else []
    finally:
        if pool is not None:
            pool.close()
            pool.join()
    coded, key = {}, {}
    for r in first + second:
        code = secrets.token_hex(6)
        key[code] = {k: r[k] for k in ("study", "seed", "cond", "role", "world")}
        coded[code] = r["panel"]
    write_json(out_dir / "runs_coded.json", coded)
    write_json(out_dir / "unblinding_key.json", key)
    log(f"  {len(coded)} runs written in {time.time() - t0:.0f}s")


def _twin_phase(spec, study, conds, base_kw_of, v5_kw_of, burn, nonlinear=False):
    worlds, donors = design(spec)

    def make(streams):
        return [dict(study=study, seed=s, cond=c, role="twin", world=worlds[s], steps=spec["steps"], burn=burn,
                     base_kw=base_kw_of(c), v5_kw=v5_kw_of(c), yoke=streams[(donors[s], c)], nonlinear=nonlinear)
                for s in spec["seeds"] for c in conds]
    return make


def _masters(spec, study, conds, base_kw_of, v5_kw_of, burn, nonlinear=False):
    worlds, _ = design(spec)
    return [dict(study=study, seed=s, cond=c, role="master", world=worlds[s], steps=spec["steps"], burn=burn,
                 base_kw=base_kw_of(c), v5_kw=v5_kw_of(c), want_stream=True, nonlinear=nonlinear)
            for s in spec["seeds"] for c in conds]


# ---------------------------------------------------------------- studies

def run_B(spec, out_dir, workers=4, log=print):
    """Graded authorship in a live world, intact vs comparator-lesioned."""
    worlds, donors = design(spec)
    conds = [(c, p) for c in ("full", "no_comparator") for p in LEVELS]
    name = lambda c, p: f"{c}@p{p:g}"
    base_kw = lambda c: {} if c == "full" else {"comparator": False}
    phase_a = [dict(study="B", seed=s, cond=name(c, 1.0), role="graded", world=worlds[s], steps=spec["steps"],
                    burn=spec["burn"], base_kw=base_kw(c), want_stream=True)
               for s in spec["seeds"] for c in ("full", "no_comparator")]

    def make(streams):
        return [dict(study="B", seed=s, cond=name(c, p), role="graded", world=worlds[s], steps=spec["steps"],
                     burn=spec["burn"], base_kw=base_kw(c), v5_kw={"authorship": p},
                     donor_actions=streams[(donors[s], name(c, 1.0))].executed)
                for s in spec["seeds"] for (c, p) in conds if p < 1.0]
    _execute(phase_a, make, out_dir, workers, log)


def run_C(spec, out_dir, workers=4, log=print):
    """Nonlinear and copula estimators on re-simulated v4 confirmatory networks."""
    none = lambda c: {}
    _execute(_masters(spec, "C", ["full"], none, none, spec["burn"], nonlinear=True),
             _twin_phase(spec, "C", ["full"], none, none, spec["burn"], nonlinear=True), out_dir, workers, log)


VARIANTS_D = {"leak1.0": {"leak": 1.0}, "leak0.3": {"leak": 0.3}, "radius0.9": {"radius": 0.9}, "radius1.1": {"radius": 1.1}}


def run_D(spec, out_dir, workers=4, log=print):
    conds = list(VARIANTS_D)
    kw = lambda c: VARIANTS_D[c]
    none = lambda c: {}
    _execute(_masters(spec, "D", conds, kw, none, spec["burn"]),
             _twin_phase(spec, "D", conds, kw, none, spec["burn"]), out_dir, workers, log)


TIMING_E = {"sham": {}, "off_late": {"comparator_stop": 3000}, "on_late": {"comparator_start": 3000}}


def run_E(spec, out_dir, workers=4, log=print):
    conds = list(TIMING_E)
    none = lambda c: {}
    kw = lambda c: TIMING_E[c]
    _execute(_masters(spec, "E", conds, none, kw, spec["burn"]),
             _twin_phase(spec, "E", conds, none, kw, spec["burn"]), out_dir, workers, log)


WIRING_F = {"standard": {}, "rerouted": {"comparator_targets": ("dmn", "association")}}


def run_F(spec, out_dir, workers=4, log=print):
    conds = list(WIRING_F)
    none = lambda c: {}
    kw = lambda c: WIRING_F[c]
    _execute(_masters(spec, "F", conds, none, kw, spec["burn"]),
             _twin_phase(spec, "F", conds, none, kw, spec["burn"]), out_dir, workers, log)


RUNNERS = {"B": run_B, "C": run_C, "D": run_D, "E": run_E, "F": run_F}


# ---------------------------------------------------------------- analysis

def _load(out_dir: Path):
    coded = json.loads((out_dir / "runs_coded.json").read_text())
    key = json.loads((out_dir / "unblinding_key.json").read_text())
    data = {}
    for code, panel in coded.items():
        k = key[code]
        data[(k["seed"], k["cond"], k["role"])] = panel
    seeds = sorted({k[0] for k in data})
    return data, seeds


def _col(data, seeds, cond, role, metric):
    return np.array([data[(s, cond, role)][metric] for s in seeds], dtype=float)


def _authorship(data, seeds, cond, metric):
    return _col(data, seeds, cond, "master", metric) - _col(data, seeds, cond, "twin", metric)


def _family(tests: Dict[str, Dict], alpha: float) -> Dict[str, Dict]:
    names = list(tests)
    for n, a in zip(names, st.holm([tests[n]["p"] for n in names])):
        tests[n]["p_holm"] = a
        tests[n]["significant"] = bool(a <= alpha)
    return tests


def analyze_B(out_dir: Path, alpha=0.05) -> Dict:
    data, seeds = _load(out_dir)
    rng = np.random.default_rng(51)
    x = np.array(LEVELS)

    def slopes(c, metric):
        Y = np.stack([_col(data, seeds, f"{c}@p{p:g}", "graded", metric) for p in LEVELS], axis=1)
        return np.polyfit(x, Y.T, 1)[0], Y

    s_full, Y_full = slopes("full", "self_persistence")
    s_nc, Y_nc = slopes("no_comparator", "self_persistence")
    s_psi, Y_psi = slopes("full", "self_psi")
    tests = _family({
        "B1_persistence_rises_with_authorship": _test(s_full, "greater", rng),
        "B2_dose_response_needs_comparator": _test(s_full - s_nc, "greater", rng),
        "B3_psi_rises_with_authorship": _test(s_psi, "greater", rng),
    }, alpha)
    match = {f"{p:g}": float(np.mean(_col(data, seeds, f"full@p{p:g}", "graded", "intention_outcome_match")))
             for p in LEVELS}
    levels = {}
    for label, Y in (("full_persistence", Y_full), ("no_comparator_persistence", Y_nc), ("full_psi", Y_psi)):
        levels[label] = {f"{p:g}": {"mean": float(Y[:, i].mean()), "ci95": st.bootstrap_ci(Y[:, i], rng=rng)}
                         for i, p in enumerate(LEVELS)}
    steps = {f"{LEVELS[i]:g}->{LEVELS[i + 1]:g}": _test(Y_full[:, i + 1] - Y_full[:, i], "two-sided", rng)
             for i in range(len(LEVELS) - 1)}
    return {"n_seeds": len(seeds), "primary": tests, "intention_outcome_match": match, "levels": levels,
            "adjacent_steps_full": steps,
            "seeds_with_positive_slope": int(np.sum(s_full > 0))}


def analyze_C(out_dir: Path, v4_campaign_dir: Path, alpha=0.05) -> Dict:
    data, seeds = _load(out_dir)
    rng = np.random.default_rng(52)
    tests = _family({
        "C1_ksg_persistence": _test(_authorship(data, seeds, "full", "ksg_persistence"), "greater", rng),
        "C2_ksg_psi": _test(_authorship(data, seeds, "full", "ksg_psi"), "greater", rng),
        "C3_gc_persistence": _test(_authorship(data, seeds, "full", "gc_persistence"), "greater", rng),
        "C4_gc_psi": _test(_authorship(data, seeds, "full", "gc_psi"), "greater", rng),
    }, alpha)
    out = {"n_seeds": len(seeds), "primary": tests,
           "ksg_parts_information": _test(_authorship(data, seeds, "full", "ksg_parts_information"), "two-sided", rng),
           "gaussian_reference_H1": _test(_authorship(data, seeds, "full", "self_persistence"), "greater", rng),
           "gaussian_reference_H4": _test(_authorship(data, seeds, "full", "self_psi"), "greater", rng)}
    from ghost_v4.campaign import _load_runs
    v4data, _ = _load_runs(v4_campaign_dir)
    diffs = [abs(data[(s, "full", r)]["self_persistence"] - v4data[(s, "full", r)]["self_persistence"])
             for s in seeds for r in ("master", "twin")]
    out["resimulation_matches_v4"] = {"max_abs_difference_self_persistence": float(np.max(diffs)),
                                      "identical": bool(np.max(diffs) == 0.0)}
    return out


def analyze_D(out_dir: Path, alpha=0.05) -> Dict:
    data, seeds = _load(out_dir)
    rng = np.random.default_rng(53)
    tests = _family({f"D_{v}_self_persistence": _test(_authorship(data, seeds, v, "self_persistence"), "greater", rng)
                     for v in VARIANTS_D}, alpha)
    sec = {}
    for v in VARIANTS_D:
        sec[f"{v}_psi"] = _test(_authorship(data, seeds, v, "self_psi"), "two-sided", rng)
        d_self = _authorship(data, seeds, v, "atlas_persistence_self")
        d_other = np.mean([_authorship(data, seeds, v, f"atlas_persistence_{p}") for p in POPULATIONS if p != "self"], axis=0)
        sec[f"{v}_self_specificity"] = _test(d_self - d_other, "two-sided", rng)
        sec[f"{v}_te_manipulation_check"] = _test(_authorship(data, seeds, v, "te_net_to_obs"), "two-sided", rng)
    return {"n_seeds": len(seeds), "primary": tests, "secondary": sec}


def analyze_E(out_dir: Path, alpha=0.05) -> Dict:
    data, seeds = _load(out_dir)
    rng = np.random.default_rng(54)
    d = {c: _authorship(data, seeds, c, "self_persistence") for c in TIMING_E}
    tests = _family({
        "E1_effect_appears_when_comparator_switched_on": _test(d["on_late"], "greater", rng),
        "E2_effect_disappears_when_comparator_switched_off": _test(d["sham"] - d["off_late"], "greater", rng),
        "E3_effect_present_in_sham_window": _test(d["sham"], "greater", rng),
    }, alpha)
    sec = {f"authorship_effect_{c}": _test(d[c], "two-sided", rng) for c in TIMING_E}
    sec["on_late_minus_sham"] = _test(d["on_late"] - d["sham"], "two-sided", rng)
    return {"n_seeds": len(seeds), "primary": tests, "secondary": sec}


def analyze_F(out_dir: Path, alpha=0.05) -> Dict:
    data, seeds = _load(out_dir)
    rng = np.random.default_rng(55)
    eff = {w: {p: _authorship(data, seeds, w, f"atlas_persistence_{p}") for p in POPULATIONS} for w in WIRING_F}
    tests = _family({
        "F1_rerouted_effect_in_dmn": _test(eff["rerouted"]["dmn"], "greater", rng),
        "F2_effect_follows_comparator": _test((eff["rerouted"]["dmn"] - eff["rerouted"]["self"])
                                              - (eff["standard"]["dmn"] - eff["standard"]["self"]), "greater", rng),
    }, alpha)
    atlas = {w: {p: _test(eff[w][p], "two-sided", rng) for p in POPULATIONS} for w in WIRING_F}
    return {"n_seeds": len(seeds), "primary": tests, "atlas": atlas}


def across_study_holm(results: Dict, alpha=0.05) -> Dict:
    rows = []
    for study, res in results.items():
        prim = res.get("primary") or {}
        for name, r in prim.items():
            if isinstance(r, dict) and "p" in r:
                rows.append((study, name, r["p"]))
    adj = st.holm([p for _, _, p in rows])
    return {f"{s}:{n}": {"p": p, "p_holm_all_v5": a, "significant": bool(a <= alpha)}
            for (s, n, p), a in zip(rows, adj)}
