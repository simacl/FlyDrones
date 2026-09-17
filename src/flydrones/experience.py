"""After development: keep using the body; experience keeps writing.

Development teaches how to drive the legs. This module leaves the three-factor
rule on every tick. Teaching valence comes from whatever body channels the
brain already has. There is no per-scene branch.
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .brain import Brain, Connectome
from .brain.plasticity import PathwaySynapses, ensure_pathway_boutons
from .capacity import research_config
from .learn import BODY_PATHWAYS, train_body

WALK_PATHWAYS = BODY_PATHWAYS[:-1]
ESCAPE_PATHWAYS = BODY_PATHWAYS[-1:]

ARENA = 1.0
START_X = 0.50
START_Y = 0.35
START_HEADING = 0.35 * math.pi
WALL = 0.02


def neural_verdict(rates: dict[str, float], rest: dict[str, float] | None = None) -> float:
    """Teaching factor from the brain's own cells. Same mix for every scene."""

    def ch(*names: str) -> float:
        s = 0.0
        for n in names:
            x = float(rates.get(n, 0.0))
            if rest is not None:
                x -= float(rest.get(n, 0.0))
            s += x
        return s

    md = ch("mdIV_L", "mdIV_R")
    chd = ch("chordotonal_L", "chordotonal_R")
    unl = ch("unloading")
    loom = 0.45 * ch("LPLC2_L", "LPLC2_R")
    pain = ch("PPL1") + 0.5 * md
    halt = 0.4 * chd
    avoid = ch("MBON04")
    relief = 0.9 * unl
    return float(np.tanh((relief - pain - halt - avoid - loom) / 70.0))


class OnlineLearner:
    """Eligibility trace + three-factor writes on motor pathways, every tick."""

    def __init__(self, brain: Brain, eta: float = 0.35, tau_s: float = 0.25, seed: int = 0):
        self.brain = brain
        self.eta = float(eta)
        self.tau_s = float(tau_s)
        added = 0
        for pre, post in BODY_PATHWAYS:
            added += ensure_pathway_boutons(brain.connectome, pre, post, syn=16.0, p=0.7, seed=seed)
        if added:
            brain.net.set_connectivity(brain.connectome.weights)
        self.walk_locs = self._make(WALK_PATHWAYS)
        self.escape_locs = self._make(ESCAPE_PATHWAYS)
        self.locs = self.walk_locs + self.escape_locs
        self.trace = [np.zeros(loc.pre.size, dtype=np.float64) for loc in self.locs]
        self.n_updates = 0
        self.last_valence = 0.0

    def _make(self, pairs) -> list[PathwaySynapses]:
        out = []
        for pre, post in pairs:
            try:
                out.append(PathwaySynapses(self.brain.connectome, pre, post))
            except ValueError:
                continue
        return out

    def drift(self) -> float:
        return float(sum(loc.drift() for loc in self.locs))

    def observe(self, dt: float) -> None:
        if dt <= 0 or not self.locs:
            return
        a = 1.0 - float(np.exp(-dt / max(self.tau_s, 1e-3)))
        counts = self.brain.last_counts
        for i, loc in enumerate(self.locs):
            x = counts[loc.pre].astype(np.float64)
            self.trace[i] = (1.0 - a) * self.trace[i] + a * x

    def reinforce(self, valence: float, kind: str = "all", dt: float = 1.0) -> float:
        if abs(valence) < 0.04 or self.eta == 0.0 or dt <= 0:
            self.last_valence = float(valence)
            return 0.0
        if kind == "walk":
            wanted = self.walk_locs
        elif kind == "escape":
            wanted = self.escape_locs
        else:
            wanted = self.locs
        if not wanted:
            return 0.0
        wrote = 0.0
        ids = {id(loc) for loc in wanted}
        step = self.eta * float(dt)
        for i, loc in enumerate(self.locs):
            if id(loc) not in ids:
                continue
            wrote += loc.update(self.trace[i], valence, step)
            loc.commit(self.brain.connectome, self.brain.net)
        self.n_updates += 1
        self.last_valence = float(valence)
        return wrote

    def verdict(self, rest: dict[str, float] | None = None) -> float:
        return neural_verdict(self.brain.last_rates, rest)


