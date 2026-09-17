"""Grow new cells that follow real type-to-type synapse statistics.

MaleCNS v1.0 is already the complete CNS of one fly. ``grow_like`` is how you
ask what 34k *more* neurons of those same types would look like: bootstrap
axons and dendrites, inherit retinotopic columns, continue hemilineage birth
order, and allow new-to-new synapses onto already-born cells. Never duplicate
the giant fiber.

    python examples/06_grow_real.py
    flydrones circuit --grow 200 --grow-report docs/growth/minifly_plus200
    flydrones circuit --grow 34000 --brain data/malecns_brain.npz --grow-report docs/growth/malecns_plus34000
"""

from pathlib import Path

from flydrones.brain import build_growth_report, build_minifly, grow_like, write_growth_report
from flydrones.config import load_config

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "growth"


def grow_and_report(n: int, seed: int = 0, probe: bool = True, list_all: bool | None = None) -> None:
    cfg = load_config()
    base = build_minifly()
    grown = grow_like(base, n, seed=seed)
    print(base.summary())
    print(grown.summary())
    info = grown.meta["grown"]
    hist = sorted(info["by_type"].items(), key=lambda kv: -kv[1])
    print("new cells by type:", ", ".join(f"{t}={c}" for t, c in hist))
    print("DNp01 still", int((grown.types == "DNp01").sum()), "(identified; not grown)")
    print(f"new→new connections: {info.get('new_to_new', 0)}")
    report = build_growth_report(base, grown, cfg if probe else None)
    stem = OUT / f"minifly_plus{n}"
    md, csv_path = write_growth_report(report, stem, list_all=list_all)
    print(f"wrote {md}")
    print(f"wrote {csv_path} ({n} rows)")
    if report.reflexes:
        from flydrones.circuit import format_table

        print()
        print(format_table(report.reflexes))


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    grow_and_report(200, seed=0, probe=True, list_all=True)
    print()
    print("On MaleCNS: flydrones circuit --grow 34000 --brain data/malecns_brain.npz --grow-report docs/growth/malecns_plus34000")
    print("That is 166k traced + 34k statistically real-like, not 34k extra EM bodies.")
    print("MiniFly stand-in at the same extra-cell count:")
    grow_and_report(34_000, seed=0, probe=True, list_all=False)
