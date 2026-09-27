import json

import numpy as np
import pytest

from ghost_v4 import classifier as clf
from ghost_v4 import metrics as mt
from ghost_v4 import prereg as pr
from ghost_v4 import surrogates as sg
from ghost_v4.engine import AgentConfig, run_agent


@pytest.fixture(scope="module")
def pair():
    donor = run_agent(AgentConfig(net_seed=41, world_seed=3, steps=1500))
    master = run_agent(AgentConfig(net_seed=40, world_seed=3, steps=1500))
    twin = run_agent(AgentConfig(net_seed=40, world_seed=3, steps=1500), yoke=donor.stream())
    return donor, master, twin


def test_engine_is_deterministic():
    a = run_agent(AgentConfig(net_seed=5, steps=300))
    b = run_agent(AgentConfig(net_seed=5, steps=300))
    assert np.array_equal(a.X, b.X)
    assert np.array_equal(a.intended, b.intended)


def test_placebo_replicate_changes_noise_not_network():
    a = run_agent(AgentConfig(net_seed=5, steps=300))
    b = run_agent(AgentConfig(net_seed=5, steps=300, replicate=1))
    assert np.array_equal(a.W, b.W)
    assert not np.array_equal(a.X, b.X)


def test_master_authors_every_action(pair):
    _, master, _ = pair
    assert np.array_equal(master.intended, master.executed)


def test_twin_receives_donor_stream_but_not_its_contingency(pair):
    donor, master, twin = pair
    assert np.array_equal(twin.obs, donor.obs)
    assert np.array_equal(twin.executed, donor.executed)
    assert np.array_equal(twin.W, master.W)              # same network
    match = np.mean(twin.intended == twin.executed)
    assert match < 0.35                                   # chance is 1/7
    assert abs(float(twin.cf_agency[500:].mean()) - 0.5) < 0.05


def test_zero_lag_metrics_are_exactly_shuffle_invariant(pair):
    _, master, _ = pair
    X = master.X[500:].astype(float)
    S = sg.shuffle(X, np.random.default_rng(0))
    assert mt.participation_ratio(X) == pytest.approx(mt.participation_ratio(S), rel=1e-10)
    assert mt.mean_abs_fc(mt.module_means(X, master.slices)) == pytest.approx(
        mt.mean_abs_fc(mt.module_means(S, master.slices)), rel=1e-10)


def test_record_panel_is_complete_and_finite(pair):
    _, master, _ = pair
    p = mt.record_panel(master, burn=500)
    for k in ("self_persistence", "self_psi", "phi_r_mean", "irr_nodes", "te_net_to_obs",
              "atlas_persistence_self", "pci_lz_mean"):
        assert k in p and np.isfinite(p[k])


def test_classifier_auc_sanity():
    r = np.random.default_rng(0)
    A = r.normal(1.0, 1.0, (40, 3))
    B = r.normal(0.0, 1.0, (40, 3))
    out = clf.paired_discrimination(A, B, ["a", "b", "c"], n_perm=50, rng=r)
    assert out["auc"] > 0.8 and out["p"] < 0.05
    null = clf.paired_discrimination(r.normal(size=(40, 3)), r.normal(size=(40, 3)), ["a", "b", "c"], n_perm=50, rng=r)
    assert null["p"] > 0.05


def test_prereg_lock_roundtrip(tmp_path, monkeypatch):
    doc = tmp_path / "prereg.json"
    doc.write_text(json.dumps({"x": 1}))
    lock = tmp_path / "lock.json"
    pr.lock(doc, lock)
    ok, bad, _ = pr.verify(doc, lock)
    assert ok and not bad
    doc.write_text(json.dumps({"x": 2}))
    ok, bad, _ = pr.verify(doc, lock)
    assert not ok and bad == ["prereg"]


@pytest.mark.slow
def test_v3_bridge_reproduces_published_seed_17():
    from ghost_v4 import v3_bridge as vb
    assert vb.v3_sha256() == vb.V3_VALIDATED_SHA256
    rec = vb.run_v3(17, steps=1700)
    assert rec["first_event_step"] == 1600
    Xw = rec["X"][1700 - vb.WINDOW:1700].astype(float)
    m = vb.v3_window_metrics(Xw, rec["slices"], rec["W"], rec["gain"][1700 - vb.WINDOW:1700], rec["base_spectral_radius"])
    online = rec["rows"][-1]
    for k in ("topology_balance", "avalanche_criticality", "multiscale_entropy", "geometry_score",
              "mesocircuit_flow", "thalamocortical_transfer", "criticality", "ei_balance"):
        assert m[k] == pytest.approx(online[k], abs=1e-9), k
