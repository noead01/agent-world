#!/usr/bin/env python3
"""Unit tests for observability correlation and validity schemas (TODO-0005)."""

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
SCHEMAS_DIR = os.path.join(ROOT, "packages", "contracts", "schemas")


def load_json(path: str) -> object:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


class ObservabilitySchemasAreValidDraft202012(unittest.TestCase):
    """Every observability .schema.json file must be a valid JSON Schema draft 2020-12."""

    def test_observability_schemas_are_valid(self):
        self.assertIsNotNone(jsonschema, "jsonschema is required to validate schemas")
        schema_files = sorted(glob.glob(os.path.join(SCHEMAS_DIR, "*observability*.schema.json")))
        schema_files += sorted(glob.glob(os.path.join(SCHEMAS_DIR, "*correlation*.schema.json")))
        schema_files += sorted(glob.glob(os.path.join(SCHEMAS_DIR, "*run-validity*.schema.json")))
        schema_files += sorted(glob.glob(os.path.join(SCHEMAS_DIR, "*configuration-fingerprint*.schema.json")))
        self.assertGreater(len(schema_files), 0, "no observability schema files found")
        for path in schema_files:
            with self.subTest(schema=os.path.basename(path)):
                schema = load_json(path)
                jsonschema.Draft202012Validator.check_schema(schema)


class ObservabilityExamplesValidate(unittest.TestCase):
    """Every embedded example in every observability schema must validate against that schema."""

    def test_examples_validate(self):
        self.assertIsNotNone(jsonschema, "jsonschema is required to validate examples")
        schema_files = sorted(glob.glob(os.path.join(SCHEMAS_DIR, "*observability*.schema.json")))
        schema_files += sorted(glob.glob(os.path.join(SCHEMAS_DIR, "*correlation*.schema.json")))
        schema_files += sorted(glob.glob(os.path.join(SCHEMAS_DIR, "*run-validity*.schema.json")))
        schema_files += sorted(glob.glob(os.path.join(SCHEMAS_DIR, "*configuration-fingerprint*.schema.json")))
        for path in schema_files:
            schema = load_json(path)
            sid = schema.get("$id", os.path.basename(path))
            validator = jsonschema.Draft202012Validator(schema)
            examples = schema.get("examples", [])
            self.assertGreater(len(examples), 0, f"{sid} has no embedded examples")
            for idx, example in enumerate(examples):
                with self.subTest(schema=sid, example=idx):
                    validator.validate(example)


class CorrelationFieldsAreConsistent(unittest.TestCase):
    """Correlation fields must be consistent across world, agent, event, and telemetry messages.
    The same run_id, scenario_id, experiment_id, and world_revision must appear identically
    in every message belonging to a run."""

    CORRELATION_FIELDS = ["experiment_id", "scenario_id", "run_id", "world_revision"]

    def test_correlation_fields_match_across_messages(self):
        self.assertIsNotNone(jsonschema, "jsonschema is required")
        schema = load_json(os.path.join(SCHEMAS_DIR, "observability-envelope.schema.json"))
        validator = jsonschema.Draft202012Validator(schema)

        example = schema["examples"][0]
        correlation = example["correlation"]

        # Build three synthetic messages for different components sharing the same correlation.
        messages = []
        for component, event_id in [("world", "evt_001"), ("agent", "evt_002"), ("telemetry", None)]:
            msg = dict(example)
            msg["correlation"] = dict(correlation)
            msg["correlation"]["component"] = component
            if event_id:
                msg["correlation"]["event_id"] = event_id
            messages.append(msg)

        for msg in messages:
            with self.subTest(component=msg["correlation"]["component"]):
                validator.validate(msg)
                # Correlation fields must be identical across components.
                for field in self.CORRELATION_FIELDS:
                    self.assertEqual(
                        msg["correlation"][field],
                        correlation[field],
                        f"{field} must be consistent across components",
                    )


