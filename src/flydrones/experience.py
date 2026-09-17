"""Online, experience-driven change after development.

Development is grow + pairing. This module keeps the same three-factor rule
running while the animal lives: climb, loom, collision. Frozen weights are
the control — learned then locked.
"""

from __future__ import annotations

import warnings
from typing import Any

import numpy as np

from .brain import Brain, Connectome
from .brain.plasticity import PathwaySynapses, ensure_pathway_boutons
from .capacity import research_config
from .learn import BODY_PATHWAYS, body_snapshot, train_body

# Lived events: (t_seconds, name, stim, valence_per_second).
# "hit" is an impulse (valence applied once).
DEFAULT_LIFE: list[tuple[float, str, dict[str, float], float]] = [
    (0.0, "rest", {}, 0.0),
    (1.0, "climb", {"T4c_L": 80.0, "T4c_R": 80.0}, 0.35),
    (3.0, "rest", {}, 0.0),
    (4.0, "loom", {"LPLC2_L": 150.0, "LPLC2_R": 0.0}, 0.35),
    (5.0, "hit", {}, -1.0),
    (5.05, "rest", {}, 0.0),
    (6.0, "climb", {"T4c_L": 80.0, "T4c_R": 80.0}, 0.35),
    (8.0, "loom", {"LPLC2_L": 150.0, "LPLC2_R": 0.0}, 0.35),
    (9.0, "rest", {}, 0.0),
    (10.0, "climb", {"T4c_L": 80.0, "T4c_R": 80.0}, 0.35),
]


class OnlineLearner:
    """Eligibility trace + three-factor writes on motor pathways, every tick."""

    def __init__(self, brain: Brain, eta: float = 0.35, tau_s: float = 0.25, seed: int = 0):
        self.brain = brain
        self.eta = float(eta)
        self.tau_s = float(tau_s)
        added = 0
        locs: list[PathwaySynapses] = []
        for pre, post in BODY_PATHWAYS:
            added += ensure_pathway_boutons(brain.connectome, pre, post, syn=16.0, p=0.7, seed=seed)
            try:
                locs.append(PathwaySynapses(brain.connectome, pre, post))
            except ValueError:
                continue
        if added:
            brain.net.set_connectivity(brain.connectome.weights)
            locs = []
            for pre, post in BODY_PATHWAYS:
                try:
                    locs.append(PathwaySynapses(brain.connectome, pre, post))
                except ValueError:
                    continue
        self.locs = locs
        self.trace = [np.zeros(loc.pre.size, dtype=np.float64) for loc in locs]
        self.n_updates = 0
        self.last_valence = 0.0

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

    def reinforce(self, valence: float) -> float:
        if not self.locs or abs(valence) < 1e-12 or self.eta == 0.0:
            self.last_valence = float(valence)
            return 0.0
        wrote = 0.0
        for i, loc in enumerate(self.locs):
            wrote += loc.update(self.trace[i], valence, self.eta)
            loc.commit(self.brain.connectome, self.brain.net)
        self.n_updates += 1
        self.last_valence = float(valence)
        return wrote


def _event_at(timeline: list[tuple[float, str, dict[str, float], float]], t: float) -> tuple[str, dict[str, float], float]:
    name, stim, val = "rest", {}, 0.0
    for ts, n, s, v in timeline:
        if t + 1e-9 >= ts:
            name, stim, val = n, s, v
    return name, stim, val


