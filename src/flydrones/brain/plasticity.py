"""KC→MBON three-factor plasticity (mushroom-body learning).

An extra Kenyon cell with frozen weights is an unread book: the pattern is
there, nobody has used it. Drosophila writes the book at KC→MBON synapses,
gated by a dopaminergic teaching signal (PPL1 aversive, PAM appetitive).

This module updates those synapses. It does **not** grow organs. The LIF
has no intracellular dopamine cascade; PPL1/PAM are the teaching *label*,
and the weight change is applied here (rate-based, not millisecond STDP).
"""

from __future__ import annotations

import re

import numpy as np
from scipy import sparse

from .connectome import Connectome
from .lif import LIFNetwork

KC_PATS = (r"^KC", r"^KCg", r"^KCab", r"^KCap")
APPROACH_PATS = (r"^MBON01",)
AVOID_PATS = (r"^MBON04",)


def _select(connectome: Connectome, pats: tuple[str, ...]) -> np.ndarray:
    types = connectome.types.astype(str)
    mask = np.zeros(connectome.n, dtype=bool)
    for pat in pats:
        rx = re.compile(pat)
        mask |= np.fromiter((bool(rx.search(t)) for t in types), dtype=bool, count=connectome.n)
    return np.flatnonzero(mask)


def _block(W: sparse.spmatrix, posts: np.ndarray, pres: np.ndarray) -> np.ndarray:
    if posts.size == 0 or pres.size == 0:
        return np.zeros((posts.size, pres.size), dtype=np.float64)
    return np.asarray(W.tocsc()[posts][:, pres].todense(), dtype=np.float64)


def _write_block(W: sparse.spmatrix, posts: np.ndarray, pres: np.ndarray, block: np.ndarray) -> sparse.csc_matrix:
    """Replace W[posts, pres] with ``block``; all other synapses stay put."""
    coo = sparse.coo_matrix(W)
    post_map = np.full(coo.shape[0], -1, dtype=np.int64)
    pre_map = np.full(coo.shape[1], -1, dtype=np.int64)
    post_map[np.asarray(posts, dtype=np.int64)] = np.arange(len(posts), dtype=np.int64)
    pre_map[np.asarray(pres, dtype=np.int64)] = np.arange(len(pres), dtype=np.int64)
    in_block = (post_map[coo.row] >= 0) & (pre_map[coo.col] >= 0)
    keep = ~in_block
    nz = np.abs(block) > 1e-8
    br, bc = np.nonzero(nz)
    rows = np.concatenate([coo.row[keep], np.asarray(posts, dtype=np.int64)[br]])
    cols = np.concatenate([coo.col[keep], np.asarray(pres, dtype=np.int64)[bc]])
    data = np.concatenate([coo.data[keep].astype(np.float32), block[br, bc].astype(np.float32)])
    out = sparse.csc_matrix((data, (rows, cols)), shape=coo.shape, dtype=np.float32)
    out.sum_duplicates()
    out.eliminate_zeros()
    return out


