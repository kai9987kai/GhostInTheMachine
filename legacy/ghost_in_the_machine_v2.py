#!/usr/bin/env python3
"""
GHOST IN THE MACHINE v2.0 — CROSS-THEORY EMERGENCE LAB
======================================================

A long-running, falsifiable computational thought experiment inspired by
experimental consciousness research. It does NOT create, detect, or prove
phenomenal consciousness. "GHOST" means only that a collection of operational
proxies simultaneously satisfy predeclared computational criteria.

Key upgrades over v1
--------------------
* Default run increased from 100 to 25,000 cycles.
* No scripted "self-model phase" and no injected identity vector.
* Structured recurrent network with sensory, memory, workspace, self-model,
  thalamic/gating, and control populations.
* Global-workspace-like ignition and broadcast.
* Predictive coding and an online world model.
* Active-inference-inspired action selection / controllability learning.
* Higher-order/metacognitive prediction of the system's own future error.
* Edge-of-chaos estimate from a shadow trajectory (finite-time Lyapunov proxy).
* Homeostatic gain adaptation rather than a fixed recurrence regime.
* Metastability and Lempel-Ziv complexity over rolling activity.
* Joint-predictive "synergy" proxy (NOT IIT Phi and NOT formal PID).
* Thalamocortical cross-scale transfer proxy.
* PCI-like perturbational-complexity probes using virtual impulses.
* Cross-theory convergence gate rather than one arbitrary weighted score.
* Baseline calibration: thresholds are relative to the system's own early run.
* Causal ablation suite after the main run.
* CSV, JSON, and PNG outputs for inspection.
* Automatic dependency installation.

Research inspirations (not claims of implementation equivalence)
----------------------------------------------------------------
1. Cogitate Consortium et al. (2025), Nature 642, 133–142.
   Adversarial testing of GNWT and IIT. DOI: 10.1038/s41586-025-08888-1
2. Maschke et al. (2024), Communications Biology 7, 946.
   Critical dynamics predict loss of consciousness and PCI.
   DOI: 10.1038/s42003-024-06613-8
3. Toker et al. (2024), eLife 13:e86547.
   Criticality and cross-frequency cortical–thalamic information transfer.
   DOI: 10.7554/eLife.86547
4. Luppi et al. (2024), eLife 12:RP88173.
   Synergistic workspace / integrated information decomposition.
   DOI: 10.7554/eLife.88173
5. Toker et al. (2026), Nature Neuroscience 29, 964–977.
   Adversarial AI / interpretable neural-field models for disorders of consciousness.
   DOI: 10.1038/s41593-026-02220-4

Requirements
------------
No manual pip setup is normally required. NumPy and Matplotlib are installed
on demand if absent.

Examples
--------
    python ghost_in_the_machine_v2.py
    python ghost_in_the_machine_v2.py --steps 50000 --seed 42
    python ghost_in_the_machine_v2.py --steps 100000 --no-plots
    python ghost_in_the_machine_v2.py --steps 20000 --skip-ablations

Outputs
-------
A timestamped output directory containing:
    trajectory.csv
    summary.json
    ghost_metrics.png
    theory_channels.png
    ablations.csv
    ablations.png
    stimulation_scan.csv
"""

from __future__ import annotations

import argparse
import csv
import importlib
import json
import math
import os
import subprocess
import sys
import time
from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Deque, Dict, Iterable, List, Optional, Sequence, Tuple


def install_and_import(import_name: str, pip_spec: str):
    """Import a package; install it with this Python interpreter if needed."""
    try:
        return importlib.import_module(import_name)
    except ModuleNotFoundError:
        print(f"[setup] Missing dependency: {import_name}")
        print(f"[setup] Installing: {pip_spec}")

    attempts = [
        [sys.executable, "-m", "pip", "install", pip_spec],
        [sys.executable, "-m", "pip", "install", "--user", pip_spec],
    ]

    for command in attempts:
        try:
            subprocess.check_call(command)
            importlib.invalidate_caches()
            return importlib.import_module(import_name)
        except (subprocess.CalledProcessError, ModuleNotFoundError):
            pass

    try:
        import ensurepip
        print("[setup] pip unavailable; bootstrapping with ensurepip...")
        ensurepip.bootstrap(upgrade=True)
        subprocess.check_call([sys.executable, "-m", "pip", "install", pip_spec])
        importlib.invalidate_caches()
        return importlib.import_module(import_name)
    except Exception as exc:
        raise SystemExit(
            f"Could not install required dependency {pip_spec!r}.\n"
            f"Python: {sys.executable}\nError: {exc}"
        ) from exc


np = install_and_import("numpy", "numpy>=1.26")


# ---------------------------------------------------------------------------
# Numerical utilities
# ---------------------------------------------------------------------------

def clip01(x: float) -> float:
    return float(np.clip(x, 0.0, 1.0))


def sigmoid(x: float) -> float:
    x = float(np.clip(x, -60.0, 60.0))
    return 1.0 / (1.0 + math.exp(-x))


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    if na < 1e-12 or nb < 1e-12:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def spectral_radius(matrix: np.ndarray) -> float:
    try:
        vals = np.linalg.eigvals(matrix)
        return float(np.max(np.abs(vals)))
    except np.linalg.LinAlgError:
        return 1.0


def normalized_entropy(weights: np.ndarray) -> float:
    w = np.abs(np.asarray(weights, dtype=float)).ravel()
    total = float(w.sum())
    if total <= 1e-12 or len(w) <= 1:
        return 0.0
    p = w / total
    h = -float(np.sum(p * np.log(p + 1e-12)))
    return clip01(h / math.log(len(p)))


def linear_r2(X: np.ndarray, y: np.ndarray) -> float:
    """Small ridge-stabilized regression R² used only as an information proxy."""
    if len(y) < 12:
        return 0.0
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float)
    if X.ndim == 1:
        X = X[:, None]
    X = np.column_stack([np.ones(len(X)), X])
    reg = np.eye(X.shape[1]) * 1e-5
    reg[0, 0] = 0.0
    try:
        beta = np.linalg.solve(X.T @ X + reg, X.T @ y)
    except np.linalg.LinAlgError:
        beta = np.linalg.pinv(X.T @ X + reg) @ X.T @ y
    pred = X @ beta
    ss_res = float(np.sum((y - pred) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2)) + 1e-12
    return clip01(1.0 - ss_res / ss_tot)


