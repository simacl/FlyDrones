"""KC→MBON training: unread book vs read book."""

import numpy as np
from scipy import sparse

from flydrones.brain import build_minicns, expand_compartment
from flydrones.brain.lif import LIFNetwork, LIFParams
from flydrones.capacity import research_config
from flydrones.cli import main
from flydrones.learn import SIMPLE_LESSONS, body_snapshot, evaluate_valence, train_body, train_odor_valence


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


def test_scene_up_walks_after_body_training():
    c = build_minicns()
    cfg = research_config()
    before = body_snapshot(c, cfg, settle_ms=120, measure_ms=200, rest_ms=50)
    assert before["climb_walk_hz"] < 2
    trained, log = train_body(c, cfg, epochs=6, eta=1.8, settle_ms=80, rest_ms=30, measure_ms=160, seed=0)
    assert log["weight_drift"] > 1.0
    after = body_snapshot(trained, cfg, settle_ms=120, measure_ms=200, rest_ms=50)
    assert after["climb_walk_hz"] > 4
    assert after["climb_lift_hz"] > before["climb_lift_hz"]


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
    assert "untrained body" in out.lower() or "climb" in out.lower()


def test_hit_wall_dodge_next_time_online_does_not_hit_again():
    from flydrones.brain import grow_like
    from flydrones.experience import live_once

    cfg = research_config()
    grown = grow_like(build_minicns(), 80, min_pop=1, seed=0)
    trained, _ = train_body(grown, cfg, epochs=6, seed=0)
    frozen = live_once(trained, cfg, online=False, seed=0)
    online = live_once(trained, cfg, online=True, seed=0)
    assert frozen["first"]["hits"] >= 1 and frozen["first"]["dodged"]
    assert online["first"]["hits"] >= 1 and online["first"]["dodged"]
    assert frozen["hit_again"]
    assert not online["hit_again"]
    assert frozen["drift"] < 1e-6
    assert online["n_updates"] > 0
    assert online["first"]["verdict_min"] < -0.15
    assert online["first"]["ppl1_max"] > 5.0


def test_verdict_comes_from_pain_cells_not_a_minus_one():
    import warnings

    from flydrones.brain import Brain
    from flydrones.experience import neural_verdict

    c = build_minicns()
    cfg = research_config()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        brain = Brain(c, cfg, seed=0)
    brain.tick({}, 120.0)
    rest = dict(brain.last_rates)
    quiet = neural_verdict(rest, rest)
    brain.tick({"mdIV_L": 170.0, "mdIV_R": 170.0, "chordotonal_L": 80.0, "chordotonal_R": 80.0}, 80.0)
    hurt = neural_verdict(brain.last_rates, rest)
    assert abs(quiet) < 0.2
    assert hurt < quiet
    assert hurt < -0.2
    assert brain.last_rates.get("PPL1", 0.0) > rest.get("PPL1", 0.0)