class KCMbonSynapses:
    """Existing KC→MBON01 (approach) and KC→MBON04 (avoid) boutons."""

    def __init__(self, connectome: Connectome, w_min: float = 0.25, w_max: float = 28.0):
        self.kc = _select(connectome, KC_PATS)
        self.approach = _select(connectome, APPROACH_PATS)
        self.avoid = _select(connectome, AVOID_PATS)
        if self.kc.size == 0:
            raise ValueError("no Kenyon cells to train")
        if self.approach.size == 0 or self.avoid.size == 0:
            raise ValueError("need MBON01 (approach) and MBON04 (avoid) for valence learning")
        self.w_min = float(w_min)
        self.w_max = float(w_max)
        W = connectome.weights
        self.w_app = _block(W, self.approach, self.kc)
        self.w_av = _block(W, self.avoid, self.kc)
        self.mask_app = np.abs(self.w_app) > 1e-8
        self.mask_av = np.abs(self.w_av) > 1e-8
        self.w_app_0 = self.w_app.copy()
        self.w_av_0 = self.w_av.copy()

    @property
    def n_boutons(self) -> int:
        return int(self.mask_app.sum() + self.mask_av.sum())

    def update(self, kc_counts: np.ndarray, valence: float, eta: float) -> float:
        """Three-factor rule: Δw ∝ KC eligibility × dopaminergic valence.

        valence > 0 (reward / PAM): potentiate KC→approach, depress KC→avoid.
        valence < 0 (punish / PPL1): the opposite.
        Only existing boutons move; signs stay excitatory (clipped positive).
        """
        r = np.asarray(kc_counts, dtype=np.float64).reshape(-1)
        if r.size != self.kc.size:
            raise ValueError(f"kc_counts length {r.size} != n_KC {self.kc.size}")
        peak = float(r.max())
        if peak <= 0:
            return 0.0
        elig = r / peak  # 0..1, silent KCs do not write
        v = float(valence)
        d_app = eta * v * elig
        d_av = eta * (-v) * elig
        before = np.abs(self.w_app).sum() + np.abs(self.w_av).sum()
        self.w_app = np.where(self.mask_app, np.clip(self.w_app + d_app[np.newaxis, :], self.w_min, self.w_max), 0.0)
        self.w_av = np.where(self.mask_av, np.clip(self.w_av + d_av[np.newaxis, :], self.w_min, self.w_max), 0.0)
        after = np.abs(self.w_app).sum() + np.abs(self.w_av).sum()
        return float(after - before)

    def commit(self, connectome: Connectome, net: LIFNetwork | None = None) -> Connectome:
        W = _write_block(connectome.weights, self.approach, self.kc, self.w_app)
        W = _write_block(W, self.avoid, self.kc, self.w_av)
        connectome.weights = W
        if net is not None:
            net.set_connectivity(W)
        return connectome

    def drift(self) -> float:
        d = np.abs(self.w_app - self.w_app_0).sum() + np.abs(self.w_av - self.w_av_0).sum()
        return float(d)


def ensure_kc_mbon_boutons(connectome: Connectome, syn: float = 3.0, p: float = 0.4, seed: int = 0) -> int:
    """Give silent Kenyon cells at least one bouton onto each MBON pool.

    ``grow_like`` usually copies axons; this is a backstop so a newborn KC can
    actually be trained instead of sitting unread.
    """
    kc = _select(connectome, KC_PATS)
    approach = _select(connectome, APPROACH_PATS)
    avoid = _select(connectome, AVOID_PATS)
    if kc.size == 0 or approach.size == 0 or avoid.size == 0:
        return 0
    W = connectome.weights.tocsc()
    rng = np.random.default_rng(seed)
    extra_r, extra_c, extra_d = [], [], []
    added = 0
    for pool in (approach, avoid):
        block = np.asarray(W[pool][:, kc].todense())
        silent = np.flatnonzero(np.abs(block).sum(axis=0) < 1e-8)
        for j in silent:
            chosen = pool[rng.random(pool.size) < p]
            if chosen.size == 0:
                chosen = rng.choice(pool, size=1)
            w = np.clip(np.round(syn * (1 + 0.2 * rng.standard_normal(chosen.size))), 1, None)
            extra_r.append(chosen.astype(np.int64))
            extra_c.append(np.full(chosen.size, kc[j], dtype=np.int64))
            extra_d.append(w.astype(np.float32))
            added += int(chosen.size)
    if not extra_r:
        return 0
    coo = W.tocoo()
    W2 = sparse.csc_matrix(
        (
            np.concatenate([coo.data.astype(np.float32), *extra_d]),
            (np.concatenate([coo.row, *extra_r]), np.concatenate([coo.col, *extra_c])),
        ),
        shape=W.shape,
        dtype=np.float32,
    )
    W2.sum_duplicates()
    connectome.weights = W2
    return added