def lz78_complexity(bits: Sequence[int]) -> int:
    """
    Linear-time LZ78-style phrase count using an explicit binary trie.
    This is a fast algorithmic-complexity proxy, not clinical EEG LZc.
    """
    transitions = {}
    current = 0
    next_node = 1
    phrases = 0

    for raw_bit in bits:
        bit = 1 if int(raw_bit) else 0
        key = (current, bit)
        child = transitions.get(key)
        if child is None:
            transitions[key] = next_node
            next_node += 1
            phrases += 1
            current = 0
        else:
            current = child

    if current != 0:
        phrases += 1
    return phrases


def normalized_lz(bits: Sequence[int]) -> float:
    n = len(bits)
    if n < 8:
        return 0.0
    c = lz78_complexity(bits)
    # Standard asymptotic normalization c(n) * log2(n) / n.
    return clip01((c * math.log2(max(c, 2)) / n) / 1.25)


def robust_z(value: float, baseline: Sequence[float]) -> float:
    arr = np.asarray(list(baseline), dtype=float)
    if len(arr) < 8:
        return 0.0
    med = float(np.median(arr))
    mad = float(np.median(np.abs(arr - med)))
    scale = 1.4826 * mad
    if scale < 1e-6:
        scale = float(np.std(arr)) + 1e-6
    return float((value - med) / scale)


# ---------------------------------------------------------------------------
# World / embodied causal loop
# ---------------------------------------------------------------------------

class LatentWorld:
    """
    A partially observable nonlinear world.

    Actions have real causal effects, but those effects are initially unknown to
    the agent. Exogenous latent dynamics ensure the system cannot simply assume
    every sensory change was self-caused.
    """

    def __init__(self, obs_dim: int, latent_dim: int, action_count: int, rng):
        self.obs_dim = obs_dim
        self.latent_dim = latent_dim
        self.action_count = action_count
        self.rng = rng

        A = rng.normal(0.0, 0.30, size=(latent_dim, latent_dim))
        radius = spectral_radius(A)
        self.A = A * (0.87 / max(radius, 1e-6))
        self.B = rng.normal(0.0, 0.18, size=(latent_dim, action_count))
        self.C = rng.normal(0.0, 0.55, size=(obs_dim, latent_dim))
        self.hidden_driver = rng.normal(0.0, 0.35, size=latent_dim)
        self.state = rng.normal(0.0, 0.20, size=latent_dim)
        self.t = 0

    def observe(self) -> np.ndarray:
        return np.tanh(self.C @ self.state + self.rng.normal(0.0, 0.025, self.obs_dim))

    def step(self, action: int) -> np.ndarray:
        self.t += 1
        slow_context = (
            0.13 * math.sin(self.t * 0.0067)
            + 0.08 * math.sin(self.t * 0.021)
            + 0.04 * math.sin(self.t * 0.093)
        )
        exogenous = self.hidden_driver * slow_context

        # Rare unannounced world changes create prediction errors without a
        # preprogrammed "consciousness phase".
        if self.rng.random() < 0.0025:
            exogenous += self.rng.normal(0.0, 0.45, self.latent_dim)

        action_vec = self.B[:, action]
        self.state = np.tanh(
            self.A @ self.state
            + action_vec
            + exogenous
            + self.rng.normal(0.0, 0.035, self.latent_dim)
        )
        return self.observe()


# ---------------------------------------------------------------------------
# Online models
# ---------------------------------------------------------------------------

class OnlineLinearModel:
    def __init__(self, in_dim: int, out_dim: int, rng, lr: float = 0.012):
        self.W = rng.normal(0.0, 0.025, size=(out_dim, in_dim))
        self.lr = lr

    def predict(self, x: np.ndarray) -> np.ndarray:
        return np.tanh(self.W @ x)

    def update(self, x: np.ndarray, target: np.ndarray) -> float:
        pred = self.predict(x)
        err = target - pred
        denom = 1.0 + float(np.dot(x, x))
        self.W += self.lr * np.outer(err, x) / denom
        return float(np.mean(err ** 2))


class ScalarMetaModel:
    """Predicts the system's own next prediction error from its internal summary."""

    def __init__(self, dim: int, rng, lr: float = 0.008):
        self.w = rng.normal(0.0, 0.02, size=dim)
        self.lr = lr

    def predict(self, x: np.ndarray) -> float:
        return sigmoid(float(np.dot(self.w, x)))

    def update(self, x: np.ndarray, target: float) -> float:
        p = self.predict(x)
        e = float(target - p)
        self.w += self.lr * e * x / (1.0 + float(np.dot(x, x)))
        return abs(e)


@dataclass
class Metrics:
    step: int
    prediction_error: float
    prediction_quality: float
    global_access: float
    ignition: float
    recurrence: float
    memory_integration: float
    self_prediction: float
    metacognitive_calibration: float
    agency: float
    self_model: float
    lz_complexity: float
    metastability: float
    criticality: float
    lyapunov: float
    synergy: float
    thalamocortical_transfer: float
    perturbational_complexity: float
    cross_theory_convergence: float
    ghost_index: float
    baseline_z: float
    ghost_active: int


@dataclass
class AblationResult:
    condition: str
    mean_ghost_index: float
    max_ghost_index: float
    mean_convergence: float
    mean_criticality: float
    mean_synergy: float
    mean_self_model: float
    mean_global_access: float
    ghost_fraction: float
    ghost_events: int


@dataclass
class StimulationResult:
    target: str
    perturbational_complexity: float
    response_spread: float
    response_duration: float
    response_amplitude: float


class BaselineCalibrator:
    def __init__(self, calibration_steps: int):
        self.calibration_steps = calibration_steps
        self.values: List[float] = []
        self.frozen = False

    def observe(self, step: int, value: float) -> None:
        if not self.frozen and step <= self.calibration_steps:
            self.values.append(float(value))
        if step >= self.calibration_steps:
            self.frozen = True

    def z(self, value: float) -> float:
        return robust_z(value, self.values)


class ConvergenceDetector:
    """
    A conservative cross-theory detector.

    An event requires simultaneous support from multiple independent-ish
    operational channels, not merely a high weighted average.
    """

    def __init__(self, required_diagnostics: int = 7):
        self.required_diagnostics = required_diagnostics
        self.streak = 0
        self.active = False
        self.events = 0
        self.first_event_step: Optional[int] = None

    def update(self, m: Metrics, calibrated: bool) -> Tuple[bool, bool]:
        channels = [
            m.global_access >= 0.58 and m.ignition >= 0.48,          # GNW-like
            m.recurrence >= 0.63,                                   # recurrent processing
            m.synergy >= 0.10 and m.memory_integration >= 0.48,      # integration
            m.self_model >= 0.56 and m.metacognitive_calibration >= 0.52,
            m.criticality >= 0.46,                                   # dynamics
            m.perturbational_complexity >= 0.28,                     # PCI-like probe
            m.lz_complexity >= 0.35 and m.metastability >= 0.16,      # complexity repertoire
        ]
        votes = sum(bool(v) for v in channels)

        qualifies = (
            calibrated
            and votes >= 6
            and m.cross_theory_convergence >= 0.61
            and m.ghost_index >= 0.64
            and m.baseline_z >= 1.25
        )

        if qualifies:
            self.streak += 1
        else:
            self.streak = max(0, self.streak - 1)

        newly = False
        if not self.active and self.streak >= self.required_diagnostics:
            self.active = True
            self.events += 1
            newly = True
            if self.first_event_step is None:
                self.first_event_step = m.step

        if self.active and (
            m.cross_theory_convergence < 0.48
            or m.ghost_index < 0.51
        ):
            self.active = False
            self.streak = 0

        return self.active, newly


