from flydrones.brain import Brain, ablate, add_silent_neurons, build_minifly, flip_signs, reverse_laterality, shuffle_wiring
from flydrones.brain.rewire import pathway_weight, scale_synapses
from flydrones.circuit import lift, probe, yaw_proxy
from flydrones.cli import main
from flydrones.config import load_config


def test_minifly_pop_scale_adds_cells_and_synapses():
    a = build_minifly()
    b = build_minifly(pop_scale=2.0)
    assert b.n == 2 * a.n
    assert b.n_connections > a.n_connections * 1.5


def test_silent_neurons_do_not_add_synapses():
    a = build_minifly()
    b = add_silent_neurons(a, 400)
    assert b.n == a.n + 400
    assert b.n_connections == a.n_connections


def test_scale_synapses_doubles_counts():
    a = build_minifly()
    b = scale_synapses(a, 2.0)
    assert b.n == a.n
    assert b.n_connections == a.n_connections
    assert abs(b.n_synapses - a.n_synapses * 2) / a.n_synapses < 0.02


def test_ablate_removes_t4c_to_vs():
    c = build_minifly()
    n0, _ = pathway_weight(c, "^T4c$", "^VS$")
    assert n0 > 0
    d = ablate(c, "^T4c$", "^VS$")
    n1, _ = pathway_weight(d, "^T4c$", "^VS$")
    assert n1 == 0
    assert d.n_connections == c.n_connections - n0


def test_ablate_kills_climb_not_yaw():
    cfg = load_config()
    healthy = probe(Brain(build_minifly(), cfg), settle_ms=400, measure_ms=500, rest_ms=200)
    lesion = probe(Brain(ablate(build_minifly(), "^T4c$", "^VS$"), cfg), settle_ms=400, measure_ms=500, rest_ms=200)
    h_climb = lift(healthy["climb"]) - lift(healthy["rest"])
    l_climb = lift(lesion["climb"]) - lift(lesion["rest"])
    assert h_climb > 15
    assert l_climb < 0.4 * h_climb
    assert yaw_proxy(lesion["yaw_right"]) > 8


def test_stronger_synapses_stronger_climb():
    cfg = load_config()
    weak = probe(Brain(build_minifly(syn_scale=0.5), cfg), settle_ms=400, measure_ms=500, rest_ms=200)
    strong = probe(Brain(build_minifly(syn_scale=2.0), cfg), settle_ms=400, measure_ms=500, rest_ms=200)
    d_weak = lift(weak["climb"]) - lift(weak["rest"])
    d_strong = lift(strong["climb"]) - lift(strong["rest"])
    assert d_strong > d_weak + 5


def test_reverse_hs_flips_optomotor_sign():
    cfg = load_config()
    healthy = probe(Brain(build_minifly(), cfg), settle_ms=400, measure_ms=500, rest_ms=200)
    reversed_ = probe(Brain(reverse_laterality(build_minifly(), "^HS$"), cfg), settle_ms=400, measure_ms=500, rest_ms=200)
    assert yaw_proxy(healthy["yaw_right"]) > 8
    assert yaw_proxy(reversed_["yaw_right"]) < -4


def test_shuffle_destroys_climb_reflex():
    cfg = load_config()
    healthy = probe(Brain(build_minifly(), cfg), settle_ms=400, measure_ms=500, rest_ms=200)
    scrambled = probe(Brain(shuffle_wiring(build_minifly(), seed=1), cfg), settle_ms=400, measure_ms=500, rest_ms=200)
    h = lift(healthy["climb"]) - lift(healthy["rest"])
    s = lift(scrambled["climb"]) - lift(scrambled["rest"])
    assert h > 15
    assert abs(s) < 0.5 * h


def test_flip_lpiv_weakens_or_reverses_descent():
    cfg = load_config()
    healthy = probe(Brain(build_minifly(), cfg), settle_ms=400, measure_ms=500, rest_ms=200)
    flipped = probe(Brain(flip_signs(build_minifly(), "^LPi_v$"), cfg), settle_ms=400, measure_ms=500, rest_ms=200)
    h = lift(healthy["descend"]) - lift(healthy["rest"])
    f = lift(flipped["descend"]) - lift(flipped["rest"])
    assert h < -8
    assert f > h + 5  # less negative, or even a climb


def test_connectome_copy_is_independent():
    a = build_minifly()
    b = a.copy()
    assert b.n == a.n
    b.weights.data[:] = 0
    assert abs(a.weights.data).sum() > 0


def test_cli_circuit(capsys):
    assert main(["circuit", "--ablate", "T4c:VS", "--settle-ms", "200", "--measure-ms", "300"]) == 0
    out = capsys.readouterr().out
    assert "climb" in out.lower() or "climbΔlift" in out


def test_preset_suite_covers_scale_and_wiring():
    from flydrones.circuit import preset_connectomes

    variants = dict(preset_connectomes())
    assert variants["baseline"].n == 850
    assert variants["2x-neurons"].n == 1700
    assert variants["+400-silent"].n == 1250
    assert variants["2x-synapses"].n_synapses > variants["baseline"].n_synapses * 1.8
    assert variants["ablate-T4c→VS"].n_connections < variants["baseline"].n_connections
