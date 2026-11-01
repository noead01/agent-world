#!/usr/bin/env python3
"""Unit tests for simulation time (TODO-0007).

Tests validate the SimulationTime class structure and Room integration
without requiring the Godot engine to be running.
"""

from __future__ import annotations

import os
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
WORLD_DIR = ROOT / "apps" / "world"
SRC_DIR = WORLD_DIR / "src"


def load_text(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


class SimulationTimeExists(unittest.TestCase):
    """The SimulationTime script must exist."""

    def test_simulation_time_gd_exists(self):
        path = os.path.join(SRC_DIR, "simulation_time.gd")
        self.assertTrue(os.path.isfile(path), "simulation_time.gd must exist")


class SimulationTimeClassDeclared(unittest.TestCase):
    """simulation_time.gd must declare class_name SimulationTime."""

    def test_has_class_name(self):
        content = load_text(os.path.join(SRC_DIR, "simulation_time.gd"))
        self.assertIn("class_name SimulationTime", content)


class SimulationTimeProperties(unittest.TestCase):
    """SimulationTime must define all required properties."""

    def test_has_required_properties(self):
        content = load_text(os.path.join(SRC_DIR, "simulation_time.gd"))
        required_props = [
            "simulation_time",
            "simulation_tick",
            "time_scale",
            "is_paused",
            "time_of_day_start_hour",
            "day_cycle_duration_s",
        ]
        for prop in required_props:
            self.assertIn(prop, content, f"simulation_time.gd must define {prop}")


class SimulationTimeMethods(unittest.TestCase):
    """SimulationTime must define all required methods."""

    def test_has_required_methods(self):
        content = load_text(os.path.join(SRC_DIR, "simulation_time.gd"))
        required_methods = [
            "func tick",
            "func pause",
            "func resume",
            "func reset",
            "func set_time_scale",
            "func get_time_of_day",
        ]
        for method in required_methods:
            self.assertIn(method, content, f"simulation_time.gd must define {method}")


class SimulationTimeSignals(unittest.TestCase):
    """SimulationTime must declare all required signals."""

    def test_has_required_signals(self):
        content = load_text(os.path.join(SRC_DIR, "simulation_time.gd"))
        required_signals = [
            "signal simulation_ticked",
            "signal simulation_paused",
            "signal simulation_resumed",
            "signal simulation_reset",
            "signal time_of_day_changed",
        ]
        for signal in required_signals:
            self.assertIn(signal, content, f"simulation_time.gd must declare {signal}")


class RoomIntegratesSimulationTime(unittest.TestCase):
    """Room must create and use SimulationTime."""

    def test_room_references_simulation_time(self):
        content = load_text(os.path.join(SRC_DIR, "room.gd"))
        self.assertIn("simulation_time.gd", content)

    def test_room_creates_sim_time_instance(self):
        content = load_text(os.path.join(SRC_DIR, "room.gd"))
        self.assertIn(".new()", content)

    def test_room_calls_tick(self):
        content = load_text(os.path.join(SRC_DIR, "room.gd"))
        self.assertIn("_sim_time.tick", content)

    def test_room_respects_pause(self):
        content = load_text(os.path.join(SRC_DIR, "room.gd"))
        self.assertIn("is_paused", content)


class RoomHasTimeScaleDemo(unittest.TestCase):
    """Room must demonstrate time scaling in its demo sequence."""

    def test_room_has_time_scale(self):
        content = load_text(os.path.join(SRC_DIR, "room.gd"))
        self.assertIn("set_time_scale", content)


class RoomHasResetDemo(unittest.TestCase):
    """Room must demonstrate reset in its demo sequence."""

    def test_room_has_reset(self):
        content = load_text(os.path.join(SRC_DIR, "room.gd"))
        self.assertIn(".reset()", content)


if __name__ == "__main__":
    unittest.main()
