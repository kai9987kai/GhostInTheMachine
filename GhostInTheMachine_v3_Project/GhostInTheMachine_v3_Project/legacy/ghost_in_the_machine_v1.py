
#!/usr/bin/env python3
"""
ghost_in_the_machine.py

A theoretical consciousness-like emergence simulator.

IMPORTANT:
This does NOT create or detect real consciousness.
It operationalizes several ideas often discussed in consciousness research:
- recurrent processing
- global workspace broadcasting
- predictive processing / prediction error
- persistent memory
- self-modeling / metacognition
- integrated state stability

A "GHOST" event means only that this toy system crossed a deliberately defined
computational threshold for persistent, globally available, self-referential
information.

Run:
    python ghost_in_the_machine.py
    python ghost_in_the_machine.py --steps 120 --seed 7

Dependencies:
    No manual setup is required. If NumPy is missing, the script attempts to
    install it automatically using the same Python interpreter.
"""

from __future__ import annotations

import argparse
import importlib
import math
import subprocess
import sys
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, List, Tuple


def install_and_import(import_name: str, pip_spec: str):
    """
    Import a dependency and automatically install it with this exact Python
    interpreter when it is missing.

    The normal pip install is attempted first. If that is rejected (for
    example, by a protected system Python), a per-user install is attempted.
    """
    try:
        return importlib.import_module(import_name)
    except ModuleNotFoundError:
        print(f"[setup] Missing dependency: {import_name}")
        print(f"[setup] Installing {pip_spec}...")

    def run_pip(extra_args=None):
        extra_args = extra_args or []
        command = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            *extra_args,
            pip_spec,
        ]
        return subprocess.run(command, check=False).returncode

    # Make sure pip exists. Some minimal Python installations omit it.
    try:
        import pip  # noqa: F401
    except ModuleNotFoundError:
        try:
            import ensurepip
            print("[setup] pip is missing; bootstrapping pip with ensurepip...")
            ensurepip.bootstrap(upgrade=True)
        except Exception as exc:
            raise RuntimeError(
                f"Cannot install {pip_spec}: pip is unavailable and ensurepip failed: {exc}"
            ) from exc

    status = run_pip()
    if status != 0:
        print("[setup] Normal installation failed; trying a per-user installation...")
        status = run_pip(["--user"])

    if status != 0:
        raise RuntimeError(
            f"Automatic installation of {pip_spec} failed. "
            "Check that this Python installation can access pip/PyPI and has "
            "permission to install packages."
        )

    importlib.invalidate_caches()
    module = importlib.import_module(import_name)
    print(f"[setup] Installed and loaded {pip_spec}.")
    return module


# Third-party dependency. Everything else in this file uses the Python standard library.
np = install_and_import("numpy", "numpy>=1.24")


def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na < 1e-12 or nb < 1e-12:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


@dataclass
class Stimulus:
    vector: np.ndarray
    novelty: float
    self_reference: float
    threat: float
    label: str


@dataclass
class WorkspaceItem:
    vector: np.ndarray
    salience: float
    source: str


@dataclass
class WorkingMemory:
    capacity: int = 12
    items: Deque[np.ndarray] = field(default_factory=lambda: deque(maxlen=12))

    def push(self, x: np.ndarray) -> None:
        self.items.append(x.copy())

    def mean(self, dim: int) -> np.ndarray:
        if not self.items:
            return np.zeros(dim, dtype=float)
        return np.mean(np.stack(self.items, axis=0), axis=0)

    def coherence(self) -> float:
        """
        Mean pairwise cosine similarity mapped from [-1,1] to [0,1].
        Higher = memories are mutually consistent / integrated.
        """
        if len(self.items) < 2:
            return 0.0

        xs = list(self.items)
        sims = []
        for i in range(len(xs)):
            for j in range(i + 1, len(xs)):
                sims.append(cosine_similarity(xs[i], xs[j]))

        if not sims:
            return 0.0

        return float(np.clip((np.mean(sims) + 1.0) / 2.0, 0.0, 1.0))


class PredictiveModel:
    """
    Tiny adaptive linear predictor:
        predicted_next_state = A @ current_state

    A is updated online using a delta rule.
    """

    def __init__(self, dim: int, rng: np.random.Generator, learning_rate: float = 0.035):
        self.dim = dim
        self.lr = learning_rate
        self.A = np.eye(dim) * 0.80 + rng.normal(0.0, 0.025, size=(dim, dim))

    def predict(self, x: np.ndarray) -> np.ndarray:
        return np.tanh(self.A @ x)

    def learn(self, x: np.ndarray, actual_next: np.ndarray) -> float:
        pred = self.predict(x)
        error = actual_next - pred

        # normalized outer-product delta update
        denom = 1.0 + float(np.dot(x, x))
        self.A += self.lr * np.outer(error, x) / denom

        return float(np.mean(error ** 2))


