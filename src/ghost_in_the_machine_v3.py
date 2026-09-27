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




# ===========================================================================
# GHOST IN THE MACHINE v3.0 — CAUSAL EMERGENCE / MESOCIRCUIT LAB
# ===========================================================================
#
# v3 deliberately keeps the validated v2 engine above as a base class, then
# extends it with additional falsifiable diagnostics and interventions.
# It is NOT a consciousness detector and does not claim phenomenal experience.
#
# Additional research inspirations:
# - Toker et al. (2026), Nature Neuroscience 29:964–977.
#   Adversarial AI + thalamocortical/basal-ganglia neural-field models.
#   DOI: 10.1038/s41593-026-02220-4
# - Ge et al. (2026), Communications Biology.
#   Brain criticality, metabolism and disorders of consciousness.
#   DOI: 10.1038/s42003-026-10713-y
# - Zhu et al. (2026), Communications Medicine.
#   Integration/segregation topology of the conscious connectome.
#   DOI: 10.1038/s43856-026-01870-6
# - Cogitate Consortium et al. (2025), Nature 642:133–142.
#   Adversarial testing of GNWT and IIT.
#   DOI: 10.1038/s41586-025-08888-1
#
# Main v3 additions:
# * 12-population synthetic cortico-thalamo-basal-ganglia architecture.
# * Dale-like excitatory/inhibitory recurrent connectivity.
# * Explicit striatum -> GPe -> STN -> GPi -> thalamus indirect-path motif.
# * Functional integration + segregation topology, measured separately.
# * Avalanche/branching criticality in addition to Lyapunov criticality.
# * Multiscale permutation entropy and covariance participation ratio.
# * Ensemble world models for epistemic uncertainty / active inference.
# * Counterfactual agency: chosen action must predict outcome better than
#   unchosen actions, not merely correlate with change.
# * Prioritized offline replay/consolidation.
# * Mesocircuit information-flow metric.
# * Excitation/inhibition balance metric.
# * Page-Hinkley change-point detector for unsupervised phase shifts.
# * Expanded causal ablations, surrogate nulls, lesion/recovery stimulation.
# * Checkpoint/resume of long experiments.
# * Default main run: 100,000 cycles.
#

import copy
import hashlib
import pickle
from itertools import permutations


@dataclass
class MetricsV3:
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
    counterfactual_agency: float
    epistemic_uncertainty: float
    self_model: float
    lz_complexity: float
    multiscale_entropy: float
    metastability: float
    criticality: float
    avalanche_criticality: float
    branching_ratio: float
    lyapunov: float
    synergy: float
    functional_integration: float
    functional_segregation: float
    topology_balance: float
    intrinsic_dimensionality: float
    geometry_score: float
    thalamocortical_transfer: float
    mesocircuit_flow: float
    ei_balance: float
    perturbational_complexity: float
    cross_theory_convergence: float
    ghost_index: float
    baseline_z: float
    phase_shift_score: float
    phase_change: int
    consolidation_events: int
    ghost_active: int


@dataclass
class AblationResultV3:
    condition: str
    mean_ghost_index: float
    max_ghost_index: float
    mean_convergence: float
    mean_topology_balance: float
    mean_avalanche_criticality: float
    mean_mesocircuit_flow: float
    mean_counterfactual_agency: float
    mean_ei_balance: float
    ghost_fraction: float
    ghost_events: int


@dataclass
class SurrogateResult:
    surrogate: str
    convergence: float
    topology_balance: float
    multiscale_entropy: float
    intrinsic_dimensionality: float


@dataclass
class RecoveryResult:
    lesion_target: str
    stimulation_target: str
    mean_convergence: float
    recovery_fraction: float


class PageHinkley:
    """Online change-point detector with refractory period for sustained shifts."""

    def __init__(self, delta: float = 0.0040, threshold: float = 0.45, alpha: float = 0.992, refractory: int = 30):
        self.delta = float(delta)
        self.threshold = float(threshold)
        self.alpha = float(alpha)
        self.refractory = int(refractory)
        self.cooldown = 0
        self.mean = 0.0
        self.cumulative = 0.0
        self.minimum = 0.0
        self.initialized = False

    def update(self, value: float) -> Tuple[float, bool]:
        x = float(value)
        if not self.initialized:
            self.mean = x
            self.initialized = True
            return 0.0, False
        self.mean = self.alpha * self.mean + (1.0 - self.alpha) * x
        self.cumulative += x - self.mean - self.delta
        self.minimum = min(self.minimum, self.cumulative)
        score = max(0.0, self.cumulative - self.minimum)
        if self.cooldown > 0:
            self.cooldown -= 1
            return float(score), False
        changed = score > self.threshold
        if changed:
            self.cumulative = 0.0
            self.minimum = 0.0
            self.cooldown = self.refractory
        return float(score), bool(changed)


