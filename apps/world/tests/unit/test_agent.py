#!/usr/bin/env python3
"""Unit tests for the embodied agent (TODO-0008).

Tests validate the Agent and MockController class structure and Room
integration without requiring the Godot engine to be running.
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


class AgentExists(unittest.TestCase):
    """The Agent script must exist."""

    def test_agent_gd_exists(self):
        path = os.path.join(SRC_DIR, "agent.gd")
        self.assertTrue(os.path.isfile(path), "agent.gd must exist")


class AgentClassDeclared(unittest.TestCase):
    """agent.gd must declare class_name Agent extending CharacterBody3D."""

    def test_has_class_name(self):
        content = load_text(os.path.join(SRC_DIR, "agent.gd"))
        self.assertIn("class_name Agent", content)

    def test_extends_character_body3d(self):
        content = load_text(os.path.join(SRC_DIR, "agent.gd"))
        self.assertIn("extends CharacterBody3D", content)


class AgentProperties(unittest.TestCase):
    """Agent must define all required properties."""

    def test_has_required_properties(self):
        content = load_text(os.path.join(SRC_DIR, "agent.gd"))
        required_props = [
            "agent_id",
            "agent_type_id",
            "agent_name",
            "move_speed",
            "turn_speed",
            "reach_distance",
            "spawn_position",
            "heading_radians",
            "status",
            "current_goal",
            "world_time_s",
        ]
        for prop in required_props:
            self.assertIn(prop, content, f"agent.gd must define {prop}")


class AgentMethods(unittest.TestCase):
    """Agent must define all required methods."""

    def test_has_required_methods(self):
        content = load_text(os.path.join(SRC_DIR, "agent.gd"))
        required_methods = [
            "func navigate_toward",
            "func turn_toward",
            "func can_reach",
            "func execute_action",
            "func interrupt_current_action",
            "func get_agent_dict",
        ]
        for method in required_methods:
            self.assertIn(method, content, f"agent.gd must define {method}")


class AgentSignals(unittest.TestCase):
    """Agent must declare all required signals."""

    def test_has_required_signals(self):
        content = load_text(os.path.join(SRC_DIR, "agent.gd"))
        required_signals = [
            "signal action_started",
            "signal action_completed",
            "signal action_failed",
            "signal action_interrupted",
        ]
        for signal in required_signals:
            self.assertIn(signal, content, f"agent.gd must declare {signal}")


class MockControllerExists(unittest.TestCase):
    """The MockController script must exist."""

    def test_mock_controller_gd_exists(self):
        path = os.path.join(SRC_DIR, "mock_controller.gd")
        self.assertTrue(os.path.isfile(path), "mock_controller.gd must exist")


class MockControllerClassDeclared(unittest.TestCase):
    """mock_controller.gd must declare class_name MockController."""

    def test_has_class_name(self):
        content = load_text(os.path.join(SRC_DIR, "mock_controller.gd"))
        self.assertIn("class_name MockController", content)


class MockControllerMethods(unittest.TestCase):
    """MockController must define required methods."""

    def test_has_required_methods(self):
        content = load_text(os.path.join(SRC_DIR, "mock_controller.gd"))
        self.assertIn("func _physics_process", content)
        self.assertIn("func set_targets", content)


class MockControllerSignals(unittest.TestCase):
    """MockController must declare required signals."""

    def test_has_required_signals(self):
        content = load_text(os.path.join(SRC_DIR, "mock_controller.gd"))
        self.assertIn("signal controller_action_issued", content)


class RoomIntegratesAgent(unittest.TestCase):
    """Room must create and use Agent, WebSocketClient, and ProtocolHandler."""

    def test_room_references_agent_gd(self):
        content = load_text(os.path.join(SRC_DIR, "room.gd"))
        self.assertIn("agent.gd", content)

    def test_room_references_websocket_client(self):
        content = load_text(os.path.join(SRC_DIR, "room.gd"))
        self.assertIn("WebSocketClient", content)

    def test_room_references_protocol_handler(self):
        content = load_text(os.path.join(SRC_DIR, "room.gd"))
        self.assertIn("ProtocolHandler", content)

    def test_room_spawns_agent(self):
        content = load_text(os.path.join(SRC_DIR, "room.gd"))
        self.assertIn("_spawn_agent", content)

    def test_room_sets_agent_room(self):
        content = load_text(os.path.join(SRC_DIR, "room.gd"))
        self.assertIn("set_room", content)

    def test_room_connects_protocol_signals(self):
        content = load_text(os.path.join(SRC_DIR, "room.gd"))
        self.assertIn("action_received.connect", content)
        self.assertIn("stale_request_rejected.connect", content)

    def test_room_sends_world_state(self):
        content = load_text(os.path.join(SRC_DIR, "room.gd"))
        self.assertIn("tick_world_state", content)

    def test_room_handles_action_received(self):
        content = load_text(os.path.join(SRC_DIR, "room.gd"))
        self.assertIn("_on_action_received", content)
        self.assertIn("execute_action", content)


class AgentSchemaCompatibility(unittest.TestCase):
    """Agent.get_agent_dict must produce output matching agent.schema.json."""

    def test_agent_dict_has_schema_fields(self):
        content = load_text(os.path.join(SRC_DIR, "agent.gd"))
        required_fields = [
            '"id"',
            '"version"',
            '"agent_type_id"',
            '"name"',
            '"position"',
            '"heading_radians"',
            '"status"',
            '"current_goal"',
            '"world_time_s"',
        ]
        for field in required_fields:
            self.assertIn(field, content, f"agent.gd get_agent_dict must include {field}")


if __name__ == "__main__":
    unittest.main()
