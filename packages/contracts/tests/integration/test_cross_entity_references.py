#!/usr/bin/env python3
"""Integration tests for contract schemas: cross-entity references and version transitions."""

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


def load_schemas() -> dict:
    schemas = {}
    for path in sorted(glob.glob(os.path.join(SCHEMAS_DIR, "*.schema.json"))):
        schema = load_json(path)
        schemas[schema["$id"]] = schema
    return schemas


class CrossEntityReferencesResolve(unittest.TestCase):
    """Identifiers referenced across entities must exist in their respective catalogs."""

    def test_scenario_references_valid_object_types(self):
        self.assertIsNotNone(jsonschema, "jsonschema is required")
        schemas = load_schemas()
        schema_files = sorted(glob.glob(os.path.join(SCHEMAS_DIR, "*.schema.json")))

        # Collect all object type ids from the standalone catalog
        catalog_path = os.path.join(SCHEMAS_DIR, "island-object-types.json")
        catalog = load_json(catalog_path)
        object_type_ids = {entry["id"] for entry in catalog["objectTypes"]}

        # Every scenario embedded example's object_type_ids should reference known types
        scenario_schema = schemas["urn:agent-world:contracts:scenario:1.0.0"]
        for example in scenario_schema.get("examples", []):
            for type_id in example.get("object_type_ids", []):
                with self.subTest(type_id=type_id):
                    self.assertIn(type_id, object_type_ids, f"unknown object type id: {type_id}")


class MalformedVersionsAreRejected(unittest.TestCase):
    """A payload declaring a malformed (non-semver) version must be rejected."""

    def test_malformed_version_rejected(self):
        self.assertIsNotNone(jsonschema, "jsonschema is required")
        schemas = load_schemas()

        for sid, schema in schemas.items():
            validator = jsonschema.Draft202012Validator(schema)
            example = schema.get("examples", [{}])[0]
            bad_version = dict(example)
            bad_version["version"] = "not-a-version"
            with self.subTest(schema=sid):
                with self.assertRaises(jsonschema.ValidationError):
                    validator.validate(bad_version)


class SchemaIdsDeclareVersion(unittest.TestCase):
    """Every schema $id must declare a semantic version in its URN."""

    def test_schema_ids_declare_version(self):
        self.assertIsNotNone(jsonschema, "jsonschema is required")
        schemas = load_schemas()
        for sid in schemas:
            with self.subTest(schema=sid):
                self.assertRegex(sid, r":\d+\.\d+\.\d+$", f"schema id {sid} does not declare a version")


class MissingRequiredFieldsAreRejected(unittest.TestCase):
    """Omitting a required field must be rejected."""

    def test_missing_required_rejected(self):
        self.assertIsNotNone(jsonschema, "jsonschema is required")
        schemas = load_schemas()

        for sid, schema in schemas.items():
            validator = jsonschema.Draft202012Validator(schema)
            example = schema.get("examples", [{}])[0]
            required = schema.get("required", [])
            if not required:
                continue
            # Remove the first required field
            field_to_remove = required[0]
            incomplete = {k: v for k, v in example.items() if k != field_to_remove}
            with self.subTest(schema=sid, field=field_to_remove):
                with self.assertRaises(jsonschema.ValidationError):
                    validator.validate(incomplete)


if __name__ == "__main__":
    unittest.main()
