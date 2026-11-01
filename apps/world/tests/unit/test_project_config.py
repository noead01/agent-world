#!/usr/bin/env python3
"""Unit tests for the Godot 4 project configuration (TODO-0002).

These tests validate project.godot without requiring the Godot engine to be
installed, providing repeatable verification of the project setup.
"""

from __future__ import annotations

import configparser
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
WORLD_DIR = os.path.join(ROOT, "apps", "world")
PROJECT_GODOT = os.path.join(WORLD_DIR, "project.godot")
MAIN_SCENE = os.path.join(WORLD_DIR, "src", "main.tscn")
MAIN_GD = os.path.join(WORLD_DIR, "src", "main.gd")


def load_project() -> configparser.ConfigParser:
    parser = configparser.ConfigParser()
    parser.read(PROJECT_GODOT)
    return parser


class ProjectGodotExistsAndParses(unittest.TestCase):
    def test_project_godot_exists(self):
        self.assertTrue(os.path.isfile(PROJECT_GODOT), "project.godot must exist")

    def test_project_godot_parses(self):
        parser = load_project()
        self.assertGreater(len(parser.sections()), 0, "project.godot must define sections")


class MainSceneConfigured(unittest.TestCase):
    def test_main_scene_defined(self):
        parser = load_project()
        self.assertIn("application", parser)
        self.assertTrue(parser.has_option("application", "run/main_scene"))
        main_scene = parser.get("application", "run/main_scene").strip('"')
        resolved = os.path.normpath(os.path.join(WORLD_DIR, main_scene.replace("res://", "")))
        self.assertTrue(os.path.isfile(resolved), "main_scene '%s' must exist" % main_scene)

    def test_main_scene_references_existing_script(self):
        with open(MAIN_SCENE, encoding="utf-8") as fh:
            content = fh.read()
        self.assertIn("res://src/room.gd", content)
        self.assertTrue(os.path.isfile(os.path.join(WORLD_DIR, "src", "room.gd")), "room.gd referenced by main.tscn must exist")


class JoltPhysicsSelected(unittest.TestCase):
    def test_physics_engine_is_jolt(self):
        parser = load_project()
        self.assertIn("physics", parser)
        self.assertTrue(parser.has_option("physics", "3d/physics_engine"))
        engine = parser.get("physics", "3d/physics_engine")
        self.assertIn("Jolt", engine, "3D physics engine must be Jolt, got: %s" % engine)


class FixedTimestepExplicit(unittest.TestCase):
    def test_fixed_timestep_defined(self):
        parser = load_project()
        self.assertTrue(parser.has_option("physics", "common/physics_fps"))
        fps = parser.getint("physics", "common/physics_fps")
        self.assertGreater(fps, 0, "fixed timestep physics_fps must be positive")


if __name__ == "__main__":
    unittest.main()