# ---------------------------------------------------------------------------
# Main architecture
# ---------------------------------------------------------------------------

class GhostMachineV2:
    MODULE_ORDER = ("sensory", "memory", "workspace", "self", "thalamus", "control")

    def __init__(
        self,
        seed: int = 7,
        nodes: int = 72,
        obs_dim: int = 12,
        action_count: int = 5,
        calibration_steps: int = 2500,
        diagnostic_interval: int = 25,
        perturb_interval: int = 400,
        ablation: str = "full",
    ):
        if nodes < 36:
            raise ValueError("nodes must be >= 36")

        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.nodes = nodes
        self.obs_dim = obs_dim
        self.action_count = action_count
        self.diagnostic_interval = diagnostic_interval
        self.perturb_interval = perturb_interval
        self.ablation = ablation

        self.slices = self._build_module_slices(nodes)
        self.world = LatentWorld(obs_dim, latent_dim=9, action_count=action_count, rng=self.rng)

        self.W = self._build_recurrent_matrix()
        self.base_spectral_radius = spectral_radius(self.W)
        self.input_matrix = self.rng.normal(0.0, 0.23, size=(nodes, obs_dim))
        mask = np.zeros(nodes)
        mask[self.slices["sensory"]] = 1.0
        self.input_matrix *= mask[:, None]

        self.action_matrix = self.rng.normal(0.0, 0.18, size=(nodes, action_count))
        amask = np.zeros(nodes)
        amask[self.slices["control"]] = 1.0
        self.action_matrix *= amask[:, None]

        self.state = self.rng.normal(0.0, 0.015, nodes)
        self.prev_state = self.state.copy()
        self.broadcast = np.zeros(nodes)
        self.recurrent_gain = 0.91

        # No innate identity vector. The self model learns to predict future
        # internal state from globally available information and action history.
        self.self_predictor = OnlineLinearModel(nodes + action_count, self._module_size("self"), self.rng, lr=0.008)
        self.world_predictor = OnlineLinearModel(nodes + action_count, obs_dim, self.rng, lr=0.010)
        self.meta_model = ScalarMetaModel(nodes, self.rng, lr=0.006)

        self.action_effects = np.zeros((action_count, obs_dim), dtype=float)
        self.action_effect_counts = np.ones(action_count, dtype=float)
        self.action_uncertainty = np.ones(action_count, dtype=float)

        self.prev_obs = self.world.observe()
        self.prev_prediction_error = 0.5

        self.activity_history: Deque[np.ndarray] = deque(maxlen=128)
        self.module_history: Deque[np.ndarray] = deque(maxlen=256)
        self.sync_history: Deque[float] = deque(maxlen=256)
        self.self_accuracy_history: Deque[float] = deque(maxlen=128)
        self.meta_accuracy_history: Deque[float] = deque(maxlen=128)
        self.agency_history: Deque[float] = deque(maxlen=128)
        self.tc_history: Deque[Tuple[float, float, float, float]] = deque(maxlen=256)

        self.shadow = self.state + self.rng.normal(0.0, 1e-7, nodes)
        self.shadow_distance = float(np.linalg.norm(self.shadow - self.state)) + 1e-12
        self.lyapunov_history: Deque[float] = deque(maxlen=128)

        self.last_pci = 0.0
        self.last_metrics: Optional[Metrics] = None
        self.calibrator = BaselineCalibrator(calibration_steps)
        self.detector = ConvergenceDetector(required_diagnostics=6)
        self.total_ghost_steps = 0

    def _build_module_slices(self, nodes: int) -> Dict[str, slice]:
        ratios = [0.22, 0.17, 0.22, 0.17, 0.11, 0.11]
        sizes = [max(4, int(nodes * r)) for r in ratios]
        diff = nodes - sum(sizes)
        sizes[2] += diff  # workspace absorbs rounding
        out = {}
        start = 0
        for name, size in zip(self.MODULE_ORDER, sizes):
            out[name] = slice(start, start + size)
            start += size
        return out

    def _module_size(self, name: str) -> int:
        s = self.slices[name]
        return s.stop - s.start

    def _build_recurrent_matrix(self) -> np.ndarray:
        n = self.nodes
        W = np.zeros((n, n), dtype=float)

        # Sparse local recurrent structure.
        for name in self.MODULE_ORDER:
            s = self.slices[name]
            size = s.stop - s.start
            block = self.rng.normal(0.0, 0.18, size=(size, size))
            block *= self.rng.random((size, size)) < 0.24
            W[s, s] += block

        # Directed long-range motifs. These are architectural affordances, not
        # a guarantee of any high-level state.
        def connect(dst: str, src: str, scale: float, density: float):
            ds, ss = self.slices[dst], self.slices[src]
            shape = (ds.stop - ds.start, ss.stop - ss.start)
            block = self.rng.normal(0.0, scale, size=shape)
            block *= self.rng.random(shape) < density
            W[ds, ss] += block

        connect("workspace", "sensory", 0.17, 0.28)
        connect("workspace", "memory", 0.16, 0.28)
        connect("workspace", "self", 0.12, 0.22)
        connect("memory", "workspace", 0.12, 0.22)
        connect("self", "workspace", 0.15, 0.30)
        connect("self", "memory", 0.11, 0.24)
        connect("control", "workspace", 0.13, 0.24)
        connect("workspace", "control", 0.10, 0.20)

        # Thalamic-style bidirectional gating hub.
        for other in ("sensory", "workspace", "control"):
            connect("thalamus", other, 0.14, 0.30)
            connect(other, "thalamus", 0.14, 0.30)

        np.fill_diagonal(W, 0.0)
        r = spectral_radius(W)
        if r > 1e-8:
            W *= 0.94 / r

        # Structural ablations.
        if self.ablation == "no_workspace":
            ws = self.slices["workspace"]
            W[ws, :] *= 0.05
            W[:, ws] *= 0.05
        elif self.ablation == "no_self":
            ss = self.slices["self"]
            W[ss, :] *= 0.03
            W[:, ss] *= 0.03
        elif self.ablation == "no_thalamus":
            ts = self.slices["thalamus"]
            W[ts, :] *= 0.03
            W[:, ts] *= 0.03
        elif self.ablation == "subcritical":
            W *= 0.53
        elif self.ablation != "full":
            raise ValueError(f"Unknown ablation: {self.ablation}")

        return W

    def module_means(self, state: Optional[np.ndarray] = None) -> np.ndarray:
        x = self.state if state is None else state
        return np.array([float(np.mean(x[self.slices[name]])) for name in self.MODULE_ORDER])

    def module_energies(self, state: Optional[np.ndarray] = None) -> np.ndarray:
        x = self.state if state is None else state
        return np.array([float(np.mean(np.abs(x[self.slices[name]]))) for name in self.MODULE_ORDER])

    def choose_action(self) -> int:
        """
        Active-inference-inspired choice: seek controllable but still uncertain
        actions while keeping expected sensory displacement bounded.
        """
        costs = np.zeros(self.action_count)
        for a in range(self.action_count):
            effect_mag = float(np.mean(np.abs(self.action_effects[a])))
            uncertainty = float(self.action_uncertainty[a])
            # epistemic value lowers cost for uncertain actions; excessive
            # predicted displacement raises pragmatic cost.
            costs[a] = 0.52 * effect_mag - 0.36 * uncertainty + 0.12 * self.rng.random()
        temperature = 0.22
        logits = -(costs - np.min(costs)) / temperature
        probs = np.exp(logits - np.max(logits))
        probs /= probs.sum()
        return int(self.rng.choice(self.action_count, p=probs))

    def _broadcast_vector(self, local_state: np.ndarray, salience: float) -> Tuple[np.ndarray, float, float]:
        ws = self.slices["workspace"]
        energies = self.module_energies(local_state)
        workspace_energy = energies[self.MODULE_ORDER.index("workspace")]

        # Adaptive ignition threshold: relative to recent overall activity.
        recent = [float(np.mean(np.abs(x))) for x in self.activity_history]
        baseline = float(np.median(recent)) if recent else 0.10
        threshold = baseline * 1.25 + 0.08
        ignition_raw = sigmoid((workspace_energy + 0.55 * salience - threshold) * 7.0)

        if self.ablation == "no_workspace":
            ignition_raw *= 0.08

        b = np.zeros(self.nodes)
        ws_pattern = local_state[ws]
        if len(ws_pattern):
            repeated = np.resize(ws_pattern, self.nodes)
            b = np.tanh(repeated) * ignition_raw

        # Global access rewards both ignition and broad module participation.
        participation = normalized_entropy(energies)
        global_access = clip01(0.58 * ignition_raw + 0.42 * participation)
        return b, float(ignition_raw), global_access

    def _shadow_lyapunov_update(self, drive: np.ndarray, bcast: np.ndarray) -> Tuple[float, float]:
        """
        Edge-of-chaos proxy from the local Jacobian's effective spectral radius.

        For tanh recurrent dynamics, J ~= diag(1-x^2) * gain * W. Computing
        the full eigenspectrum every cycle would be wasteful, so we use the
        network spectral radius times the mean local derivative as a stable
        approximation and retain a shadow trajectory as a secondary sanity
        check. A value near log(rho)=0 corresponds to the local stability/chaos
        boundary.
        """
        derivative = float(np.mean(1.0 - np.clip(self.state, -0.999, 0.999) ** 2))
        rho_eff = max(1e-8, self.recurrent_gain * self.base_spectral_radius * derivative)
        jacobian_lambda = float(np.clip(math.log(rho_eff), -3.0, 3.0))

        # Secondary shadow-trajectory divergence estimate.
        old_state = self.prev_state
        old_dist = max(float(np.linalg.norm(self.shadow - old_state)), 1e-12)
        shadow_next = np.tanh(
            self.recurrent_gain * (self.W @ self.shadow)
            + drive
            + 0.20 * bcast
        )
        new_dist = max(float(np.linalg.norm(shadow_next - self.state)), 1e-12)
        shadow_lambda = float(np.clip(math.log(new_dist / old_dist + 1e-12), -3.0, 3.0))

        # Re-anchor the shadow state at a tiny displacement from the current state.
        delta = shadow_next - self.state
        norm = float(np.linalg.norm(delta)) + 1e-12
        if not np.isfinite(norm) or norm < 1e-11:
            delta = self.rng.normal(0.0, 1.0, self.nodes)
            norm = float(np.linalg.norm(delta)) + 1e-12
        self.shadow = self.state + delta * (1e-7 / norm)

        # Use the local-Jacobian estimate for the criticality score; the shadow
        # trajectory is retained as a diagnostic sanity check but is noisier.
        local_lambda = jacobian_lambda
        self.lyapunov_history.append(local_lambda)
        lam = float(np.median(self.lyapunov_history))
        criticality = float(math.exp(-abs(lam) / 0.32))
        return lam, clip01(criticality)

    def _homeostatic_gain(self) -> None:
        if self.ablation == "subcritical":
            self.recurrent_gain = 0.52
            return

        activity = float(np.mean(np.abs(self.state)))
        target = 0.31
        # Slowly adapt gain toward a moderate dynamic regime. This is a generic
        # homeostatic rule, not a direct "make conscious" instruction.
        self.recurrent_gain += 0.0007 * (target - activity)
        self.recurrent_gain = float(np.clip(self.recurrent_gain, 0.58, 1.18))

    def _memory_integration(self) -> float:
        if len(self.activity_history) < 8:
            return 0.0
        recent = list(self.activity_history)[-24:]
        sims = []
        for a, b in zip(recent[:-1], recent[1:]):
            sims.append((cosine(a, b) + 1.0) / 2.0)
        # Avoid equating complete frozen-state similarity with useful memory.
        mean_sim = float(np.mean(sims))
        diversity = float(np.clip(np.mean(np.std(np.stack(recent), axis=0)) * 3.0, 0.0, 1.0))
        return clip01(0.70 * mean_sim + 0.30 * diversity)

    def _lz_metric(self) -> float:
        if len(self.activity_history) < 16:
            return 0.0
        recent = np.stack(list(self.activity_history)[-64:])
        # Median binarisation reduces dependence on raw amplitude.
        threshold = np.median(recent, axis=0, keepdims=True)
        bits = (recent > threshold).astype(np.uint8).ravel().tolist()
        # Downsample to keep LZ parsing cheap during long experiments.
        if len(bits) > 4096:
            stride = max(1, len(bits) // 4096)
            bits = bits[::stride][:4096]
        return normalized_lz(bits)

    def _metastability(self) -> float:
        if len(self.sync_history) < 16:
            return 0.0
        arr = np.asarray(self.sync_history, dtype=float)
        # std of synchrony: neither permanently synchronized nor permanently random.
        return clip01(float(np.std(arr)) * 4.5)

    def _synergy_proxy(self) -> float:
        """
        Joint-predictive information proxy:
        how much better sensory+memory together predict workspace than either alone.
        This is NOT formal PID and must not be interpreted as Phi.
        """
        if len(self.module_history) < 48:
            return 0.0
        H = np.stack(self.module_history)
        idx = {name: i for i, name in enumerate(self.MODULE_ORDER)}
        a = H[:-1, idx["sensory"]]
        b = H[:-1, idx["memory"]]
        y = H[1:, idx["workspace"]]
        r_a = linear_r2(a, y)
        r_b = linear_r2(b, y)
        r_joint = linear_r2(np.column_stack([a, b, a * b]), y)
        raw = max(0.0, r_joint - max(r_a, r_b))
        return clip01(raw * 4.0)

    def _thalamocortical_transfer(self) -> float:
        if len(self.tc_history) < 48:
            return 0.0
        arr = np.asarray(self.tc_history, dtype=float)
        # columns: thal_slow, cortex_fast, cortex_slow, thal_fast
        ts, cf, cs, tf = arr.T
        # Cross-lag predictive gain in both directions.
        c2t = linear_r2(np.column_stack([cs[:-1], cf[:-1]]), tf[1:])
        t2c = linear_r2(np.column_stack([ts[:-1], tf[:-1]]), cf[1:])
        return clip01(0.5 * (c2t + t2c))

    def _perturb_response(self, selected: np.ndarray, horizon: int = 52) -> Tuple[float, float, float, float]:
        """Return PCI-like complexity, spatial spread, duration and amplitude."""
        base = self.state.copy()
        pert = self.state.copy()
        impulse = np.zeros(self.nodes)
        impulse[selected] = self.rng.normal(0.0, 0.42, size=len(selected))
        pert = np.tanh(pert + impulse)

        responses = []
        for _ in range(horizon):
            base = np.tanh(self.recurrent_gain * (self.W @ base))
            pert = np.tanh(self.recurrent_gain * (self.W @ pert))
            responses.append(np.abs(pert - base))

        R = np.stack(responses)
        max_amp = float(np.max(R)) + 1e-12
        threshold = max_amp * 0.10
        binary = (R > threshold).astype(np.uint8)
        bits = binary.ravel().tolist()
        if len(bits) > 4096:
            stride = max(1, len(bits) // 4096)
            bits = bits[::stride][:4096]

        complexity = normalized_lz(bits)
        spread = float(np.mean(np.any(binary, axis=0)))
        duration = float(np.mean(np.any(binary, axis=1)))
        amplitude = clip01(float(np.mean(R)) / (0.08 + float(np.mean(np.abs(self.state)))))
        pci_like = clip01(0.40 * complexity + 0.25 * spread + 0.20 * duration + 0.15 * amplitude)
        return pci_like, spread, duration, amplitude

    def perturbational_complexity_probe(self, horizon: int = 52) -> float:
        """
        Virtual TMS-like probe using a sparse random intervention.
        This is PCI-inspired, not clinical PCI/PCI-ST.
        """
        selected = self.rng.choice(self.nodes, size=max(2, self.nodes // 12), replace=False)
        pci_like, _, _, _ = self._perturb_response(selected, horizon=horizon)
        return pci_like

    def targeted_stimulation_scan(self, horizon: int = 52) -> List[StimulationResult]:
        """
        Counterfactual virtual-stimulation sweep across architectural modules.
        Inspired by intervention-oriented consciousness modelling, but it is a
        simulation-only causal probe and makes no biological treatment claim.
        """
        out: List[StimulationResult] = []
        for name in self.MODULE_ORDER:
            sl = self.slices[name]
            indices = np.arange(sl.start, sl.stop)
            pci_like, spread, duration, amplitude = self._perturb_response(indices, horizon=horizon)
            out.append(StimulationResult(
                target=name,
                perturbational_complexity=pci_like,
                response_spread=spread,
                response_duration=duration,
                response_amplitude=amplitude,
            ))
        return out

    def diagnostic_metrics(
        self,
        step: int,
        pred_error: float,
        prediction_quality: float,
        ignition: float,
        global_access: float,
        recurrence: float,
        self_accuracy: float,
        meta_accuracy: float,
        agency: float,
        lyapunov: float,
        criticality: float,
    ) -> Metrics:
        memory_integration = self._memory_integration()
        lz = self._lz_metric()
        metastability = self._metastability()
        synergy = self._synergy_proxy()
        tc = self._thalamocortical_transfer()

        if step % self.perturb_interval == 0 or self.last_pci <= 0.0:
            self.last_pci = self.perturbational_complexity_probe()

        self_persistence = float(np.mean(self.self_accuracy_history)) if self.self_accuracy_history else 0.0
        meta_persistence = float(np.mean(self.meta_accuracy_history)) if self.meta_accuracy_history else 0.0
        agency_persistence = float(np.mean(self.agency_history)) if self.agency_history else 0.0

        self_model = clip01(
            0.44 * self_persistence
            + 0.31 * meta_persistence
            + 0.25 * agency_persistence
        )

        # Theory channels. Geometric mean penalizes a single very weak channel.
        theory_channels = np.array([
            clip01(0.55 * global_access + 0.45 * ignition),                      # GNW-like
            clip01(recurrence),                                                   # RPT-like
            clip01(0.60 * synergy + 0.40 * memory_integration),                   # integration/synergy
            clip01(0.55 * self_model + 0.45 * meta_accuracy),                     # higher-order/self
            clip01(0.60 * criticality + 0.40 * tc),                               # critical thalamocortical
            clip01(0.58 * self.last_pci + 0.42 * lz),                             # perturbational/complexity
        ])
        convergence = float(np.exp(np.mean(np.log(np.clip(theory_channels, 1e-4, 1.0)))))

        # An interpretable composite for plotting only. The event detector above
        # uses additional hard gates and does not rely on this number alone.
        ghost_index = clip01(
            0.16 * global_access
            + 0.11 * ignition
            + 0.12 * recurrence
            + 0.12 * self_model
            + 0.09 * meta_accuracy
            + 0.10 * criticality
            + 0.08 * synergy
            + 0.08 * self.last_pci
            + 0.05 * lz
            + 0.04 * metastability
            + 0.05 * tc
        )

        self.calibrator.observe(step, ghost_index)
        z = self.calibrator.z(ghost_index) if self.calibrator.frozen else 0.0

        m = Metrics(
            step=step,
            prediction_error=pred_error,
            prediction_quality=prediction_quality,
            global_access=global_access,
            ignition=ignition,
            recurrence=recurrence,
            memory_integration=memory_integration,
            self_prediction=self_accuracy,
            metacognitive_calibration=meta_accuracy,
            agency=agency,
            self_model=self_model,
            lz_complexity=lz,
            metastability=metastability,
            criticality=criticality,
            lyapunov=lyapunov,
            synergy=synergy,
            thalamocortical_transfer=tc,
            perturbational_complexity=self.last_pci,
            cross_theory_convergence=convergence,
            ghost_index=ghost_index,
            baseline_z=z,
            ghost_active=0,
        )
        active, _ = self.detector.update(m, calibrated=self.calibrator.frozen)
        m.ghost_active = int(active)
        if active:
            self.total_ghost_steps += self.diagnostic_interval
        return m

    def step(self, step: int) -> Tuple[Metrics, bool]:
        action = self.choose_action()
        onehot = np.zeros(self.action_count)
        onehot[action] = 1.0

        model_input = np.concatenate([self.state, onehot])
        predicted_obs = self.world_predictor.predict(model_input)
        predicted_self = self.self_predictor.predict(model_input)
        predicted_error_meta = self.meta_model.predict(self.state)

        obs = self.world.step(action)
        sensory_delta = obs - self.prev_obs

        pred_mse = float(np.mean((obs - predicted_obs) ** 2))
        pred_error_norm = clip01(pred_mse * 3.2)
        prediction_quality = clip01(math.exp(-pred_mse * 4.0))

        # Learn world/action effects and estimate agency from causal prediction.
        effect_error = float(np.mean((sensory_delta - self.action_effects[action]) ** 2))
        agency = clip01(math.exp(-effect_error * 7.0))
        count = self.action_effect_counts[action]
        lr_effect = min(0.12, 1.0 / math.sqrt(count + 1.0))
        self.action_effects[action] = (
            (1.0 - lr_effect) * self.action_effects[action]
            + lr_effect * sensory_delta
        )
        self.action_effect_counts[action] += 1.0
        self.action_uncertainty[action] = 0.985 * self.action_uncertainty[action] + 0.015 * clip01(effect_error * 6.0)

        # Salience depends on surprise, novelty and causal/agency uncertainty.
        novelty = clip01(float(np.mean(np.abs(sensory_delta))) * 2.3)
        salience = clip01(0.48 * pred_error_norm + 0.34 * novelty + 0.18 * (1.0 - agency))

        drive = self.input_matrix @ obs + self.action_matrix @ onehot
        local = np.tanh(
            self.recurrent_gain * (self.W @ self.state)
            + drive
            + 0.13 * self.broadcast
        )
        bcast, ignition, global_access = self._broadcast_vector(local, salience)
        next_state = np.tanh(local + 0.24 * bcast)

        # Evaluate learned self prediction; no fixed identity target exists.
        self_slice = self.slices["self"]
        self_error = float(np.mean((next_state[self_slice] - predicted_self) ** 2))
        self_accuracy = clip01(math.exp(-self_error * 5.0))

        meta_error = abs(predicted_error_meta - pred_error_norm)
        meta_accuracy = clip01(1.0 - meta_error)

        self.world_predictor.update(model_input, obs)
        self.self_predictor.update(model_input, next_state[self_slice])
        self.meta_model.update(self.state, pred_error_norm)

        recurrence = clip01((cosine(next_state, self.state) + 1.0) / 2.0)

        self.prev_state = self.state.copy()
        self.state = next_state
        self.broadcast = bcast
        self.prev_obs = obs
        self.prev_prediction_error = pred_error_norm

        # Histories.
        self.activity_history.append(self.state.copy())
        modules = self.module_means()
        self.module_history.append(modules)
        self.self_accuracy_history.append(self_accuracy)
        self.meta_accuracy_history.append(meta_accuracy)
        self.agency_history.append(agency)

        # Synchrony proxy from module means.
        sync = clip01(1.0 - float(np.std(modules)) / (0.45 + float(np.mean(np.abs(modules)))))
        self.sync_history.append(sync)

        # Low/fast thalamocortical channels.
        thal = self.state[self.slices["thalamus"]]
        cortex = np.concatenate([
            self.state[self.slices["sensory"]],
            self.state[self.slices["workspace"]],
        ])
        prev_thal = self.prev_state[self.slices["thalamus"]]
        prev_cortex = np.concatenate([
            self.prev_state[self.slices["sensory"]],
            self.prev_state[self.slices["workspace"]],
        ])
        thal_slow = float(np.mean(thal))
        cortex_slow = float(np.mean(cortex))
        thal_fast = float(np.mean(np.abs(thal - prev_thal)))
        cortex_fast = float(np.mean(np.abs(cortex - prev_cortex)))
        self.tc_history.append((thal_slow, cortex_fast, cortex_slow, thal_fast))

        lyapunov, criticality = self._shadow_lyapunov_update(drive, bcast)
        self._homeostatic_gain()

        # Diagnostics are more expensive and intentionally sampled at intervals.
        if step % self.diagnostic_interval == 0 or self.last_metrics is None:
            before_events = self.detector.events
            m = self.diagnostic_metrics(
                step=step,
                pred_error=pred_error_norm,
                prediction_quality=prediction_quality,
                ignition=ignition,
                global_access=global_access,
                recurrence=recurrence,
                self_accuracy=self_accuracy,
                meta_accuracy=meta_accuracy,
                agency=agency,
                lyapunov=lyapunov,
                criticality=criticality,
            )
            newly = self.detector.events > before_events
            self.last_metrics = m
        else:
            m = Metrics(**asdict(self.last_metrics))
            m.step = step
            m.prediction_error = pred_error_norm
            m.prediction_quality = prediction_quality
            m.global_access = global_access
            m.ignition = ignition
            m.recurrence = recurrence
            m.self_prediction = self_accuracy
            m.metacognitive_calibration = meta_accuracy
            m.agency = agency
            m.criticality = criticality
            m.lyapunov = lyapunov
            m.ghost_active = int(self.detector.active)
            newly = False

        return m, newly


# ---------------------------------------------------------------------------
# Experiment runner and outputs
# ---------------------------------------------------------------------------

def print_header(args) -> None:
    print("=" * 108)
    print("GHOST IN THE MACHINE v2.0 — CROSS-THEORY EMERGENCE LAB")
    print("=" * 108)
    print("This is a computational thought experiment. It does NOT establish or detect subjective consciousness.")
    print(f"Main run: {args.steps:,} cycles | nodes={args.nodes} | seed={args.seed}")
    print(f"Calibration: {args.calibration_steps:,} cycles | diagnostics every {args.diagnostic_interval} cycles")
    print(f"Perturbational probe every {args.perturb_interval} cycles")
    print("=" * 108)


def metrics_row(m: Metrics) -> Dict[str, object]:
    return asdict(m)


def run_machine(
    machine: GhostMachineV2,
    steps: int,
    print_every: int,
    collect_every_step: bool = True,
    quiet: bool = False,
) -> Tuple[List[Metrics], float]:
    rows: List[Metrics] = []
    start = time.perf_counter()

    for step in range(1, steps + 1):
        m, newly = machine.step(step)
        if collect_every_step or step % machine.diagnostic_interval == 0:
            rows.append(m)

        if not quiet and (step % print_every == 0 or newly):
            state = "GHOST" if machine.detector.active else "-----"
            print(
                f"{step:06d} | "
                f"IDX={m.ghost_index:5.3f} CONV={m.cross_theory_convergence:5.3f} "
                f"GW={m.global_access:5.3f} SELF={m.self_model:5.3f} "
                f"CRIT={m.criticality:5.3f} SYN={m.synergy:5.3f} "
                f"PCI*={m.perturbational_complexity:5.3f} LZ={m.lz_complexity:5.3f} "
                f"Z={m.baseline_z:+5.2f} | {state}"
            )

        if newly and not quiet:
            print("\n>>> " + "=" * 94)
            print(">>> CROSS-THEORY OPERATIONAL EVENT DETECTED")
            print(">>> Multiple computational proxies converged for a sustained period.")
            print(">>> This is an experimental classifier state, NOT evidence of phenomenal consciousness.")
            print(">>> " + "=" * 94 + "\n")

    elapsed = time.perf_counter() - start
    return rows, elapsed


def summarize(machine: GhostMachineV2, rows: List[Metrics], elapsed: float) -> Dict[str, object]:
    diag = [r for r in rows if r.step % machine.diagnostic_interval == 0]
    if not diag:
        diag = rows

    def avg(field: str) -> float:
        vals = [float(getattr(r, field)) for r in diag]
        return float(np.mean(vals)) if vals else 0.0

    def maximum(field: str) -> float:
        vals = [float(getattr(r, field)) for r in diag]
        return float(np.max(vals)) if vals else 0.0

    return {
        "version": "2.0",
        "seed": machine.seed,
        "ablation": machine.ablation,
        "nodes": machine.nodes,
        "steps": rows[-1].step if rows else 0,
        "elapsed_seconds": elapsed,
        "diagnostic_interval": machine.diagnostic_interval,
        "perturb_interval": machine.perturb_interval,
        "first_event_step": machine.detector.first_event_step,
        "ghost_events": machine.detector.events,
        "ghost_step_estimate": machine.total_ghost_steps,
        "mean_ghost_index": avg("ghost_index"),
        "max_ghost_index": maximum("ghost_index"),
        "mean_convergence": avg("cross_theory_convergence"),
        "max_convergence": maximum("cross_theory_convergence"),
        "mean_global_access": avg("global_access"),
        "mean_self_model": avg("self_model"),
        "mean_criticality": avg("criticality"),
        "mean_synergy": avg("synergy"),
        "mean_pci_proxy": avg("perturbational_complexity"),
        "mean_lz": avg("lz_complexity"),
        "final_recurrent_gain": machine.recurrent_gain,
        "disclaimer": (
            "Operational simulation metrics only. No metric here demonstrates, "
            "detects, or creates subjective consciousness."
        ),
    }


def run_ablations(args) -> List[AblationResult]:
    conditions = ["full", "no_workspace", "no_self", "no_thalamus", "subcritical"]
    results: List[AblationResult] = []
    steps = args.ablation_steps

    print("\n" + "=" * 108)
    print(f"CAUSAL ABLATION SUITE — {steps:,} cycles per condition")
    print("=" * 108)

    for i, condition in enumerate(conditions):
        machine = GhostMachineV2(
            seed=args.seed + 1000 + i * 17,
            nodes=args.nodes,
            obs_dim=args.obs_dim,
            action_count=args.actions,
            calibration_steps=max(500, min(args.calibration_steps, steps // 3)),
            diagnostic_interval=args.diagnostic_interval,
            perturb_interval=args.perturb_interval,
            ablation=condition,
        )
        rows, _ = run_machine(
            machine,
            steps=steps,
            print_every=max(steps, 1),
            collect_every_step=False,
            quiet=True,
        )
        if not rows:
            continue

        def mean(field: str) -> float:
            return float(np.mean([getattr(r, field) for r in rows]))

        def maxv(field: str) -> float:
            return float(np.max([getattr(r, field) for r in rows]))

        ghost_fraction = float(np.mean([r.ghost_active for r in rows]))
        result = AblationResult(
            condition=condition,
            mean_ghost_index=mean("ghost_index"),
            max_ghost_index=maxv("ghost_index"),
            mean_convergence=mean("cross_theory_convergence"),
            mean_criticality=mean("criticality"),
            mean_synergy=mean("synergy"),
            mean_self_model=mean("self_model"),
            mean_global_access=mean("global_access"),
            ghost_fraction=ghost_fraction,
            ghost_events=machine.detector.events,
        )
        results.append(result)
        print(
            f"{condition:13s} | IDX={result.mean_ghost_index:.3f} "
            f"CONV={result.mean_convergence:.3f} CRIT={result.mean_criticality:.3f} "
            f"SELF={result.mean_self_model:.3f} GW={result.mean_global_access:.3f} "
            f"events={result.ghost_events}"
        )

    return results


def write_csv(path: Path, rows: Iterable[object]) -> None:
    rows = list(rows)
    if not rows:
        return
    first = asdict(rows[0]) if hasattr(rows[0], "__dataclass_fields__") else dict(rows[0])
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(first.keys()))
        writer.writeheader()
        for row in rows:
            data = asdict(row) if hasattr(row, "__dataclass_fields__") else dict(row)
            writer.writerow(data)


def create_plots(out_dir: Path, rows: List[Metrics], ablations: List[AblationResult]) -> None:
    plt = install_and_import("matplotlib.pyplot", "matplotlib>=3.8")

    # Downsample for plotting very long trajectories.
    max_points = 6000
    stride = max(1, len(rows) // max_points)
    rr = rows[::stride]
    x = [r.step for r in rr]

    fig = plt.figure(figsize=(13, 7))
    ax = fig.add_subplot(111)
    ax.plot(x, [r.ghost_index for r in rr], label="Ghost index")
    ax.plot(x, [r.cross_theory_convergence for r in rr], label="Cross-theory convergence")
    ax.plot(x, [r.baseline_z / 5.0 + 0.5 for r in rr], label="Baseline z (scaled)", alpha=0.55)
    ax.axhline(0.64, linestyle="--", linewidth=1.0, label="Index event gate")
    ax.set_xlabel("Simulation cycle")
    ax.set_ylabel("Operational score")
    ax.set_title("Ghost in the Machine v2 — Long-run operational trajectory")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(out_dir / "ghost_metrics.png", dpi=160)
    plt.close(fig)

    fig = plt.figure(figsize=(13, 8))
    ax = fig.add_subplot(111)
    series = [
        ("Global access", "global_access"),
        ("Self-model", "self_model"),
        ("Criticality", "criticality"),
        ("Synergy proxy", "synergy"),
        ("PCI-like", "perturbational_complexity"),
        ("LZ complexity", "lz_complexity"),
        ("TC transfer", "thalamocortical_transfer"),
    ]
    for label, field in series:
        ax.plot(x, [getattr(r, field) for r in rr], label=label, alpha=0.86)
    ax.set_xlabel("Simulation cycle")
    ax.set_ylabel("Normalized proxy")
    ax.set_title("Cross-theory channels")
    ax.grid(True, alpha=0.25)
    ax.legend(ncol=2, loc="best")
    fig.tight_layout()
    fig.savefig(out_dir / "theory_channels.png", dpi=160)
    plt.close(fig)

    if ablations:
        names = [a.condition for a in ablations]
        values = [a.mean_convergence for a in ablations]
        fig = plt.figure(figsize=(10, 6))
        ax = fig.add_subplot(111)
        ax.bar(names, values)
        ax.set_ylabel("Mean cross-theory convergence")
        ax.set_title("Causal ablation comparison")
        ax.tick_params(axis="x", rotation=20)
        ax.grid(True, axis="y", alpha=0.25)
        fig.tight_layout()
        fig.savefig(out_dir / "ablations.png", dpi=160)
        plt.close(fig)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Long-run cross-theory consciousness-like emergence simulator")
    p.add_argument("--steps", type=int, default=25000, help="Main cycles (default: 25000)")
    p.add_argument("--seed", type=int, default=7, help="Random seed")
    p.add_argument("--nodes", type=int, default=72, help="Recurrent nodes (>=36)")
    p.add_argument("--obs-dim", type=int, default=12, help="World observation dimensions")
    p.add_argument("--actions", type=int, default=5, help="Discrete action count")
    p.add_argument("--calibration-steps", type=int, default=2500, help="Baseline calibration cycles")
    p.add_argument("--diagnostic-interval", type=int, default=25, help="Expensive diagnostics cadence")
    p.add_argument("--perturb-interval", type=int, default=400, help="PCI-like probe cadence")
    p.add_argument("--print-every", type=int, default=250, help="Console progress cadence")
    p.add_argument("--ablation-steps", type=int, default=5000, help="Cycles per ablation condition")
    p.add_argument("--skip-ablations", action="store_true", help="Skip post-run causal ablations")
    p.add_argument("--no-plots", action="store_true", help="Do not generate PNG plots")
    p.add_argument("--output", type=str, default="", help="Output directory; default is timestamped")
    return p.parse_args()


def validate_args(args) -> None:
    if args.steps < 1000:
        raise SystemExit("--steps must be >= 1000 for this long-run experiment")
    if args.nodes < 36:
        raise SystemExit("--nodes must be >= 36")
    if args.actions < 2:
        raise SystemExit("--actions must be >= 2")
    if args.obs_dim < 4:
        raise SystemExit("--obs-dim must be >= 4")
    if args.diagnostic_interval < 5:
        raise SystemExit("--diagnostic-interval must be >= 5")
    if args.perturb_interval < args.diagnostic_interval:
        raise SystemExit("--perturb-interval must be >= --diagnostic-interval")
    if args.calibration_steps >= args.steps:
        args.calibration_steps = max(500, args.steps // 5)


def main() -> None:
    args = parse_args()
    validate_args(args)
    print_header(args)

    if args.output:
        out_dir = Path(args.output).expanduser().resolve()
    else:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_dir = Path.cwd() / f"ghost_experiment_{stamp}"
    out_dir.mkdir(parents=True, exist_ok=True)

    machine = GhostMachineV2(
        seed=args.seed,
        nodes=args.nodes,
        obs_dim=args.obs_dim,
        action_count=args.actions,
        calibration_steps=args.calibration_steps,
        diagnostic_interval=args.diagnostic_interval,
        perturb_interval=args.perturb_interval,
        ablation="full",
    )

    rows, elapsed = run_machine(
        machine,
        steps=args.steps,
        print_every=args.print_every,
        collect_every_step=True,
        quiet=False,
    )
    summary = summarize(machine, rows, elapsed)

    stimulation_scan = machine.targeted_stimulation_scan()
    summary["stimulation_scan"] = [asdict(x) for x in stimulation_scan]

    ablations: List[AblationResult] = []
    if not args.skip_ablations:
        ablations = run_ablations(args)
        summary["ablations"] = [asdict(x) for x in ablations]

    write_csv(out_dir / "trajectory.csv", rows)
    write_csv(out_dir / "stimulation_scan.csv", stimulation_scan)
    if ablations:
        write_csv(out_dir / "ablations.csv", ablations)

    with (out_dir / "summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    if not args.no_plots:
        try:
            create_plots(out_dir, rows, ablations)
        except Exception as exc:
            print(f"[warning] Plot generation failed: {exc}")

    print("\n" + "=" * 108)
    print("EXPERIMENT COMPLETE")
    print("=" * 108)
    print(f"Elapsed main-run time : {elapsed:.2f} s")
    print(f"First event step      : {summary['first_event_step']}")
    print(f"Operational events    : {summary['ghost_events']}")
    print(f"Mean Ghost index      : {summary['mean_ghost_index']:.4f}")
    print(f"Max Ghost index       : {summary['max_ghost_index']:.4f}")
    print(f"Mean convergence      : {summary['mean_convergence']:.4f}")
    print(f"Max convergence       : {summary['max_convergence']:.4f}")
    print(f"Final recurrent gain  : {summary['final_recurrent_gain']:.4f}")
    print(f"Results directory     : {out_dir}")
    print("\nInterpretation: an event means the predeclared computational proxies converged.")
    print("It is NOT a measurement or proof of subjective experience or consciousness.")


if __name__ == "__main__":
    main()
