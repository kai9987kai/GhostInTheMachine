import math

import numpy as np
import pytest

from ghost_v4.engine import AgentConfig, run_agent
from ghost_v5 import estimators as est
from ghost_v5.engine import V5Config, run_agent_v5


# ---------------------------------------------------------------- engine

def test_v5_defaults_reproduce_v4_master_bit_for_bit():
    cfg = AgentConfig(net_seed=21, world_seed=4, steps=400)
    a = run_agent(cfg)
    b = run_agent_v5(V5Config(base=cfg))
    assert np.array_equal(a.X, b.X)
    assert np.array_equal(a.obs, b.obs)
    assert np.array_equal(a.executed, b.executed)


def test_v5_defaults_reproduce_v4_twin_bit_for_bit():
    donor = run_agent(AgentConfig(net_seed=22, world_seed=4, steps=400))
    cfg = AgentConfig(net_seed=21, world_seed=4, steps=400)
    a = run_agent(cfg, yoke=donor.stream())
    b = run_agent_v5(V5Config(base=cfg), yoke=donor.stream())
    assert np.array_equal(a.X, b.X)


def test_graded_authorship_controls_contingency():
    donor = run_agent(AgentConfig(net_seed=31, world_seed=4, steps=3000))
    for p in (0.0, 0.5):
        rec = run_agent_v5(V5Config(base=AgentConfig(net_seed=30, world_seed=4, steps=3000), authorship=p),
                           donor_actions=donor.executed)
        match = float(np.mean(rec.intended == rec.executed))
        expected = p + (1 - p) / 7.0
        assert abs(match - expected) < 0.05, (p, match, expected)


def test_comparator_window_and_rerouting_change_only_what_they_claim():
    cfg = AgentConfig(net_seed=40, world_seed=4, steps=600)
    full = run_agent_v5(V5Config(base=cfg))
    late = run_agent_v5(V5Config(base=cfg, comparator_start=300))
    off = run_agent(AgentConfig(net_seed=40, world_seed=4, steps=600, comparator=False))
    assert np.array_equal(late.X[:300], off.X[:300])          # comparator silent before 300
    assert not np.array_equal(late.X[300:], off.X[300:])
    stop = run_agent_v5(V5Config(base=cfg, comparator_stop=300))
    assert np.array_equal(stop.X[:300], full.X[:300])
    rer = run_agent_v5(V5Config(base=cfg, comparator_targets=("dmn", "association")))
    assert np.array_equal(rer.W, full.W)                      # same network; only the comparator mask moved
    assert not np.array_equal(rer.X, full.X)


# ---------------------------------------------------------------- estimators

def test_copula_normalize_is_rank_gaussian():
    r = np.random.default_rng(0)
    x = np.exp(r.standard_normal(5000))                        # skewed marginal
    z = est.copula_normalize(x)
    assert abs(z.mean()) < 0.01 and abs(z.std() - 1) < 0.02
    assert np.array_equal(np.argsort(z), np.argsort(x))


def test_ksg_matches_gaussian_ground_truth():
    r = np.random.default_rng(1)
    rho = 0.6
    a = r.standard_normal(3000)
    b = rho * a + math.sqrt(1 - rho ** 2) * r.standard_normal(3000)
    assert est.ksg_mi(a, b) == pytest.approx(-0.5 * math.log(1 - rho ** 2), abs=0.03)
    assert abs(est.ksg_mi(a, r.standard_normal(3000))) < 0.02


def test_ksg_sees_nonlinear_dependence_that_gaussian_misses():
    from ghost_v4 import infotheory as it
    r = np.random.default_rng(2)
    a = r.standard_normal(3000)
    b = a ** 2 + 0.3 * r.standard_normal(3000)
    assert it.gaussian_mi(a, b) < 0.01
    assert est.ksg_mi(a, b) > 0.5


def test_gc_and_ksg_psi_agree_on_sign_for_controls():
    from ghost_v4 import controls
    r = np.random.default_rng(3)
    indep = controls.independent_ar(r, T=2000, n=6, phi=0.9)
    flock = controls.shared_mode(r, T=2000, n=6)
    for fn in (est.gc_emergence, est.ksg_emergence):
        assert fn(indep, indep.mean(axis=1))["psi"] > 0
        assert fn(flock, flock.mean(axis=1))["psi"] < 0
