"""Map MiniFly descending neurons onto NeuroMechFly's left/right walking drive.

NeuroMechFly (https://neuromechfly.org) is the body — a MuJoCo fly with compound
eyes, legs, adhesion, and a CPG that reads a two-value descending command.
FlyDrones is the brain. They meet at DNg02 L/R.

    python examples/05_neuromechfly.py              # no FlyGym needed
    python examples/05_neuromechfly.py --flygym     # walk, needs FlyGym 2
"""

from __future__ import annotations

import sys
from pathlib import Path

from flydrones.brain import Brain, build_minifly, reverse_laterality
from flydrones.circuit import probe
from flydrones.config import load_config
from flydrones.motor.descending import from_dng02

cfg = load_config()


def row(name: str, rates: dict, rest: dict) -> str:
    d = from_dng02(rates["DNg02_L"], rates["DNg02_R"], baseline_l=rest["DNg02_L"], baseline_r=rest["DNg02_R"])
    return (
        f"{name:12s}  DNg02 L/R {rates['DNg02_L']:5.1f}/{rates['DNg02_R']:5.1f} Hz  "
        f"->  descending [{d.left:.2f}, {d.right:.2f}]  (FlyGym L, R)"
    )


def show(title: str, connectome) -> None:
    print(title)
    b = Brain(connectome, cfg)
    r = probe(b, settle_ms=500, measure_ms=500, rest_ms=200)
    rest = r["rest"]
    print(row("rest", rest, rest))
    for stim in ("climb", "yaw_right", "loom_left"):
        print(row(stim, r[stim], rest))
    print()


show("MiniFly, intact wiring", build_minifly())
show("MiniFly, HS axons crossed to the other hemisphere", reverse_laterality(build_minifly(), "^HS$"))
print("yaw_right should swap L/R descending when HS is reversed: the body turns the other way.")
print("The CPG, the drone stick and the safety governor never changed — only who HS talks to.")
print()
print("To walk this in NeuroMechFly:")
print("  pip install 'flygym @ git+https://github.com/NeLy-EPFL/flygym.git@v2.1.0'")
print("  flydrones fly --drone flygym --config configs/neuromechfly.yaml --input gesture --seconds 8")

if "--flygym" in sys.argv:
    from flydrones.drones import make_drone
    from flydrones.runtime import Pilot, run_embodied

    cfg_nmf = load_config(Path(__file__).resolve().parents[1] / "configs" / "neuromechfly.yaml")
    drone = make_drone("flygym")
    pilot = Pilot(Brain(build_minifly(), cfg_nmf), drone, cfg_nmf)
    run_embodied([pilot], 4.0, hz=20)
    h = pilot.history[-1]
    print(f"after 4 s: x={h['x'] * 1e3:.1f} mm  y={h['y'] * 1e3:.1f} mm  (NeuroMechFly thorax)")
