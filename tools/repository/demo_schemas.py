#!/usr/bin/env python3
"""Demonstrate the TODO-0004 contract schemas end-to-end.

User-visible feature: a complete experiment envelope containing every core
entity type validates against its versioned schema, while incompatible or
malformed payloads are rejected with clear errors.

Usage:
    python3 tools/repository/demo_schemas.py
"""

from __future__ import annotations

import json
import os
import sys

try:
    import jsonschema
except ImportError:  # pragma: no cover
    print("ERROR: jsonschema is required. Install it to run the demo.")
    sys.exit(1)

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCHEMAS_DIR = os.path.join(ROOT, "packages", "contracts", "schemas")


def load_json(path: str) -> object:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def load_schemas() -> dict:
    schemas = {}
    for path in sorted(os.path.join(SCHEMAS_DIR, f) for f in os.listdir(SCHEMAS_DIR) if f.endswith(".schema.json")):
        schema = load_json(path)
        schemas[schema["$id"]] = schema
    return schemas


def entity_name(sid: str) -> str:
    return sid.rsplit(":", 2)[-2]


# One valid instance of every core entity type, forming a complete experiment envelope.
ENVELOPE = {
    "urn:agent-world:contracts:scenario:1.0.0": {
        "id": "first_benchmark_room",
        "name": "First Benchmark Room",
        "version": "1.0.0",
        "description": "A single room with manipulable objects and immovable flora.",
        "object_type_ids": ["coconut_palm_tree", "coconut", "seashell"],
        "world_bounds_m": {"x_min": -5, "x_max": 5, "z_min": -3.2, "z_max": 3.2},
        "gravity_m_per_s2": 9.8,
        "time_of_day_start_hour": 6,
        "seed": 42,
        "spawn_configurations": [
            {
                "type_id": "coconut_palm_tree",
                "instance_id": "palm_01",
                "position": {"x": 0, "y": 0, "z": -2},
                "orientation_degrees": {"x": 0, "y": 0, "z": 0},
                "size_scale": 1.0,
            }
        ],
    },
    "urn:agent-world:contracts:run:1.0.0": {
        "id": "run_20261101_demo",
        "scenario_id": "first_benchmark_room",
        "version": "1.0.0",
        "agent_id": "wanderer_01",
        "started_at": "2026-11-01T06:00:00Z",
        "ended_at": None,
        "simulation_time_s": 0,
        "status": "running",
        "random_seed": 42,
    },
    "urn:agent-world:contracts:agent:1.0.0": {
        "id": "wanderer_01",
        "version": "1.0.0",
        "agent_type_id": "exploration_agent",
        "name": "Wanderer",
        "drive_weights": {"curiosity": 0.7, "stability": 0.3},
        "position": {"x": 0, "y": 0.56, "z": 1.5},
        "heading_radians": 0,
        "status": "observing the world",
        "current_goal": "Taking in the surroundings",
        "world_time_s": 0,
    },
    "urn:agent-world:contracts:observation:1.0.0": {
        "id": "obs_001",
        "run_id": "run_20261101_demo",
        "agent_id": "wanderer_01",
        "timestamp_s": 12.5,
        "version": "1.0.0",
        "observation_type_id": "visual_object",
        "target_instance_id": "coconut_01",
        "target_type_id": "coconut",
        "properties": {"color": "#e7be69", "radius_m": 0.15, "distance_m": 2.3},
        "confidence": 0.95,
    },
    "urn:agent-world:contracts:intention:1.0.0": {
        "id": "int_001",
        "run_id": "run_20261101_demo",
        "agent_id": "wanderer_01",
        "timestamp_s": 15.0,
        "version": "1.0.0",
        "intention_type_id": "touch",
        "target_instance_id": "coconut_01",
        "target_type_id": "coconut",
        "thought": "I want to learn whether the coconut moves when touched.",
        "goal": "Test the coconut",
        "status": "formed",
    },
    "urn:agent-world:contracts:action:1.0.0": {
        "id": "act_001",
        "run_id": "run_20261101_demo",
        "agent_id": "wanderer_01",
        "timestamp_s": 20.0,
        "version": "1.0.0",
        "action_type_id": "touch",
        "target_instance_id": "coconut_01",
        "parameters": {"approach_distance_m": 0.5},
        "intention_id": "int_001",
        "result": "success",
        "result_description": "The coconut began to move after being touched.",
    },
    "urn:agent-world:contracts:event:1.0.0": {
        "id": "evt_001",
        "run_id": "run_20261101_demo",
        "agent_id": "wanderer_01",
        "timestamp_s": 20.5,
        "version": "1.0.0",
        "event_type_id": "object_moved",
        "target_instance_id": "coconut_01",
        "description": "The coconut began to move after being touched.",
        "severity": "notice",
        "metadata": {"displacement_m": 0.4},
    },
    "urn:agent-world:contracts:fact:1.0.0": {
        "id": "fact_coconut_moves",
        "version": "1.0.0",
        "scenario_id": "first_benchmark_room",
        "statement": "Coconuts move when touched.",
        "prerequisite_fact_ids": [],
        "qualifying_evidence": [
            {
                "observation_type_id": "tactile_contact",
                "target_type_id": "coconut",
                "required_properties": ["moved"],
            }
        ],
        "verification_criteria": "Agent observes a coconut changing position after a touch action.",
        "run_id": "run_20261101_demo",
        "discovery_stage": "hypothesized",
        "verified_at_s": None,
    },
    "urn:agent-world:contracts:belief:1.0.0": {
        "id": "belief_001",
        "run_id": "run_20261101_demo",
        "agent_id": "wanderer_01",
        "fact_id": "fact_coconut_moves",
        "timestamp_s": 22.0,
        "version": "1.0.0",
        "content": "The coconut moves when I touch it.",
        "confidence": 0.8,
        "is_correct": True,
        "evidence_ids": ["ev_001"],
    },
    "urn:agent-world:contracts:evidence:1.0.0": {
        "id": "ev_001",
        "run_id": "run_20261101_demo",
        "agent_id": "wanderer_01",
        "timestamp_s": 21.0,
        "version": "1.0.0",
        "evidence_type_id": "direct_observation",
        "observation_ids": ["obs_002"],
        "supports_fact_id": "fact_coconut_moves",
        "description": "Observed the coconut change position after being touched.",
        "strength": 0.9,
        "supports_belief_ids": ["belief_001"],
    },
    "urn:agent-world:contracts:memory:1.0.0": {
        "id": "mem_001",
        "run_id": "run_20261101_demo",
        "agent_id": "wanderer_01",
        "timestamp_s": 22.0,
        "version": "1.0.0",
        "memory_type_id": "belief_memory",
        "source_record_id": "belief_001",
        "source_record_type": "belief",
        "content_summary": "Believes coconuts move when touched, confidence 0.8.",
        "importance": 0.7,
        "last_accessed_s": 30.0,
        "retention_priority": 0.6,
    },
}


