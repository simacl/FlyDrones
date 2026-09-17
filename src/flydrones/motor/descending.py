"""Descending-neuron interface shared by the drone stick and NeuroMechFly.

FlyDrones reads DNg02 L/R (and a few other DNs) as a flight stick. NeuroMechFly's
``HybridTurningController`` reads a two-value descending drive that sets left and
right CPG amplitude. Same *shape* of interface — independent left/right descending
drive — different effectors (quad motors vs. a walking CPG).

This mapping is engineering, not biology: DNg02 is a *flight* descending neuron
(Namiki et al. 2022, wing-stroke amplitude). Walking uses other DNs. We reuse the
independent L/R pattern because that is what both stacks actually expose.
See https://neuromechfly.org and docs/SCIENCE.md.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .command import FlightCommand

# FlyGym v2 turning-controller tutorial uses ~0.4 (slow) and ~1.2 (fast).
DRIVE_LO = 0.2
DRIVE_HI = 1.6
DRIVE_REST = 0.8  # mid-walk drive when the stick is centred


@dataclass
class DescendingDrive:
    """Left/right descending command in FlyGym units (roughly 0.2–1.6)."""

    left: float
    right: float
    escape: bool = False

    def as_array(self) -> np.ndarray:
        return np.array([self.left, self.right], dtype=np.float64)


def _clip(v: float, lo: float = DRIVE_LO, hi: float = DRIVE_HI) -> float:
    return float(max(lo, min(hi, v)))


def from_dng02(
    rate_l: float,
    rate_r: float,
    baseline_l: float = 31.0,
    baseline_r: float = 31.0,
    rest: float = DRIVE_REST,
    hz_to_drive: float = 0.012,
    lo: float = DRIVE_LO,
    hi: float = DRIVE_HI,
) -> DescendingDrive:
    """Map raw DNg02 rates (Hz) onto independent left/right descending drive.

    ``hz_to_drive=0.012`` sends a +33 Hz bump (typical MiniFly climb on one side)
    to about +0.4 FlyGym units, i.e. rest 0.8 → 1.2, matching the tutorial's
    "fast" side.
    """
    return DescendingDrive(
        left=_clip(rest + hz_to_drive * (rate_l - baseline_l), lo, hi),
        right=_clip(rest + hz_to_drive * (rate_r - baseline_r), lo, hi),
    )


def from_command(
    cmd: FlightCommand,
    rest: float = DRIVE_REST,
    speed_gain: float = 0.45,
    turn_gain: float = 0.40,
    lo: float = DRIVE_LO,
    hi: float = DRIVE_HI,
) -> DescendingDrive:
    """Invert the drone stick back into left/right descending drive.

    FlyDrones' decoder is ``throttle ∝ L+R``, ``yaw ∝ R−L``. Walking has no
    altitude, so throttle and forward both add to mean walking speed. Escape
    (giant fiber) zeros both sides — a stand-in for a startle halt; a real jump
    takeoff is not implemented here.
    """
    if cmd.escape:
        return DescendingDrive(left=lo, right=lo, escape=True)
    speed = rest + speed_gain * (0.6 * cmd.forward + 0.4 * max(0.0, cmd.throttle))
    return DescendingDrive(
        left=_clip(speed - turn_gain * cmd.yaw, lo, hi),
        right=_clip(speed + turn_gain * cmd.yaw, lo, hi),
        escape=False,
    )
