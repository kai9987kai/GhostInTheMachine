"""
Forensic bridge to the frozen v3 build.

The v3 source file is never modified: v3 results must stay reproducible from
the exact bytes whose SHA-256 is recorded in docs/SHA256SUMS.txt. This module
loads that file, verifies its hash, and adds *measurement and control hooks*
by subclassing:

* recording of every state, observation, action and gain value;
* a cross-yoked twin (world replaced by a replay of another run's observations);
* a clamped-gain control (v3's homeostatic ramp disabled);
* a frozen-learning control (all predictive-model learning rates set to zero).

It also exposes v3's own history-based metric methods as pure functions of a
recorded window, by calling the unbound v3 methods on a minimal namespace.
That makes surrogate tests *metric-identical* to v3: the same code, applied to
real and surrogate windows of identical length.
"""

from __future__ import annotations

import hashlib
import importlib.util
import math
import sys
from collections import deque
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
from typing import Dict, List, Optional

WINDOW = 257

import numpy as np

V3_PATH = Path(__file__).resolve().parents[1] / "ghost_in_the_machine_v3.py"
V3_VALIDATED_SHA256 = "2e5c8321c1e3cb8c85349a2f994f0c62cd16014ad2d5d26935d7b427650dd5c3"
_MODULE_NAME = "ghost_in_the_machine_v3"


