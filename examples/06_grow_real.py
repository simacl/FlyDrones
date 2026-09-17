"""Grow new cells that follow real type-to-type synapse statistics.

MaleCNS v1.0 is already the complete CNS of one fly. ``grow_like`` is how you
ask what 34k *more* neurons of those same types would look like: bootstrap
axons and dendrites from existing cells, never duplicate the giant fiber.

    python examples/06_grow_real.py
    flydrones circuit --grow 34000 --brain data/malecns_brain.npz
"""

from collections import Counter

from flydrones.brain import build_minifly, grow_like
from flydrones.circuit import format_table, run_variant
from flydrones.config import load_config

cfg = load_config()
base = build_minifly()
grown = grow_like(base, 200, seed=0)
hist = Counter(grown.types[base.n :])
print(base.summary())
print(grown.summary())
print("new cells by type:", ", ".join(f"{t}={c}" for t, c in hist.most_common()))
print("DNp01 still", int((grown.types == "DNp01").sum()), "(identified; not grown)")
print()
rows = [
    run_variant("baseline MiniFly", base, cfg, settle_ms=500, measure_ms=500),
    run_variant("+200 grown like real types", grown, cfg, settle_ms=500, measure_ms=500),
]
print(format_table(rows))
print()
print("On MaleCNS: flydrones circuit --grow 34000 --brain data/malecns_brain.npz")
print("That is 166k traced + 34k statistically real-like, not 34k extra EM bodies.")
