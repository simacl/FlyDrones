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


# Unique identified neurons: one (or a pair) per animal. Growing more of them
# would not be a real cell of that type.
_IDENTIFIED = frozenset({"DNp01", "GF"})


def grow_like(
    connectome: Connectome,
    n: int,
    *,
    seed: int = 0,
    min_pop: int = 5,
    type_pats: list[str] | None = None,
    name: str | None = None,
) -> Connectome:
    """Grow ``n`` new cells by resampling real type-to-type synapses.

    MaleCNS v1.0 is already the complete CNS of one male fly (~166k neurons).
    There are not 34k extra traced cells hiding in that volume. This operation
    is the research stand-in for *neurogenesis that follows the same rules*:

    * pick a cell type and side with probability equal to how common it is
      (rare / identified types such as the giant fiber are never drawn)
    * copy that type's **empirical axon**: out-degree and (target, weight)
      pairs are bootstrap samples of real synapses from existing cells of
      the same type
    * copy that type's **empirical dendrites** the same way
    * newborns only innervate the already-there scaffold (birth order);
      they do not yet synapse onto each other
    * neurotransmitter sign comes with the sampled weights

    The original connectome block is unchanged. On MaleCNS,
    ``grow_like(c, 34_000)`` is how you ask for a 200k brain whose extra
    cells are statistically the same kind of neuron, not a grafted gadget.
    """
    if n <= 0:
        return connectome.copy(name)
    rng = np.random.default_rng(seed)
    types = connectome.types.astype(str)
    sides = connectome.sides.astype(str)
    keys = np.array([f"{t}\t{s}" for t, s in zip(types, sides)])
    unique, inv, counts = np.unique(keys, return_inverse=True, return_counts=True)

    eligible: list[tuple[str, int, np.ndarray]] = []
    pats = [re.compile(p) for p in (type_pats or [])]
    for i, (key, count) in enumerate(zip(unique, counts)):
        t, _s = key.split("\t", 1)
        if t in _IDENTIFIED or count < min_pop:
            continue
        if pats and not any(p.search(t) for p in pats):
            continue
        eligible.append((key, int(count), np.flatnonzero(inv == i)))
    if not eligible:
        raise ValueError("no eligible populations to grow (identified/rare types are skipped)")

    pop_keys = [e[0] for e in eligible]
    pop_w = np.array([e[1] for e in eligible], dtype=np.float64)
    pop_w /= pop_w.sum()
    members = {e[0]: e[2] for e in eligible}

    csc = connectome.weights.tocsc()
    csr = connectome.weights.tocsr()
    coo = csc.tocoo()
    out_pool: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    in_pool: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    out_deg: dict[str, np.ndarray] = {}
    in_deg: dict[str, np.ndarray] = {}
    for key, _count, idx in eligible:
        posts, wouts = [], []
        pres, wins = [], []
        od, idg = [], []
        for i in idx:
            a, b = int(csc.indptr[i]), int(csc.indptr[i + 1])
            posts.append(csc.indices[a:b])
            wouts.append(csc.data[a:b])
            od.append(b - a)
            c0, c1 = int(csr.indptr[i]), int(csr.indptr[i + 1])
            pres.append(csr.indices[c0:c1])
            wins.append(csr.data[c0:c1])
            idg.append(c1 - c0)
        if any(p.size for p in posts):
            out_pool[key] = (np.concatenate(posts), np.concatenate(wouts).astype(np.float32))
        else:
            out_pool[key] = (np.zeros(0, dtype=np.int64), np.zeros(0, dtype=np.float32))
        if any(p.size for p in pres):
            in_pool[key] = (np.concatenate(pres), np.concatenate(wins).astype(np.float32))
        else:
            in_pool[key] = (np.zeros(0, dtype=np.int64), np.zeros(0, dtype=np.float32))
        out_deg[key] = np.asarray(od, dtype=np.int64)
        in_deg[key] = np.asarray(idg, dtype=np.int64)

    old_n = connectome.n
    extra_r: list[np.ndarray] = []
    extra_c: list[np.ndarray] = []
    extra_d: list[np.ndarray] = []
    new_types: list[str] = []
    new_sides: list[str] = []
    grown_hist: dict[str, int] = {}

    drawn = rng.choice(len(pop_keys), size=n, p=pop_w)
    for k, pop_i in enumerate(drawn):
        key = pop_keys[int(pop_i)]
        t, s = key.split("\t", 1)
        nid = old_n + k
        new_types.append(t)
        new_sides.append(s)
        grown_hist[t] = grown_hist.get(t, 0) + 1
        idx_e = int(rng.integers(members[key].size))
        k_out = int(out_deg[key][idx_e])
        k_in = int(in_deg[key][idx_e])
        posts, wouts = out_pool[key]
        if k_out and posts.size:
            ch = rng.integers(0, posts.size, size=k_out)
            extra_r.append(posts[ch].astype(np.int64))
            extra_c.append(np.full(k_out, nid, dtype=np.int64))
            extra_d.append(wouts[ch].astype(np.float32))
        pres, wins = in_pool[key]
        if k_in and pres.size:
            ch = rng.integers(0, pres.size, size=k_in)
            extra_r.append(np.full(k_in, nid, dtype=np.int64))
            extra_c.append(pres[ch].astype(np.int64))
            extra_d.append(wins[ch].astype(np.float32))

    chunks_r = [coo.row, *extra_r]
    chunks_c = [coo.col, *extra_c]
    chunks_d = [coo.data, *extra_d]
    W2 = sparse.csc_matrix(
        (np.concatenate(chunks_d).astype(np.float32), (np.concatenate(chunks_r), np.concatenate(chunks_c))),
        shape=(old_n + n, old_n + n),
        dtype=np.float32,
    )
    W2.sum_duplicates()
    W2.eliminate_zeros()

    sc = None
    if connectome.superclass is not None:
        sc = np.concatenate([connectome.superclass, np.full(n, "")])
    bids = None
    if connectome.body_ids is not None:
        extra_ids = np.arange(int(connectome.body_ids.max()) + 1, int(connectome.body_ids.max()) + 1 + n, dtype=np.int64)
        bids = np.concatenate([connectome.body_ids, extra_ids])
    added = int(W2.nnz) - int(connectome.n_connections)
    return Connectome(
        name=name or f"{connectome.name}+{n}grown",
        weights=W2,
        types=np.concatenate([types, np.asarray(new_types)]),
        sides=np.concatenate([sides, np.asarray(new_sides)]),
        superclass=sc,
        body_ids=bids,
        groups={k: v.copy() for k, v in connectome.groups.items()},
        meta={
            **connectome.meta,
            "grown": {
                "n": n,
                "new_connections": added,
                "by_type": grown_hist,
                "seed": seed,
                "min_pop": min_pop,
                "type_pats": type_pats,
            },
        },
    )
