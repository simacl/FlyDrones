"""MaleCNS research: extra cells, then train, then test new skills.

Uses MiniCNS (MaleCNS type names) unless ``data/malecns_brain.npz`` exists.

    python examples/07_malecns_expand.py
    flydrones expand --brain minicns --grow-kc 160 --report docs/growth/malecns_train.md
    flydrones expand --brain data/malecns_brain.npz --grow-kc 2000
"""

from pathlib import Path

from flydrones.brain import build_minicns, load_connectome
from flydrones.capacity import research_config
from flydrones.learn import format_training_report, run_training_experiment

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
    exp = run_training_experiment(base, cfg, extra_kc=extra, epochs=8, seed=0)
    text = format_training_report(exp, title=f"MaleCNS training ({base.name})")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print(text)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
