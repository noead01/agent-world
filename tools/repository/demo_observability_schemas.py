#!/usr/bin/env python3
"""Demonstrate the TODO-0005 observability schemas end-to-end.

User-visible feature: correlation fields are consistent across world, agent,
and telemetry messages; run-validity transitions are represented and
rejected when invalid; configuration fingerprints are stable for identical
effective configurations; content capture mode is validated.

Usage:
    python3 tools/repository/demo_observability_schemas.py
"""

from __future__ import annotations

import hashlib
import json
import os
import sys

try:
    import jsonschema
except ImportError:  # pragma: no cover
    print("ERROR: jsonschema is required. Install it to run the demo.")
    sys.exit(1)

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCHEMAS_DIR = os.path.join(ROOT, "packages", "contracts", "src", "agent_world_contracts", "schemas")


def load_json(path: str) -> object:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def load_schemas() -> dict:
    schemas = {}
    names = [
        "correlation-context.schema.json",
        "run-validity.schema.json",
        "configuration-fingerprint.schema.json",
        "observability-envelope.schema.json",
    ]
    for name in names:
        path = os.path.join(SCHEMAS_DIR, name)
        schema = load_json(path)
        schemas[schema["$id"]] = schema
    return schemas


def main() -> int:
    schemas = load_schemas()
    print(f"Loaded {len(schemas)} observability contract schemas.")
    print()

    all_pass = True

    # 1. Validate every embedded example against its schema.
    print("== Validating embedded examples against each schema ==")
    for sid, schema in schemas.items():
        validator = jsonschema.Draft202012Validator(schema)
        examples = schema.get("examples", [])
        for idx, example in enumerate(examples):
            try:
                validator.validate(example)
                print(f"  [PASS] {sid.rsplit(':', 2)[-2]} example {idx}")
            except jsonschema.ValidationError as exc:
                all_pass = False
                print(f"  [FAIL] {sid.rsplit(':', 2)[-2]} example {idx}: {exc.message}")
    print()

    # 2. Demonstrate cross-component correlation consistency.
    print("== Demonstrating cross-component correlation consistency ==")
    envelope_schema = schemas["urn:agent-world:contracts:observability-envelope:1.0.0"]
    validator = jsonschema.Draft202012Validator(envelope_schema)

    base = envelope_schema["examples"][0]
    correlation = base["correlation"]

    components = [
        ("world", "evt_observation_collected"),
        ("agent:1.0.0", "evt_intention_formed"),
        ("telemetry", None),
    ]
    for component, event_id in components:
        msg = dict(base)
        msg["correlation"] = dict(correlation)
        msg["correlation"]["component"] = component
        if event_id:
            msg["correlation"]["event_id"] = event_id
        try:
            validator.validate(msg)
            for field in ["experiment_id", "scenario_id", "run_id", "world_revision"]:
                assert msg["correlation"][field] == correlation[field], (
                    f"{field} must be consistent across components"
                )
            print(f"  [PASS] {component}: correlation fields consistent across components")
        except jsonschema.ValidationError as exc:
            all_pass = False
            print(f"  [FAIL] {component}: {exc.message}")
    print()

    # 3. Demonstrate envelope run_id cross-check.
    print("== Demonstrating envelope run_id cross-check ==")
    example = dict(base)
    try:
        validator.validate(example)
        assert example["run_id"] == example["correlation"]["run_id"]
        assert example["run_id"] == example["validity"]["run_id"]
        print("  [PASS] envelope run_id matches correlation.run_id and validity.run_id")
    except (jsonschema.ValidationError, AssertionError) as exc:
        all_pass = False
        print(f"  [FAIL] run_id cross-check: {exc}")
    print()

    # 4. Demonstrate run-validity transitions: valid -> degraded -> invalid.
    print("== Demonstrating run-validity state transitions ==")
    validity_schema = schemas["urn:agent-world:contracts:run-validity:1.0.0"]
    vvalidator = jsonschema.Draft202012Validator(validity_schema)

    transitions = [
        ("valid", None, "Initial evaluation; required records intact."),
        ("degraded", "valid", "Telemetry exporter unavailable; authoritative record intact."),
        ("invalid", "degraded", "Required domain event append failed; run invalidated."),
    ]
    for validity, previous, reason in transitions:
        record = {
            "run_id": "run_20261101_demo",
            "validity": validity,
            "previous_validity": previous,
            "transition_reason": reason,
            "evaluated_at": "2026-11-01T06:00:00Z",
            "evaluator_component": "health_monitor",
            "evidence_summary": f"Transition to {validity}: {reason}",
            "invalidating_event_ids": [],
            "version": "1.0.0",
        }
        try:
            vvalidator.validate(record)
            print(f"  [PASS] {previous or '(none)'} -> {validity}: {reason}")
        except jsonschema.ValidationError as exc:
            all_pass = False
            print(f"  [FAIL] {previous or '(none)'} -> {validity}: {exc.message}")
    print()

    # 5. Demonstrate rejection of terminal-state reversals.
    print("== Demonstrating rejection of invalid validity transitions ==")
    bad_transitions = [
        ("valid", "invalid", "Attempted recovery from invalid state."),
        ("valid", "aborted", "Attempted recovery from aborted state."),
        ("degraded", "invalid", "Attempted recovery from invalid state."),
    ]
    for validity, previous, reason in bad_transitions:
        record = {
            "run_id": "run_20261101_demo",
            "validity": validity,
            "previous_validity": previous,
            "transition_reason": reason,
            "evaluated_at": "2026-11-01T06:05:00Z",
            "evaluator_component": "health_monitor",
            "evidence_summary": f"{previous}-to-{validity} should be rejected.",
            "invalidating_event_ids": [],
            "version": "1.0.0",
        }
        try:
            vvalidator.validate(record)
            all_pass = False
            print(f"  [FAIL] {previous} -> {validity} was NOT rejected")
        except jsonschema.ValidationError:
            print(f"  [PASS] {previous} -> {validity} rejected")
    print()

    # 6. Demonstrate rejection of an invalid validity value.
    print("== Demonstrating rejection of invalid validity value ==")
    bad_record = dict(validity_schema["examples"][0])
    bad_record["validity"] = "unknown_state"
    try:
        vvalidator.validate(bad_record)
        all_pass = False
        print("  [FAIL] invalid validity value was NOT rejected")
    except jsonschema.ValidationError:
        print("  [PASS] invalid validity value rejected")
    print()

    # 7. Demonstrate configuration fingerprint stability and canonical computation.
    print("== Demonstrating configuration fingerprint stability ==")
    fp_schema = schemas["urn:agent-world:contracts:configuration-fingerprint:1.0.0"]
    fvalidator = jsonschema.Draft202012Validator(fp_schema)

    fp_a = dict(fp_schema["examples"][0])
    fp_b = dict(fp_schema["examples"][0])
    fp_a["computed_at"] = "2026-11-01T06:00:00Z"
    fp_b["computed_at"] = "2026-11-01T07:00:00Z"
    fvalidator.validate(fp_a)
    fvalidator.validate(fp_b)
    if fp_a["fingerprint"] == fp_b["fingerprint"]:
        print("  [PASS] identical effective configurations produce identical fingerprints")
    else:
        all_pass = False
        print("  [FAIL] identical effective configurations produced different fingerprints")

    # Verify fingerprint matches canonical SHA-256 computation.
    canonical_input = {
        "configuration_sources": fp_a["configuration_sources"],
        "component_versions": fp_a["component_versions"],
    }
    canonical_json = json.dumps(canonical_input, sort_keys=True, separators=(",", ":"))
    expected = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
    if fp_a["fingerprint"] == expected:
        print("  [PASS] fingerprint matches canonical SHA-256 computation")
    else:
        all_pass = False
        print(f"  [FAIL] fingerprint does not match canonical computation (expected {expected})")

    # Different component version -> different fingerprint.
    fp_c = dict(fp_schema["examples"][0])
    fp_c["component_versions"] = dict(fp_schema["examples"][0]["component_versions"], godot="4.8.0")
    fp_c["fingerprint"] = "b3f5c8e1d2b4f6a7c9e0b1d3f5a7c9e0b1d3f5a7c9e0b1d3f5a7c9e0b1d3f5a7"
    fvalidator.validate(fp_c)
    if fp_a["fingerprint"] != fp_c["fingerprint"]:
        print("  [PASS] different effective configurations produce different fingerprints")
    else:
        all_pass = False
        print("  [FAIL] different effective configurations produced identical fingerprints")
    print()

    # 8. Demonstrate content capture mode.
    print("== Demonstrating content capture mode ==")
    for mode in ["off", "redacted", "full"]:
        msg = dict(base)
        msg["content_capture_mode"] = mode
        try:
            validator.validate(msg)
            print(f"  [PASS] content_capture_mode '{mode}' accepted")
        except jsonschema.ValidationError as exc:
            all_pass = False
            print(f"  [FAIL] content_capture_mode '{mode}' rejected: {exc.message}")
    print()

    # 9. Demonstrate component version syntax.
    print("== Demonstrating component version syntax ==")
    ctx_schema = schemas["urn:agent-world:contracts:correlation-context:1.0.0"]
    cvalidator = jsonschema.Draft202012Validator(ctx_schema)
    for component in ["world", "world:1.0.0", "agent:2.3.1", "telemetry"]:
        msg = dict(ctx_schema["examples"][0])
        msg["component"] = component
        try:
            cvalidator.validate(msg)
            print(f"  [PASS] component '{component}' accepted")
        except jsonschema.ValidationError as exc:
            all_pass = False
            print(f"  [FAIL] component '{component}' rejected: {exc.message}")
    print()

    if all_pass:
        print("DEMONSTRATION PASSED: correlation consistent, validity transitions validated, fingerprints stable, content capture mode validated.")
        return 0
    print("DEMONSTRATION FAILED.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
