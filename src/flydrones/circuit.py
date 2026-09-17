"""Probe a connectome with a small stimulus battery and compare wiring lesions.

The decoder is left alone: we report descending-neuron rates, which is what
the drone actually reads. Differences here are differences in flight.
"""

from __future__ import annotations

from collections import OrderedDict

from .brain import (
    Brain,
    Connectome,
    ablate,
    add_silent_neurons,
    flip_signs,
    load_connectome,
    reverse_laterality,
    scale_synapses,
    shuffle_wiring,
)
from .brain.synthetic import build_minifly

STIMULI = OrderedDict(
    [
        ("rest", {}),
        ("climb", {"T4c_L": 80.0, "T4c_R": 80.0}),  # scene drifts up → should raise DNg02
        ("descend", {"T4d_L": 80.0, "T4d_R": 80.0}),  # scene drifts down → should drop DNg02
        ("yaw_right", {"T4a_R": 80.0, "T4b_L": 80.0}),  # rightward optic flow → DNg02_R > L
        ("loom_left", {"LPLC2_L": 150.0, "LC4_L": 120.0}),  # left looming → giant fiber + DNp03_L
    ]
)

def lift(rates: dict[str, float]) -> float:
    return rates.get("DNg02_L", 0.0) + rates.get("DNg02_R", 0.0)


def yaw_proxy(rates: dict[str, float]) -> float:
    return rates.get("DNg02_R", 0.0) - rates.get("DNg02_L", 0.0)


def escape(rates: dict[str, float]) -> float:
    return max(rates.get("DNp01_L", 0.0), rates.get("DNp01_R", 0.0))


def probe(
    brain: Brain,
    settle_ms: float = 800.0,
    measure_ms: float = 800.0,
    rest_ms: float = 400.0,
) -> dict[str, dict[str, float]]:
    """Return mean group rates (Hz) for each stimulus in ``STIMULI``."""
    brain.tick({}, settle_ms)
    out: dict[str, dict[str, float]] = {}
    for name, inp in STIMULI.items():
        if name != "rest":
            brain.tick({}, rest_ms)
        out[name] = dict(brain.tick(inp, measure_ms))
    return out


def summarise_row(name: str, connectome: Connectome, rates: dict[str, dict[str, float]], rtf: float) -> dict:
    rest = rates["rest"]
    return {
        "variant": name,
        "neurons": connectome.n,
        "connections": connectome.n_connections,
        "synapses": connectome.n_synapses,
        "lift_rest": lift(rest),
        "climb_d_lift": lift(rates["climb"]) - lift(rest),
        "descend_d_lift": lift(rates["descend"]) - lift(rest),
        "yaw_right": yaw_proxy(rates["yaw_right"]),
        "loom_escape": escape(rates["loom_left"]),
        "loom_saccade": rates["loom_left"].get("DNp03_L", 0.0) - rates["loom_left"].get("DNp03_R", 0.0),
        "rtf": rtf,
    }


def format_table(rows: list[dict]) -> str:
    cols = [
        ("variant", "variant", "<20"),
        ("neurons", "N", ">6"),
        ("connections", "conn", ">6"),
        ("climb_d_lift", "climbΔlift", ">11"),
        ("descend_d_lift", "descΔlift", ">10"),
        ("yaw_right", "yaw R−L", ">9"),
        ("loom_escape", "loom GF", ">8"),
        ("loom_saccade", "sacc L−R", ">10"),
        ("rtf", "rtf", ">6"),
    ]
    header = "  ".join(f"{title:{fmt}}" for _, title, fmt in cols)
    lines = [header, "-" * len(header)]
    for row in rows:
        cells = []
        for key, _title, fmt in cols:
            val = row[key]
            if key == "variant":
                cells.append(f"{val:{fmt}}")
            elif key in ("neurons", "connections"):
                cells.append(f"{int(val):{fmt}d}")
            elif key == "rtf":
                cells.append(f"{val:{fmt}.1f}x" if val == val else f"{'—':{fmt}}")
            else:
                cells.append(f"{val:{fmt}.1f}")
        lines.append("  ".join(cells))
    lines += [
        "",
        "climbΔlift  DNg02 L+R during scene-up minus rest. Open palm climb uses this.",
        "descΔlift   same, scene-down. Hand-drop descent uses this (should be negative).",
        "yaw R−L     DNg02_R − DNg02_L during rightward flow. Should be positive.",
        "loom GF     giant-fiber rate (max L/R) during left looming. Escape trigger.",
        "sacc L−R    DNp03_L − DNp03_R. Left loom should turn away (positive).",
        "rtf         brain-time / wall-time of the last tick (higher = faster).",
    ]
    return "\n".join(lines)


def _type_pat(raw: str) -> str:
    token = raw.replace("_", "")
    return f"^{raw}$" if token.isalnum() else raw


def apply_ops(
    connectome: Connectome,
    *,
    syn_scale: float = 1.0,
    extra_neurons: int = 0,
    ablate_path: str | None = None,
    flip: str | None = None,
    shuffle: bool = False,
    reverse: str | None = None,
    shuffle_seed: int = 1,
) -> Connectome:
    c = connectome
    if syn_scale != 1.0:
        c = scale_synapses(c, syn_scale)
    if extra_neurons:
        c = add_silent_neurons(c, extra_neurons)
    if ablate_path:
        if ":" not in ablate_path:
            raise ValueError("--ablate needs pre:post type regexes, e.g. T4c:VS")
        pre, post = ablate_path.split(":", 1)
        c = ablate(c, _type_pat(pre), _type_pat(post))
    if flip:
        c = flip_signs(c, _type_pat(flip))
    if reverse:
        c = reverse_laterality(c, _type_pat(reverse))
    if shuffle:
        c = shuffle_wiring(c, seed=shuffle_seed)
    return c


def preset_connectomes() -> list[tuple[str, Connectome]]:
    """A small suite that answers: more cells, more synapses, different wiring."""
    base = build_minifly()
    return [
        ("baseline", base),
        ("2x-synapses", build_minifly(syn_scale=2.0)),
        ("0.3x-synapses", build_minifly(syn_scale=0.3)),
        ("2x-neurons", build_minifly(pop_scale=2.0)),
        ("2x-neurons-norm", build_minifly(pop_scale=2.0, normalize=True)),
        ("+400-silent", add_silent_neurons(base, 400)),
        ("ablate-T4c→VS", ablate(base, "^T4c$", "^VS$")),
        ("flip-LPi_v", flip_signs(base, "^LPi_v$")),
        ("reverse-HS", reverse_laterality(base, "^HS$")),
        ("shuffle", shuffle_wiring(base, seed=1)),
    ]


def run_variant(name: str, connectome: Connectome, cfg: dict, **probe_kw) -> dict:
    brain = Brain(connectome, cfg)
    rates = probe(brain, **probe_kw)
    return summarise_row(name, connectome, rates, float(brain.realtime_factor))


def load_or_minifly(
    source: str | None,
    pop_scale: float = 1.0,
    syn_scale: float = 1.0,
    extra_neurons: int = 0,
    normalize: bool = False,
) -> Connectome:
    if source and str(source).lower() not in ("minifly", "synthetic", "mini"):
        c = load_connectome(source)
        if extra_neurons:
            c = add_silent_neurons(c, extra_neurons)
        if syn_scale != 1.0:
            c = scale_synapses(c, syn_scale)
        return c
    return build_minifly(
        pop_scale=pop_scale,
        syn_scale=syn_scale,
        extra_neurons=extra_neurons,
        normalize=normalize,
    )