def main() -> int:
    schemas = load_schemas()
    print(f"Loaded {len(schemas)} versioned contract schemas.")
    print()

    all_pass = True

    # 1. Validate the complete experiment envelope.
    print("== Validating complete experiment envelope (every core entity) ==")
    for sid, schema in schemas.items():
        name = entity_name(sid)
        instance = ENVELOPE.get(sid)
        if instance is None:
            print(f"  [SKIP] {name}: no envelope instance provided")
            continue
        validator = jsonschema.Draft202012Validator(schema)
        try:
            validator.validate(instance)
            print(f"  [PASS] {name} ({sid})")
        except jsonschema.ValidationError as exc:
            all_pass = False
            print(f"  [FAIL] {name} ({sid}): {exc.message}")

    print()

    # 2. Demonstrate rejection of an incompatible/malformed version.
    print("== Demonstrating rejection of incompatible versions ==")
    for sid, schema in schemas.items():
        name = entity_name(sid)
        validator = jsonschema.Draft202012Validator(schema)
        example = dict(schema.get("examples", [{}])[0])
        bad_version = dict(example)
        bad_version["version"] = "not-a-version"
        try:
            validator.validate(bad_version)
            all_pass = False
            print(f"  [FAIL] {name}: malformed version was NOT rejected")
        except jsonschema.ValidationError:
            print(f"  [PASS] {name}: malformed version rejected")

    print()

    # 3. Demonstrate rejection of unknown fields.
    print("== Demonstrating rejection of unknown (malformed) fields ==")
    for sid, schema in schemas.items():
        name = entity_name(sid)
        validator = jsonschema.Draft202012Validator(schema)
        example = dict(schema.get("examples", [{}])[0])
        bad_field = dict(example)
        bad_field["__unknown_field__"] = "should be rejected"
        try:
            validator.validate(bad_field)
            all_pass = False
            print(f"  [FAIL] {name}: unknown field was NOT rejected")
        except jsonschema.ValidationError:
            print(f"  [PASS] {name}: unknown field rejected")

    print()

    if all_pass:
        print("DEMONSTRATION PASSED: every entity validates, and incompatible/malformed payloads are rejected.")
        return 0
    print("DEMONSTRATION FAILED.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
