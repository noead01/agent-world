#!/usr/bin/env python3
"""Unit tests for the Godot 4 physical room (TODO-0006).

Tests validate the room scene structure, object metadata, and physics
configuration without requiring the Godot engine to be running.
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


class RoomSceneExists(unittest.TestCase):
    """The room scene must exist and reference the room script."""

    def test_room_tscn_exists(self):
        path = os.path.join(SRC_DIR, "room.tscn")
        self.assertTrue(os.path.isfile(path), "room.tscn must exist")

    def test_room_gd_exists(self):
        path = os.path.join(SRC_DIR, "room.gd")
        self.assertTrue(os.path.isfile(path), "room.gd must exist")

    def test_rigid_object_gd_exists(self):
        path = os.path.join(SRC_DIR, "rigid_object.gd")
        self.assertTrue(os.path.isfile(path), "rigid_object.gd must exist")


class RoomSceneReferencesScripts(unittest.TestCase):
    """room.tscn must reference room.gd and rigid_object.gd."""

    def test_room_tscn_references_room_gd(self):
        content = load_text(os.path.join(SRC_DIR, "room.tscn"))
        self.assertIn('res://src/room.gd', content)

    def test_room_tscn_references_rigid_object_gd(self):
        content = load_text(os.path.join(SRC_DIR, "room.tscn"))
        room_gd = load_text(os.path.join(SRC_DIR, "room.gd"))
        self.assertIn('res://src/rigid_object.gd', room_gd)


class RigidObjectMetadata(unittest.TestCase):
    """rigid_object.gd must define metadata fields for all required properties."""

    def test_rigid_object_has_metadata_fields(self):
        content = load_text(os.path.join(SRC_DIR, "rigid_object.gd"))
        required_fields = [
            "instance_id", "type_id", "object_name", "kind",
            "mass_kg", "brittleness", "throwable", "stackable",
            "friction", "bounciness", "density_kg_per_m3",
            "dimensions_m",
        ]
        for field in required_fields:
            self.assertIn(field, content, f"rigid_object.gd must define {field}")

    def test_rigid_object_has_get_metadata(self):
        content = load_text(os.path.join(SRC_DIR, "rigid_object.gd"))
        self.assertIn("def get_metadata", content)

    def test_rigid_object_has_configure(self):
        content = load_text(os.path.join(SRC_DIR, "rigid_object.gd"))
        self.assertIn("func configure", content)

    def test_rigid_object_has_get_metadata(self):
        content = load_text(os.path.join(SRC_DIR, "rigid_object.gd"))
        self.assertIn("func get_metadata", content)


class RoomHasFourObjects(unittest.TestCase):
    """The room must spawn exactly four objects with stable IDs."""

    def test_room_spawns_four_objects(self):
        content = load_text(os.path.join(SRC_DIR, "room.gd"))
        # Count instance_id definitions in the spawn definitions
        instance_ids = re.findall(r'"instance_id":\s*"([^"]+)"', content)
        self.assertEqual(len(instance_ids), 4, "room must spawn exactly 4 objects")
        # All instance IDs must be unique
        self.assertEqual(len(set(instance_ids)), 4, "all instance IDs must be unique")


class ObjectsHavePhysicalProperties(unittest.TestCase):
    """Each object must have mass, friction, bounciness, and dimensions."""

    def test_objects_have_physical_properties(self):
        content = load_text(os.path.join(SRC_DIR, "room.gd"))
        required_props = [
            "mass_kg", "friction", "bounciness",
            "density_kg_per_m3", "dimensions_m",
        ]
        for prop in required_props:
            self.assertIn(prop, content, f"room.gd must define {prop} for objects")


class RoomHasStaticBoundaries(unittest.TestCase):
    """The room must have static boundary walls (StaticBody3D)."""

    def test_room_has_static_bodies(self):
        content = load_text(os.path.join(SRC_DIR, "room.gd"))
        self.assertIn("StaticBody3D", content)
        self.assertIn("CollisionShape3D", content)
        self.assertIn("BoxShape3D", content)

    def test_room_has_six_walls(self):
        content = load_text(os.path.join(SRC_DIR, "room.gd"))
        # Should create floor, ceiling, and 4 walls = 6 boundaries
        wall_names = ["floor", "ceiling", "wall_west", "wall_east", "wall_north", "wall_south"]
        for name in wall_names:
            self.assertIn(name, content, f"room must have {name} boundary")


class JoltPhysicsConfigured(unittest.TestCase):
    """The room must configure Jolt physics engine."""

    def test_jolt_physics_configured(self):
        content = load_text(os.path.join(SRC_DIR, "room.gd"))
        self.assertIn("JoltPhysics", content)
        self.assertIn("physics_fps", content)
        self.assertIn("default_gravity", content)


class RoomHasEventRecorder(unittest.TestCase):
    """The room must integrate EventRecorder for domain event capture."""

    def test_room_has_event_recorder(self):
        content = load_text(os.path.join(SRC_DIR, "room.gd"))
        assert "EventRecorder" in content
        assert "event_recorder" in content.lower()
        assert "_event_recorder" in content or "event_recorder" in content
        assert "start_run" in content
        assert "append_event" in content
        assert "end_run" in content


if __name__ == "__main__":
    unittest.main()
