"""Hit a wall in the world, dodge, ask whether the next approach still hits.

Development teaches how to drive the legs. This module does not pair that
again. The animal walks in an arena. Collision and dodge are lived events.
Those events keep writing — they are not frozen into a lesson.
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
START_Y = 0.18
START_HEADING = 0.5 * math.pi
WALL = 0.02


def neural_verdict(rates: dict[str, float], rest: dict[str, float] | None = None) -> float:
    """Teaching factor from the brain's own cells, not a Python hit flag."""

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
    # Only judge while body channels are speaking. PPL1/MBON then pick the sign.
    if md + unl < 20.0:
        return 0.0
    pain = ch("PPL1") + 0.5 * md
    halt = 0.4 * chd
    avoid = ch("MBON04")
    relief = 0.9 * unl
    return float(np.tanh((relief - pain - halt - avoid) / 90.0))


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

    def reinforce(self, valence: float, kind: str = "all") -> float:
        if not self.locs or abs(valence) < 0.06 or self.eta == 0.0:
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
        for i, loc in enumerate(self.locs):
            if id(loc) not in ids:
                continue
            wrote += loc.update(self.trace[i], valence, self.eta)
            loc.commit(self.brain.connectome, self.brain.net)
        self.n_updates += 1
        self.last_valence = float(valence)
        return wrote

    def verdict(self, rest: dict[str, float] | None = None) -> float:
        return neural_verdict(self.brain.last_rates, rest)


@dataclass
class Body:
    x: float = START_X
    y: float = START_Y
    heading: float = START_HEADING
    hits: int = 0
    dodged: bool = False
    path: list[tuple[float, float, float]] = field(default_factory=list)
    contact: float = 0.0
    halt: float = 0.0
    unload: float = 0.0

    @property
    def wall_dist(self) -> float:
        return min(self.x, self.y, ARENA - self.x, ARENA - self.y)

    def senses(self, speed: float, prev_speed: float, hit: bool, away: bool) -> dict[str, float]:
        """World + body. Contact, halt, unload, loom — not a punishment label."""
        face_north = float(max(0.0, math.sin(self.heading)))
        t4 = 80.0 * face_north
        dist_n = max(ARENA - self.y, 0.02)
        closing = float(max(0.0, speed * math.sin(self.heading)))
        loom = float(min(160.0, 12.0 * closing / dist_n)) if closing > 0.02 else 0.0
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
        before_n = ARENA - self.y
        self.heading += turn * dt
        self.x += speed * math.cos(self.heading) * dt
        self.y += speed * math.sin(self.heading) * dt
        hit = False
        if self.x < WALL:
            self.x = WALL + 0.04
            self.heading = 0.0
            hit = True
        elif self.x > ARENA - WALL:
            self.x = ARENA - WALL - 0.04
            self.heading = math.pi
            hit = True
        if self.y < WALL:
            self.y = WALL + 0.04
            self.heading = 0.5 * math.pi
            hit = True
        elif self.y > ARENA - WALL:
            self.y = ARENA - 0.16
            self.heading = -0.5 * math.pi
            hit = True
        if hit:
            self.hits += 1
        away = (ARENA - self.y) > before_n + 1e-4
        if self.hits and away:
            self.dodged = True
        self.path.append((self.x, self.y, speed))
        return hit, away