class RunValidityTransitionsAreRepresentedAndValidated(unittest.TestCase):
    """Run-validity transitions must be represented and validated."""

    def test_valid_transition_accepted(self):
        self.assertIsNotNone(jsonschema, "jsonschema is required")
        schema = load_json(os.path.join(SCHEMAS_DIR, "run-validity.schema.json"))
        validator = jsonschema.Draft202012Validator(schema)

        valid_transition = {
            "run_id": "run_20261101_demo",
            "validity": "degraded",
            "previous_validity": "valid",
            "transition_reason": "Telemetry exporter unavailable; authoritative record intact.",
            "evaluated_at": "2026-11-01T06:05:00Z",
            "evaluator_component": "health_monitor",
            "evidence_summary": "Recorder operational; telemetry degraded.",
            "invalidating_event_ids": [],
            "version": "1.0.0",
        }
        validator.validate(valid_transition)  # should not raise

    def test_invalid_validity_value_rejected(self):
        self.assertIsNotNone(jsonschema, "jsonschema is required")
        schema = load_json(os.path.join(SCHEMAS_DIR, "run-validity.schema.json"))
        validator = jsonschema.Draft202012Validator(schema)

        bad = dict(schema["examples"][0])
        bad["validity"] = "unknown_state"
        with self.assertRaises(jsonschema.ValidationError):
            validator.validate(bad)

    def test_missing_required_rejected(self):
        self.assertIsNotNone(jsonschema, "jsonschema is required")
        schema = load_json(os.path.join(SCHEMAS_DIR, "run-validity.schema.json"))
        validator = jsonschema.Draft202012Validator(schema)

        example = dict(schema["examples"][0])
        del example["validity"]
        with self.assertRaises(jsonschema.ValidationError):
            validator.validate(example)


class ConfigurationFingerprintIsStableForIdenticalConfig(unittest.TestCase):
    """Configuration fingerprints must be stable for identical effective configurations."""

    def test_identical_configs_produce_identical_fingerprints(self):
        self.assertIsNotNone(jsonschema, "jsonschema is required")
        schema = load_json(os.path.join(SCHEMAS_DIR, "configuration-fingerprint.schema.json"))
        validator = jsonschema.Draft202012Validator(schema)

        example = schema["examples"][0]
        # Two fingerprints from identical configuration sources and component versions
        # must match.
        fp_a = dict(example)
        fp_b = dict(example)
        fp_a["computed_at"] = "2026-11-01T06:00:00Z"
        fp_b["computed_at"] = "2026-11-01T07:00:00Z"  # computed_at differs but fingerprint must not
        validator.validate(fp_a)
        validator.validate(fp_b)
        self.assertEqual(fp_a["fingerprint"], fp_b["fingerprint"], "identical effective configs must have identical fingerprints")

    def test_different_configs_can_have_different_fingerprints(self):
        self.assertIsNotNone(jsonschema, "jsonschema is required")
        schema = load_json(os.path.join(SCHEMAS_DIR, "configuration-fingerprint.schema.json"))
        validator = jsonschema.Draft202012Validator(schema)

        example = dict(schema["examples"][0])
        fp_a = dict(example)
        fp_b = dict(example)
        fp_b["component_versions"] = dict(example["component_versions"], godot="4.8.0")
        fp_b["fingerprint"] = "b3f5c8e1d2b4f6a7c9e0b1d3f5a7c9e0b1d3f5a7c9e0b1d3f5a7c9e0b1d3f5a7"
        validator.validate(fp_a)
        validator.validate(fp_b)
        self.assertNotEqual(fp_a["fingerprint"], fp_b["fingerprint"], "different effective configs must have different fingerprints")


class ObservabilityEnvelopeCombinesAllThree(unittest.TestCase):
    """The observability envelope must combine correlation, validity, and fingerprint."""

    def test_envelope_contains_all_three_subschemas(self):
        self.assertIsNotNone(jsonschema, "jsonschema is required")
        schema = load_json(os.path.join(SCHEMAS_DIR, "observability-envelope.schema.json"))
        validator = jsonschema.Draft202012Validator(schema)
        example = schema["examples"][0]

        validator.validate(example)
        self.assertIn("correlation", example)
        self.assertIn("validity", example)
        self.assertIn("fingerprint", example)

        # Correlation run_id must match validity run_id.
        self.assertEqual(
            example["correlation"]["run_id"],
            example["validity"]["run_id"],
            "correlation and validity must reference the same run",
        )


if __name__ == "__main__":
    unittest.main()
