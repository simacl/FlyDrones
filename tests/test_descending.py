import importlib.util

import pytest

from flydrones.motor import FlightCommand, from_command, from_dng02


def test_dng02_independent_sides():
    d = from_dng02(60, 30, baseline_l=30, baseline_r=30)
    assert d.left > d.right + 0.2
    rest = from_dng02(31, 31)
    assert abs(rest.left - 0.8) < 0.05
    assert abs(rest.right - 0.8) < 0.05


def test_yaw_right_command_raises_right_drive():
    d = from_command(FlightCommand(forward=0.4, yaw=0.5))
    assert d.right > d.left
    halt = from_command(FlightCommand(escape=True))
    assert halt.escape and halt.left <= 0.21 and halt.right <= 0.21


def test_reversed_hs_swaps_descending_turn():
    from flydrones.brain import Brain, build_minifly, reverse_laterality
    from flydrones.circuit import probe
    from flydrones.config import load_config

    cfg = load_config()
    healthy = probe(Brain(build_minifly(), cfg), settle_ms=400, measure_ms=500, rest_ms=200)
    lesion = probe(Brain(reverse_laterality(build_minifly(), "^HS$"), cfg), settle_ms=400, measure_ms=500, rest_ms=200)
    h = from_dng02(healthy["yaw_right"]["DNg02_L"], healthy["yaw_right"]["DNg02_R"])
    L = from_dng02(lesion["yaw_right"]["DNg02_L"], lesion["yaw_right"]["DNg02_R"])
    assert h.right > h.left
    assert L.left > L.right


@pytest.mark.skipif(importlib.util.find_spec("flygym") is not None, reason="flygym is installed")
def test_flygym_backend_explains_install():
    from flydrones.drones import make_drone

    with pytest.raises(ImportError, match="neuromechfly.org"):
        make_drone("flygym")