def _approach(
    brain: Brain,
    learner: OnlineLearner,
    *,
    online: bool,
    dt_ms: float,
    seconds: float,
) -> dict[str, Any]:
    body = Body()
    dt = dt_ms / 1000.0
    t = 0.0
    speed = 0.0
    prev_speed = 0.0
    hit, away = False, False
    felt_pain = False
    log: list[dict[str, Any]] = []
    brain.tick({}, 80.0)
    rest = dict(brain.last_rates)
    while t < seconds - 1e-9:
        stim = body.senses(speed, prev_speed, hit, away)
        if body.contact > 0.4:
            felt_pain = True
        rates = brain.tick(stim, dt_ms)
        learner.observe(dt)
        v = neural_verdict(rates, rest)
        if online:
            learner.reinforce(v)
        prev_speed = speed
        hit, away = body.step(rates, dt)
        speed = body.path[-1][2] if body.path else 0.0
        log.append(
            {
                "t": t,
                "x": body.x,
                "y": body.y,
                "hits": body.hits,
                "walk": 0.5 * (rates.get("T3_MN_L", 0.0) + rates.get("T3_MN_R", 0.0)),
                "escape": max(rates.get("DNp01_L", 0.0), rates.get("DNp01_R", 0.0)),
                "wall": body.wall_dist,
                "verdict": v,
                "ppl1": float(rates.get("PPL1", 0.0)),
            }
        )
        t += dt
        if felt_pain and body.dodged and body.contact < 0.08:
            break
    return {
        "hits": body.hits,
        "dodged": bool(body.dodged and body.hits > 0),
        "min_wall": float(min((row["wall"] for row in log), default=body.wall_dist)),
        "min_north": float(min((ARENA - row["y"] for row in log), default=ARENA - body.y)),
        "end_y": body.y,
        "end_x": body.x,
        "seconds": t,
        "path": log[:: max(1, len(log) // 30)],
        "walk_mean": float(np.mean([row["walk"] for row in log])) if log else 0.0,
        "escape_max": float(max((row["escape"] for row in log), default=0.0)),
        "verdict_min": float(min((row["verdict"] for row in log), default=0.0)),
        "ppl1_max": float(max((row["ppl1"] for row in log), default=0.0)),
    }


def live_once(
    connectome: Connectome,
    cfg: dict | None = None,
    *,
    online: bool = True,
    dt_ms: float = 50.0,
    eta: float = 1.2,
    seed: int = 0,
    approach_s: float = 6.0,
    **_ignored: Any,
) -> dict[str, Any]:
    """Two approaches at the same wall. Pose resets. Weights do not, if online."""
    cfg = cfg or research_config()
    lived = connectome.copy(f"{connectome.name}+{'online' if online else 'frozen'}")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        brain = Brain(lived, cfg, seed=seed)
    learner = OnlineLearner(brain, eta=eta if online else 0.0, seed=seed)
    first = _approach(brain, learner, online=online, dt_ms=dt_ms, seconds=approach_s)
    second = _approach(brain, learner, online=online, dt_ms=dt_ms, seconds=approach_s)
    return {
        "online": online,
        "n": lived.n,
        "hits": int(first["hits"] + second["hits"]),
        "first": first,
        "second": second,
        "n_updates": learner.n_updates,
        "drift": learner.drift(),
        "connectome": lived,
        "hit_again": bool(second["hits"] > 0),
    }


def run_online_experiment(
    connectome: Connectome,
    cfg: dict | None = None,
    *,
    develop: bool = True,
    epochs: int = 6,
    seed: int = 0,
    eta: float = 1.2,
) -> dict[str, Any]:
    """Develop control, then two approaches at the wall."""
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
        a, b = run["first"], run["second"]
        again = "还会撞" if run["hit_again"] else "没再撞"
        return [
            f"## {tag}",
            "",
            f"- 第一次：撞 {a['hits']} 次，躲开了={a['dodged']}，离北墙最近 {a['min_north']:.3f}，判定最低 {a.get('verdict_min', 0):.2f}",
            f"- 第二次：撞 {b['hits']} 次，离北墙最近 {b['min_north']:.3f} → **{again}**",
            "",
        ]

    fr, on = exp["frozen"], exp["online"]
    lines = [
        f"# {title or '场地里撞墙，躲开，下次还会不会撞'}",
        "",
        "发育只教会怎么动腿。放到场地里走。今天撞了墙、躲开了。问下次还会不会撞。",
        "痛、急停、卸力、逼近进脑子，由 PPL1 和 MBON 自己判定。程序不写 −1。",
        "",
        *arm("墙上那次没写进去", fr),
        *arm("撞和躲当场写", on),
        "第一次两边都会撞、都会躲。第二次：没写进去的还撞；当场写的"
        + ("没再撞。" if not on["hit_again"] else "还是撞了。"),
        "",
    ]
    return "\n".join(lines)