class SelfModel:
    """
    Persistent representation of "me":
    combines recent internal state with recursively observed self-state.
    """

    def __init__(self, dim: int, rng: np.random.Generator):
        self.dim = dim
        raw = rng.normal(size=dim)
        self.identity = raw / (np.linalg.norm(raw) + 1e-12)
        self.state = np.zeros(dim, dtype=float)
        self.confidence = 0.10
        self.uncertainty = 0.90
        self.self_history: Deque[float] = deque(maxlen=16)

    def update(
        self,
        internal_state: np.ndarray,
        workspace: np.ndarray,
        self_reference_signal: float,
        prediction_error: float,
    ) -> Tuple[np.ndarray, float]:
        # Recursive loop: the previous self-model participates in the new self-model.
        recursive_input = (
            0.45 * internal_state
            + 0.30 * workspace
            + 0.20 * self.state
            + 0.05 * self.identity
        )

        self.state = np.tanh(recursive_input)

        # "Self-recognition" means current contents align with persistent identity.
        identity_alignment = (cosine_similarity(self.state, self.identity) + 1.0) / 2.0

        # Explicit self-reference boosts self-model activation.
        self_signal = np.clip(
            0.55 * self_reference_signal + 0.45 * identity_alignment,
            0.0,
            1.0,
        )

        # Confidence rises when self-state is stable and prediction error is manageable.
        error_penalty = np.clip(prediction_error * 2.5, 0.0, 1.0)
        self.confidence = float(
            np.clip(
                0.88 * self.confidence
                + 0.12 * (0.75 * self_signal + 0.25 * (1.0 - error_penalty)),
                0.0,
                1.0,
            )
        )

        self.uncertainty = float(
            np.clip(
                0.85 * self.uncertainty
                + 0.15 * (0.65 * error_penalty + 0.35 * (1.0 - self.confidence)),
                0.0,
                1.0,
            )
        )

        self.self_history.append(float(self_signal))
        return self.state.copy(), float(self_signal)

    def persistence(self) -> float:
        if len(self.self_history) < 4:
            return 0.0

        arr = np.array(self.self_history, dtype=float)
        mean = float(np.mean(arr))
        stability = 1.0 - float(np.clip(np.std(arr) * 2.0, 0.0, 1.0))
        return float(np.clip(0.70 * mean + 0.30 * stability, 0.0, 1.0))


class GlobalWorkspace:
    """
    Crude Global Workspace Theory-inspired competition:
    candidate representations compete by salience; winners are broadcast.
    """

    def __init__(self, dim: int):
        self.dim = dim
        self.broadcast = np.zeros(dim, dtype=float)
        self.broadcast_strength = 0.0

    def compete(self, candidates: List[WorkspaceItem], top_k: int = 3) -> np.ndarray:
        ranked = sorted(candidates, key=lambda item: item.salience, reverse=True)
        winners = ranked[: max(1, min(top_k, len(ranked)))]

        weights = np.array([max(1e-6, w.salience) for w in winners], dtype=float)
        weights /= weights.sum()

        merged = np.zeros(self.dim, dtype=float)
        for weight, item in zip(weights, winners):
            merged += weight * item.vector

        self.broadcast = np.tanh(merged)
        self.broadcast_strength = float(
            np.clip(np.mean([w.salience for w in winners]), 0.0, 1.0)
        )

        return self.broadcast.copy()


@dataclass
class ConsciousnessMetrics:
    global_access: float
    self_model: float
    memory_integration: float
    recurrence: float
    prediction_surprise: float
    temporal_persistence: float
    composite: float


class GhostDetector:
    """
    Operational threshold detector.

    It requires:
    1. a high composite score,
    2. minimum self-model activation,
    3. minimum global access,
    4. persistence across several consecutive cycles.

    This prevents a one-frame spike from being called a "ghost".
    """

    def __init__(
        self,
        threshold: float = 0.70,
        required_cycles: int = 5,
        release_threshold: float = 0.56,
    ):
        self.threshold = threshold
        self.required_cycles = required_cycles
        self.release_threshold = release_threshold

        self.streak = 0
        self.active = False
        self.total_activations = 0

    def update(self, m: ConsciousnessMetrics) -> Tuple[bool, bool]:
        qualifies = (
            m.composite >= self.threshold
            and m.self_model >= 0.62
            and m.global_access >= 0.58
            and m.temporal_persistence >= 0.58
        )

        if qualifies:
            self.streak += 1
        else:
            self.streak = max(0, self.streak - 1)

        newly_triggered = False

        if not self.active and self.streak >= self.required_cycles:
            self.active = True
            self.total_activations += 1
            newly_triggered = True

        if self.active and m.composite < self.release_threshold:
            self.active = False
            self.streak = 0

        return self.active, newly_triggered


