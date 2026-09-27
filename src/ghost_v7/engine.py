"""
v7 agent engine: the v6 agent with the comparator input split into two parts.

The live comparator input is the mismatch m_t = obs_t - forward_model(x_t, intention_t).
v7 writes it as the sum of

    feedback    f_t = c + B x_t, the part a fixed linear map predicts from the
                network's own current state (B, c fitted beforehand by ridge
                regression on a reference run), and
    innovation  i_t = m_t - f_t, the rest.

From cycle ``replay_start`` either part can be replaced by a prescribed stream while
the other stays live: ``fb_replay`` replaces f_t, ``inn_replay`` replaces i_t. With
both live the comparator injects f_t + (m_t - f_t) = m_t, as in v7. With a live
feedback part and a replayed innovation, the comparator still closes a loop through
the network's own state; with a replayed feedback part it does not.

Everything v6 can do (``cmp_replay``, ``cmp_gain``, authorship) is kept, and with
default settings v7 reproduces v6 (and so v5 and v4) bit for bit
(tests/test_v7.py).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np

from ghost_v4.engine import (AgentConfig, LatentWorld, Record, Stream, _projection, build_recurrent_matrix,
                             build_slices)


@dataclass(frozen=True)
class V7Config:
    base: AgentConfig
    authorship: float = 1.0
    cmp_gain: float = 1.0
    replay_start: int = 0
    comparator_targets: Tuple[str, ...] = ("self", "association")

    def label(self) -> str:
        parts = [self.base.label()]
        if self.authorship != 1.0:
            parts.append(f"auth{self.authorship:g}")
        if self.cmp_gain != 1.0:
            parts.append(f"gain{self.cmp_gain:g}")
        if tuple(self.comparator_targets) != ("self", "association"):
            parts.append("cmp->" + "+".join(self.comparator_targets))
        return "|".join(parts)


def run_agent_v7(v7: V7Config, yoke: Optional[Stream] = None, donor_actions: Optional[np.ndarray] = None,
                 cmp_replay: Optional[np.ndarray] = None, fb_B: Optional[np.ndarray] = None,
                 fb_c: Optional[np.ndarray] = None, fb_replay: Optional[np.ndarray] = None,
                 inn_replay: Optional[np.ndarray] = None) -> Record:
    cfg = v7.base
    n, A, D = cfg.nodes, cfg.actions, cfg.obs_dim
    T = cfg.steps
    if yoke is not None and len(yoke.executed) < T:
        raise ValueError("yoke stream shorter than requested steps")
    if v7.authorship < 1.0 and yoke is None and (donor_actions is None or len(donor_actions) < T):
        raise ValueError("graded authorship needs a donor action sequence of length >= steps")
    if cmp_replay is not None:
        cmp_replay = np.asarray(cmp_replay, dtype=float)
        if cmp_replay.shape[0] < T or cmp_replay.shape[1] != D:
            raise ValueError("cmp_replay must have shape (>= steps, obs_dim)")
    split = fb_B is not None
    if split:
        if cmp_replay is not None:
            raise ValueError("use either cmp_replay or the feedback/innovation split, not both")
        fb_B = np.asarray(fb_B, dtype=float)
        fb_c = np.zeros(D) if fb_c is None else np.asarray(fb_c, dtype=float)
        if fb_B.shape != (D, cfg.nodes) or fb_c.shape != (D,):
            raise ValueError("fb_B must be (obs_dim, nodes) and fb_c (obs_dim,)")
        for name, arr in (("fb_replay", fb_replay), ("inn_replay", inn_replay)):
            if arr is not None and (arr.shape[0] < T or arr.shape[1] != D):
                raise ValueError(f"{name} must have shape (>= steps, obs_dim)")
    elif fb_replay is not None or inn_replay is not None:
        raise ValueError("fb_replay / inn_replay need fb_B")

    net = np.random.default_rng([cfg.net_seed, 101])
    act_rng = np.random.default_rng([cfg.net_seed, 202, cfg.replicate])
    auth_rng = np.random.default_rng([cfg.net_seed, 909, cfg.replicate])
    slices = build_slices(n)
    W = build_recurrent_matrix(net, n, slices)
    if cfg.lesion != "none":
        a, b = slices[cfg.lesion]
        W[a:b, :] *= 0.04
        W[:, a:b] *= 0.04
    g = cfg.radius

    W_in = _projection(net, n, D, slices, ["sensory"], 0.23)
    W_eff = _projection(net, n, A, slices, ["control", "self"], 0.18)
    W_cmp = _projection(net, n, D, slices, list(v7.comparator_targets), 0.20)
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
    mm_vec = np.empty((T, D), dtype=float)          # full live mismatch, float64 so it can be replayed exactly
    inj_rec = np.zeros(T, dtype=np.float32)         # RMS of the comparator input actually injected

    for t in range(T):
        base = Wf[:, :, :n] @ x
        preds = np.tanh(base[:, None, :] + Wf[:, :, n:].transpose(0, 2, 1))
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
            if v7.authorship < 1.0 and auth_rng.random() >= v7.authorship:
                executed = int(donor_actions[t])
            obs = world.step(executed)
        else:
            executed = int(yoke.executed[t])
            obs = np.asarray(yoke.obs[t + 1], dtype=float)

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

        drive = W_in @ obs + W_eff @ e_int
        if cfg.comparator:
            if split and t >= v7.replay_start:
                fb_live = fb_c + fb_B @ x
                fb = fb_replay[t] if fb_replay is not None else fb_live
                inn = inn_replay[t] if inn_replay is not None else mismatch - fb_live
                src = fb + inn
            else:
                src = cmp_replay[t] if (cmp_replay is not None and t >= v7.replay_start) else mismatch
            if v7.cmp_gain != 1.0:
                src = v7.cmp_gain * src
            drive += W_cmp @ src
            inj_rec[t] = math.sqrt(float(np.mean(src ** 2)))
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
            err_f = obs[None, :] - np.tanh(Wf @ inp)
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
        mm_vec[t] = mismatch

        x = x_new
        obs_prev = obs

    rec = Record(
        config=cfg, mode="master" if yoke is None else "yoked", slices=slices,
        X=X, obs=OBS, intended=intended_rec, executed=executed_rec,
        ignition=ign_rec, cf_agency=cf_rec, pred_error=pe_rec, self_error=se_rec,
        mismatch=mm_rec, gain=g, W=W, final_state=x.copy(),
        yoked_to=None if yoke is None else yoke.source_net_seed,
    )
    rec.v7 = v7
    rec.mismatch_vec = mm_vec
    rec.injected_rms = inj_rec
    return rec
