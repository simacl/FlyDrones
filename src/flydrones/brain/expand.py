"""MaleCNS research path: new effectors vs more of the same vs more capacity.

Two different operations, which must not be confused:

* ``grow_like`` / ``expand_compartment`` resample types the connectome already
  has (Kenyon cells, EPG, T3_MN, …). That cannot invent a tail.
* ``graft_appendage`` inserts a **new cell type the fly never had**, wired from
  existing drivers. That can add a motor pool for a tail or an extra leg pair.
  Whether it is a *new ability* is a measured question: if the new pool is a
  copy of DNp01 or of T3_MN, the animal gained a muscle, not a new behaviour.
"""

from __future__ import annotations

import re

import numpy as np
from scipy import sparse

from .connectome import Connectome
from .rewire import grow_like

# Type regexes that match MiniCNS *and* typical MaleCNS / neuPrint names.
COMPARTMENTS: dict[str, list[str]] = {
    "mushroom_body": [r"^KC", r"^KCg", r"^KCab", r"^KCap", r"^MBON", r"^PPL1", r"^PAM"],
    "kenyon": [r"^KC", r"^KCg", r"^KCab", r"^KCap"],
    "central_complex": [r"^EPG", r"^PEN", r"^PEG", r"^PFN", r"^PFR", r"^Delta7", r"^Δ7"],
    "flight": [r"^DNg02", r"^DNp01", r"^DNp03", r"^T4", r"^T5", r"^HS$", r"^VS$"],
    "vnc_leg": [r"^T1_MN", r"^T2_MN", r"^T3_MN", r"leg.*MN"],
}

APPENDAGES = {
    "tail": {
        "cell_type": "TailMN",
        "n": 8,
        "side": "",
        "drivers": [r"^DNp01$", r"^GF$"],
        "fallback_drivers": [r"^DNg02"],
        "note": "unpaired abdominal motor pool; fly has no tail",
    },
    "extra_legs": {
        "cell_type": "LegMN_A3",
        "n_per_side": 4,
        "drivers": [r"^T3_MN$"],
        "fallback_drivers": [r"^T2_MN$", r"^DNg02"],
        "note": "serial-homologue extra segment, copied from the last existing leg",
    },
}


def _extend_arr(old, extra, n_old: int, n_extra: int, fill):
    if old is None and extra is None:
        return None
    if old is None:
        old = np.full(n_old, fill)
    if extra is None:
        extra = np.full(n_extra, fill)
    return np.concatenate([old, extra])


def _select_drivers(connectome: Connectome, patterns: list[str], side: str | None) -> np.ndarray:
    types = connectome.types.astype(str)
    sides = connectome.sides.astype(str)
    mask = np.zeros(connectome.n, dtype=bool)
    for pat in patterns:
        rx = re.compile(pat)
        mask |= np.fromiter((bool(rx.search(t)) for t in types), dtype=bool, count=connectome.n)
    if side:
        mask &= sides == side
    return np.flatnonzero(mask)


