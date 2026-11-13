#!/usr/bin/env python3
"""Acceptance tests for contract schemas: canonical protocol examples and compatibility fixtures."""

from __future__ import annotations

import glob
import json
import os
import unittest

try:
    import jsonschema
except ImportError:  # pragma: no cover
    jsonschema = None

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
SCHEMAS_DIR = os.path.join(ROOT, "packages", "contracts", "src", "agent_world_contracts", "schemas")


def load_json(path: str) -> object:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


class EveryCoreEntityHasSchemaAndExample(unittest.TestCase):
    """Acceptance criterion: every core entity has a schema with a representative example."""

    EXPECTED_ENTITIES = {
        "object-type",
        "scenario",
        "run",
        "agent",
        "observation",
        "intention",
        "action",
        "event",
        "fact",
        "belief",
        "evidence",
        "memory",
    }

    def test_all_core_entities_covered(self):
        self.assertIsNotNone(jsonschema, "jsonschema is required")
        schema_files = sorted(glob.glob(os.path.join(SCHEMAS_DIR, "*.schema.json")))
        covered = set()
        for path in schema_files:
            schema = load_json(path)
            sid = schema.get("$id", "")
            # Extract the entity name from the URN (last segment before :1.0.0)
            entity = sid.rsplit(":", 2)[-2] if ":" in sid else os.path.basename(path)
            covered.add(entity)
            examples = schema.get("examples", [])
            self.assertGreater(len(examples), 0, f"{sid} must have at least one representative example")
        missing = self.EXPECTED_ENTITIES - covered
        self.assertEqual(missing, set(), f"missing schemas for entities: {missing}")


class RepresentativeExamplesSerializeAndValidate(unittest.TestCase):
    """Acceptance criterion: representative examples serialize and validate successfully."""

    def test_examples_round_trip(self):
        self.assertIsNotNone(jsonschema, "jsonschema is required")
        schema_files = sorted(glob.glob(os.path.join(SCHEMAS_DIR, "*.schema.json")))
        for path in schema_files:
            schema = load_json(path)
            sid = schema.get("$id", os.path.basename(path))
            validator = jsonschema.Draft202012Validator(schema)
            examples = schema.get("examples", [])
            for idx, example in enumerate(examples):
                # Serialize to JSON and back to prove serializability
                serialized = json.dumps(example)
                deserialized = json.loads(serialized)
                with self.subTest(schema=sid, example=idx):
                    validator.validate(deserialized)


class MalformedVersionIsRejected(unittest.TestCase):
    """Acceptance criterion: schemas reject malformed (non-semver) version strings."""

    def test_malformed_version_rejected(self):
        self.assertIsNotNone(jsonschema, "jsonschema is required")
        schema_files = sorted(glob.glob(os.path.join(SCHEMAS_DIR, "*.schema.json")))
        for path in schema_files:
            schema = load_json(path)
            sid = schema.get("$id", os.path.basename(path))
            validator = jsonschema.Draft202012Validator(schema)
            example = schema.get("examples", [{}])[0]
            bad = dict(example)
            bad["version"] = "not-a-version"
            with self.subTest(schema=sid):
                with self.assertRaises(jsonschema.ValidationError):
                    validator.validate(bad)


class MalformedPayloadRejected(unittest.TestCase):
    """Acceptance criterion: schemas reject malformed payloads (unknown fields)."""

    def test_unknown_field_rejected(self):
        self.assertIsNotNone(jsonschema, "jsonschema is required")
        schema_files = sorted(glob.glob(os.path.join(SCHEMAS_DIR, "*.schema.json")))
        for path in schema_files:
            schema = load_json(path)
            sid = schema.get("$id", os.path.basename(path))
            validator = jsonschema.Draft202012Validator(schema)
            example = schema.get("examples", [{}])[0]
            bad = dict(example)
            bad["__unknown_field__"] = "should be rejected"
            with self.subTest(schema=sid):
                with self.assertRaises(jsonschema.ValidationError):
                    validator.validate(bad)


if __name__ == "__main__":
    unittest.main()
