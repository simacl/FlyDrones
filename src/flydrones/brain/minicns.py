"""MiniCNS: a MaleCNS-shaped toy, not a flight-only cartoon.

MiniFly only contains visual motion and flight descending neurons. Research
questions about *new body parts* and *capacity / intelligence* need a
connectome that already has a mushroom body, a heading circuit and walking
motor pools — the compartments MaleCNS actually has. MiniCNS is that scaffold
in a few hundred cells, using MaleCNS-like type names so the same operations
run on a built ``malecns_brain.npz``.

It is still not EM data.
"""

from __future__ import annotations

import numpy as np
from scipy import sparse

from .connectome import Connectome


def build_minicns(seed: int = 3) -> Connectome:
    """Compact CNS: vision→flight DN, AL→KC→MBON, EPG heading, T1–T3 leg MNs."""
    rng = np.random.default_rng(seed)
    pops: list[tuple[str, int, str, float]] = []

    def add(name: str, n: int, side: str, sign: float = 1.0) -> None:
        pops.append((name, n, side, sign))

    for s in ("L", "R"):
        add("T4c", 12, s, +1.0)
        add("VS", 3, s, +1.0)
        add("LPLC2", 12, s, +1.0)
        add("DNg02", 8, s, +1.0)
        add("DNp03", 2, s, +1.0)
        add("DNp01", 1, s, +1.0)
        add("EPG", 8, s, +1.0)
        add("T1_MN", 4, s, +1.0)
        add("T2_MN", 4, s, +1.0)
        add("T3_MN", 4, s, +1.0)
    add("uPN_DM1", 10, "", +1.0)
    add("uPN_DM2", 10, "", +1.0)
    add("uPN_DM3", 10, "", +1.0)
    add("uPN_DM4", 10, "", +1.0)
    add("KCg-m", 80, "", +1.0)
    add("MBON01", 2, "L", +1.0)
    add("MBON04", 2, "L", -1.0)
    add("PPL1-g1pedc", 2, "L", +1.0)

    types, sides, sign = [], [], []
    index: dict[tuple[str, str], np.ndarray] = {}
    start = 0
    for name, n, side, sg in pops:
        index[(name, side)] = np.arange(start, start + n)
        types += [name] * n
        sides += [side] * n
        sign += [sg] * n
        start += n
    N = start
    sign_arr = np.asarray(sign, dtype=np.float32)

    rows: list[np.ndarray] = []
    cols: list[np.ndarray] = []
    vals: list[np.ndarray] = []

    def connect(pre, post, syn: float, p: float = 1.0, jitter: float = 0.25) -> None:
        pre, post = np.asarray(pre), np.asarray(post)
        if pre.size == 0 or post.size == 0:
            return
        P, Q = np.meshgrid(pre, post)
        mask = rng.random(P.shape) < p
        w = syn * (1 + jitter * rng.standard_normal(P.shape))
        w = np.clip(np.round(np.abs(w)), 1, None)
        rows.append(Q[mask])
        cols.append(P[mask])
        vals.append(w[mask])

    def g(name: str, side: str = "") -> np.ndarray:
        return index[(name, side)]

    for s in ("L", "R"):
        o = "R" if s == "L" else "L"
        connect(g("T4c", s), g("VS", s), 5, p=0.85)
        connect(g("VS", s), g("DNg02", s), 10, p=0.9)
        connect(g("VS", s), g("DNg02", o), 5, p=0.5)
        connect(g("LPLC2", s), g("DNp01", s), 12, p=1.0)
        connect(g("LPLC2", s), g("DNp03", s), 10, p=1.0)
        connect(g("DNp03", s), g("DNg02", s), 6, p=0.8)
        epg = g("EPG", s)
        if epg.size >= 2:
            connect(epg, np.roll(epg, -1), 8, p=1.0, jitter=0.05)
            connect(epg, np.roll(epg, 1), 4, p=1.0, jitter=0.05)
        connect(g("EPG", s), g("T1_MN", s), 10, p=0.9)
        connect(g("T1_MN", s), g("T2_MN", s), 10, p=0.9)
        connect(g("T2_MN", s), g("T3_MN", s), 10, p=0.9)
        connect(g("DNg02", s), g("T1_MN", s), 2, p=0.3)

    pns = np.concatenate([g("uPN_DM1"), g("uPN_DM2"), g("uPN_DM3"), g("uPN_DM4")])
    kcs = g("KCg-m")
    connect(pns, kcs, 6, p=0.18)
    connect(kcs, g("MBON01", "L"), 3, p=0.35)
    connect(kcs, g("MBON04", "L"), 3, p=0.35)
    connect(g("PPL1-g1pedc", "L"), kcs, 2, p=0.2)

    r = np.concatenate(rows) if rows else np.zeros(0, dtype=np.int64)
    c = np.concatenate(cols) if cols else np.zeros(0, dtype=np.int64)
    v = np.concatenate(vals).astype(np.float32) * sign_arr[c] if vals else np.zeros(0, dtype=np.float32)
    W = sparse.csc_matrix((v, (r, c)), shape=(N, N), dtype=np.float32)
    return Connectome(
        name="minicns-malecns-toy",
        weights=W,
        types=np.asarray(types),
        sides=np.asarray(sides),
        body_ids=np.arange(N, dtype=np.int64),
        meta={"synthetic": True, "malecns_toy": True, "grid": [6, 8], "seed": seed},
    ).ensure_geometry()