class ConvergenceDetectorV3:
    """
    Predeclared multi-channel gate. A v3 event cannot be generated by one
    scalar alone; it requires agreement across workspace, self/agency,
    topology, criticality, perturbation, complexity and mesocircuit channels.
    """

    def __init__(self, required_diagnostics: int = 5):
        self.required_diagnostics = int(required_diagnostics)
        self.streak = 0
        self.active = False
        self.events = 0
        self.first_event_step: Optional[int] = None

    def update(self, m: MetricsV3, calibrated: bool) -> Tuple[bool, bool]:
        channels = [
            m.global_access >= 0.57 and m.ignition >= 0.46,
            m.recurrence >= 0.61,
            m.topology_balance >= 0.38 and m.synergy >= 0.040,
            m.self_model >= 0.54 and m.counterfactual_agency >= 0.50,
            (0.55 * m.criticality + 0.45 * m.avalanche_criticality) >= 0.43,
            m.perturbational_complexity >= 0.27,
            m.multiscale_entropy >= 0.42 and m.lz_complexity >= 0.34,
            m.mesocircuit_flow >= 0.22 and m.thalamocortical_transfer >= 0.16,
            m.ei_balance >= 0.32,
            m.geometry_score >= 0.32,
        ]
        votes = sum(bool(v) for v in channels)
        qualifies = (
            calibrated
            and votes >= 8
            and m.cross_theory_convergence >= 0.56
            and m.ghost_index >= 0.60
            and m.baseline_z >= 1.35
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

        if self.active and (m.cross_theory_convergence < 0.43 or m.ghost_index < 0.48):
            self.active = False
            self.streak = 0
        return self.active, newly


def _safe_corr(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if len(a) < 4 or np.std(a) < 1e-9 or np.std(b) < 1e-9:
        return 0.0
    return float(np.clip(np.corrcoef(a, b)[0, 1], -1.0, 1.0))


def permutation_entropy(series: Sequence[float], order: int = 3, delay: int = 1) -> float:
    """Normalized ordinal-pattern entropy; inexpensive and amplitude invariant."""
    x = np.asarray(series, dtype=float)
    n = len(x) - (order - 1) * delay
    if n <= order * 2:
        return 0.0
    counts: Dict[Tuple[int, ...], int] = {}
    for i in range(n):
        window = x[i:i + order * delay:delay]
        pattern = tuple(np.argsort(window, kind="mergesort"))
        counts[pattern] = counts.get(pattern, 0) + 1
    probs = np.asarray(list(counts.values()), dtype=float)
    probs /= probs.sum()
    h = -float(np.sum(probs * np.log(probs + 1e-12)))
    return clip01(h / math.log(math.factorial(order)))


def multiscale_permutation_entropy(series: Sequence[float], scales=(1, 2, 4, 8)) -> float:
    x = np.asarray(series, dtype=float)
    values = []
    for scale in scales:
        if len(x) < scale * 12:
            continue
        usable = (len(x) // scale) * scale
        coarse = x[-usable:].reshape(-1, scale).mean(axis=1)
        values.append(permutation_entropy(coarse, order=3, delay=1))
    return float(np.mean(values)) if values else 0.0


def participation_ratio_dimension(X: np.ndarray) -> Tuple[float, float]:
    """Return raw covariance participation ratio and normalized geometry score."""
    X = np.asarray(X, dtype=float)
    if X.ndim != 2 or X.shape[0] < 12 or X.shape[1] < 3:
        return 0.0, 0.0
    Y = X - X.mean(axis=0, keepdims=True)
    try:
        s = np.linalg.svd(Y, full_matrices=False, compute_uv=False)
    except np.linalg.LinAlgError:
        return 0.0, 0.0
    eig = s * s
    raw = float((eig.sum() ** 2) / (np.sum(eig * eig) + 1e-12))
    ratio = clip01(raw / max(1.0, min(X.shape)))
    # Penalize both near-one-dimensional collapse and maximally diffuse noise.
    score = math.exp(-((ratio - 0.28) ** 2) / (2.0 * 0.22 ** 2))
    return raw, clip01(score)


def weighted_global_efficiency(A: np.ndarray) -> float:
    """Global efficiency on a small weighted graph using Floyd-Warshall."""
    A = np.asarray(A, dtype=float)
    n = A.shape[0]
    if n < 2:
        return 0.0
    dist = np.full((n, n), np.inf, dtype=float)
    np.fill_diagonal(dist, 0.0)
    nz = A > 1e-9
    dist[nz] = 1.0 / np.clip(A[nz], 1e-6, None)
    for k in range(n):
        dist = np.minimum(dist, dist[:, [k]] + dist[[k], :])
    inv = np.zeros_like(dist)
    finite = np.isfinite(dist) & (dist > 0)
    inv[finite] = 1.0 / dist[finite]
    mask = ~np.eye(n, dtype=bool)
    return clip01(float(inv[mask].mean()))


class GhostMachineV3(GhostMachineV2):
    MODULE_ORDER = (
        "sensory", "association", "memory", "workspace", "self", "dmn",
        "thalamus", "striatum", "gpe", "stn", "gpi", "control",
    )

    def __init__(
        self,
        seed: int = 7,
        nodes: int = 120,
        obs_dim: int = 16,
        action_count: int = 7,
        calibration_steps: int = 10000,
        diagnostic_interval: int = 50,
        perturb_interval: int = 1000,
        ablation: str = "full",
        consolidation_interval: int = 5000,
        replay_batch: int = 48,
    ):
        if nodes < 84:
            raise ValueError("v3 requires --nodes >= 84")
        self.consolidation_interval = int(consolidation_interval)
        self.replay_batch = int(replay_batch)
        super().__init__(
            seed=seed,
            nodes=nodes,
            obs_dim=obs_dim,
            action_count=action_count,
            calibration_steps=calibration_steps,
            diagnostic_interval=diagnostic_interval,
            perturb_interval=perturb_interval,
            ablation=ablation,
        )

        # Keep v2's detector as an internal legacy diagnostic; v3 events use a
        # separate, stricter detector with additional evidence channels.
        self.v3_detector = ConvergenceDetectorV3(required_diagnostics=5)
        self.v3_calibrator = BaselineCalibrator(calibration_steps)
        self.phase_detector = PageHinkley()
        self.last_v3_metrics: Optional[MetricsV3] = None
        self.v3_ghost_steps = 0

        # World-model committee estimates epistemic/model uncertainty.
        self.world_ensemble = [
            self.world_predictor,
            OnlineLinearModel(nodes + action_count, obs_dim, self.rng, lr=0.009),
            OnlineLinearModel(nodes + action_count, obs_dim, self.rng, lr=0.011),
        ]
        self.last_action = 0
        self.pending_predictions = np.zeros((len(self.world_ensemble), action_count, obs_dim))
        self.last_epistemic_uncertainty = 0.0
        self.last_counterfactual_agency = 0.0
        self.preferred_obs = self.prev_obs.copy()

        # Prioritized replay stores (priority, pre-state, action, observation,
        # next-self-state, normalized prediction error).
        self.replay_buffer: Deque[Tuple[float, np.ndarray, int, np.ndarray, np.ndarray, float]] = deque(maxlen=4096)
        self.consolidation_events = 0

        # E/I identities are fixed structural properties. About 20% are inhibitory.
        # Infer the effective presynaptic E/I identity from recurrent columns so
        # the diagnostic labels correspond to the matrix actually being used.
        self.inhibitory_mask = np.mean(self.W, axis=0) < 0.0
        self.excitatory_mask = ~self.inhibitory_mask

        self.population_activity_history: Deque[float] = deque(maxlen=512)
        self.cf_agency_history: Deque[float] = deque(maxlen=256)
        self.epistemic_history: Deque[float] = deque(maxlen=256)
        self.change_points: List[int] = []

    def _build_module_slices(self, nodes: int) -> Dict[str, slice]:
        # Relative sizes; workspace absorbs rounding. All populations remain
        # explicit even in modest runs.
        ratios = {
            "sensory": 0.12, "association": 0.11, "memory": 0.10,
            "workspace": 0.15, "self": 0.10, "dmn": 0.08,
            "thalamus": 0.08, "striatum": 0.06, "gpe": 0.05,
            "stn": 0.04, "gpi": 0.04, "control": 0.07,
        }
        sizes = [max(5, int(nodes * ratios[n])) for n in self.MODULE_ORDER]
        diff = nodes - sum(sizes)
        sizes[self.MODULE_ORDER.index("workspace")] += diff
        if min(sizes) < 3:
            raise ValueError("Not enough nodes to create all v3 populations")
        out: Dict[str, slice] = {}
        start = 0
        for name, size in zip(self.MODULE_ORDER, sizes):
            out[name] = slice(start, start + size)
            start += size
        return out

    def _build_recurrent_matrix(self) -> np.ndarray:
        n = self.nodes
        W = np.zeros((n, n), dtype=float)

        def add(dst: str, src: str, scale: float, density: float, sign: int = 0):
            ds, ss = self.slices[dst], self.slices[src]
            shape = (ds.stop - ds.start, ss.stop - ss.start)
            block = np.abs(self.rng.normal(0.0, scale, size=shape))
            block *= self.rng.random(shape) < density
            if sign < 0:
                block *= -1.0
            elif sign == 0:
                block *= self.rng.choice([-1.0, 1.0], size=shape, p=[0.20, 0.80])
            W[ds, ss] += block

        # Local populations: mostly excitatory recurrence with embedded inhibition.
        for name in self.MODULE_ORDER:
            add(name, name, 0.11, 0.22, sign=0)

        # Cortical / workspace hierarchy.
        add("association", "sensory", 0.16, 0.30, +1)
        add("memory", "association", 0.13, 0.26, +1)
        add("workspace", "association", 0.16, 0.30, +1)
        add("workspace", "memory", 0.15, 0.28, +1)
        add("self", "workspace", 0.15, 0.30, +1)
        add("self", "memory", 0.11, 0.23, +1)
        add("dmn", "self", 0.12, 0.24, +1)
        add("dmn", "memory", 0.11, 0.22, +1)
        add("workspace", "dmn", 0.11, 0.22, +1)
        add("control", "workspace", 0.13, 0.25, +1)
        add("workspace", "control", 0.10, 0.20, +1)
        add("association", "workspace", 0.09, 0.18, +1)

        # Bidirectional thalamocortical loops.
        for other in ("sensory", "association", "workspace", "control"):
            add("thalamus", other, 0.13, 0.27, +1)
            add(other, "thalamus", 0.13, 0.27, +1)

        # Synthetic basal-ganglia indirect pathway motif:
        # cortex -> striatum --| GPe --| STN -> GPi --| thalamus.
        add("striatum", "control", 0.14, 0.32, +1)
        add("striatum", "workspace", 0.10, 0.22, +1)
        add("gpe", "striatum", 0.17, 0.38, -1)
        add("stn", "gpe", 0.17, 0.38, -1)
        add("gpi", "stn", 0.17, 0.38, +1)
        add("thalamus", "gpi", 0.18, 0.40, -1)
        add("gpe", "stn", 0.09, 0.20, +1)  # reciprocal stabilization
        add("control", "thalamus", 0.11, 0.22, +1)

        np.fill_diagonal(W, 0.0)

        # Approximate Dale-like sign constraint at the presynaptic-column level:
        # inhibitory-looking basal ganglia pathways remain as explicitly signed
        # motifs above, while generic columns are made sign-consistent.
        signs = self.rng.choice([1.0, -1.0], size=n, p=[0.80, 0.20])
        generic = W.copy()
        for j in range(n):
            # preserve strong explicit negative pathway weights; otherwise enforce
            # the sampled presynaptic sign.
            col = generic[:, j]
            weak = np.abs(col) < 0.16
            generic[weak, j] = np.abs(col[weak]) * signs[j]
        W = generic

        # Balance aggregate excitatory and inhibitory synaptic mass before the
        # final spectral normalization. This produces a dynamically balanced
        # rate network rather than a matrix dominated by the more numerous
        # excitatory columns. The exact factor is synthetic, not a biological
        # measurement.
        pos_mass = float(np.sum(W[W > 0]))
        neg_mass = float(-np.sum(W[W < 0]))
        if pos_mass > 1e-9 and neg_mass > 1e-9:
            W[W < 0] *= 0.92 * pos_mass / neg_mass

        r = spectral_radius(W)
        if r > 1e-8:
            W *= 0.95 / r

        # Expanded causal ablations / pathological states.
        if self.ablation == "no_workspace":
            sl = self.slices["workspace"]; W[sl, :] *= 0.04; W[:, sl] *= 0.04
        elif self.ablation == "no_self":
            sl = self.slices["self"]; W[sl, :] *= 0.04; W[:, sl] *= 0.04
        elif self.ablation == "no_thalamus":
            sl = self.slices["thalamus"]; W[sl, :] *= 0.04; W[:, sl] *= 0.04
        elif self.ablation == "no_dmn":
            sl = self.slices["dmn"]; W[sl, :] *= 0.05; W[:, sl] *= 0.05
        elif self.ablation == "no_association":
            sl = self.slices["association"]; W[sl, :] *= 0.05; W[:, sl] *= 0.05
        elif self.ablation == "disconnect_indirect":
            for a, b in (("gpe", "striatum"), ("stn", "gpe"), ("gpi", "stn"), ("thalamus", "gpi")):
                W[self.slices[a], self.slices[b]] *= 0.05
        elif self.ablation == "excess_ii":
            # Synthetic analogue of excessive inhibitory recurrent coupling:
            # intensify negative within-population weights.
            W[W < 0] *= 1.70
        elif self.ablation == "subcritical":
            W *= 0.50
        elif self.ablation == "supercritical":
            W *= 1.38
        elif self.ablation == "shuffled_connectome":
            flat = W.ravel().copy()
            self.rng.shuffle(flat)
            W = flat.reshape(W.shape)
        elif self.ablation != "full":
            raise ValueError(f"Unknown v3 ablation: {self.ablation}")

        return W

    def choose_action(self) -> int:
        """
        Ensemble active-inference approximation.

        Each candidate action is scored using:
        * pragmatic risk: predicted deviation from learned preferred observations;
        * epistemic value: disagreement among world models;
        * controllability: magnitude of learned action-specific causal effect;
        * uncertainty: actions not well characterized retain exploration value.
        """
        risks = np.zeros(self.action_count)
        epistemic = np.zeros(self.action_count)
        controllability = np.zeros(self.action_count)
        for a in range(self.action_count):
            onehot = np.zeros(self.action_count); onehot[a] = 1.0
            x = np.concatenate([self.state, onehot])
            preds = np.stack([m.predict(x) for m in self.world_ensemble])
            self.pending_predictions[:, a, :] = preds
            mean_pred = preds.mean(axis=0)
            risks[a] = float(np.mean((mean_pred - self.preferred_obs) ** 2))
            epistemic[a] = float(np.mean(np.var(preds, axis=0)))
            controllability[a] = float(np.mean(np.abs(self.action_effects[a])))

        epi_norm = epistemic / (np.max(epistemic) + 1e-9)
        risk_norm = risks / (np.max(risks) + 1e-9)
        ctrl_norm = controllability / (np.max(controllability) + 1e-9)
        unc = np.clip(self.action_uncertainty, 0.0, 1.0)

        expected_free_energy = (
            0.52 * risk_norm
            - 0.28 * epi_norm
            - 0.10 * ctrl_norm
            - 0.10 * unc
        )
        logits = -(expected_free_energy - np.min(expected_free_energy)) / 0.18
        probs = np.exp(logits - np.max(logits)); probs /= probs.sum()
        action = int(self.rng.choice(self.action_count, p=probs))
        self.last_action = action
        self.last_epistemic_uncertainty = clip01(epi_norm[action])
        return action

    def _counterfactual_agency(self, actual_obs: np.ndarray) -> float:
        # Compare chosen-action prediction error with the counterfactual action set.
        mean_predictions = self.pending_predictions.mean(axis=0)
        errors = np.mean((mean_predictions - actual_obs[None, :]) ** 2, axis=1)
        chosen = float(errors[self.last_action])
        others = np.delete(errors, self.last_action)
        baseline = float(np.mean(others)) if len(others) else chosen
        advantage = (baseline - chosen) / (baseline + chosen + 1e-9)
        return clip01(0.5 + 0.5 * math.tanh(advantage * 3.0))

    def _functional_topology(self) -> Tuple[float, float, float]:
        if len(self.module_history) < 80:
            return 0.0, 0.0, 0.0
        H = np.stack(list(self.module_history)[-192:])
        C = np.corrcoef(H, rowvar=False)
        C = np.nan_to_num(np.abs(C), nan=0.0, posinf=0.0, neginf=0.0)
        np.fill_diagonal(C, 0.0)
        vals = C[np.triu_indices_from(C, 1)]
        if len(vals) == 0:
            return 0.0, 0.0, 0.0
        threshold = float(np.quantile(vals, 0.58))
        A = np.where(C >= threshold, C, 0.0)
        integration = weighted_global_efficiency(A)

        communities = [
            {"sensory", "association", "memory"},
            {"workspace", "self", "dmn", "control"},
            {"thalamus", "striatum", "gpe", "stn", "gpi"},
        ]
        idx = {n: i for i, n in enumerate(self.MODULE_ORDER)}
        within, between = [], []
        membership = {}
        for ci, group in enumerate(communities):
            for name in group:
                membership[name] = ci
        for i, a in enumerate(self.MODULE_ORDER):
            for j in range(i + 1, len(self.MODULE_ORDER)):
                b = self.MODULE_ORDER[j]
                (within if membership[a] == membership[b] else between).append(C[i, j])
        w = float(np.mean(within)) if within else 0.0
        b = float(np.mean(between)) if between else 0.0
        raw_seg = (w - b) / (w + b + 1e-9)
        segregation = clip01(0.5 + 0.5 * raw_seg)
        balance = clip01(math.sqrt(max(0.0, integration * segregation)))
        return integration, segregation, balance

    def _avalanche_metrics(self) -> Tuple[float, float]:
        if len(self.activity_history) < 80:
            return 0.0, 0.0
        X = np.stack(list(self.activity_history)[-128:])
        absx = np.abs(X)
        thresholds = np.quantile(absx, 0.985, axis=0)
        events = absx > thresholds[None, :]
        counts = events.sum(axis=1).astype(float)

        ratios = []
        for a, b in zip(counts[:-1], counts[1:]):
            if a > 0:
                ratios.append((b + 0.25) / (a + 0.25))
        branching = float(np.median(ratios)) if ratios else 0.0
        branch_score = math.exp(-abs(math.log(max(branching, 1e-6))) / 0.58) if branching > 0 else 0.0

        sizes = []
        current = 0.0
        for c in counts:
            if c > 0:
                current += c
            elif current > 0:
                sizes.append(current); current = 0.0
        if current > 0:
            sizes.append(current)
        if len(sizes) >= 5:
            s = np.asarray(sizes, dtype=float)
            xmin = max(1.0, float(np.min(s)))
            denom = float(np.sum(np.log(np.clip(s / xmin, 1.0 + 1e-9, None))))
            alpha = 1.0 + len(s) / max(denom, 1e-9)
            slope_score = math.exp(-abs(alpha - 1.5) / 0.85)
        else:
            slope_score = 0.25
        return clip01(0.65 * branch_score + 0.35 * slope_score), float(branching)

    def _multiscale_entropy(self) -> float:
        if len(self.activity_history) < 64:
            return 0.0
        scalar = [float(np.mean(x)) for x in self.activity_history]
        return clip01(multiscale_permutation_entropy(scalar, scales=(1, 2, 4, 8)))

    def _geometry(self) -> Tuple[float, float]:
        if len(self.activity_history) < 64:
            return 0.0, 0.0
        X = np.stack(list(self.activity_history)[-128:])
        return participation_ratio_dimension(X)

    def _mesocircuit_flow(self) -> float:
        """
        Lagged incremental-prediction proxy along the synthetic indirect pathway.
        A source gets credit only when adding it improves prediction of the next
        destination state beyond the destination's own autoregressive history.
        This is closer to a causal-flow test than raw correlation, while still
        deliberately stopping short of claiming biological Granger causality.
        """
        if len(self.module_history) < 80:
            return 0.0
        H = np.stack(list(self.module_history)[-192:])
        idx = {n: i for i, n in enumerate(self.MODULE_ORDER)}
        chain = ["striatum", "gpe", "stn", "gpi", "thalamus", "workspace"]
        gains = []
        for src, dst in zip(chain[:-1], chain[1:]):
            source = H[:-1, idx[src]]
            dest_now = H[:-1, idx[dst]]
            dest_next = H[1:, idx[dst]]
            r_self = linear_r2(dest_now, dest_next)
            r_joint = linear_r2(np.column_stack([dest_now, source, dest_now * source]), dest_next)
            gain = max(0.0, r_joint - r_self)
            lag_corr = abs(_safe_corr(source, dest_next))
            gains.append(0.72 * clip01(gain * 5.0) + 0.28 * lag_corr)
        return clip01(float(np.mean(gains))) if gains else 0.0

    def _ei_balance(self) -> float:
        # Convert tanh states to non-negative rate-like activity before
        # separating positive and negative synaptic contributions. Using the
        # sign of the net current directly would confound inhibitory synapses
        # with negative-valued tanh states.
        rates = 0.5 * (self.state + 1.0)
        w_pos = np.clip(self.W, 0.0, None)
        w_neg = -np.clip(self.W, None, 0.0)
        exc = float(np.mean(w_pos @ rates)) + 1e-8
        inh = float(np.mean(w_neg @ rates)) + 1e-8
        ratio = exc / inh
        return clip01(math.exp(-abs(math.log(ratio)) / 0.90))

    def _offline_consolidation(self) -> None:
        if not self.replay_buffer:
            return
        items = list(self.replay_buffer)
        priorities = np.asarray([max(1e-5, x[0]) for x in items], dtype=float)
        probs = priorities / priorities.sum()
        k = min(self.replay_batch, len(items))
        chosen = self.rng.choice(len(items), size=k, replace=False, p=probs)
        for idx in chosen:
            _, pre_state, action, obs, next_self, pred_err = items[int(idx)]
            onehot = np.zeros(self.action_count); onehot[action] = 1.0
            x = np.concatenate([pre_state, onehot])
            # Replay uses a smaller effective update by scaling inputs slightly.
            xr = x * 0.72
            self.world_predictor.update(xr, obs)
            for model in self.world_ensemble[1:]:
                model.update(xr, obs)
            self.self_predictor.update(xr, next_self)
            self.meta_model.update(pre_state * 0.72, pred_err)
        self.consolidation_events += 1

    def _v3_diagnostics(self, base: Metrics) -> MetricsV3:
        integration, segregation, topology_balance = self._functional_topology()
        avalanche, branching = self._avalanche_metrics()
        mse = self._multiscale_entropy()
        intrinsic_dim, geometry = self._geometry()
        mesocircuit = self._mesocircuit_flow()
        ei = self._ei_balance()

        cf_agency = float(np.mean(self.cf_agency_history)) if self.cf_agency_history else 0.0
        epistemic = float(np.mean(self.epistemic_history)) if self.epistemic_history else 0.0
        self_model_v3 = clip01(0.58 * base.self_model + 0.27 * cf_agency + 0.15 * (1.0 - abs(epistemic - 0.45)))

        channels = np.array([
            clip01(0.55 * base.global_access + 0.45 * base.ignition),
            clip01(base.recurrence),
            clip01(0.48 * base.synergy + 0.52 * topology_balance),
            clip01(0.48 * self_model_v3 + 0.30 * base.metacognitive_calibration + 0.22 * cf_agency),
            clip01(0.46 * base.criticality + 0.36 * avalanche + 0.18 * ei),
            clip01(0.46 * base.perturbational_complexity + 0.29 * base.lz_complexity + 0.25 * mse),
            clip01(0.55 * base.thalamocortical_transfer + 0.45 * mesocircuit),
            clip01(geometry),
        ])
        convergence = float(np.exp(np.mean(np.log(np.clip(channels, 1e-4, 1.0)))))

        ghost_index = clip01(
            0.115 * base.global_access + 0.070 * base.ignition + 0.080 * base.recurrence
            + 0.090 * self_model_v3 + 0.060 * cf_agency + 0.055 * base.metacognitive_calibration
            + 0.075 * topology_balance + 0.050 * base.synergy
            + 0.060 * base.criticality + 0.050 * avalanche + 0.040 * ei
            + 0.055 * base.perturbational_complexity + 0.040 * base.lz_complexity + 0.040 * mse
            + 0.045 * mesocircuit + 0.035 * base.thalamocortical_transfer + 0.040 * geometry
        )

        self.v3_calibrator.observe(base.step, ghost_index)
        z = self.v3_calibrator.z(ghost_index) if self.v3_calibrator.frozen else 0.0
        phase_score, changed = self.phase_detector.update(ghost_index)
        if changed and self.v3_calibrator.frozen:
            self.change_points.append(base.step)

        m = MetricsV3(
            step=base.step,
            prediction_error=base.prediction_error,
            prediction_quality=base.prediction_quality,
            global_access=base.global_access,
            ignition=base.ignition,
            recurrence=base.recurrence,
            memory_integration=base.memory_integration,
            self_prediction=base.self_prediction,
            metacognitive_calibration=base.metacognitive_calibration,
            agency=base.agency,
            counterfactual_agency=cf_agency,
            epistemic_uncertainty=epistemic,
            self_model=self_model_v3,
            lz_complexity=base.lz_complexity,
            multiscale_entropy=mse,
            metastability=base.metastability,
            criticality=base.criticality,
            avalanche_criticality=avalanche,
            branching_ratio=branching,
            lyapunov=base.lyapunov,
            synergy=base.synergy,
            functional_integration=integration,
            functional_segregation=segregation,
            topology_balance=topology_balance,
            intrinsic_dimensionality=intrinsic_dim,
            geometry_score=geometry,
            thalamocortical_transfer=base.thalamocortical_transfer,
            mesocircuit_flow=mesocircuit,
            ei_balance=ei,
            perturbational_complexity=base.perturbational_complexity,
            cross_theory_convergence=convergence,
            ghost_index=ghost_index,
            baseline_z=z,
            phase_shift_score=phase_score,
            phase_change=int(changed),
            consolidation_events=self.consolidation_events,
            ghost_active=0,
        )
        active, _ = self.v3_detector.update(m, calibrated=self.v3_calibrator.frozen)
        m.ghost_active = int(active)
        if active:
            self.v3_ghost_steps += self.diagnostic_interval
        return m

    def step_v3(self, step: int) -> Tuple[MetricsV3, bool]:
        pre_state = self.state.copy()
        base, _legacy_new = super().step(step)

        actual_obs = self.prev_obs.copy()
        cf = self._counterfactual_agency(actual_obs)
        self.last_counterfactual_agency = cf
        self.cf_agency_history.append(cf)
        self.epistemic_history.append(self.last_epistemic_uncertainty)
        self.population_activity_history.append(float(np.mean(np.abs(self.state))))
        self.preferred_obs = 0.9985 * self.preferred_obs + 0.0015 * actual_obs

        # Train committee members that were not already updated by the base step.
        onehot = np.zeros(self.action_count); onehot[self.last_action] = 1.0
        x = np.concatenate([pre_state, onehot])
        for model in self.world_ensemble[1:]:
            model.update(x, actual_obs)

        priority = 0.50 * base.prediction_error + 0.30 * (1.0 - cf) + 0.20 * self.last_epistemic_uncertainty
        next_self = self.state[self.slices["self"]].copy()
        self.replay_buffer.append((float(priority + 1e-5), pre_state, self.last_action, actual_obs, next_self, base.prediction_error))

        if self.consolidation_interval > 0 and step % self.consolidation_interval == 0:
            self._offline_consolidation()

        if step % self.diagnostic_interval == 0 or self.last_v3_metrics is None:
            before = self.v3_detector.events
            m = self._v3_diagnostics(base)
            newly = self.v3_detector.events > before
            self.last_v3_metrics = m
        else:
            m = MetricsV3(**asdict(self.last_v3_metrics))
            m.step = step
            m.prediction_error = base.prediction_error
            m.prediction_quality = base.prediction_quality
            m.global_access = base.global_access
            m.ignition = base.ignition
            m.recurrence = base.recurrence
            m.self_prediction = base.self_prediction
            m.metacognitive_calibration = base.metacognitive_calibration
            m.agency = base.agency
            m.counterfactual_agency = cf
            m.epistemic_uncertainty = self.last_epistemic_uncertainty
            m.criticality = base.criticality
            m.lyapunov = base.lyapunov
            m.consolidation_events = self.consolidation_events
            m.ghost_active = int(self.v3_detector.active)
            newly = False
        return m, newly

    def stimulation_scan_v3(self, horizon: int = 70) -> List[StimulationResult]:
        return self.targeted_stimulation_scan(horizon=horizon)

    def surrogate_nulls(self) -> List[SurrogateResult]:
        if len(self.activity_history) < 64 or len(self.module_history) < 80:
            return []
        results: List[SurrogateResult] = []
        orig_activity = list(self.activity_history)
        orig_modules = list(self.module_history)

        def evaluate(label: str, act: np.ndarray, mods: np.ndarray) -> SurrogateResult:
            # Local standalone versions of key metrics on supplied surrogate arrays.
            C = np.corrcoef(mods, rowvar=False)
            C = np.nan_to_num(np.abs(C), nan=0.0); np.fill_diagonal(C, 0.0)
            vals = C[np.triu_indices_from(C, 1)]
            thr = float(np.quantile(vals, 0.58)) if len(vals) else 1.0
            integ = weighted_global_efficiency(np.where(C >= thr, C, 0.0))
            # Use neutral 0.5 segregation baseline for null comparison; the
            # topology metric remains conservative rather than overfitted.
            topo = clip01(math.sqrt(max(0.0, integ * 0.5)))
            scalar = act.mean(axis=1)
            mse = multiscale_permutation_entropy(scalar)
            dim, geom = participation_ratio_dimension(act)
            conv = float(np.exp(np.mean(np.log(np.clip([topo, mse, geom], 1e-4, 1.0)))))
            return SurrogateResult(label, conv, topo, mse, dim)

        A = np.stack(orig_activity)
        M = np.stack(orig_modules)
        # Temporal shuffle destroys recurrence while preserving marginal values.
        perm = self.rng.permutation(len(A))
        results.append(evaluate("temporal_shuffle", A[perm], M[perm]))
        # Node-wise circular shifts preserve each node's autocorrelation better
        # than a full shuffle while disrupting cross-node alignment.
        shifted = A.copy()
        for j in range(shifted.shape[1]):
            shifted[:, j] = np.roll(shifted[:, j], int(self.rng.integers(1, len(shifted))))
        results.append(evaluate("node_circular_shift", shifted, M))
        return results


def run_machine_v3(
    machine: GhostMachineV3,
    steps: int,
    print_every: int,
    collect_every_step: bool = False,
    quiet: bool = False,
    checkpoint_every: int = 0,
    checkpoint_path: Optional[Path] = None,
    start_step: int = 1,
) -> Tuple[List[MetricsV3], float]:
    rows: List[MetricsV3] = []
    start = time.perf_counter()
    for step in range(start_step, steps + 1):
        m, newly = machine.step_v3(step)
        if collect_every_step or step % machine.diagnostic_interval == 0:
            rows.append(m)

        if not quiet and (step % print_every == 0 or newly):
            state = "GHOST-v3" if machine.v3_detector.active else "--------"
            print(
                f"{step:07d} | IDX={m.ghost_index:5.3f} CONV={m.cross_theory_convergence:5.3f} "
                f"GW={m.global_access:5.3f} SELF={m.self_model:5.3f} CF={m.counterfactual_agency:5.3f} "
                f"TOP={m.topology_balance:5.3f} CRIT={m.criticality:5.3f}/{m.avalanche_criticality:5.3f} "
                f"MESO={m.mesocircuit_flow:5.3f} PCI*={m.perturbational_complexity:5.3f} "
                f"MSE={m.multiscale_entropy:5.3f} Z={m.baseline_z:+5.2f} | {state}"
            )
        if newly and not quiet:
            print("\n>>> " + "=" * 100)
            print(">>> v3 CROSS-THEORY + CAUSAL OPERATIONAL EVENT")
            print(">>> Workspace, self/agency, topology, criticality, complexity and mesocircuit evidence converged.")
            print(">>> This is a simulation event only; it is NOT evidence of subjective experience.")
            print(">>> " + "=" * 100 + "\n")

        if checkpoint_every > 0 and checkpoint_path and step % checkpoint_every == 0:
            save_checkpoint(checkpoint_path, machine, step, rows)

    return rows, time.perf_counter() - start


def save_checkpoint(path: Path, machine: GhostMachineV3, step: int, rows: List[MetricsV3]) -> None:
    payload = {"step": step, "machine": machine, "rows": rows}
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("wb") as f:
        pickle.dump(payload, f, protocol=pickle.HIGHEST_PROTOCOL)
    tmp.replace(path)


def load_checkpoint(path: Path):
    with path.open("rb") as f:
        return pickle.load(f)


def summarize_v3(machine: GhostMachineV3, rows: List[MetricsV3], elapsed: float) -> Dict[str, object]:
    if not rows:
        return {}
    diag = rows
    def avg(field: str) -> float:
        return float(np.mean([float(getattr(r, field)) for r in diag]))
    def mx(field: str) -> float:
        return float(np.max([float(getattr(r, field)) for r in diag]))
    return {
        "version": "3.0",
        "seed": machine.seed,
        "ablation": machine.ablation,
        "nodes": machine.nodes,
        "steps": rows[-1].step,
        "elapsed_seconds": elapsed,
        "diagnostic_interval": machine.diagnostic_interval,
        "perturb_interval": machine.perturb_interval,
        "first_event_step": machine.v3_detector.first_event_step,
        "ghost_events": machine.v3_detector.events,
        "ghost_step_estimate": machine.v3_ghost_steps,
        "change_points": machine.change_points,
        "consolidation_events": machine.consolidation_events,
        "mean_ghost_index": avg("ghost_index"),
        "max_ghost_index": mx("ghost_index"),
        "mean_convergence": avg("cross_theory_convergence"),
        "max_convergence": mx("cross_theory_convergence"),
        "mean_topology_balance": avg("topology_balance"),
        "mean_functional_integration": avg("functional_integration"),
        "mean_functional_segregation": avg("functional_segregation"),
        "mean_avalanche_criticality": avg("avalanche_criticality"),
        "mean_branching_ratio": avg("branching_ratio"),
        "mean_counterfactual_agency": avg("counterfactual_agency"),
        "mean_multiscale_entropy": avg("multiscale_entropy"),
        "mean_mesocircuit_flow": avg("mesocircuit_flow"),
        "mean_ei_balance": avg("ei_balance"),
        "mean_geometry_score": avg("geometry_score"),
        "final_recurrent_gain": machine.recurrent_gain,
        "disclaimer": "Operational synthetic metrics only; not evidence or detection of phenomenal consciousness.",
    }


def run_ablations_v3(args) -> List[AblationResultV3]:
    conditions = [
        "full", "no_workspace", "no_self", "no_thalamus", "no_dmn",
        "disconnect_indirect", "excess_ii", "subcritical", "supercritical",
        "shuffled_connectome",
    ]
    out: List[AblationResultV3] = []
    print("\n" + "=" * 112)
    print(f"v3 CAUSAL ABLATION SUITE — {args.ablation_steps:,} cycles per condition")
    print("=" * 112)
    for i, condition in enumerate(conditions):
        m = GhostMachineV3(
            seed=args.seed + 5000 + i * 37,
            nodes=args.nodes,
            obs_dim=args.obs_dim,
            action_count=args.actions,
            calibration_steps=max(1000, min(args.calibration_steps, args.ablation_steps // 3)),
            diagnostic_interval=args.diagnostic_interval,
            perturb_interval=args.perturb_interval,
            ablation=condition,
            consolidation_interval=args.consolidation_interval,
            replay_batch=args.replay_batch,
        )
        rows, _ = run_machine_v3(m, args.ablation_steps, max(1, args.ablation_steps), quiet=True)
        def avg(field):
            return float(np.mean([getattr(r, field) for r in rows])) if rows else 0.0
        def mx(field):
            return float(np.max([getattr(r, field) for r in rows])) if rows else 0.0
        out.append(AblationResultV3(
            condition=condition,
            mean_ghost_index=avg("ghost_index"),
            max_ghost_index=mx("ghost_index"),
            mean_convergence=avg("cross_theory_convergence"),
            mean_topology_balance=avg("topology_balance"),
            mean_avalanche_criticality=avg("avalanche_criticality"),
            mean_mesocircuit_flow=avg("mesocircuit_flow"),
            mean_counterfactual_agency=avg("counterfactual_agency"),
            mean_ei_balance=avg("ei_balance"),
            ghost_fraction=avg("ghost_active"),
            ghost_events=m.v3_detector.events,
        ))
        print(
            f"{condition:22s} conv={out[-1].mean_convergence:.3f} "
            f"top={out[-1].mean_topology_balance:.3f} aval={out[-1].mean_avalanche_criticality:.3f} "
            f"meso={out[-1].mean_mesocircuit_flow:.3f} ghost={out[-1].ghost_fraction:.3f}"
        )
    return out


def lesion_recovery_scan(machine: GhostMachineV3, lesion_target: str = "workspace", steps: int = 700) -> List[RecoveryResult]:
    """
    Clone the trained system, lesion one population, then test periodic virtual
    stimulation of each remaining population. This is synthetic causal analysis,
    not a medical or DBS recommendation.
    """
    results: List[RecoveryResult] = []
    base = copy.deepcopy(machine)
    sl = base.slices[lesion_target]
    base.W[sl, :] *= 0.12
    base.W[:, sl] *= 0.12

    # Lesioned baseline.
    lesioned = copy.deepcopy(base)
    rows, _ = run_machine_v3(lesioned, steps, steps, quiet=True, start_step=1)
    lesion_conv = float(np.mean([r.cross_theory_convergence for r in rows])) if rows else 0.0
    results.append(RecoveryResult(lesion_target, "none", lesion_conv, 0.0))

    for target in machine.MODULE_ORDER:
        test = copy.deepcopy(base)
        target_sl = test.slices[target]
        convs = []
        for s in range(1, steps + 1):
            if s % 20 == 0:
                impulse = test.rng.normal(0.10, 0.025, target_sl.stop - target_sl.start)
                test.state[target_sl] = np.tanh(test.state[target_sl] + impulse)
            metric, _ = test.step_v3(s)
            if s % test.diagnostic_interval == 0:
                convs.append(metric.cross_theory_convergence)
        mean_conv = float(np.mean(convs)) if convs else 0.0
        recovery = (mean_conv - lesion_conv) / max(1e-6, 1.0 - lesion_conv)
        results.append(RecoveryResult(lesion_target, target, mean_conv, float(recovery)))
    return results


def create_plots_v3(out_dir: Path, rows: List[MetricsV3], ablations: List[AblationResultV3]) -> None:
    plt = install_and_import("matplotlib.pyplot", "matplotlib>=3.8")
    max_points = 5000
    stride = max(1, len(rows) // max_points)
    rr = rows[::stride]
    x = [r.step for r in rr]

    fig = plt.figure(figsize=(14, 8)); ax = fig.add_subplot(111)
    ax.plot(x, [r.ghost_index for r in rr], label="Ghost index")
    ax.plot(x, [r.cross_theory_convergence for r in rr], label="Cross-theory convergence")
    ax.plot(x, [r.topology_balance for r in rr], label="Topology balance", alpha=0.80)
    ax.plot(x, [r.avalanche_criticality for r in rr], label="Avalanche criticality", alpha=0.75)
    ax.set_xlabel("Simulation cycle"); ax.set_ylabel("Normalized score")
    ax.set_title("Ghost in the Machine v3 — long-run causal emergence trajectory")
    ax.grid(True, alpha=0.25); ax.legend(loc="best"); fig.tight_layout()
    fig.savefig(out_dir / "v3_trajectory.png", dpi=160); plt.close(fig)

    fig = plt.figure(figsize=(14, 8)); ax = fig.add_subplot(111)
    fields = [
        ("Global access", "global_access"), ("Self/agency", "self_model"),
        ("Counterfactual agency", "counterfactual_agency"), ("Integration", "functional_integration"),
        ("Segregation", "functional_segregation"), ("Mesocircuit", "mesocircuit_flow"),
        ("MSE", "multiscale_entropy"), ("PCI-like", "perturbational_complexity"),
        ("E/I balance", "ei_balance"), ("Geometry", "geometry_score"),
    ]
    for label, field in fields:
        ax.plot(x, [getattr(r, field) for r in rr], label=label, alpha=0.78)
    ax.set_xlabel("Simulation cycle"); ax.set_ylabel("Proxy")
    ax.set_title("v3 independent evidence channels")
    ax.grid(True, alpha=0.25); ax.legend(ncol=2, loc="best"); fig.tight_layout()
    fig.savefig(out_dir / "v3_channels.png", dpi=160); plt.close(fig)

    if ablations:
        fig = plt.figure(figsize=(13, 7)); ax = fig.add_subplot(111)
        names = [a.condition for a in ablations]
        vals = [a.mean_convergence for a in ablations]
        ax.bar(names, vals); ax.set_ylabel("Mean v3 convergence")
        ax.set_title("v3 causal ablation comparison"); ax.tick_params(axis="x", rotation=35)
        ax.grid(True, axis="y", alpha=0.25); fig.tight_layout()
        fig.savefig(out_dir / "v3_ablations.png", dpi=160); plt.close(fig)


def parse_args_v3() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Ghost in the Machine v3 — long-run causal emergence laboratory")
    p.add_argument("--steps", type=int, default=100000, help="Main cycles (default: 100000)")
    p.add_argument("--seed", type=int, default=17)
    p.add_argument("--nodes", type=int, default=120)
    p.add_argument("--obs-dim", type=int, default=16)
    p.add_argument("--actions", type=int, default=7)
    p.add_argument("--calibration-steps", type=int, default=10000)
    p.add_argument("--diagnostic-interval", type=int, default=50)
    p.add_argument("--perturb-interval", type=int, default=1000)
    p.add_argument("--print-every", type=int, default=1000)
    p.add_argument("--consolidation-interval", type=int, default=5000)
    p.add_argument("--replay-batch", type=int, default=48)
    p.add_argument("--ablation-steps", type=int, default=3000)
    p.add_argument("--skip-ablations", action="store_true")
    p.add_argument("--skip-recovery", action="store_true")
    p.add_argument("--recovery-steps", type=int, default=700)
    p.add_argument("--lesion-target", type=str, default="workspace")
    p.add_argument("--checkpoint-every", type=int, default=10000)
    p.add_argument("--resume", type=str, default="", help="Resume from a v3 checkpoint pickle")
    p.add_argument("--no-plots", action="store_true")
    p.add_argument("--output", type=str, default="")
    return p.parse_args()


def validate_args_v3(args) -> None:
    if args.steps < 5000:
        raise SystemExit("--steps must be >= 5000 for v3")
    if args.nodes < 84:
        raise SystemExit("--nodes must be >= 84")
    if args.diagnostic_interval < 10:
        raise SystemExit("--diagnostic-interval must be >= 10")
    if args.perturb_interval < args.diagnostic_interval:
        raise SystemExit("--perturb-interval must be >= diagnostic interval")
    if args.calibration_steps >= args.steps:
        args.calibration_steps = max(1000, args.steps // 5)
    if args.lesion_target not in GhostMachineV3.MODULE_ORDER:
        raise SystemExit(f"Unknown lesion target {args.lesion_target!r}")


def print_header_v3(args) -> None:
    print("=" * 116)
    print("GHOST IN THE MACHINE v3.0 — CAUSAL EMERGENCE / MESOCIRCUIT LAB")
    print("=" * 116)
    print("Computational thought experiment only. No output is evidence, detection, or creation of subjective consciousness.")
    print(f"Main run: {args.steps:,} cycles | nodes={args.nodes} | actions={args.actions} | seed={args.seed}")
    print(f"Calibration: {args.calibration_steps:,} | diagnostics={args.diagnostic_interval} | PCI-like probe={args.perturb_interval}")
    print(f"Offline consolidation every {args.consolidation_interval:,} cycles | checkpoint every {args.checkpoint_every:,}")
    print("=" * 116)


def script_sha256() -> str:
    try:
        return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    except Exception:
        return "unavailable"


def main_v3() -> None:
    args = parse_args_v3(); validate_args_v3(args); print_header_v3(args)
    if args.output:
        out_dir = Path(args.output).expanduser().resolve()
    else:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_dir = Path.cwd() / f"ghost_v3_experiment_{stamp}"
    out_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = out_dir / "checkpoint.pkl"

    if args.resume:
        payload = load_checkpoint(Path(args.resume).expanduser().resolve())
        machine = payload["machine"]
        rows = payload.get("rows", [])
        start_step = int(payload["step"]) + 1
        print(f"[resume] loaded checkpoint at cycle {start_step - 1:,}")
        more, elapsed = run_machine_v3(
            machine, args.steps, args.print_every, collect_every_step=False,
            checkpoint_every=args.checkpoint_every, checkpoint_path=checkpoint_path,
            start_step=start_step,
        )
        rows.extend(more)
    else:
        machine = GhostMachineV3(
            seed=args.seed, nodes=args.nodes, obs_dim=args.obs_dim, action_count=args.actions,
            calibration_steps=args.calibration_steps, diagnostic_interval=args.diagnostic_interval,
            perturb_interval=args.perturb_interval, ablation="full",
            consolidation_interval=args.consolidation_interval, replay_batch=args.replay_batch,
        )
        rows, elapsed = run_machine_v3(
            machine, args.steps, args.print_every, collect_every_step=False,
            checkpoint_every=args.checkpoint_every, checkpoint_path=checkpoint_path,
        )

    summary = summarize_v3(machine, rows, elapsed)
    summary["script_sha256"] = script_sha256()
    summary["research_basis"] = [
        "10.1038/s41593-026-02220-4",
        "10.1038/s42003-026-10713-y",
        "10.1038/s43856-026-01870-6",
        "10.1038/s41586-025-08888-1",
        "10.1038/s42003-024-06613-8",
        "10.7554/eLife.86547",
    ]

    stim = machine.stimulation_scan_v3()
    surrogates = machine.surrogate_nulls()
    ablations: List[AblationResultV3] = []
    recovery: List[RecoveryResult] = []

    if not args.skip_ablations:
        ablations = run_ablations_v3(args)
        summary["ablations"] = [asdict(x) for x in ablations]
    if not args.skip_recovery:
        print("\nRunning lesion/recovery stimulation scan...")
        recovery = lesion_recovery_scan(machine, lesion_target=args.lesion_target, steps=args.recovery_steps)
        summary["lesion_recovery"] = [asdict(x) for x in recovery]

    summary["stimulation_scan"] = [asdict(x) for x in stim]
    summary["surrogate_nulls"] = [asdict(x) for x in surrogates]

    write_csv(out_dir / "trajectory_v3.csv", rows)
    write_csv(out_dir / "stimulation_scan_v3.csv", stim)
    write_csv(out_dir / "surrogate_nulls_v3.csv", surrogates)
    if ablations:
        write_csv(out_dir / "ablations_v3.csv", ablations)
    if recovery:
        write_csv(out_dir / "lesion_recovery_v3.csv", recovery)
    with (out_dir / "summary_v3.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    if not args.no_plots:
        try:
            create_plots_v3(out_dir, rows, ablations)
        except Exception as exc:
            print(f"[warning] v3 plot generation failed: {exc}")

    print("\n" + "=" * 116)
    print("v3 EXPERIMENT COMPLETE")
    print("=" * 116)
    print(f"Main-run elapsed       : {elapsed:.2f} s")
    print(f"First v3 event         : {summary.get('first_event_step')}")
    print(f"v3 events              : {summary.get('ghost_events')}")
    print(f"Mean convergence       : {summary.get('mean_convergence', 0.0):.4f}")
    print(f"Max convergence        : {summary.get('max_convergence', 0.0):.4f}")
    print(f"Topology balance       : {summary.get('mean_topology_balance', 0.0):.4f}")
    print(f"Avalanche criticality  : {summary.get('mean_avalanche_criticality', 0.0):.4f}")
    print(f"Counterfactual agency  : {summary.get('mean_counterfactual_agency', 0.0):.4f}")
    print(f"Mesocircuit flow       : {summary.get('mean_mesocircuit_flow', 0.0):.4f}")
    print(f"Change points          : {summary.get('change_points')}")
    print(f"Consolidation events   : {summary.get('consolidation_events')}")
    print(f"Results directory      : {out_dir}")
    print("\nInterpretation: 'GHOST-v3' is a sustained multi-proxy computational event only.")
    print("It neither proves nor measures phenomenal consciousness.")


if __name__ == "__main__":
    main_v3()
