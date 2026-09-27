import numpy as np
import pytest

from ghost_v4 import infotheory as it
from ghost_v4.engine import AgentConfig
from ghost_v6.engine import V6Config, run_agent_v6
from ghost_v7 import studies as S
from ghost_v7.engine import V7Config, run_agent_v7
from ghost_v7.meta import _rho_from_nats, hksj


# ---------------------------------------------------------------- engine

def test_v7_defaults_reproduce_v6_master_and_twin_bit_for_bit():
    cfg = AgentConfig(net_seed=21, world_seed=4, steps=400)
    assert np.array_equal(run_agent_v6(V6Config(base=cfg)).X, run_agent_v7(V7Config(base=cfg)).X)
    donor = run_agent_v6(V6Config(base=AgentConfig(net_seed=22, world_seed=4, steps=400)))
    assert np.array_equal(run_agent_v6(V6Config(base=cfg), yoke=donor.stream()).X,
                          run_agent_v7(V7Config(base=cfg), yoke=donor.stream()).X)


def test_split_with_both_parts_live_is_the_live_run():
    cfg = AgentConfig(net_seed=26, world_seed=4, steps=400)
    live = run_agent_v7(V7Config(base=cfg))
    B, c, _ = S.fit_state_feedback(live.X, live.mismatch_vec, 200)
    split = run_agent_v7(V7Config(base=cfg, replay_start=200), fb_B=B, fb_c=c)
    assert np.array_equal(live.X[:200], split.X[:200])
    assert np.allclose(live.X, split.X, atol=1e-6)


def test_replaying_both_own_parts_approximately_reproduces_the_run():
    cfg = AgentConfig(net_seed=27, world_seed=4, steps=400)
    live = run_agent_v7(V7Config(base=cfg))
    B, c, _ = S.fit_state_feedback(live.X, live.mismatch_vec, 200)
    fb, inn = S.feedback_streams(live.X, live.mismatch_vec, B, c)
    assert np.allclose(fb + inn, live.mismatch_vec)
    rep = run_agent_v7(V7Config(base=cfg, replay_start=200), fb_B=B, fb_c=c, fb_replay=fb, inn_replay=inn)
    assert np.allclose(live.X, rep.X, atol=1e-3)


def test_desynchronizing_one_part_changes_the_run_after_the_window_only():
    cfg = AgentConfig(net_seed=28, world_seed=4, steps=400)
    live = run_agent_v7(V7Config(base=cfg))
    B, c, _ = S.fit_state_feedback(live.X, live.mismatch_vec, 200)
    fb, inn = S.feedback_streams(live.X, live.mismatch_vec, B, c)
    for kw in ({"inn_replay": S.window_shift(inn, 200)}, {"fb_replay": S.window_shift(fb, 200)}):
        alt = run_agent_v7(V7Config(base=cfg, replay_start=200), fb_B=B, fb_c=c, **kw)
        assert np.array_equal(live.X[:200], alt.X[:200])
        assert not np.allclose(live.X[200:], alt.X[200:])


def test_split_arguments_are_validated():
    cfg = V7Config(base=AgentConfig(steps=50))
    with pytest.raises(ValueError):
        run_agent_v7(cfg, fb_replay=np.zeros((50, 16)))
    with pytest.raises(ValueError):
        run_agent_v7(cfg, fb_B=np.zeros((16, 120)), cmp_replay=np.zeros((50, 16)))
    with pytest.raises(ValueError):
        run_agent_v7(cfg, fb_B=np.zeros((3, 3)))


# ---------------------------------------------------------------- decomposition and robust statistics

def test_state_feedback_fit_recovers_a_linear_map():
    r = np.random.default_rng(3)
    T, n, D, burn = 3000, 12, 4, 500
    X = r.standard_normal((T, n))
    B_true = r.normal(0, 0.5, (D, n))
    mm = np.zeros((T, D))
    mm[1:] = X[:-1] @ B_true.T + 0.3 * r.standard_normal((T - 1, D))
    B, c, r2 = S.fit_state_feedback(X, mm, burn)
    assert np.allclose(B, B_true, atol=0.05)
    expected = 1.0 - 0.09 * D / np.sum(np.var(mm[burn:], axis=0))
    assert abs(r2 - expected) < 0.03


def test_signed_rank_resists_a_few_extreme_networks():
    r = np.random.default_rng(4)
    d = np.concatenate([r.normal(0.1, 0.05, 22), [-0.9, -0.9]])
    from ghost_v4 import stats as st
    assert st.sign_flip_test(d, "greater", rng=r) > 0.05          # the mean is dragged down
    assert S.signed_rank_test(d, "greater", rng=r) < 0.01         # the ranks are not
    assert abs(S.hodges_lehmann(r.normal(0.3, 0.1, 400)) - 0.3) < 0.02


def test_signed_rank_null_is_calibrated():
    r = np.random.default_rng(5)
    ps = [S.signed_rank_test(r.standard_normal(30), "greater", n_perm=2000, rng=r) for _ in range(300)]
    assert 0.02 < np.mean(np.array(ps) <= 0.05) < 0.10


def test_rho_is_the_exact_bounded_form_of_gaussian_persistence():
    r = np.random.default_rng(6)
    x = np.zeros(4000)
    for t in range(1, 4000):
        x[t] = 0.9 * x[t - 1] + r.standard_normal()
    I = it.gaussian_mi(x[:-1], x[1:])
    assert abs(_rho_from_nats(np.array([I]))[0] - np.corrcoef(x[:-1], x[1:])[0, 1]) < 1e-9


def test_hksj_interval_brackets_the_estimate():
    r = np.random.default_rng(7)
    groups = {f"s{i}": r.normal(0.1 + 0.05 * r.standard_normal(), 0.1, 40) for i in range(6)}
    h = hksj(groups)
    from ghost_v6.meta import random_effects
    mu = random_effects(groups)["pooled_mean_diff"]
    assert h["ci95"][0] < mu < h["ci95"][1] and h["t_crit"] > 1.96


# ---------------------------------------------------------------- end to end (tiny)

def test_study_K_runs_and_analyzes_end_to_end(tmp_path):
    spec = {"seeds": [100, 101, 102], "world_blocks": 1, "world_seed_base": 1, "steps": 400, "burn": 200}
    S.run_K(spec, tmp_path / "K", workers=1, log=lambda *a: None)
    res = S.analyze_K(tmp_path / "K")
    assert set(res["primary"]) == {"K1_desynchronization_costs_the_author", "K2_live_state_feedback_restores",
                                   "K3_live_innovation_restores", "K4_synchrony_matters_more_for_the_author"}
    assert res["account"] in ("feedback", "innovation", "both", "undetermined")
    assert 0.0 <= res["state_predictable_share"]["master"] <= 1.0
    lv = res["levels"]
    assert abs(lv["master:shift"]["injected_rms"] - lv["master:live"]["injected_rms"]) < 1e-6
