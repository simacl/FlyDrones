"""Perturb a connectome without touching the decoder or the drone.

These operations change *who talks to whom* (or how strongly). The motor
read-out still looks at the same descending-neuron groups; if the wiring no
longer drives those groups, the drone's reflexes change or vanish. That is
the point of the experiments in ``flydrones circuit``.
"""

from __future__ import annotations

import re

import numpy as np
from scipy import sparse

from .connectome import Connectome


def _match_types(types: np.ndarray, pattern: str) -> np.ndarray:
    rx = re.compile(pattern)
    return np.fromiter((bool(rx.search(str(t))) for t in types), dtype=bool, count=len(types))


def scale_synapses(connectome: Connectome, factor: float, name: str | None = None) -> Connectome:
    """Multiply every synapse count. ``factor=2`` is a stronger PSP at the same addresses."""
    out = connectome.copy(name or f"{connectome.name}-syn{factor:g}")
    W = out.weights.copy()
    W.data = (W.data * np.float32(factor)).astype(np.float32)
    W.eliminate_zeros()
    out.weights = W
    out.meta = {**out.meta, "syn_scale": factor}
    return out


def add_silent_neurons(connectome: Connectome, n: int, cell_type: str = "silent") -> Connectome:
    """Pad with unconnected neurons. Flight is unchanged; every LIF step still updates them."""
    if n <= 0:
        return connectome.copy()
    W = connectome.weights.tocoo()
    n2 = connectome.n + n
    weights = sparse.csc_matrix((W.data, (W.row, W.col)), shape=(n2, n2), dtype=np.float32)
    types = np.concatenate([connectome.types, np.full(n, cell_type)])
    sides = np.concatenate([connectome.sides.astype(str), np.full(n, "")])
    sc = None
    if connectome.superclass is not None:
        sc = np.concatenate([connectome.superclass, np.full(n, "")])
    bids = None
    if connectome.body_ids is not None:
        extra = np.arange(int(connectome.body_ids.max()) + 1, int(connectome.body_ids.max()) + 1 + n, dtype=np.int64)
        bids = np.concatenate([connectome.body_ids, extra])
    out = Connectome(
        name=f"{connectome.name}+{n}silent",
        weights=weights,
        types=types,
        sides=sides,
        superclass=sc,
        body_ids=bids,
        groups={k: v.copy() for k, v in connectome.groups.items()},
        meta={**connectome.meta, "extra_neurons": n},
    )
    return out


def ablate(connectome: Connectome, pre: str, post: str, side: str | None = None, name: str | None = None) -> Connectome:
    """Zero directed connections from cell types matching ``pre`` to those matching ``post``."""
    out = connectome.copy(name or f"{connectome.name}-ablate-{pre}-{post}")
    W = out.weights.tocoo()
    pre_m = _match_types(out.types, pre)
    post_m = _match_types(out.types, post)
    if side:
        pre_m &= out.sides.astype(str) == side
        post_m &= out.sides.astype(str) == side
    drop = pre_m[W.col] & post_m[W.row]
    keep = ~drop
    out.weights = sparse.csc_matrix((W.data[keep], (W.row[keep], W.col[keep])), shape=W.shape, dtype=np.float32)
    out.meta = {**out.meta, "ablate": {"pre": pre, "post": post, "side": side, "removed": int(drop.sum())}}
    return out


def flip_signs(connectome: Connectome, types: str | list[str], name: str | None = None) -> Connectome:
    """Negate outgoing synapses of matching neurons (excitatory ↔ inhibitory)."""
    if isinstance(types, str):
        types = [types]
    out = connectome.copy(name or f"{connectome.name}-flip")
    mask = np.zeros(out.n, dtype=bool)
    for pat in types:
        mask |= _match_types(out.types, pat)
    W = out.weights.tocoo()
    data = W.data.copy()
    data[mask[W.col]] *= -1
    out.weights = sparse.csc_matrix((data, (W.row, W.col)), shape=W.shape, dtype=np.float32)
    out.meta = {**out.meta, "flip": types, "flipped_neurons": int(mask.sum())}
    return out


def shuffle_wiring(connectome: Connectome, seed: int = 0, name: str | None = None) -> Connectome:
    """Keep every axon and its synapse counts, but pick new postsynaptic addresses at random.

    Out-degree is preserved (up to colliding onto the same target). Circuit identity is not.
    """
    out = connectome.copy(name or f"{connectome.name}-shuffled")
    W = out.weights.tocoo()
    rng = np.random.default_rng(seed)
    new_rows = rng.integers(0, out.n, size=W.nnz, dtype=np.int64)
    self = new_rows == W.col
    new_rows[self] = (new_rows[self] + 1) % out.n
    shuffled = sparse.csc_matrix((W.data, (new_rows, W.col)), shape=W.shape, dtype=np.float32)
    shuffled.sum_duplicates()
    shuffled.eliminate_zeros()
    out.weights = shuffled
    out.meta = {**out.meta, "shuffled": True, "shuffle_seed": seed}
    return out


def reverse_laterality(connectome: Connectome, pre: str, name: str | None = None) -> Connectome:
    """Send each outgoing synapse of matching neurons to the contralateral counterpart of its target.

    Same-side excitation becomes opposite-side excitation. For MiniFly HS this
    reverses the optomotor turn: a rightward scene now yaws left.
    """
    out = connectome.copy(name or f"{connectome.name}-rev-{pre}")
    types = out.types.astype(str)
    sides = out.sides.astype(str)
    pre_m = _match_types(types, pre)
    counterpart = _contralateral_index(types, sides)
    W = out.weights.tocoo()
    new_rows = W.row.copy()
    hit = pre_m[W.col]
    dest = counterpart[W.row[hit]]
    valid = dest >= 0
    idx = np.flatnonzero(hit)
    new_rows[idx[valid]] = dest[valid]
    out.weights = sparse.csc_matrix((W.data, (new_rows, W.col)), shape=W.shape, dtype=np.float32)
    out.weights.sum_duplicates()
    out.meta = {**out.meta, "reverse_laterality": pre, "rewired": int(valid.sum())}
    return out


def _contralateral_index(types: np.ndarray, sides: np.ndarray) -> np.ndarray:
    """For each neuron, index of the same-rank cell of the same type on the other side, or -1."""
    other = {"L": "R", "R": "L"}
    buckets: dict[tuple[str, str], list[int]] = {}
    for i, (t, s) in enumerate(zip(types, sides)):
        buckets.setdefault((t, s), []).append(i)
    out = np.full(len(types), -1, dtype=np.int64)
    for (t, s), idxs in buckets.items():
        o = other.get(s)
        if not o:
            continue
        contra = buckets.get((t, o), [])
        if not contra:
            continue
        for k, i in enumerate(idxs):
            out[i] = contra[k % len(contra)]
    return out


def pathway_weight(connectome: Connectome, pre: str, post: str) -> tuple[int, float]:
    """(n_connections, mean signed synapse count) from ``pre`` types to ``post`` types."""
    W = connectome.weights.tocoo()
    pre_m = _match_types(connectome.types, pre)
    post_m = _match_types(connectome.types, post)
    hit = pre_m[W.col] & post_m[W.row]
    if not hit.any():
        return 0, 0.0
    data = W.data[hit]
    return int(hit.sum()), float(data.mean())
