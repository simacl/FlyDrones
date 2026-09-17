"""Probes for grafted effectors and mushroom-body capacity.

These measurements answer the two MaleCNS research questions without pretending
the drone stick is the whole brain.

1. Novel ability: does a grafted TailMN / LegMN_A3 do something *other* than
   copy an existing descending or leg-motor command?
2. More powerful / more intelligent: does expanding Kenyon cells raise the
   linear separability of odor patterns? (Capacity, not general intelligence.)
"""

from __future__ import annotations

from collections import OrderedDict

import numpy as np

from .brain import Brain, Connectome
from .config import load_config

EXPAND_STIMULI = OrderedDict(
    [
        ("rest", {}),
        ("climb", {"T4c_L": 80.0, "T4c_R": 80.0}),
        ("loom", {"LPLC2_L": 150.0, "LPLC2_R": 0.0}),
        ("walk", {"T3_MN_L": 120.0, "T3_MN_R": 120.0}),
        ("odor_DM1", {"PN_DM1": 120.0}),
        ("odor_DM4", {"PN_DM4": 120.0}),
    ]
)

RESEARCH_IO = {
    "inputs": {
        "T4c_L": {"types": ["^T4c$"], "side": "L"},
        "T4c_R": {"types": ["^T4c$"], "side": "R"},
        "LPLC2_L": {"types": ["^LPLC2$"], "side": "L"},
        "LPLC2_R": {"types": ["^LPLC2$"], "side": "R"},
        "PN_DM1": {"types": ["^uPN_DM1$"]},
        "PN_DM2": {"types": ["^uPN_DM2$"]},
        "PN_DM3": {"types": ["^uPN_DM3$"]},
        "PN_DM4": {"types": ["^uPN_DM4$"]},
    },
    "outputs": {
        "DNg02_L": {"types": ["^DNg02"], "side": "L"},
        "DNg02_R": {"types": ["^DNg02"], "side": "R"},
        "DNp01_L": {"types": ["^DNp01$", "^GF$"], "side": "L"},
        "DNp01_R": {"types": ["^DNp01$", "^GF$"], "side": "R"},
        "T3_MN_L": {"types": ["^T3_MN$"], "side": "L"},
        "T3_MN_R": {"types": ["^T3_MN$"], "side": "R"},
        "EPG": {"types": ["^EPG"]},
        "KC": {"types": ["^KC", "^KCg"]},
        "MBON01": {"types": ["^MBON01"]},
        "MBON04": {"types": ["^MBON04"]},
        "TailMN": {"types": ["^TailMN$"]},
        "LegMN_A3_L": {"types": ["^LegMN_A3$"], "side": "L"},
        "LegMN_A3_R": {"types": ["^LegMN_A3$"], "side": "R"},
    },
}


def research_config(path=None) -> dict:
    cfg = load_config(path)
    cfg["inputs"] = {**cfg.get("inputs", {}), **RESEARCH_IO["inputs"]}
    cfg["outputs"] = {**cfg.get("outputs", {}), **RESEARCH_IO["outputs"]}
    cfg.setdefault("brain", {})
    cfg["brain"].setdefault("bias", {})
    cfg["brain"]["bias"].setdefault("DNg02_L", 8.0)
    cfg["brain"]["bias"].setdefault("DNg02_R", 8.0)
    return cfg


def _rate(brain: Brain, name: str) -> float:
    return float(brain.last_rates.get(name, 0.0))


def probe_effectors(
    connectome: Connectome,
    cfg: dict | None = None,
    settle_ms: float = 400.0,
    measure_ms: float = 500.0,
    rest_ms: float = 150.0,
) -> dict[str, dict[str, float]]:
    """Mean group rates under rest / climb / loom / two odors."""
    import warnings

    cfg = cfg or research_config()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        brain = Brain(connectome, cfg)
    brain.tick({}, settle_ms)
    out: dict[str, dict[str, float]] = {}
    for name, inp in EXPAND_STIMULI.items():
        if name != "rest":
            brain.tick({}, rest_ms)
        rates = dict(brain.tick(inp, measure_ms))
        out[name] = rates
    return out