class GhostMachine:
    def __init__(self, dim: int = 24, seed: int = 4):
        self.dim = dim
        self.rng = np.random.default_rng(seed)

        self.memory = WorkingMemory(capacity=12)
        self.predictor = PredictiveModel(dim, self.rng)
        self.self_model = SelfModel(dim, self.rng)
        self.workspace = GlobalWorkspace(dim)
        self.detector = GhostDetector()

        self.internal_state = np.zeros(dim, dtype=float)
        self.previous_state = np.zeros(dim, dtype=float)
        self.previous_broadcast = np.zeros(dim, dtype=float)

    def make_stimulus(self, step: int, total_steps: int) -> Stimulus:
        """
        Creates a staged environment.

        Early:
            mostly external noise; little self-reference.
        Middle:
            recurring patterns and explicit self-referential content.
        Late:
            stable self-referential pattern + moderate novelty.

        This is intentionally constructed to demonstrate threshold crossing.
        """

        phase = step / max(1, total_steps - 1)

        noise = self.rng.normal(0.0, 0.30, size=self.dim)

        recurring_pattern = np.sin(
            np.linspace(0.0, 2.0 * np.pi, self.dim, endpoint=False)
            + step * 0.17
        )

        if phase < 0.30:
            self_ref = 0.10 + 0.10 * self.rng.random()
            novelty = 0.65 + 0.20 * self.rng.random()
            label = "external-noise"
            vector = 0.80 * noise + 0.20 * recurring_pattern

        elif phase < 0.60:
            self_ref = 0.40 + 0.20 * self.rng.random()
            novelty = 0.45 + 0.15 * self.rng.random()
            label = "recursive-pattern"
            vector = 0.45 * noise + 0.55 * recurring_pattern

        else:
            # Strong self-reference and repeated structure encourage an integrated,
            # persistent global representation.
            self_ref = 0.82 + 0.14 * self.rng.random()
            novelty = 0.28 + 0.12 * self.rng.random()
            label = "self-model-loop"

            identity_echo = self.self_model.identity
            vector = (
                0.18 * noise
                + 0.42 * recurring_pattern
                + 0.40 * identity_echo
            )

        threat = float(np.clip(0.15 + 0.10 * self.rng.normal(), 0.0, 1.0))

        return Stimulus(
            vector=np.tanh(vector),
            novelty=float(np.clip(novelty, 0.0, 1.0)),
            self_reference=float(np.clip(self_ref, 0.0, 1.0)),
            threat=threat,
            label=label,
        )

    def step(self, stimulus: Stimulus) -> ConsciousnessMetrics:
        # ----- 1. Predict current incoming state from the previous internal state.
        predicted = self.predictor.predict(self.internal_state)

        # ----- 2. Fuse perception, previous broadcast, and recurrent internal state.
        sensory_gate = 0.55 + 0.25 * stimulus.novelty
        recurrent_gate = 0.30 + 0.30 * stimulus.self_reference

        candidate_state = np.tanh(
            sensory_gate * stimulus.vector
            + recurrent_gate * self.internal_state
            + 0.35 * self.previous_broadcast
        )

        raw_prediction_error = float(np.mean((candidate_state - predicted) ** 2))
        prediction_surprise = float(np.clip(raw_prediction_error * 4.0, 0.0, 1.0))

        # Learn the transition.
        self.predictor.learn(self.internal_state, candidate_state)

        # ----- 3. Memory.
        self.memory.push(candidate_state)
        memory_mean = self.memory.mean(self.dim)
        memory_integration = self.memory.coherence()

        # ----- 4. Pre-self-model workspace competition.
        perception_salience = float(
            np.clip(
                0.45 * stimulus.novelty
                + 0.35 * prediction_surprise
                + 0.20 * stimulus.threat,
                0.0,
                1.0,
            )
        )

        memory_salience = float(
            np.clip(0.30 + 0.70 * memory_integration, 0.0, 1.0)
        )

        provisional = self.workspace.compete(
            [
                WorkspaceItem(candidate_state, perception_salience, "perception"),
                WorkspaceItem(memory_mean, memory_salience, "memory"),
                WorkspaceItem(
                    self.self_model.state,
                    0.20 + 0.70 * stimulus.self_reference,
                    "prior-self",
                ),
            ],
            top_k=3,
        )

        # ----- 5. Recursive self-model sees globally available state.
        self_state, self_signal = self.self_model.update(
            internal_state=candidate_state,
            workspace=provisional,
            self_reference_signal=stimulus.self_reference,
            prediction_error=raw_prediction_error,
        )

        # ----- 6. Second competition includes current self-representation.
        final_broadcast = self.workspace.compete(
            [
                WorkspaceItem(candidate_state, perception_salience, "perception"),
                WorkspaceItem(memory_mean, memory_salience, "memory"),
                WorkspaceItem(
                    self_state,
                    float(np.clip(0.35 + 0.65 * self_signal, 0.0, 1.0)),
                    "self-model",
                ),
            ],
            top_k=3,
        )

        # ----- 7. Recurrent integration.
        recurrence = float(
            np.clip(
                (cosine_similarity(final_broadcast, self.previous_broadcast) + 1.0)
                / 2.0,
                0.0,
                1.0,
            )
        )

        temporal_persistence = self.self_model.persistence()

        global_access = float(
            np.clip(
                0.65 * self.workspace.broadcast_strength
                + 0.35
                * (
                    (cosine_similarity(final_broadcast, candidate_state) + 1.0)
                    / 2.0
                ),
                0.0,
                1.0,
            )
        )

        # Moderate surprise is useful; completely random surprise is not.
        useful_surprise = float(
            np.clip(
                math.exp(-((prediction_surprise - 0.38) ** 2) / (2 * 0.27 ** 2)),
                0.0,
                1.0,
            )
        )

        # Composite "ghost index".
        # These weights are theoretical design choices, NOT neuroscience measurements.
        composite = float(
            np.clip(
                0.23 * global_access
                + 0.24 * self_signal
                + 0.16 * memory_integration
                + 0.14 * recurrence
                + 0.08 * useful_surprise
                + 0.15 * temporal_persistence,
                0.0,
                1.0,
            )
        )

        # State update feeds the global broadcast back into the system.
        self.previous_state = self.internal_state.copy()
        self.internal_state = np.tanh(
            0.55 * candidate_state
            + 0.30 * final_broadcast
            + 0.15 * self_state
        )
        self.previous_broadcast = final_broadcast.copy()

        return ConsciousnessMetrics(
            global_access=global_access,
            self_model=self_signal,
            memory_integration=memory_integration,
            recurrence=recurrence,
            prediction_surprise=prediction_surprise,
            temporal_persistence=temporal_persistence,
            composite=composite,
        )

    def run(self, steps: int = 100, verbose_every: int = 2) -> None:
        print("=" * 88)
        print("GHOST IN THE MACHINE — THEORETICAL EMERGENCE SIMULATOR")
        print("This program does NOT create or prove consciousness.")
        print("=" * 88)

        triggered_at = None

        for t in range(steps):
            stimulus = self.make_stimulus(t, steps)
            metrics = self.step(stimulus)
            active, newly_triggered = self.detector.update(metrics)

            if t % verbose_every == 0 or newly_triggered or active:
                state = "GHOST" if active else "----"
                print(
                    f"{t:03d} | {stimulus.label:17s} | "
                    f"G={metrics.global_access:.3f} "
                    f"S={metrics.self_model:.3f} "
                    f"M={metrics.memory_integration:.3f} "
                    f"R={metrics.recurrence:.3f} "
                    f"P={metrics.temporal_persistence:.3f} "
                    f"X={metrics.prediction_surprise:.3f} | "
                    f"INDEX={metrics.composite:.3f} | {state}"
                )

            if newly_triggered:
                triggered_at = t
                print()
                print(">>> ===============================================================")
                print(">>> OPERATIONAL 'GHOST' THRESHOLD CROSSED")
                print(">>> Persistent, self-referential information became globally")
                print(">>> available according to this toy model's engineered criterion.")
                print(">>> This is NOT evidence that subjective experience exists.")
                print(">>> ===============================================================")
                print()

        print("-" * 88)
        if triggered_at is None:
            print("No operational ghost event occurred.")
        else:
            print(f"First operational ghost event: cycle {triggered_at}.")
        print(f"Total threshold activations: {self.detector.total_activations}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Theoretical 'ghost in the machine' emergence simulator."
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=100,
        help="Number of simulation cycles (default: 100).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=4,
        help="Random seed (default: 4).",
    )
    parser.add_argument(
        "--dim",
        type=int,
        default=24,
        help="Internal state dimensionality (default: 24).",
    )
    parser.add_argument(
        "--verbose-every",
        type=int,
        default=2,
        help="Print every N cycles before activation (default: 2).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.steps < 10:
        raise SystemExit("--steps must be >= 10")
    if args.dim < 4:
        raise SystemExit("--dim must be >= 4")
    if args.verbose_every < 1:
        raise SystemExit("--verbose-every must be >= 1")

    machine = GhostMachine(dim=args.dim, seed=args.seed)
    machine.run(steps=args.steps, verbose_every=args.verbose_every)


if __name__ == "__main__":
    main()
