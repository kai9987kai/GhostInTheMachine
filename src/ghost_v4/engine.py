"""
The v4 agent: a closed-loop recurrent self/world-modelling system that can also
be run as a cross-yoked twin.

Changes relative to the v3 engine, each motivated by the v3 forensic audit:

* No gain ramp. v3's homeostatic rule chased an activity target (0.31) that
  the network never reached, so recurrent gain rose monotonically to its 1.18
  ceiling while the v3 event fired. v4 fixes the effective spectral radius
  g * rho(W) as a declared design parameter (default 1.0).
* Efference copy and comparator (reafference principle; von Holst &
  Mittelstaedt 1950; Frith, Blakemore & Wolpert 2000). The agent's motor
  command is copied to its forward models and to the self/control populations;
  the mismatch between predicted and actual consequences is fed back.
* Self-surprise feedback: the self model's own prediction error re-enters the
  self and workspace populations, so the self model has causal work to do.
* Full trajectory recording. Every observational metric in v4 is a pure
  function of the recorded arrays, so real and surrogate data pass through an
  identical pipeline (v3 computed metrics online, which made a metric-identical
  surrogate test impossible).
* Yoked mode. A twin network receives, step for step, the observation stream
  and executed actions recorded from ANOTHER agent's closed-loop run in the same
  world. It still forms its own intentions (policy, efference copy, learning)
  but those intentions no longer cause what it senses. This is the yoked-control
  design of behavioural neuroscience and a computational analogue of Baars'
  contrastive method: matched stimulation, different causal relationship.

The population labels are computational abstractions, not anatomy.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field, replace
from typing import Dict, Optional, Tuple

import numpy as np

POPULATIONS = (
    "sensory", "association", "memory", "workspace", "self", "dmn",
    "thalamus", "striatum", "gpe", "stn", "gpi", "control",
)

_RATIOS = {
    "sensory": 0.12, "association": 0.11, "memory": 0.10,
    "workspace": 0.15, "self": 0.10, "dmn": 0.08,
    "thalamus": 0.08, "striatum": 0.06, "gpe": 0.05,
    "stn": 0.04, "gpi": 0.04, "control": 0.07,
}


@dataclass(frozen=True)
class AgentConfig:
    net_seed: int = 0
    world_seed: int = 1
    nodes: int = 120
    obs_dim: int = 16
    latent_dim: int = 9
    actions: int = 7
    steps: int = 6000
    radius: float = 1.0          # fixed effective spectral radius g * rho(W)
    leak: float = 0.5            # leaky rate units: x <- (1-leak) x + leak tanh(.); 1.0 = v3's memoryless update
    temperature: float = 0.18    # policy softmax temperature
    learning: bool = True
    efference: bool = True       # motor command copied to network + forward model
    comparator: bool = True      # predicted-vs-actual sensory mismatch fed back
    self_feedback: bool = True   # self-model prediction error fed back
    lesion: str = "none"         # a population name to silence, or "none"
    replicate: int = 0           # re-seeds world noise + action sampling only (placebo A/A runs)

    def label(self) -> str:
        parts = []
        if not self.learning:
            parts.append("frozen")
        if not self.efference:
            parts.append("no_efference")
        if not self.comparator:
            parts.append("no_comparator")
        if not self.self_feedback:
            parts.append("no_selffeedback")
        if self.lesion != "none":
            parts.append(f"lesion_{self.lesion}")
        if self.replicate:
            parts.append(f"rep{self.replicate}")
        return "+".join(parts) or "full"


@dataclass
class Stream:
    """What a yoked twin receives: observations (T+1) and executed actions (T)."""
    obs: np.ndarray
    executed: np.ndarray
    source_net_seed: int


@dataclass
class Record:
    config: AgentConfig
    mode: str                      # "master" | "yoked"
    slices: Dict[str, Tuple[int, int]]
    X: np.ndarray                  # (T, nodes) state after each step
    obs: np.ndarray                # (T+1, obs_dim); obs[t+1] is sensed at step t
    intended: np.ndarray           # (T,) the agent's own motor command
    executed: np.ndarray           # (T,) what the world actually received
    ignition: np.ndarray
    cf_agency: np.ndarray
    pred_error: np.ndarray
    self_error: np.ndarray
    mismatch: np.ndarray
    gain: float
    W: np.ndarray
    final_state: np.ndarray
    yoked_to: Optional[int] = None

    def stream(self) -> Stream:
        return Stream(self.obs.copy(), self.executed.copy(), self.config.net_seed)

    def population(self, name: str, start: int = 0) -> np.ndarray:
        a, b = self.slices[name]
        return self.X[start:, a:b]


def build_slices(nodes: int) -> Dict[str, Tuple[int, int]]:
    sizes = [max(5, int(nodes * _RATIOS[n])) for n in POPULATIONS]
    sizes[POPULATIONS.index("workspace")] += nodes - sum(sizes)
    out, start = {}, 0
    for name, size in zip(POPULATIONS, sizes):
        out[name] = (start, start + size)
        start += size
    return out


def build_recurrent_matrix(rng: np.random.Generator, nodes: int, slices) -> np.ndarray:
    """The v3 cortico-thalamo-basal-ganglia motif (Dale-like, indirect pathway), unchanged."""
    W = np.zeros((nodes, nodes))

    def add(dst, src, scale, density, sign=0):
        (da, db), (sa, sb) = slices[dst], slices[src]
        shape = (db - da, sb - sa)
        block = np.abs(rng.normal(0.0, scale, size=shape)) * (rng.random(shape) < density)
        if sign < 0:
            block *= -1.0
        elif sign == 0:
            block *= rng.choice([-1.0, 1.0], size=shape, p=[0.20, 0.80])
        W[da:db, sa:sb] += block

    for name in POPULATIONS:
        add(name, name, 0.11, 0.22, 0)
    for dst, src, sc, de in (
        ("association", "sensory", 0.16, 0.30), ("memory", "association", 0.13, 0.26),
        ("workspace", "association", 0.16, 0.30), ("workspace", "memory", 0.15, 0.28),
        ("self", "workspace", 0.15, 0.30), ("self", "memory", 0.11, 0.23),
        ("dmn", "self", 0.12, 0.24), ("dmn", "memory", 0.11, 0.22),
        ("workspace", "dmn", 0.11, 0.22), ("control", "workspace", 0.13, 0.25),
        ("workspace", "control", 0.10, 0.20), ("association", "workspace", 0.09, 0.18),
    ):
        add(dst, src, sc, de, +1)
    for other in ("sensory", "association", "workspace", "control"):
        add("thalamus", other, 0.13, 0.27, +1)
        add(other, "thalamus", 0.13, 0.27, +1)
    add("striatum", "control", 0.14, 0.32, +1)
    add("striatum", "workspace", 0.10, 0.22, +1)
    add("gpe", "striatum", 0.17, 0.38, -1)
    add("stn", "gpe", 0.17, 0.38, -1)
    add("gpi", "stn", 0.17, 0.38, +1)
    add("thalamus", "gpi", 0.18, 0.40, -1)
    add("gpe", "stn", 0.09, 0.20, +1)
    add("control", "thalamus", 0.11, 0.22, +1)
    np.fill_diagonal(W, 0.0)

    signs = rng.choice([1.0, -1.0], size=nodes, p=[0.80, 0.20])
    for j in range(nodes):
        weak = np.abs(W[:, j]) < 0.16
        W[weak, j] = np.abs(W[weak, j]) * signs[j]
    pos, neg = float(W[W > 0].sum()), float(-W[W < 0].sum())
    if pos > 1e-9 and neg > 1e-9:
        W[W < 0] *= 0.92 * pos / neg
    rho = float(np.max(np.abs(np.linalg.eigvals(W))))
    return W / max(rho, 1e-9)  # unit spectral radius; gain sets the regime


class LatentWorld:
    """The v3 partially observable nonlinear world, with its own random streams."""

    def __init__(self, world_seed: int, noise_seed: int, obs_dim: int, latent_dim: int, actions: int):
        p = np.random.default_rng(world_seed)
        A = p.normal(0.0, 0.30, size=(latent_dim, latent_dim))
        self.A = A * (0.87 / max(float(np.max(np.abs(np.linalg.eigvals(A)))), 1e-6))
        self.B = p.normal(0.0, 0.18, size=(latent_dim, actions))
        self.C = p.normal(0.0, 0.55, size=(obs_dim, latent_dim))
        self.hidden_driver = p.normal(0.0, 0.35, size=latent_dim)
        self.rng = np.random.default_rng([world_seed, noise_seed, 7])
        self.state = self.rng.normal(0.0, 0.20, size=latent_dim)
        self.t = 0

    def observe(self) -> np.ndarray:
        return np.tanh(self.C @ self.state + self.rng.normal(0.0, 0.025, len(self.C)))

    def step(self, action: int) -> np.ndarray:
        self.t += 1
        ctx = 0.13 * math.sin(self.t * 0.0067) + 0.08 * math.sin(self.t * 0.021) + 0.04 * math.sin(self.t * 0.093)
        exo = self.hidden_driver * ctx
        if self.rng.random() < 0.0025:
            exo = exo + self.rng.normal(0.0, 0.45, len(self.state))
        self.state = np.tanh(self.A @ self.state + self.B[:, action] + exo
                             + self.rng.normal(0.0, 0.035, len(self.state)))
        return self.observe()


def _projection(rng, nodes, width, slices, targets, scale):
    M = rng.normal(0.0, scale, size=(nodes, width))
    mask = np.zeros(nodes)
    for t in targets:
        a, b = slices[t]
        mask[a:b] = 1.0
    return M * mask[:, None]


def run_agent(cfg: AgentConfig, yoke: Optional[Stream] = None) -> Record:
    """Simulate one agent for cfg.steps cycles (closed loop, or yoked to `yoke`)."""
    n, A, D = cfg.nodes, cfg.actions, cfg.obs_dim
    T = cfg.steps
    if yoke is not None and len(yoke.executed) < T:
        raise ValueError("yoke stream shorter than requested steps")

    net = np.random.default_rng([cfg.net_seed, 101])
    act_rng = np.random.default_rng([cfg.net_seed, 202, cfg.replicate])
    slices = build_slices(n)
    W = build_recurrent_matrix(net, n, slices)
    if cfg.lesion != "none":
        a, b = slices[cfg.lesion]
        W[a:b, :] *= 0.04
        W[:, a:b] *= 0.04
    g = cfg.radius

    W_in = _projection(net, n, D, slices, ["sensory"], 0.23)
    W_eff = _projection(net, n, A, slices, ["control", "self"], 0.18)
    W_cmp = _projection(net, n, D, slices, ["self", "association"], 0.20)
    s0, s1 = slices["self"]
    ns = s1 - s0
    W_ss = _projection(net, n, ns, slices, ["self", "workspace"], 0.20)
    w0, w1 = slices["workspace"]
    W_b = net.normal(0.0, 1.0 / math.sqrt(w1 - w0), size=(n, w1 - w0))

    K = 3
    lrs = np.array([0.010, 0.009, 0.011])
    Wf = net.normal(0.0, 0.025, size=(K, D, n + A))
    Wself = net.normal(0.0, 0.025, size=(ns, n + A))
    wmeta = net.normal(0.0, 0.02, size=n)

    world = None
    if yoke is None:
        world = LatentWorld(cfg.world_seed, cfg.net_seed * 1000 + cfg.replicate, D, cfg.latent_dim, A)
        obs_prev = world.observe()
    else:
        obs_prev = np.asarray(yoke.obs[0], dtype=float)

    x = net.normal(0.0, 0.015, n)
    bcast = np.zeros(n)
    self_err_vec = np.zeros(ns)
    preferred = obs_prev.copy()
    effects = np.zeros((A, D))
    effect_counts = np.ones(A)
    uncertainty = np.ones(A)
    act_ema = 0.05
    eye_A = np.eye(A)

    X = np.empty((T, n), dtype=np.float32)
    OBS = np.empty((T + 1, D), dtype=np.float32)
    OBS[0] = obs_prev
    intended_rec = np.empty(T, dtype=np.int16)
    executed_rec = np.empty(T, dtype=np.int16)
    ign_rec = np.empty(T, dtype=np.float32)
    cf_rec = np.empty(T, dtype=np.float32)
    pe_rec = np.empty(T, dtype=np.float32)
    se_rec = np.empty(T, dtype=np.float32)
    mm_rec = np.empty(T, dtype=np.float32)

    for t in range(T):
        # --- policy: expected-free-energy-style scoring of every candidate action
        base = Wf[:, :, :n] @ x                                      # (K, D)
        preds = np.tanh(base[:, None, :] + Wf[:, :, n:].transpose(0, 2, 1))  # (K, A, D)
        mean_pred = preds.mean(axis=0)
        risk = np.mean((mean_pred - preferred) ** 2, axis=1)
        epi = np.mean(preds.var(axis=0), axis=1)
        ctrl = np.mean(np.abs(effects), axis=1)
        efe = (0.52 * risk / (risk.max() + 1e-9) - 0.28 * epi / (epi.max() + 1e-9)
               - 0.10 * ctrl / (ctrl.max() + 1e-9) - 0.10 * np.clip(uncertainty, 0, 1))
        logits = -(efe - efe.min()) / cfg.temperature
        probs = np.exp(logits - logits.max())
        probs /= probs.sum()
        intended = int(act_rng.choice(A, p=probs))

        if yoke is None:
            executed = intended
            obs = world.step(executed)
        else:
            executed = int(yoke.executed[t])
            obs = np.asarray(yoke.obs[t + 1], dtype=float)

        # --- comparator: consequence predicted from the agent's OWN command
        e_int = eye_A[intended] if cfg.efference else np.zeros(A)
        pred_obs = mean_pred[intended] if cfg.efference else mean_pred.mean(axis=0)
        mismatch = obs - pred_obs
        pred_mse = float(np.mean(mismatch ** 2))
        pred_err = min(1.0, pred_mse * 3.2)

        errs = np.mean((mean_pred - obs) ** 2, axis=1)
        chosen = float(errs[intended])
        others = float((errs.sum() - chosen) / (A - 1))
        adv = (others - chosen) / (others + chosen + 1e-9)
        cf = 0.5 + 0.5 * math.tanh(3.0 * adv)

        delta = obs - obs_prev
        eff_err = float(np.mean((delta - effects[intended]) ** 2))
        agency = math.exp(-7.0 * eff_err)
        if cfg.learning:
            lr_e = min(0.12, 1.0 / math.sqrt(effect_counts[intended] + 1.0))
            effects[intended] += lr_e * (delta - effects[intended])
            effect_counts[intended] += 1.0
            uncertainty[intended] = 0.985 * uncertainty[intended] + 0.015 * min(1.0, eff_err * 6.0)

        novelty = min(1.0, float(np.mean(np.abs(delta))) * 2.3)
        salience = min(1.0, 0.48 * pred_err + 0.34 * novelty + 0.18 * (1.0 - agency))

        # --- recurrent update with sensory input, efference copy and feedback
        drive = W_in @ obs + W_eff @ e_int
        if cfg.comparator:
            drive += W_cmp @ mismatch
        if cfg.self_feedback:
            drive += W_ss @ self_err_vec
        local = np.tanh(g * (W @ x) + drive + 0.13 * bcast)
        ws_energy = float(np.mean(np.abs(local[w0:w1])))
        threshold = 1.25 * act_ema + 0.08
        z = 7.0 * (ws_energy + 0.55 * salience - threshold)
        ignition = 1.0 / (1.0 + math.exp(-max(-60.0, min(60.0, z))))
        bcast = np.tanh(W_b @ local[w0:w1]) * ignition
        x_new = (1.0 - cfg.leak) * x + cfg.leak * np.tanh(local + 0.24 * bcast)

        inp = np.concatenate([x, e_int])
        pred_self = np.tanh(Wself @ inp)
        self_err_vec = x_new[s0:s1] - pred_self
        meta_pred = 1.0 / (1.0 + math.exp(-max(-60.0, min(60.0, float(wmeta @ x)))))

        if cfg.learning:
            denom = 1.0 + float(inp @ inp)
            err_f = obs[None, :] - np.tanh(Wf @ inp)                 # (K, D)
            Wf += (lrs[:, None, None] * err_f[:, :, None] * inp[None, None, :]) / denom
            Wself += 0.008 * np.outer(self_err_vec, inp) / denom
            wmeta += 0.006 * (pred_err - meta_pred) * x / (1.0 + float(x @ x))
        preferred = 0.9985 * preferred + 0.0015 * obs
        act_ema = 0.98 * act_ema + 0.02 * float(np.mean(np.abs(x_new)))

        X[t] = x_new
        OBS[t + 1] = obs
        intended_rec[t] = intended
        executed_rec[t] = executed
        ign_rec[t] = ignition
        cf_rec[t] = cf
        pe_rec[t] = pred_err
        se_rec[t] = float(np.mean(self_err_vec ** 2))
        mm_rec[t] = math.sqrt(pred_mse)

        x = x_new
        obs_prev = obs

    return Record(
        config=cfg, mode="master" if yoke is None else "yoked", slices=slices,
        X=X, obs=OBS, intended=intended_rec, executed=executed_rec,
        ignition=ign_rec, cf_agency=cf_rec, pred_error=pe_rec, self_error=se_rec,
        mismatch=mm_rec, gain=g, W=W, final_state=x.copy(),
        yoked_to=None if yoke is None else yoke.source_net_seed,
    )


def perturbational_response(W: np.ndarray, gain: float, state: np.ndarray, indices: np.ndarray,
                            rng: np.random.Generator, horizon: int = 60, leak: float = 1.0) -> Dict[str, float]:
    """
    Virtual TMS-like probe (the v3 procedure): perturb `indices`, propagate the
    autonomous network, and summarize the spatiotemporal response. PCI-inspired,
    not clinical PCI.
    """
    from .temporal import normalized_lz76
    base = state.copy()
    pert = state.copy()
    impulse = np.zeros_like(state)
    impulse[indices] = rng.normal(0.0, 0.42, size=len(indices))
    pert = np.tanh(pert + impulse)
    R = np.empty((horizon, len(state)))
    for h in range(horizon):
        base = (1.0 - leak) * base + leak * np.tanh(gain * (W @ base))
        pert = (1.0 - leak) * pert + leak * np.tanh(gain * (W @ pert))
        R[h] = np.abs(pert - base)
    binary = R > (R.max() + 1e-12) * 0.10
    return {
        "lz": normalized_lz76(binary.ravel()),
        "spread": float(np.mean(binary.any(axis=0))),
        "duration": float(np.mean(binary.any(axis=1))),
        "amplitude": float(np.mean(R)),
    }
