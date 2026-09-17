"""Train mushroom-body valence, then ask the brain — not a sidecar classifier.

The untrained KC→MBON weights are an unread book. Training is reading it.
Extra Kenyon cells only matter if they are trained too.

Question 1 (new ability the wiring did not come with): approach one odor,
avoid another. A fly is not born knowing which smell is food.

Question 2 (stronger after training): same rule, then compare MBON margin
and overlapping mixtures. Extra KCs raise the odor-map rank; training spends it.
"""

from __future__ import annotations

import warnings
from typing import Any

import numpy as np

from .brain import Brain, Connectome
from .brain.expand import expand_compartment
from .brain.plasticity import KCMbonSynapses, ensure_kc_mbon_boutons
from .capacity import odor_capacity, research_config

# valence +1 = reward / approach; −1 = punish / avoid
SIMPLE_LESSONS: list[tuple[dict[str, float], float, str]] = [
    ({"PN_DM1": 140.0}, 1.0, "DM1"),
    ({"PN_DM4": 140.0}, -1.0, "DM4"),
]

MIX_LESSONS: list[tuple[dict[str, float], float, str]] = [
    ({"PN_DM1": 90.0, "PN_DM2": 90.0}, 1.0, "DM1+DM2"),
    ({"PN_DM1": 90.0, "PN_DM3": 90.0}, -1.0, "DM1+DM3"),
    ({"PN_DM2": 90.0, "PN_DM4": 90.0}, 1.0, "DM2+DM4"),
    ({"PN_DM3": 90.0, "PN_DM4": 90.0}, -1.0, "DM3+DM4"),
]


def _brain(connectome: Connectome, cfg: dict, seed: int) -> Brain:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return Brain(connectome, cfg, seed=seed)


def _valence(rates: dict[str, float]) -> float:
    return float(rates.get("MBON01", 0.0) - rates.get("MBON04", 0.0))


def evaluate_valence(
    connectome: Connectome,
    lessons: list[tuple[dict[str, float], float, str]],
    cfg: dict | None = None,
    *,
    settle_ms: float = 200.0,
    rest_ms: float = 80.0,
    measure_ms: float = 300.0,
    seed: int = 1,
    repeats: int = 2,
) -> dict[str, Any]:
    """Read MBON01−MBON04 for each lesson. No classifier on KC vectors."""
    cfg = cfg or research_config()
    brain = _brain(connectome, cfg, seed)
    brain.tick({}, settle_ms)
    per: list[dict[str, Any]] = []
    hits = []
    for _rep in range(repeats):
        for stim, target, name in lessons:
            brain.tick({}, rest_ms)
            rates = dict(brain.tick(stim, measure_ms))
            pref = _valence(rates)
            ok = (pref > 0) == (target > 0) and abs(pref) > 0.5
            hits.append(ok)
            per.append(
                {
                    "name": name,
                    "target": float(target),
                    "preference": pref,
                    "MBON01": float(rates.get("MBON01", 0.0)),
                    "MBON04": float(rates.get("MBON04", 0.0)),
                    "correct": bool(ok),
                }
            )
    goods = [p["preference"] for p in per if p["target"] > 0]
    bads = [p["preference"] for p in per if p["target"] < 0]
    margin = float(np.mean(goods) - np.mean(bads)) if goods and bads else float("nan")
    return {
        "accuracy": float(np.mean(hits)) if hits else float("nan"),
        "margin": margin,
        "n_kc": int((np.char.find(connectome.types.astype(str), "KC") >= 0).sum()),
        "trials": per,
    }


