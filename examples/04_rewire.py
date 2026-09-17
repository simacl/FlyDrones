"""Stimulate MiniFly, then grow it, cut it, or scramble the wiring.

    python examples/04_rewire.py
"""

from flydrones.brain import (
    ablate,
    add_silent_neurons,
    build_minifly,
    clone_neurons,
    flip_signs,
    reverse_laterality,
    shuffle_wiring,
)
from flydrones.circuit import format_table, run_variant
from flydrones.config import load_config

cfg = load_config()
base = build_minifly()
variants = [
    ("baseline", base),
    ("2x synapses", build_minifly(syn_scale=2.0)),
    ("2x neurons", build_minifly(pop_scale=2.0)),
    ("2x neurons, drive held constant", build_minifly(pop_scale=2.0, normalize=True)),
    ("+400 silent cells", add_silent_neurons(base, 400)),
    ("clone T4c (same VS targets, louder)", clone_neurons(base, "^T4c$", 96)),
    ("clone T4c, drive held constant", clone_neurons(base, "^T4c$", 96, normalize=True)),
    ("cut T4c→VS (no climb)", ablate(base, "^T4c$", "^VS$")),
    ("LPi_v sign flip", flip_signs(base, "^LPi_v$")),
    ("HS axons to other side", reverse_laterality(base, "^HS$")),
    ("shuffled addresses", shuffle_wiring(base, seed=1)),
]
rows = [run_variant(name, c, cfg, settle_ms=600, measure_ms=600) for name, c in variants]
print(format_table(rows))
print()
print("The decoder never changed. If climbΔlift collapses, the drone will not climb to an open palm.")
