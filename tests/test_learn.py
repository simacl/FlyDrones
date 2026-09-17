"""KC→MBON training: unread book vs read book."""

import numpy as np
from scipy import sparse

from flydrones.brain import build_minicns, expand_compartment
from flydrones.brain.lif import LIFNetwork, LIFParams
from flydrones.capacity import research_config
from flydrones.cli import main
from flydrones.learn import SIMPLE_LESSONS, evaluate_valence, train_odor_valence


def test_untrained_mbon_has_no_preference():
    c = build_minicns()
    ev = evaluate_valence(c, SIMPLE_LESSONS, research_config(), settle_ms=120, rest_ms=40, measure_ms=180, seed=3, repeats=1)
    assert ev["n_kc"] == 80
    assert ev["accuracy"] <= 0.5


def test_training_writes_a_two_odor_preference():
    c = build_minicns()
    trained, log = train_odor_valence(
        c, SIMPLE_LESSONS, research_config(), epochs=6, eta=1.4, settle_ms=100, rest_ms=40, measure_ms=180, seed=0
    )
    assert log["n_boutons"] > 0
    assert log["weight_drift"] > 1.0
    after = evaluate_valence(trained, SIMPLE_LESSONS, research_config(), settle_ms=120, rest_ms=40, measure_ms=200, seed=9, repeats=2)
    before = evaluate_valence(c, SIMPLE_LESSONS, research_config(), settle_ms=120, rest_ms=40, measure_ms=200, seed=9, repeats=2)
    assert after["accuracy"] >= 0.75
    assert after["margin"] > before["margin"]
    assert after["margin"] > 2.0


def test_extra_kc_untrained_is_still_unread():
    grown = expand_compartment(build_minicns(), "kenyon", 80, seed=0)
    ev = evaluate_valence(grown, SIMPLE_LESSONS, research_config(), settle_ms=100, rest_ms=40, measure_ms=160, seed=2, repeats=1)
    assert ev["n_kc"] == 160
    assert ev["accuracy"] <= 0.5


def test_set_connectivity_changes_propagation():
    w0 = sparse.csc_matrix((np.zeros(2, np.float32), (np.array([1, 2]), np.array([0, 1]))), shape=(3, 3))
    w1 = sparse.csc_matrix((np.full(2, 200.0, np.float32), (np.array([1, 2]), np.array([0, 1]))), shape=(3, 3))
    net = LIFNetwork(w0, LIFParams(noise_mv=0), seed=1)
    net.set_input(np.array([0]), 120.0)
    silent, _ = net.run(400)
    net.reset()
    net.set_connectivity(w1)
    net.set_input(np.array([0]), 120.0)
    loud, _ = net.run(400)
    assert loud[2] > silent[2]


def test_cli_expand_train(capsys):
    assert main(["expand", "--brain", "minicns", "--no-train", "--graft", "tail"]) == 0
    out = capsys.readouterr().out
    assert "tail" in out.lower()
    assert "n_KC" in out or "Kenyon" in out or "sidecar" in out.lower()