def load_v3():
    """Import the frozen v3 file as a module (cached in sys.modules for pickling)."""
    if _MODULE_NAME in sys.modules:
        return sys.modules[_MODULE_NAME]
    spec = importlib.util.spec_from_file_location(_MODULE_NAME, V3_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[_MODULE_NAME] = mod
    spec.loader.exec_module(mod)
    return mod


def v3_sha256() -> str:
    return hashlib.sha256(V3_PATH.read_bytes()).hexdigest()


v3 = load_v3()


class ReplayWorld:
    """Stands in for v3's LatentWorld: returns another run's observations in order."""

    def __init__(self, obs: np.ndarray):
        self.obs = np.asarray(obs, dtype=float)
        self.t = 0

    def observe(self) -> np.ndarray:
        return self.obs[self.t].copy()

    def step(self, action: int) -> np.ndarray:  # the twin's command has no effect
        self.t += 1
        return self.obs[self.t].copy()


class RecordingV3(v3.GhostMachineV3):
    def __init__(self, *args, yoke_obs: Optional[np.ndarray] = None, clamp_gain: Optional[float] = None,
                 freeze_learning: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        self.clamp_gain = clamp_gain
        if clamp_gain is not None:
            self.recurrent_gain = float(clamp_gain)
        if yoke_obs is not None:
            self.world = ReplayWorld(yoke_obs)
            self.prev_obs = self.world.observe()
            self.preferred_obs = self.prev_obs.copy()
        if freeze_learning:
            for model in [self.world_predictor, self.self_predictor, self.meta_model, *self.world_ensemble]:
                model.lr = 0.0
        self.rec_states: List[np.ndarray] = []
        self.rec_obs: List[np.ndarray] = [self.prev_obs.copy()]
        self.rec_actions: List[int] = []
        self.rec_gain: List[float] = []

    def _homeostatic_gain(self) -> None:
        if self.clamp_gain is not None:
            self.recurrent_gain = float(self.clamp_gain)
            return
        super()._homeostatic_gain()

    def step_v3(self, step: int):
        gain_used = float(self.recurrent_gain)  # the gain this step's dynamics and Jacobian estimate use
        m, newly = super().step_v3(step)
        self.rec_states.append(self.state.copy())
        self.rec_obs.append(self.prev_obs.copy())
        self.rec_actions.append(int(self.last_action))
        self.rec_gain.append(gain_used)
        return m, newly


def run_v3(seed: int, steps: int = 5000, yoke_obs: Optional[np.ndarray] = None,
           clamp_gain: Optional[float] = None, freeze_learning: bool = False,
           calibration_steps: int = 1000, diagnostic_interval: int = 50, perturb_interval: int = 500) -> Dict:
    """Run one v3 machine with the validated short-run configuration; return a record dict."""
    m = RecordingV3(
        seed=seed, nodes=120, obs_dim=16, action_count=7, calibration_steps=calibration_steps,
        diagnostic_interval=diagnostic_interval, perturb_interval=perturb_interval,
        consolidation_interval=5000, replay_batch=48,
        yoke_obs=yoke_obs, clamp_gain=clamp_gain, freeze_learning=freeze_learning,
    )
    rows = []
    for step in range(1, steps + 1):
        row, _ = m.step_v3(step)
        if step % diagnostic_interval == 0:
            rows.append(asdict(row))
    return {
        "seed": seed,
        "rows": rows,
        "first_event_step": m.v3_detector.first_event_step,
        "events": m.v3_detector.events,
        "ghost_steps": m.v3_ghost_steps,
        "X": np.stack(m.rec_states),
        "obs": np.stack(m.rec_obs).astype(np.float32),
        "actions": np.asarray(m.rec_actions, dtype=np.int16),
        "gain": np.asarray(m.rec_gain),
        "W": m.W,
        "slices": {k: (v.start, v.stop) for k, v in m.slices.items()},
        "base_spectral_radius": m.base_spectral_radius,
        "calibration_steps": calibration_steps,
        "diagnostic_interval": diagnostic_interval,
    }


# ---------------------------------------------------------------------------
# Detector audits
# ---------------------------------------------------------------------------

CHANNEL_NAMES = ("workspace", "recurrence", "topology+synergy", "self+cf_agency", "criticality",
                 "pci", "entropy+lz", "mesocircuit+tc", "ei_balance", "geometry")


def v3_votes(r: Dict) -> np.ndarray:
    """The ten Boolean channels exactly as ConvergenceDetectorV3.update evaluates them."""
    return np.array([
        r["global_access"] >= 0.57 and r["ignition"] >= 0.46,
        r["recurrence"] >= 0.61,
        r["topology_balance"] >= 0.38 and r["synergy"] >= 0.040,
        r["self_model"] >= 0.54 and r["counterfactual_agency"] >= 0.50,
        (0.55 * r["criticality"] + 0.45 * r["avalanche_criticality"]) >= 0.43,
        r["perturbational_complexity"] >= 0.27,
        r["multiscale_entropy"] >= 0.42 and r["lz_complexity"] >= 0.34,
        r["mesocircuit_flow"] >= 0.22 and r["thalamocortical_transfer"] >= 0.16,
        r["ei_balance"] >= 0.32,
        r["geometry_score"] >= 0.32,
    ], dtype=bool)


def detector_audit(rec: Dict) -> Dict:
    rows = rec["rows"]
    cal = rec["calibration_steps"]
    post = [r for r in rows if r["step"] > cal]
    V = np.array([v3_votes(r) for r in post])
    pass_rate = V.mean(axis=0)
    free = [CHANNEL_NAMES[i] for i in range(10) if pass_rate[i] >= 0.95]
    gates = {
        "votes>=8": float(np.mean(V.sum(axis=1) >= 8)),
        "convergence>=0.56": float(np.mean([r["cross_theory_convergence"] >= 0.56 for r in post])),
        "ghost_index>=0.60": float(np.mean([r["ghost_index"] >= 0.60 for r in post])),
        "baseline_z>=1.35": float(np.mean([r["baseline_z"] >= 1.35 for r in post])),
    }
    # Hysteresis: once active, how often was the switch-off condition ever met?
    active_rows = [r for r in rows if r["ghost_active"]]
    off_met = [r["cross_theory_convergence"] < 0.43 or r["ghost_index"] < 0.48 for r in post]
    first = rec["first_event_step"]
    T = len(rec["X"])
    di = rec["diagnostic_interval"]
    gain = rec["gain"]
    cap_hit = int(np.argmax(gain >= 1.18 - 1e-9)) + 1 if np.any(gain >= 1.18 - 1e-9) else None
    return {
        "pass_rate": dict(zip(CHANNEL_NAMES, pass_rate.round(4).tolist())),
        "free_votes": free,
        "n_free_votes": len(free),
        "gate_pass_rates": gates,
        "switch_off_condition_rate_post_calibration": float(np.mean(off_met)) if off_met else float("nan"),
        "active_fraction": len(active_rows) / max(1, len(rows)),
        "persistence_equals_hysteresis": (first is not None and rec["ghost_steps"] == T - first + di),
        "gain_at_first_event": float(gain[first - 1]) if first else None,
        "gain_cap_reached_step": cap_hit,
        "gain_start": float(gain[0]),
        "gain_end": float(gain[-1]),
        "activity_mean": float(np.mean(np.abs(rec["X"]))),
        "homeostatic_target": 0.31,
    }


# ---------------------------------------------------------------------------
# v3 metric methods as pure functions of a recorded window
# ---------------------------------------------------------------------------

_ORDER = v3.GhostMachineV3.MODULE_ORDER


def _module_means(X: np.ndarray, slices: Dict) -> np.ndarray:
    return np.stack([X[:, slices[n][0]:slices[n][1]].mean(axis=1) for n in _ORDER], axis=1)


def v3_window_metrics(Xw: np.ndarray, slices: Dict, W: np.ndarray, gains: np.ndarray,
                      base_rho: float) -> Dict[str, float]:
    """
    Evaluate v3's own metric methods on a 257-step state window `Xw`, with the
    same history lengths the online v3 machine keeps (activity 128, modules 256,
    256 thalamocortical increments, which need one extra preceding state).
    """
    M = _module_means(Xw[-256:], slices)
    sync = [v3.clip01(1.0 - float(np.std(mm)) / (0.45 + float(np.mean(np.abs(mm))))) for mm in M]
    tc = []
    th = slices["thalamus"]
    cx = np.r_[np.arange(*slices["sensory"]), np.arange(*slices["workspace"])]
    for t in range(len(Xw) - 256, len(Xw)):
        cur, prev = Xw[t], Xw[t - 1]
        tc.append((float(np.mean(cur[th[0]:th[1]])), float(np.mean(np.abs(cur[cx] - prev[cx]))),
                   float(np.mean(cur[cx])), float(np.mean(np.abs(cur[th[0]:th[1]] - prev[th[0]:th[1]])))))
    ns = SimpleNamespace(
        MODULE_ORDER=_ORDER,
        activity_history=deque(list(Xw[-128:]), maxlen=128),
        module_history=deque(list(M), maxlen=256),
        sync_history=deque(sync, maxlen=256),
        tc_history=deque(tc, maxlen=256),
        state=Xw[-1].astype(float),
        W=W,
    )
    G = v3.GhostMachineV3
    integ, seg, topo = G._functional_topology(ns)
    aval, branching = G._avalanche_metrics(ns)
    dim, geom = G._geometry(ns)
    # v3's local-Jacobian edge-of-chaos estimate (median over the 128-step history).
    lam = []
    for x, g in zip(Xw[-128:], gains[-128:]):
        deriv = float(np.mean(1.0 - np.clip(x, -0.999, 0.999) ** 2))
        lam.append(float(np.clip(math.log(max(1e-8, g * base_rho * deriv)), -3.0, 3.0)))
    crit = v3.clip01(math.exp(-abs(float(np.median(lam))) / 0.32))
    return {
        "topology_balance": topo,
        "functional_integration": integ,
        "functional_segregation": seg,
        "avalanche_criticality": aval,
        "multiscale_entropy": G._multiscale_entropy(ns),
        "geometry_score": geom,
        "intrinsic_dimensionality": dim,
        "mesocircuit_flow": G._mesocircuit_flow(ns),
        "lz_complexity": G._lz_metric(ns),
        "synergy": G._synergy_proxy(ns),
        "memory_integration": G._memory_integration(ns),
        "metastability": G._metastability(ns),
        "thalamocortical_transfer": G._thalamocortical_transfer(ns),
        "ei_balance": G._ei_balance(ns),
        "criticality": crit,
    }


V3_METRIC_KIND = {
    # What each v3 metric reads, derived from its code (see docs and paper):
    "topology_balance": "zero-lag", "functional_integration": "zero-lag", "functional_segregation": "zero-lag",
    "geometry_score": "zero-lag", "intrinsic_dimensionality": "zero-lag", "ei_balance": "instantaneous",
    "criticality": "zero-lag", "avalanche_criticality": "lagged", "multiscale_entropy": "univariate-temporal",
    "lz_complexity": "temporal", "mesocircuit_flow": "lagged-linear", "synergy": "lagged-linear",
    "memory_integration": "lagged", "metastability": "zero-lag", "thalamocortical_transfer": "lagged-linear",
}
