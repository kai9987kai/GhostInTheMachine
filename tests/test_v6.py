import numpy as np
import pytest

from ghost_v4.engine import AgentConfig
from ghost_v5.engine import V5Config, run_agent_v5
from ghost_v6 import studies as S
from ghost_v6.engine import V6Config, run_agent_v6
from ghost_v6.posthoc_v5 import d33


# ---------------------------------------------------------------- engine

def test_v6_defaults_reproduce_v5_master_and_twin_bit_for_bit():
    cfg = AgentConfig(net_seed=21, world_seed=4, steps=400)
    a, b = run_agent_v5(V5Config(base=cfg)), run_agent_v6(V6Config(base=cfg))
    assert np.array_equal(a.X, b.X) and np.array_equal(a.executed, b.executed)
    donor = run_agent_v5(V5Config(base=AgentConfig(net_seed=22, world_seed=4, steps=400)))
    ta = run_agent_v5(V5Config(base=cfg), yoke=donor.stream())
    tb = run_agent_v6(V6Config(base=cfg), yoke=donor.stream())
    assert np.array_equal(ta.X, tb.X)


def test_v6_graded_authorship_matches_v5():
    donor = run_agent_v5(V5Config(base=AgentConfig(net_seed=31, world_seed=4, steps=400)))
    cfg = AgentConfig(net_seed=30, world_seed=4, steps=400)
    a = run_agent_v5(V5Config(base=cfg, authorship=0.9), donor_actions=donor.executed)
    b = run_agent_v6(V6Config(base=cfg, authorship=0.9), donor_actions=donor.executed)
    assert np.array_equal(a.X, b.X)


def test_replaying_own_prediction_error_reproduces_the_run_exactly():
    cfg = AgentConfig(net_seed=23, world_seed=4, steps=400)
    live = run_agent_v6(V6Config(base=cfg))
    again = run_agent_v6(V6Config(base=cfg), cmp_replay=live.mismatch_vec)
    assert np.array_equal(live.X, again.X)
    assert np.allclose(live.injected_rms, live.mismatch)          # live: injected = the mismatch itself


def test_replay_changes_nothing_before_the_window_and_something_after():
    cfg = AgentConfig(net_seed=24, world_seed=4, steps=400)
    live = run_agent_v6(V6Config(base=cfg))
    alt = run_agent_v6(V6Config(base=cfg, replay_start=200), cmp_replay=S.window_shift(live.mismatch_vec, 200))
    assert np.array_equal(live.X[:200], alt.X[:200])
    assert not np.array_equal(live.X[200:], alt.X[200:])
    # the forward model still sees the real world: its live mismatch is recorded, not the replayed one
    assert not np.allclose(alt.injected_rms[200:], alt.mismatch[200:])


def test_gain_zero_equals_comparator_lesion_and_gain_scales_injection():
    cfg = AgentConfig(net_seed=25, world_seed=4, steps=300)
    off = run_agent_v6(V6Config(base=AgentConfig(net_seed=25, world_seed=4, steps=300, comparator=False)))
    g0 = run_agent_v6(V6Config(base=cfg, cmp_gain=0.0))
    assert np.array_equal(off.X, g0.X)
    g2 = run_agent_v6(V6Config(base=cfg, cmp_gain=2.0))
    assert np.isclose(g2.injected_rms[0], 2.0 * g2.mismatch[0], rtol=1e-5)


def test_replay_shape_is_checked():
    with pytest.raises(ValueError):
        run_agent_v6(V6Config(base=AgentConfig(steps=50)), cmp_replay=np.zeros((10, 16)))


# ---------------------------------------------------------------- stream interventions

def test_window_interventions_preserve_what_they_claim():
    r = np.random.default_rng(0)
    T, burn = 1000, 400
    M = np.cumsum(r.standard_normal((T, 4)), axis=0) * 0.1 + r.standard_normal((T, 4))
    Y = 3.0 * r.standard_normal((T, 4)) + 1.0
    sh = S.window_shift(M, burn)
    assert np.array_equal(sh[:burn], M[:burn])
    assert np.allclose(np.sort(sh[burn:], axis=0), np.sort(M[burn:], axis=0))
    assert not np.allclose(sh[burn:], M[burn:])
    ph = S.window_phase(M, burn, np.random.default_rng(1))
    assert np.allclose(np.abs(np.fft.rfft(ph[burn:], axis=0)), np.abs(np.fft.rfft(M[burn:], axis=0)))
    assert np.allclose(np.cov(ph[burn:].T), np.cov(M[burn:].T))    # cross-covariance kept
    sc = S.window_rescale(Y, M, burn)
    assert np.allclose(sc[burn:].mean(axis=0), M[burn:].mean(axis=0))
    assert np.allclose(sc[burn:].std(axis=0), M[burn:].std(axis=0))
    assert np.allclose(np.corrcoef(sc[burn:, 0], Y[burn:, 0])[0, 1], 1.0)


# ---------------------------------------------------------------- statistics

def test_tost_equivalence():
    r = np.random.default_rng(2)
    near_zero = r.normal(0.0, 0.02, 48)
    assert S.tost(near_zero, 0.04, r)["equivalent"]
    far = r.normal(0.08, 0.02, 48)
    assert not S.tost(far, 0.04, r)["equivalent"]


def test_within_network_fisher_z_sign():
    Y = np.array([[1, 2, 3, 4, 5.0], [5, 4, 3, 2, 1.0]])
    Z = np.array([[5, 4, 3, 2, 1.0], [5, 4, 3, 2, 1.0]])
    z = S._fisher_z_within(Y, Z)
    assert z[0] < -3 and z[1] > 3


def test_small_telescopes_d33():
    assert abs(d33(48) - 0.1752) < 1e-3


# ---------------------------------------------------------------- end to end (tiny)

def test_study_G_runs_and_analyzes_end_to_end(tmp_path):
    spec = {"seeds": [100, 101, 102], "world_blocks": 1, "world_seed_base": 1, "steps": 360, "burn": 180}
    S.run_G(spec, tmp_path / "G", workers=1, log=lambda *a: None)
    res = S.analyze_G(tmp_path / "G")
    assert set(res["primary"]) == {"G1_pe_content_necessary", "G2_pe_content_sufficient",
                                   "G3_contingency_matters", "G4_amplitude_matters"}
    assert res["account"] in ("amplitude", "contingency", "undetermined")
    inj = res["injected_rms"]
    assert inj["master:off"] == 0.0 and inj["twin:off"] == 0.0
    # rescaling gives the twin's stream the master's amplitude (per channel), so injected RMS moves toward the master's
    assert abs(inj["master:twinPE_scaled"] - inj["master:live"]) < abs(inj["master:twinPE"] - inj["master:live"]) + 1e-9