def _ahead(x: float, y: float, heading: float) -> float:
    dx, dy = math.cos(heading), math.sin(heading)
    hits = []
    if dx > 1e-6:
        hits.append((ARENA - x) / dx)
    if dx < -1e-6:
        hits.append(x / -dx)
    if dy > 1e-6:
        hits.append((ARENA - y) / dy)
    if dy < -1e-6:
        hits.append(y / -dy)
    return float(min((t for t in hits if t > 0.0), default=ARENA))


@dataclass
class Body:
    x: float = START_X
    y: float = START_Y
    heading: float = START_HEADING
    hits: int = 0
    path: list[tuple[float, float, float]] = field(default_factory=list)
    contact: float = 0.0
    halt: float = 0.0
    unload: float = 0.0

    @property
    def edge_dist(self) -> float:
        return min(self.x, self.y, ARENA - self.x, ARENA - self.y)

    def senses(self, speed: float, prev_speed: float, hit: bool, away: bool) -> dict[str, float]:
        face_up = float(max(0.0, math.sin(self.heading)))
        t4 = 40.0 + 50.0 * face_up
        dist = max(_ahead(self.x, self.y, self.heading), 0.02)
        closing = float(max(0.0, speed))
        loom = float(min(160.0, 12.0 * closing / dist)) if closing > 0.02 else 0.0
        self.contact = 1.0 if hit else 0.62 * self.contact
        self.halt = max(float(max(0.0, prev_speed - speed)) / 0.35, 0.55 * self.halt)
        self.unload = 1.0 if away else 0.55 * self.unload
        pain = 170.0 * self.contact
        chord = min(150.0, 220.0 * self.halt)
        return {
            "T4c_L": t4,
            "T4c_R": t4,
            "LPLC2_L": loom,
            "LPLC2_R": 0.4 * loom,
            "mdIV_L": pain,
            "mdIV_R": pain,
            "chordotonal_L": chord,
            "chordotonal_R": chord,
            "unloading": 100.0 * self.unload,
        }

    def step(self, rates: dict[str, float], dt: float) -> tuple[bool, bool]:
        walk_l = float(rates.get("T3_MN_L", 0.0))
        walk_r = float(rates.get("T3_MN_R", 0.0))
        turn = 0.03 * (walk_r - walk_l)
        esc = max(float(rates.get("DNp01_L", 0.0)), float(rates.get("DNp01_R", 0.0)))
        speed = 0.018 * (walk_l + walk_r)
        if esc > 50.0:
            speed -= 0.003 * (esc - 50.0)
        before = self.edge_dist
        self.heading += turn * dt
        self.x += speed * math.cos(self.heading) * dt
        self.y += speed * math.sin(self.heading) * dt
        hit = False
        if self.x < WALL:
            self.x = WALL + 0.03
            self.heading = math.pi - self.heading
            hit = True
        elif self.x > ARENA - WALL:
            self.x = ARENA - WALL - 0.03
            self.heading = math.pi - self.heading
            hit = True
        if self.y < WALL:
            self.y = WALL + 0.03
            self.heading = -self.heading
            hit = True
        elif self.y > ARENA - WALL:
            self.y = ARENA - WALL - 0.03
            self.heading = -self.heading
            hit = True
        if hit:
            self.hits += 1
        away = self.edge_dist > before + 1e-4
        self.path.append((self.x, self.y, speed))
        return hit, away


def _usage(log: list[dict[str, Any]], t0: float, t1: float) -> dict[str, float]:
    rows = [r for r in log if t0 - 1e-9 <= r["t"] < t1 - 1e-9]
    if not rows:
        return {"contacts": 0.0, "walk": 0.0, "edge": 0.0, "writes": 0.0, "ticks": 0.0, "seconds": 0.0}
    return {
        "contacts": float(sum(1 for r in rows if r["contacted"])),
        "walk": float(np.mean([r["walk"] for r in rows])),
        "edge": float(np.mean([1.0 if r["edge"] < 0.12 else 0.0 for r in rows])),
        "writes": float(sum(1 for r in rows if r["wrote"])),
        "ticks": float(len(rows)),
        "seconds": float(rows[-1]["t"] - rows[0]["t"] + 1e-9),
    }