def train_odor_valence(
    connectome: Connectome,
    lessons: list[tuple[dict[str, float], float, str]] | None = None,
    cfg: dict | None = None,
    *,
    epochs: int = 8,
    eta: float = 1.4,
    settle_ms: float = 180.0,
    rest_ms: float = 60.0,
    measure_ms: float = 250.0,
    seed: int = 0,
) -> tuple[Connectome, dict[str, Any]]:
    """Pair each odor with reward (+) or punishment (−) and write KC→MBON.

    Returns a copy of the connectome with trained weights, plus a log.
    """
    lessons = lessons or SIMPLE_LESSONS
    cfg = cfg or research_config()
    trained = connectome.copy(f"{connectome.name}+trained")
    n_new = ensure_kc_mbon_boutons(trained, seed=seed)
    brain = _brain(trained, cfg, seed)
    loc = KCMbonSynapses(trained)
    log = {
        "epochs": epochs,
        "eta": eta,
        "n_kc": int(loc.kc.size),
        "n_boutons": loc.n_boutons,
        "new_boutons": n_new,
        "rule": "three-factor KC→MBON (PAM reward / PPL1 punish)",
        "lessons": [name for _s, _v, name in lessons],
        "weight_drift": 0.0,
    }
    rng = np.random.default_rng(seed)
    order = list(lessons)
    brain.tick({}, settle_ms)
    for _epoch in range(epochs):
        rng.shuffle(order)
        for stim, valence, _name in order:
            brain.net.reset()
            brain.tick({}, rest_ms)
            brain.tick(stim, measure_ms)
            loc.update(brain.last_counts[loc.kc], valence, eta)
            loc.commit(trained, brain.net)
    log["weight_drift"] = loc.drift()
    trained.meta = {
        **trained.meta,
        "trained": {"epochs": epochs, "eta": eta, "lessons": log["lessons"], "weight_drift": log["weight_drift"]},
    }
    return trained, log


def _pack(label: str, untrained: dict, trained: dict, train_log: dict | None = None) -> dict[str, Any]:
    return {
        "label": label,
        "n_kc": trained.get("n_kc", untrained.get("n_kc")),
        "untrained_accuracy": untrained["accuracy"],
        "untrained_margin": untrained["margin"],
        "trained_accuracy": trained["accuracy"],
        "trained_margin": trained["margin"],
        "train": train_log or {},
        "untrained_trials": untrained["trials"],
        "trained_trials": trained["trials"],
    }


def run_training_experiment(
    connectome: Connectome,
    cfg: dict | None = None,
    *,
    extra_kc: int = 160,
    epochs: int = 8,
    seed: int = 0,
    eval_repeats: int = 2,
) -> dict[str, Any]:
    """Unread book vs read book, small mushroom body vs grown one."""
    cfg = cfg or research_config()
    base = connectome.copy()
    grown = expand_compartment(base, "kenyon", extra_kc, seed=seed) if extra_kc else None

    def one(c: Connectome, lessons, tag: str) -> dict[str, Any]:
        frozen = odor_capacity(c, cfg, n_repeats=4, measure_ms=250, settle_ms=150, seed=seed)
        before = evaluate_valence(c, lessons, cfg, seed=seed + 1, repeats=eval_repeats)
        trained_c, log = train_odor_valence(c, lessons, cfg, epochs=epochs, seed=seed)
        after = evaluate_valence(trained_c, lessons, cfg, seed=seed + 7, repeats=eval_repeats)
        row = _pack(tag, before, after, log)
        row["frozen_kc_classifier"] = frozen
        row["connectome"] = trained_c.name
        row["neurons"] = trained_c.n
        return row

    out: dict[str, Any] = {
        "baseline_simple": one(base, SIMPLE_LESSONS, "baseline 2-odor"),
        "baseline_mix": one(base, MIX_LESSONS, "baseline mixtures"),
        "extra_kc": extra_kc,
    }
    if grown is not None:
        out["grown_simple"] = one(grown, SIMPLE_LESSONS, f"+{extra_kc} KC 2-odor")
        out["grown_mix"] = one(grown, MIX_LESSONS, f"+{extra_kc} KC mixtures")
        out["grown_n"] = grown.n
        out["grown_kc"] = int((np.char.find(grown.types.astype(str), "KC") >= 0).sum())
    return out


