"""MaleCNS research path: can extra cells add a tail, extra legs, or intelligence?

Uses MiniCNS (MaleCNS type names) unless ``data/malecns_brain.npz`` exists.

    python examples/07_malecns_expand.py
    flydrones expand --brain minicns --graft tail --graft extra-legs --grow-kc 120
    flydrones expand --brain data/malecns_brain.npz --graft tail --grow-kc 2000
"""

from pathlib import Path

from flydrones.brain import build_minicns, expand_compartment, graft_appendage, grow_like
from flydrones.capacity import effector_verdict, odor_capacity, probe_effectors, research_config

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "growth" / "malecns_expand.md"


def _block(title: str, connectome, cfg) -> str:
    rates = probe_effectors(connectome, cfg)
    v = effector_verdict(connectome, rates)
    cap = odor_capacity(connectome, cfg, n_repeats=5, seed=0)
    lines = [f"## {title}", "", connectome.summary(), ""]
    for name, row in v.items():
        corr = f", copy of {row['copy_of']} (r={row['corr']:.2f})" if row.get("copy_of") else ""
        lines.append(
            f"- **{name}**: `{row['status']}`{corr}. loom {row.get('loom_hz', 0):.1f} Hz, "
            f"climb {row.get('climb_hz', 0):.1f} Hz"
            + (f", walk {row.get('walk_hz', 0):.1f} Hz" if "walk_hz" in row else "")
            + f". {row['note']}"
        )
    lines += [
        "",
        f"- Kenyon cells: **{cap['n_kc']}**, odor nearest-centroid accuracy "
        f"**{cap['accuracy']:.2f}**, pattern rank {cap['pattern_rank']}",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    cfg = research_config()
    base = build_minicns()
    grown = grow_like(base, 100, min_pop=1, seed=0)
    grafted = graft_appendage(graft_appendage(base, "tail", seed=0), "extra_legs", seed=1)
    smarter = expand_compartment(base, "kenyon", 160, seed=0)
    text = "\n".join(
        [
            "# MaleCNS expansion experiments (MiniCNS stand-in)",
            "",
            "Real MaleCNS: `flydrones download malecns && flydrones build-brain`, then rerun with `--brain data/malecns_brain.npz`.",
            "",
            "Question 1: can extra neurons become a **tail** or **two extra legs**?",
            "Question 2: can extra neurons make the brain **more powerful / more intelligent**?",
            "",
            _block("A. Unmodified MiniCNS (MaleCNS compartments, no graft)", base, cfg),
            _block("B. grow_like +100 existing types (no new organ)", grown, cfg),
            _block("C. graft tail + extra leg pair", grafted, cfg),
            _block("D. +160 Kenyon cells (mushroom-body capacity)", smarter, cfg),
            "### How to read this",
            "",
            "- `absent`: that body part does not exist. `grow_like` stays in this column for tail/legs.",
            "- `coupled`: a new muscle fired, but it copies DNp01 or T3_MN. Extra effector, not a new behaviour.",
            "- `distinct`: stimulus-locked and not a copy — the only status that would count as a new ability.",
            "- Kenyon accuracy is odor-pattern capacity, not general intelligence. There is still no learning rule unless you add one.",
            "",
        ]
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print(text)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
