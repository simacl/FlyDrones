"""Grow the whole CNS, train, read motors.

    python examples/07_malecns_expand.py
    flydrones expand --brain minicns --grow 160 --report docs/growth/malecns_train.md
"""

from pathlib import Path

from flydrones.brain import build_minicns, load_connectome
from flydrones.capacity import research_config
from flydrones.learn import format_embodied_report, run_embodied_experiment

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "growth" / "malecns_train.md"


def main() -> None:
    npz = ROOT / "data" / "malecns_brain.npz"
    if npz.exists():
        base = load_connectome(npz)
        extra = 2000
    else:
        base = build_minicns()
        extra = 160
    cfg = research_config()
    exp = run_embodied_experiment(base, cfg, extra=extra, epochs=8, seed=0)
    text = format_embodied_report(exp, title=f"MaleCNS growth+train ({base.name})")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print(text)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