def live_once(
    connectome: Connectome,
    cfg: dict | None = None,
    *,
    online: bool = True,
    timeline: list[tuple[float, str, dict[str, float], float]] | None = None,
    dt_ms: float = 50.0,
    eta: float = 0.35,
    seed: int = 0,
    snapshot_s: tuple[float, ...] = (0.0, 3.0, 6.0, 12.0),
    probe_kw: dict | None = None,
) -> dict[str, Any]:
    """Play a life. ``online=False`` watches the same events with frozen weights."""
    cfg = cfg or research_config()
    timeline = timeline or DEFAULT_LIFE
    probe_kw = probe_kw or dict(settle_ms=120.0, measure_ms=180.0, rest_ms=50.0)
    lived = connectome.copy(f"{connectome.name}+{'online' if online else 'frozen'}")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        brain = Brain(lived, cfg, seed=seed)
    learner = OnlineLearner(brain, eta=eta if online else 0.0, seed=seed)
    t_end = max(ts for ts, *_ in timeline) + 2.0
    dt = dt_ms / 1000.0
    brain.tick({}, 120.0)
    want = list(snapshot_s)
    snaps: list[dict[str, Any]] = []
    drift: list[tuple[float, float, str]] = []
    hits = 0
    t = 0.0
    snap_set = set()
    fired_hits: set[float] = set()
    while t < t_end + 1e-9:
        name, stim, val = _event_at(timeline, t)
        if name == "hit":
            hit_ts = max(ts for ts, n, *_ in timeline if n == "hit" and t + 1e-9 >= ts)
            brain.tick({}, dt_ms)
            learner.observe(dt)
            if hit_ts not in fired_hits:
                learner.reinforce(-1.0)
                hits += 1
                fired_hits.add(hit_ts)
            name = "rest"
        else:
            brain.tick(stim, dt_ms)
            learner.observe(dt)
            if val:
                learner.reinforce(val)
        drift.append((t, learner.drift(), name))
        for mark in want:
            if t + 1e-9 >= mark and mark not in snap_set:
                snaps.append({"t": mark, "event": name, **body_snapshot(lived, cfg, **probe_kw)})
                snap_set.add(mark)
        t += dt
    return {
        "online": online,
        "n": lived.n,
        "hits": hits,
        "n_updates": learner.n_updates,
        "drift": learner.drift(),
        "drift_trace": drift[:: max(1, len(drift) // 40)],
        "snapshots": snaps,
        "connectome": lived,
    }


def run_online_experiment(
    connectome: Connectome,
    cfg: dict | None = None,
    *,
    develop: bool = True,
    epochs: int = 6,
    seed: int = 0,
    eta: float = 0.35,
) -> dict[str, Any]:
    """Development, then the same life twice: frozen vs still learning."""
    cfg = cfg or research_config()
    start = connectome.copy()
    devel_log: dict[str, Any] = {}
    if develop:
        start, devel_log = train_body(start, cfg, epochs=epochs, seed=seed)
    before = body_snapshot(start, cfg, settle_ms=120.0, measure_ms=180.0, rest_ms=50.0)
    frozen = live_once(start, cfg, online=False, seed=seed, eta=eta)
    online = live_once(start, cfg, online=True, seed=seed, eta=eta)
    return {
        "developed": bool(develop),
        "devel": devel_log,
        "before": before,
        "frozen": frozen,
        "online": online,
    }


def format_online_report(exp: dict[str, Any], title: str | None = None) -> str:
    def row(tag: str, snap: dict[str, Any]) -> str:
        return (
            f"- **{tag}**: climb→lift {snap['climb_lift_hz']:.1f} Hz, "
            f"climb→walk {snap['climb_walk_hz']:.1f} Hz, "
            f"loom→escape {snap['loom_escape_hz']:.1f} Hz"
        )

    lines = [
        f"# {title or 'After development: keep changing with experience'}",
        "",
        "Same life twice. Frozen = learned then locked. Online = climb/loom keep writing, a hit punishes.",
        "",
        row("after development", exp["before"]),
        "",
        f"Frozen end drift **{exp['frozen']['drift']:.1f}**, updates {exp['frozen']['n_updates']}.",
        "",
    ]
    for s in exp["frozen"]["snapshots"]:
        lines.append(row(f"frozen t={s['t']:.0f}s", s))
    lines += [
        "",
        f"Online end drift **{exp['online']['drift']:.1f}**, updates {exp['online']['n_updates']}, hits {exp['online']['hits']}.",
        "",
    ]
    for s in exp["online"]["snapshots"]:
        lines.append(row(f"online t={s['t']:.0f}s", s))
    fr = exp["frozen"]["snapshots"]
    on = exp["online"]["snapshots"]
    if fr and on:
        fw, ow = fr[-1]["climb_walk_hz"], on[-1]["climb_walk_hz"]
        lines += [
            "",
            f"By the end, walk-to-scene-up is {fw:.1f} Hz if frozen and {ow:.1f} Hz if it kept living.",
            "The hit is in the middle: online weights move through it; frozen ones do not.",
            "",
        ]
    return "\n".join(lines)