def live_once(
    connectome: Connectome,
    cfg: dict | None = None,
    *,
    online: bool = True,
    dt_ms: float = 50.0,
    eta: float = 0.25,
    seed: int = 0,
    seconds: float = 8.0,
    **_ignored: Any,
) -> dict[str, Any]:
    """One stretch in the environment. Pose is not reset. Weights write if online."""
    cfg = cfg or research_config()
    lived = connectome.copy(f"{connectome.name}+{'online' if online else 'frozen'}")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        brain = Brain(lived, cfg, seed=seed)
    learner = OnlineLearner(brain, eta=eta if online else 0.0, seed=seed)
    body = Body()
    dt = dt_ms / 1000.0
    t = 0.0
    speed = 0.0
    prev_speed = 0.0
    hit, away = False, False
    log: list[dict[str, Any]] = []
    brain.tick({}, 80.0)
    rest = dict(brain.last_rates)
    while t < seconds - 1e-9:
        stim = body.senses(speed, prev_speed, hit, away)
        rates = brain.tick(stim, dt_ms)
        learner.observe(dt)
        n0 = learner.n_updates
        v = neural_verdict(rates, rest)
        if online:
            learner.reinforce(v, dt=dt)
        wrote = learner.n_updates > n0
        prev_speed = speed
        hit, away = body.step(rates, dt)
        speed = body.path[-1][2] if body.path else 0.0
        log.append(
            {
                "t": t,
                "x": body.x,
                "y": body.y,
                "hits": body.hits,
                "contacted": bool(hit),
                "walk": 0.5 * (rates.get("T3_MN_L", 0.0) + rates.get("T3_MN_R", 0.0)),
                "escape": max(rates.get("DNp01_L", 0.0), rates.get("DNp01_R", 0.0)),
                "edge": body.edge_dist,
                "verdict": v,
                "ppl1": float(rates.get("PPL1", 0.0)),
                "wrote": wrote,
            }
        )
        t += dt
    mid = seconds * 0.5
    early = _usage(log, 0.0, mid)
    late = _usage(log, mid, seconds + 1e-6)
    return {
        "online": online,
        "n": lived.n,
        "hits": body.hits,
        "early": early,
        "late": late,
        "n_updates": learner.n_updates,
        "drift": learner.drift(),
        "connectome": lived,
        "verdict_min": float(min((row["verdict"] for row in log), default=0.0)),
        "ppl1_max": float(max((row["ppl1"] for row in log), default=0.0)),
        "path": log[:: max(1, len(log) // 40)],
        "writes_early": int(early["writes"]),
        "writes_late": int(late["writes"]),
        "continuous": bool(early["writes"] > 0 and late["writes"] > 0),
    }


def run_online_experiment(
    connectome: Connectome,
    cfg: dict | None = None,
    *,
    develop: bool = True,
    epochs: int = 6,
    seed: int = 0,
    eta: float = 0.25,
) -> dict[str, Any]:
    """Develop control, then one stretch with writing off vs on."""
    cfg = cfg or research_config()
    start = connectome.copy()
    devel_log: dict[str, Any] = {}
    if develop:
        start, devel_log = train_body(start, cfg, epochs=epochs, seed=seed)
    frozen = live_once(start, cfg, online=False, seed=seed, eta=eta)
    online = live_once(start, cfg, online=True, seed=seed, eta=eta)
    return {
        "developed": bool(develop),
        "devel": devel_log,
        "frozen": frozen,
        "online": online,
    }


def format_online_report(exp: dict[str, Any], title: str | None = None) -> str:
    def arm(tag: str, run: dict[str, Any]) -> list[str]:
        a, b = run["early"], run["late"]
        return [
            f"## {tag}",
            "",
            f"- 前半写入 {a['writes']:.0f}/{a['ticks']:.0f} 拍，后半写入 {b['writes']:.0f}/{b['ticks']:.0f} 拍，漂移 {run['drift']:.1f}",
            f"- 前半走 {a['walk']:.1f} Hz，后半走 {b['walk']:.1f} Hz",
            f"- 整段都在写：{run['continuous']}",
            "",
        ]

    fr, on = exp["frozen"], exp["online"]
    lines = [
        f"# {title or '在线持续写入'}",
        "",
        "发育只教会怎么动腿。规则全程开着，不按场景分写。",
        "身体有哪些通路就进哪些信号，PPL1 判定。看前半和后半都有没有写。程序不写 −1。",
        "",
        *arm("没写进去", fr),
        *arm("当场写", on),
        "当场写的前半和后半都在写。" if on["continuous"] and not fr["continuous"] else "写入没有贯穿整段。",
        "",
    ]
    return "\n".join(lines)
