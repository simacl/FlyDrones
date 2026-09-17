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


def clone_neurons(
    connectome: Connectome,
    type_pat: str,
    n: int,
    side: str | None = None,
    seed: int = 0,
    jitter: float = 0.0,
    normalize: bool = False,
    name: str | None = None,
) -> Connectome:
    """Add neurons of an existing type by cloning real axons and dendrites.

    Each new cell copies one randomly chosen exemplar of the same type (and
    side, if given):

    * outgoing synapses land on the **same postsynaptic partners** (same sign
      and roughly the same weight)
    * incoming synapses come from the **same presynaptic partners**
    * self-loops, if any, stay on the clone

    That is the wiring rule for "more of this cell type". It is not a random
    graph. Isolated padding (``add_silent_neurons``) and whole-network
    ``pop_scale`` (which also grows every *other* population) are different.

    If ``normalize``, every outgoing synapse from this type — old and new —
    is scaled by ``n_old / (n_old + n)`` so mean drive onto downstream cells
    stays put. Use that when the extra cells should only average noise.
    Skip it when you want a louder pathway.

    Identified neurons (one giant fiber per side) should not be cloned.
    """
    if n <= 0:
        return connectome.copy(name)
    types = connectome.types.astype(str)
    sides = connectome.sides.astype(str)
    mask = _match_types(types, type_pat)
    if side:
        mask &= sides == side
    pool = np.flatnonzero(mask)
    if pool.size == 0:
        raise ValueError(f"no neurons matching {type_pat!r} side={side!r}")

    rng = np.random.default_rng(seed)
    exemplars = rng.choice(pool, size=n, replace=True)
    csc = connectome.weights.tocsc()
    csr = connectome.weights.tocsr()
    old_n = connectome.n
    coo = csc.tocoo()
    chunks_r, chunks_c, chunks_d = [coo.row], [coo.col], [coo.data]

    for k, e in enumerate(exemplars):
        nid = old_n + int(k)
        c0, c1 = int(csc.indptr[e]), int(csc.indptr[e + 1])
        posts = csc.indices[c0:c1].copy()
        wout = csc.data[c0:c1].copy()
        posts = np.where(posts == e, nid, posts)
        if jitter and wout.size:
            wout = wout * np.float32(1.0 + jitter * rng.standard_normal(wout.size))
        if posts.size:
            chunks_r.append(posts.astype(np.int64))
            chunks_c.append(np.full(posts.size, nid, dtype=np.int64))
            chunks_d.append(wout.astype(np.float32))

        r0, r1 = int(csr.indptr[e]), int(csr.indptr[e + 1])
        pres = csr.indices[r0:r1]
        win = csr.data[r0:r1]
        keep = pres != e
        pres, win = pres[keep].copy(), win[keep].copy()
        if jitter and win.size:
            win = win * np.float32(1.0 + jitter * rng.standard_normal(win.size))
        if pres.size:
            chunks_r.append(np.full(pres.size, nid, dtype=np.int64))
            chunks_c.append(pres.astype(np.int64))
            chunks_d.append(win.astype(np.float32))

    new_n = old_n + n
    W2 = sparse.csc_matrix(
        (np.concatenate(chunks_d).astype(np.float32), (np.concatenate(chunks_r), np.concatenate(chunks_c))),
        shape=(new_n, new_n),
        dtype=np.float32,
    )
    W2.sum_duplicates()
    W2.eliminate_zeros()
    if normalize:
        grown = np.zeros(new_n, dtype=bool)
        grown[:old_n] = mask
        grown[old_n:] = True
        factor = np.float32(pool.size / (pool.size + n))
        W2 = W2.tocoo()
        data = W2.data.copy()
        data[grown[W2.col]] *= factor
        W2 = sparse.csc_matrix((data, (W2.row, W2.col)), shape=W2.shape, dtype=np.float32)

    sc = None
    if connectome.superclass is not None:
        extra_sc = connectome.superclass[exemplars]
        sc = np.concatenate([connectome.superclass, extra_sc])
    bids = None
    if connectome.body_ids is not None:
        extra_ids = np.arange(int(connectome.body_ids.max()) + 1, int(connectome.body_ids.max()) + 1 + n, dtype=np.int64)
        bids = np.concatenate([connectome.body_ids, extra_ids])
    return Connectome(
        name=name or f"{connectome.name}+{n}×{type_pat}",
        weights=W2,
        types=np.concatenate([types, types[exemplars]]),
        sides=np.concatenate([sides, sides[exemplars]]),
        superclass=sc,
        body_ids=bids,
        groups={k: v.copy() for k, v in connectome.groups.items()},
        meta={
            **connectome.meta,
            "cloned": {"type": type_pat, "n": n, "side": side, "normalize": normalize, "seed": seed},
        },
    )


def parse_clone_spec(spec: str) -> tuple[str, str | None, int]:
    """``T4c:96`` or ``T4c:L:48`` → (type, side, count)."""
    parts = spec.split(":")
    if len(parts) == 2:
        return parts[0], None, int(parts[1])
    if len(parts) == 3:
        return parts[0], parts[1], int(parts[2])
    raise ValueError("--clone needs Type:N or Type:side:N, e.g. T4c:96 or T4c:L:48")
