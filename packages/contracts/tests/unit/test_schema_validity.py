#!/usr/bin/env python3
"""Unit tests for contract schemas: schema validity and example validation."""

from __future__ import annotations

import glob
import json
import os
import unittest

try:
    import jsonschema
except ImportError:  # pragma: no cover - jsonschema is a dev dependency
    jsonschema = None

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
SCHEMAS_DIR = os.path.join(ROOT, "packages", "contracts", "src", "agent_world_contracts", "schemas")


def load_json(path: str) -> object:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


class SchemasAreValidDraft202012(unittest.TestCase):
    """Every .schema.json file must be a valid JSON Schema draft 2020-12."""

    def test_all_schemas_are_valid(self):
        self.assertIsNotNone(jsonschema, "jsonschema is required to validate schemas")
        schema_files = sorted(glob.glob(os.path.join(SCHEMAS_DIR, "*.schema.json")))
        self.assertGreater(len(schema_files), 0, "no schema files found")
        for path in schema_files:
            with self.subTest(schema=os.path.basename(path)):
                schema = load_json(path)
                jsonschema.Draft202012Validator.check_schema(schema)


class EmbeddedExamplesValidate(unittest.TestCase):
    """Every embedded example in every schema must validate against that schema."""

    def test_examples_validate(self):
        self.assertIsNotNone(jsonschema, "jsonschema is required to validate examples")
        schema_files = sorted(glob.glob(os.path.join(SCHEMAS_DIR, "*.schema.json")))
        for path in schema_files:
            schema = load_json(path)
            sid = schema.get("$id", os.path.basename(path))
            validator = jsonschema.Draft202012Validator(schema)
            examples = schema.get("examples", [])
            self.assertGreater(len(examples), 0, f"{sid} has no embedded examples")
            for idx, example in enumerate(examples):
                with self.subTest(schema=sid, example=idx):
                    validator.validate(example)


class StableIdentifierFormat(unittest.TestCase):
    """Every core entity schema that declares an id field must use the stable identifier pattern."""

    ID_PATTERN = r"^[a-z][a-z0-9_-]*$"

    def test_id_fields_use_stable_pattern(self):
        self.assertIsNotNone(jsonschema, "jsonschema is required")
        schema_files = sorted(glob.glob(os.path.join(SCHEMAS_DIR, "*.schema.json")))
        for path in schema_files:
            schema = load_json(path)
            props = schema.get("properties", {})
            if "id" not in props:
                continue  # context blocks and state machines need not declare an entity id
            with self.subTest(schema=schema.get("$id", path)):
                self.assertIn("id", props, f"{schema.get('$id')} missing id property")
                id_prop = props["id"]
                self.assertEqual(id_prop.get("type"), "string")
                self.assertEqual(id_prop.get("pattern"), self.ID_PATTERN)


class VersionDeclaration(unittest.TestCase):
    """Every core entity schema that declares a version field must use semantic versioning pattern."""

    def test_version_fields_declared(self):
        self.assertIsNotNone(jsonschema, "jsonschema is required")
        schema_files = sorted(glob.glob(os.path.join(SCHEMAS_DIR, "*.schema.json")))
        for path in schema_files:
            schema = load_json(path)
            props = schema.get("properties", {})
            if "version" not in props:
                continue  # context blocks and state machines need not declare a schema version
            with self.subTest(schema=schema.get("$id", path)):
                self.assertIn("version", props, f"{schema.get('$id')} missing version property")
                version_prop = props["version"]
                self.assertEqual(version_prop.get("type"), "string")
                self.assertIsNotNone(version_prop.get("pattern"))


class MalformedPayloadsAreRejected(unittest.TestCase):
    """Schemas with additionalProperties: false must reject unknown fields."""

    def test_additional_properties_false(self):
        self.assertIsNotNone(jsonschema, "jsonschema is required")
        schema_files = sorted(glob.glob(os.path.join(SCHEMAS_DIR, "*.schema.json")))
        for path in schema_files:
            schema = load_json(path)
            with self.subTest(schema=schema.get("$id", path)):
                self.assertEqual(schema.get("additionalProperties"), False)


if __name__ == "__main__":
    unittest.main()