def _corr(a: np.ndarray, b: np.ndarray) -> float:
    if a.size < 2 or b.size < 2 or np.allclose(a, a[0]) or np.allclose(b, b[0]):
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def effector_verdict(connectome: Connectome, rates: dict[str, dict[str, float]]) -> dict:
    """Classify grafted pools: missing, silent, coupled copy, or distinct."""
    types = set(connectome.types.astype(str))
    stims = list(rates)
    tail = np.array([rates[s].get("TailMN", 0.0) for s in stims])
    gf = np.array([max(rates[s].get("DNp01_L", 0.0), rates[s].get("DNp01_R", 0.0)) for s in stims])
    lift = np.array([rates[s].get("DNg02_L", 0.0) + rates[s].get("DNg02_R", 0.0) for s in stims])
    t3 = np.array([rates[s].get("T3_MN_L", 0.0) + rates[s].get("T3_MN_R", 0.0) for s in stims])
    legs = np.array([rates[s].get("LegMN_A3_L", 0.0) + rates[s].get("LegMN_A3_R", 0.0) for s in stims])

    def classify(signal: np.ndarray, copies: list[tuple[str, np.ndarray]], present: bool) -> dict:
        if not present:
            return {"status": "absent", "note": "type not in connectome (grow_like cannot invent it)"}
        if float(np.nanmax(signal)) < 2.0:
            return {"status": "silent", "note": "motor pool exists but does not fire"}
        corrs = {name: _corr(signal, src) for name, src in copies}
        best = max(corrs, key=lambda k: abs(corrs[k]) if corrs[k] == corrs[k] else -1)
        r = corrs[best]
        if r == r and abs(r) >= 0.75:
            return {
                "status": "coupled",
                "copy_of": best,
                "corr": r,
                "note": "new muscle on an old command — extra effector, not a new behaviour",
            }
        return {
            "status": "distinct",
            "corr": corrs,
            "note": "stimulus-locked and not a copy of the tested DNs — candidate new ability",
        }

    has_tail = "TailMN" in types
    legs_present = "LegMN_A3" in types
    return {
        "tail": {**classify(tail, [("DNp01", gf), ("DNg02", lift)], has_tail), "loom_hz": float(rates["loom"].get("TailMN", 0.0)), "climb_hz": float(rates["climb"].get("TailMN", 0.0))},
        "extra_legs": {
            **classify(legs, [("T3_MN", t3), ("DNg02", lift)], legs_present),
            "loom_hz": float(rates["loom"].get("LegMN_A3_L", 0.0) + rates["loom"].get("LegMN_A3_R", 0.0)),
            "climb_hz": float(rates["climb"].get("LegMN_A3_L", 0.0) + rates["climb"].get("LegMN_A3_R", 0.0)),
            "walk_hz": float(rates.get("walk", {}).get("LegMN_A3_L", 0.0) + rates.get("walk", {}).get("LegMN_A3_R", 0.0)),
        },
    }


def odor_capacity(
    connectome: Connectome,
    cfg: dict | None = None,
    n_repeats: int = 6,
    measure_ms: float = 400.0,
    settle_ms: float = 250.0,
    seed: int = 0,
) -> dict:
    """Linear odor discrimination from Kenyon-cell population rates.

    Four glomerulus channels (DM1–DM4). Each trial is one-hot. A nearest-centroid
    classifier on the KC rate vector is fit on half the repeats and tested on
    the rest. More KCs raise capacity when the expansion is sparse; they do not
    by themselves add a learning rule.
    """
    import warnings

    cfg = cfg or research_config()
    odors = [("PN_DM1", "DM1"), ("PN_DM2", "DM2"), ("PN_DM3", "DM3"), ("PN_DM4", "DM4")]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        brain = Brain(connectome, cfg, seed=seed)
    kc_idx = brain.connectome.group("KC")
    if kc_idx.size == 0:
        return {"n_kc": 0, "accuracy": float("nan"), "note": "no Kenyon cells"}
    X = []
    y = []
    brain.tick({}, settle_ms)
    rng = np.random.default_rng(seed)
    order = []
    for r in range(n_repeats):
        for inp, label in odors:
            order.append((inp, label, r))
    rng.shuffle(order)
    for inp, label, _r in order:
        brain.tick({}, 80.0)
        brain.tick({inp: 140.0}, measure_ms)
        vec = brain.last_counts[kc_idx].astype(np.float64)
        X.append(vec)
        y.append(label)
    X = np.vstack(X)
    y = np.asarray(y)
    # even/odd split by appearance order
    train = np.zeros(len(y), dtype=bool)
    seen: dict[str, int] = {}
    for i, lab in enumerate(y):
        seen[lab] = seen.get(lab, 0) + 1
        train[i] = seen[lab] % 2 == 1
    test = ~train
    centroids = {}
    for lab in np.unique(y[train]):
        centroids[lab] = X[train][y[train] == lab].mean(axis=0)
    pred = []
    for row in X[test]:
        pred.append(min(centroids, key=lambda lab: np.linalg.norm(row - centroids[lab])))
    acc = float(np.mean(np.asarray(pred) == y[test])) if test.any() else float("nan")
    rank = int(np.linalg.matrix_rank(X, tol=1e-6))
    return {
        "n_kc": int(kc_idx.size),
        "accuracy": acc,
        "pattern_rank": rank,
        "n_patterns": int(len(odors)),
        "n_repeats": n_repeats,
    }
