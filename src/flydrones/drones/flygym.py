"""Optional NeuroMechFly body: FlyDrones descending neurons -> FlyGym walking CPG.

NeuroMechFly / FlyGym is EPFL's digital twin of an adult fly
(https://neuromechfly.org). This adapter does not vendor their physics; it
imports FlyGym 2 if you have installed it and feeds it the same left/right
descending drive FlyDrones already computes for drones.

    pip install 'flygym @ git+https://github.com/NeLy-EPFL/flygym.git@v2.1.0'
    flydrones fly --drone flygym --config configs/neuromechfly.yaml --input gesture --seconds 8

Without FlyGym this module still imports: constructing ``FlyGymDrone`` raises
a clear error pointing at the docs.
"""

from __future__ import annotations

import math
import os
import time

import numpy as np

from ..motor.command import FlightCommand
from ..motor.descending import DescendingDrive, from_command
from ..safety import Telemetry
from .base import Drone

INSTALL = (
    "NeuroMechFly (FlyGym 2) is not installed.\n"
    "  pip install 'flygym @ git+https://github.com/NeLy-EPFL/flygym.git@v2.1.0'\n"
    "Docs: https://neuromechfly.org"
)


def _import_flygym():
    try:
        from flygym import Simulation
        from flygym.anatomy import BodySegment, ContactBodiesPreset
        from flygym.compose import FlatGroundWorld
        from flygym.utils.math import Rotation3D
        from flygym_demo.complex_terrain import (
            HybridControllerObservation,
            HybridTurningController,
            LocomotionAction,
            PreprogrammedSteps,
            apply_locomotion_action,
            make_locomotion_fly,
        )
    except ImportError as e:
        raise ImportError(INSTALL) from e
    return {
        "Simulation": Simulation,
        "BodySegment": BodySegment,
        "ContactBodiesPreset": ContactBodiesPreset,
        "FlatGroundWorld": FlatGroundWorld,
        "Rotation3D": Rotation3D,
        "HybridControllerObservation": HybridControllerObservation,
        "HybridTurningController": HybridTurningController,
        "LocomotionAction": LocomotionAction,
        "PreprogrammedSteps": PreprogrammedSteps,
        "apply_locomotion_action": apply_locomotion_action,
        "make_locomotion_fly": make_locomotion_fly,
    }


class FlyGymDrone(Drone):
    """Walk a NeuroMechFly body from FlyDrones ``FlightCommand``s.

    FlyGym's physics step is 0.1 ms; each ``send()`` advances ``dt_s`` of
    simulated time (default 50 ms, i.e. one 20 Hz control tick). Units in
    FlyGym are millimetres; telemetry is converted to metres so the rest of
    FlyDrones can keep its drone-shaped numbers. Use ``configs/neuromechfly.yaml``
    so the safety floor (0.3 m) is not applied to a 1 mm-tall animal.
    """

    name = "flygym"
    has_camera = False

    def __init__(self, dt_s: float = 0.05, headless: bool = True, seed: int = 0):
        if headless:
            os.environ.setdefault("MUJOCO_GL", "osmesa")
        fg = _import_flygym()
        fly = fg["make_locomotion_fly"](name="flydrones", add_adhesion=True, colorize=True)
        world = fg["FlatGroundWorld"]()
        world.add_fly(
            fly,
            [0, 0, 0.8],
            fg["Rotation3D"]("quat", [1, 0, 0, 0]),
            bodysegs_with_ground_contact=fg["ContactBodiesPreset"].TIBIA_TARSUS_ONLY,
            add_ground_contact_sensors=False,
        )
        sim = fg["Simulation"](world)
        steps = fg["PreprogrammedSteps"]()
        dof_order = fly.get_actuated_jointdofs_order("position")
        controller = fg["HybridTurningController"](
            timestep=sim.timestep,
            preprogrammed_steps=steps,
            output_dof_order=dof_order,
        )
        sim.reset()
        controller.reset(seed=seed)
        initial = fg["LocomotionAction"](
            joint_angles=steps.default_pose_by_dof_order(dof_order),
            adhesion_onoff=np.ones(6, dtype=bool),
        )
        fg["apply_locomotion_action"](sim, fly.name, initial)
        sim.warmup()

        self._fg = fg
        self._fly = fly
        self._sim = sim
        self._controller = controller
        self._thorax = fly.get_bodysegs_order().index(fg["BodySegment"]("c_thorax"))
        self._dt_s = float(dt_s)
        self._nsub = max(1, int(round(self._dt_s / sim.timestep)))
        self._t0 = time.monotonic()
        self._yaw_prev = 0.0
        self.last_drive = DescendingDrive(0.8, 0.8)
        self.collisions = 0
        self._flying = False

    def connect(self) -> None:
        print(f"NeuroMechFly body ready (FlyGym dt={self._sim.timestep * 1e3:.2f} ms, {self._nsub} substeps/tick)")

    def takeoff(self) -> None:
        self._flying = True  # "in motion"; the animal is walking, not flying

    def land(self) -> None:
        self._flying = False
        halt = DescendingDrive(0.2, 0.2)
        self._step_physics(halt)

    def send(self, cmd: FlightCommand) -> None:
        if not self._flying:
            return
        self.last_drive = from_command(cmd)
        self._step_physics(self.last_drive)

    def _step_physics(self, drive: DescendingDrive) -> None:
        fg = self._fg
        dn = drive.as_array()
        for _ in range(self._nsub):
            obs = fg["HybridControllerObservation"].from_sim(self._sim, self._fly.name)
            action = self._controller.step(dn, obs)
            fg["apply_locomotion_action"](self._sim, self._fly.name, action)
            self._sim.step_with_profile()

    def telemetry(self) -> Telemetry:
        pos = self._sim.get_body_positions(self._fly.name)[self._thorax]  # mm
        quat = self._sim.get_body_rotations(self._fly.name)[self._thorax]  # wxyz
        yaw = _yaw_from_quat(quat)
        dt = self._dt_s if self._dt_s > 0 else 1.0
        yaw_rate = (yaw - self._yaw_prev) / dt
        # unwrap
        if yaw_rate > 180:
            yaw_rate -= 360
        elif yaw_rate < -180:
            yaw_rate += 360
        self._yaw_prev = yaw
        return Telemetry(
            t=time.monotonic() - self._t0,
            alt_m=float(pos[2] / 1000.0),
            yaw_deg=float(yaw),
            yaw_rate_dps=float(yaw_rate),
            x_m=float(pos[0] / 1000.0),
            y_m=float(pos[1] / 1000.0),
            flying=self._flying,
        )

    def close(self) -> None:
        self._flying = False


def _yaw_from_quat(q: np.ndarray) -> float:
    """Yaw in degrees from a (w, x, y, z) quaternion. FlyGym ground plane is XY."""
    w, x, y, z = [float(v) for v in q]
    return math.degrees(math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z)))