def graft_motor_pool(
    connectome: Connectome,
    cell_type: str,
    n: int,
    *,
    side: str = "",
    drivers: list[str],
    fallback_drivers: list[str] | None = None,
    syn: float = 7.0,
    p: float = 0.75,
    seed: int = 0,
) -> Connectome:
    """Add a motor pool that does not exist in the connectome.

    Dendrites come from existing *driver* types (same-side if ``side`` is set).
    Axons are empty: these cells are read out as a new effector, like DNg02.
    """
    if n <= 0:
        return connectome.copy()
    rng = np.random.default_rng(seed)
    pre = _select_drivers(connectome, drivers, side or None)
    if pre.size == 0 and fallback_drivers:
        pre = _select_drivers(connectome, fallback_drivers, side or None)
    if pre.size == 0:
        pre = _select_drivers(connectome, drivers, None)
    if pre.size == 0 and fallback_drivers:
        pre = _select_drivers(connectome, fallback_drivers, None)
    if pre.size == 0:
        raise ValueError(f"no driver neurons for graft {cell_type!r} (tried {drivers})")

    old_n = connectome.n
    syn_use = syn if pre.size > 6 else max(syn, 80.0)
    p_use = p if pre.size > 6 else 1.0
    extra_r, extra_c, extra_d = [], [], []
    for k in range(n):
        nid = old_n + k
        take = rng.random(pre.size) < p_use
        chosen = pre[take]
        if chosen.size == 0:
            chosen = rng.choice(pre, size=min(3, pre.size), replace=False)
        w = np.clip(np.round(syn_use * (1 + 0.15 * rng.standard_normal(chosen.size))), 1, None)
        extra_r.append(np.full(chosen.size, nid, dtype=np.int64))
        extra_c.append(chosen.astype(np.int64))
        extra_d.append(w.astype(np.float32))

    coo = connectome.weights.tocoo()
    W2 = sparse.csc_matrix(
        (
            np.concatenate([coo.data, *extra_d]).astype(np.float32),
            (np.concatenate([coo.row, *extra_r]), np.concatenate([coo.col, *extra_c])),
        ),
        shape=(old_n + n, old_n + n),
        dtype=np.float32,
    )
    W2.sum_duplicates()
    extra_types = np.full(n, cell_type)
    extra_sides = np.full(n, side)
    extra_lin = np.full(n, f"{cell_type}_{side or 'U'}")
    extra_birth = np.arange(n, dtype=np.int32)
    extra_cols = np.full(n, -1, dtype=np.int32)
    bids = None
    if connectome.body_ids is not None:
        extra_ids = np.arange(int(connectome.body_ids.max()) + 1, int(connectome.body_ids.max()) + 1 + n, dtype=np.int64)
        bids = np.concatenate([connectome.body_ids, extra_ids])
    sc = _extend_arr(connectome.superclass, np.full(n, "grafted_motor"), old_n, n, "")
    grafted = list(connectome.meta.get("grafted") or [])
    grafted.append({"cell_type": cell_type, "n": n, "side": side, "drivers": drivers, "synapses": int(sum(x.size for x in extra_d))})
    return Connectome(
        name=f"{connectome.name}+{n}×{cell_type}{side}",
        weights=W2,
        types=np.concatenate([connectome.types.astype(str), extra_types]),
        sides=np.concatenate([connectome.sides.astype(str), extra_sides]),
        superclass=sc,
        body_ids=bids,
        groups={k: v.copy() for k, v in connectome.groups.items()},
        meta={**connectome.meta, "grafted": grafted},
        columns=_extend_arr(connectome.columns, extra_cols, old_n, n, -1),
        lineage=_extend_arr(connectome.lineage, extra_lin, old_n, n, ""),
        birth=_extend_arr(connectome.birth, extra_birth, old_n, n, -1),
    )


def graft_appendage(connectome: Connectome, kind: str, seed: int = 0) -> Connectome:
    """Insert a tail or an extra leg pair. See ``APPENDAGES``."""
    if kind not in APPENDAGES:
        raise ValueError(f"unknown appendage {kind!r}; choose from {sorted(APPENDAGES)}")
    spec = APPENDAGES[kind]
    if kind == "tail":
        return graft_motor_pool(
            connectome,
            spec["cell_type"],
            int(spec["n"]),
            side=str(spec.get("side", "")),
            drivers=list(spec["drivers"]),
            fallback_drivers=list(spec.get("fallback_drivers") or []),
            seed=seed,
        )
    out = connectome
    for i, side in enumerate(("L", "R")):
        out = graft_motor_pool(
            out,
            spec["cell_type"],
            int(spec["n_per_side"]),
            side=side,
            drivers=list(spec["drivers"]),
            fallback_drivers=list(spec.get("fallback_drivers") or []),
            seed=seed + i + 1,
        )
    return out


def expand_compartment(connectome: Connectome, compartment: str, n: int, seed: int = 0) -> Connectome:
    """Grow *n* extra cells inside an existing MaleCNS compartment (not a new organ)."""
    if compartment not in COMPARTMENTS:
        raise ValueError(f"unknown compartment {compartment!r}; choose from {sorted(COMPARTMENTS)}")
    return grow_like(connectome, n, type_pats=COMPARTMENTS[compartment], min_pop=1, seed=seed)
