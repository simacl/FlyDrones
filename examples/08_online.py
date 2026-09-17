"""After development: live, keep changing, or freeze.

python examples/08_online.py
flydrones expand --brain minicns --grow 80 --life --report docs/growth/malecns_life.md
"""

from pathlib import Path

from flydrones.brain import build_minicns, grow_like, load_connectome
from flydrones.capacity import research_config
from flydrones.experience import format_online_report, run_online_experiment

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "growth" / "malecns_life.md"


def main() -> None:
    npz = ROOT / "data" / "malecns_brain.npz"
    if npz.exists():
        base = load_connectome(npz)
        extra = 400
    else:
        base = build_minicns()
        extra = 80
    cfg = research_config()
    grown = grow_like(base, extra, min_pop=1, seed=0)
    exp = run_online_experiment(grown, cfg, develop=True, epochs=6, seed=0)
    text = format_online_report(exp, title=f"Online experience ({grown.name})")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print(text)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
