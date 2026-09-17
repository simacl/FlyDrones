"""MaleCNS expansion: new body parts vs Kenyon-cell capacity."""

from flydrones.brain import build_minicns, expand_compartment, graft_appendage, grow_like
from flydrones.capacity import effector_verdict, odor_capacity, probe_effectors, research_config
from flydrones.cli import main


def test_minicns_has_mb_cx_and_legs():
    c = build_minicns()
    types = set(c.types.astype(str))
    assert "KCg-m" in types and "EPG" in types and "T3_MN" in types
    assert "DNp01" in types
    assert "TailMN" not in types and "LegMN_A3" not in types


def test_grow_like_cannot_invent_a_tail():
    c = grow_like(build_minicns(), 80, min_pop=1, seed=0)
    assert "TailMN" not in set(c.types.astype(str))
    assert "LegMN_A3" not in set(c.types.astype(str))
    assert (c.types == "DNp01").sum() == 2


def test_graft_tail_is_coupled_to_giant_fiber():
    base = build_minicns()
    grafted = graft_appendage(base, "tail", seed=0)
    assert (grafted.types == "TailMN").sum() == 8
    cfg = research_config()
    rates = probe_effectors(grafted, cfg, settle_ms=250, measure_ms=350, rest_ms=80)
    v = effector_verdict(grafted, rates)
    assert v["tail"]["status"] in ("coupled", "distinct")
    assert v["tail"]["loom_hz"] > v["tail"]["climb_hz"]
    assert v["tail"]["loom_hz"] > 5
    ungrafted = effector_verdict(base, probe_effectors(base, cfg, settle_ms=200, measure_ms=250, rest_ms=50))
    assert ungrafted["tail"]["status"] == "absent"


def test_graft_extra_legs_copies_t3():
    c = graft_appendage(build_minicns(), "extra_legs", seed=1)
    assert (c.types == "LegMN_A3").sum() == 8
    assert ((c.types == "LegMN_A3") & (c.sides == "L")).sum() == 4
    rates = probe_effectors(c, research_config(), settle_ms=250, measure_ms=350, rest_ms=80)
    v = effector_verdict(c, rates)
    assert v["extra_legs"]["status"] != "absent"


def test_more_kenyon_cells_raise_pattern_rank():
    base = build_minicns()
    grown = expand_compartment(base, "kenyon", 120, seed=0)
    assert (grown.types == "KCg-m").sum() == (base.types == "KCg-m").sum() + 120
    cfg = research_config()
    a = odor_capacity(base, cfg, n_repeats=4, measure_ms=250, settle_ms=150, seed=0)
    b = odor_capacity(grown, cfg, n_repeats=4, measure_ms=250, settle_ms=150, seed=0)
    assert a["n_kc"] == 80
    assert b["n_kc"] == 200
    assert 0.0 <= a["accuracy"] <= 1.0
    assert b["pattern_rank"] >= a["pattern_rank"]


def test_cli_expand_graft(capsys):
    assert main(["expand", "--brain", "minicns", "--graft", "tail", "--graft", "extra_legs"]) == 0
    out = capsys.readouterr().out
    assert "tail" in out.lower()
    assert "n_KC" in out or "Kenyon" in out