def format_training_report(exp: dict[str, Any], title: str | None = None) -> str:
    lines = [
        f"# {title or 'MaleCNS training: extra cells, then read the book'}",
        "",
        "Untrained MBON readout = closed book. Nearest-centroid on KC rates is a sidecar",
        "that peeks at the pages without the fly having learned. Training writes KC→MBON.",
        "",
        "## 1. New ability the original wiring does not have",
        "",
        "Pair DM1 with reward and DM4 with punishment. The brain is not born knowing",
        "which smell is food. After training, preference is `MBON01 − MBON04`.",
        "",
    ]

    def row(d: dict) -> list[str]:
        frozen = d.get("frozen_kc_classifier") or {}
        return [
            f"### {d['label']}",
            "",
            f"- Kenyon cells: **{d['n_kc']}**",
            f"- untrained MBON accuracy **{d['untrained_accuracy']:.2f}** (margin {d['untrained_margin']:.1f} Hz) — book closed",
            f"- trained MBON accuracy **{d['trained_accuracy']:.2f}** (margin {d['trained_margin']:.1f} Hz) — book read",
            f"- frozen KC nearest-centroid (sidecar, not the fly): {frozen.get('accuracy', float('nan'))}",
            f"- weight drift {d.get('train', {}).get('weight_drift', float('nan')):.1f} synapse-count units",
            "",
        ]

    lines += row(exp["baseline_simple"])
    if "grown_simple" in exp:
        lines += row(exp["grown_simple"])
        gs, bs = exp["grown_simple"], exp["baseline_simple"]
        if gs["untrained_accuracy"] < 0.75 and gs["trained_accuracy"] >= 0.75:
            lines += [
                "Extra Kenyon cells **without** training still fail. Same cells **with** training acquire the preference.",
                "",
            ]
        if bs["trained_accuracy"] >= 0.75:
            lines += [
                "The small mushroom body can already learn this 2-odor skill once you train it.",
                "The new ability is the association, not a new organ.",
                "",
            ]
        if gs["trained_margin"] > bs["trained_margin"] + 1.0:
            lines += [
                f"After the same training, extra Kenyon cells separate good vs bad more strongly "
                f"(MBON margin {gs['trained_margin']:.1f} vs {bs['trained_margin']:.1f} Hz).",
                "",
            ]
    lines += [
        "## 2. Stronger after training (overlapping mixtures)",
        "",
        "Four blends that share glomeruli: DM1+DM2 / DM2+DM4 rewarded, DM1+DM3 / DM3+DM4 punished.",
        "Linear KC rank is the capacity; training is what spends it.",
        "",
        *row(exp["baseline_mix"]),
    ]
    if "grown_mix" in exp:
        lines += row(exp["grown_mix"])
        bm, gm = exp["baseline_mix"], exp["grown_mix"]
        if gm["trained_accuracy"] > bm["trained_accuracy"] + 1e-9:
            lines += [
                f"After the same training, +{exp.get('extra_kc', 0)} Kenyon cells beat the original "
                f"({gm['trained_accuracy']:.2f} vs {bm['trained_accuracy']:.2f}). That is extra capacity *used*.",
                "",
            ]
        elif gm["trained_margin"] > bm["trained_margin"] + 1.0:
            lines += [
                "Accuracy tied; the grown mushroom body separated good vs bad with a larger MBON margin "
                f"({gm['trained_margin']:.1f} vs {bm['trained_margin']:.1f} Hz).",
                "",
            ]
        else:
            lines += [
                "On this mixture set the grown mushroom body did not beat the original after training. "
                "Extra cells are not automatic intelligence; they help when the untrained rank was the bottleneck.",
                "",
            ]
    lines += [
        "### How to read this",
        "",
        "- **untrained**: extra cells do nothing useful at the MBON (unread book).",
        "- **trained**: the fly now has an odor preference it was not wired with.",
        "- **frozen KC classifier**: a human-side linear probe. It is not learning inside the connectome.",
        "- Tail / extra legs were examples of *new functions*, not organs. The function tested here is learned valence.",
        "",
    ]
    return "\n".join(lines)
