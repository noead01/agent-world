#!/usr/bin/env python3
"""Unit tests for run_record.py"""
import tempfile
import os
import json

from agent_world_contracts.run_record import RunRecord


def _record(events, validity_history, status="completed"):
    return RunRecord(
        run_id="run_test",
        scenario_id="test_scenario",
        version="1.0.0",
        agent_id="agent_01",
        started_at="2026-11-10T00:00:00Z",
        ended_at="2026-11-10T00:01:00Z" if status == "completed" else None,
        simulation_time_s=60.0,
        status=status,
        random_seed=42,
        events=events,
        validity_history=validity_history,
    )


def _event(event_type_id, event_id):
    return {
        "id": event_id,
        "run_id": "run_test",
        "timestamp_s": 0.0,
        "version": "1.0.0",
        "event_type_id": event_type_id,
        "target_instance_id": "",
        "description": "",
        "severity": "info",
        "metadata": {},
    }


def _validity(current, previous):
    return {
        "run_id": "run_test",
        "validity": current,
        "previous_validity": previous,
        "transition_reason": "",
        "evaluated_at": "2026-11-10T00:00:00Z",
        "evaluator_component": "event_recorder",
        "evidence_summary": "",
        "invalidating_event_ids": [],
        "version": "1.0.0",
    }

def test_load_run_record():
    with tempfile.TemporaryDirectory() as tmpdir:
        run_dir = os.path.join(tmpdir, "run_test")
        os.makedirs(run_dir)
        
        # Write run.json
        run_meta = {
            "id": "run_test",
            "scenario_id": "test_scenario",
            "version": "1.0.0",
            "agent_id": "agent_01",
            "started_at": "2026-11-10T00:00:00Z",
            "ended_at": "2026-11-10T00:01:00Z",
            "simulation_time_s": 60.0,
            "status": "completed",
            "random_seed": 42,
        }
        with open(os.path.join(run_dir, "run.json"), "w") as f:
            json.dump(run_meta, f)
        
        # Write events.jsonl
        events = [
            {"id": "evt_1", "run_id": "run_test", "timestamp_s": 0.0, "version": "1.0.0", "event_type_id": "run_started", "target_instance_id": "", "description": "Run started", "severity": "info", "metadata": {}},
            {"id": "evt_2", "run_id": "run_test", "timestamp_s": 10.0, "version": "1.0.0", "event_type_id": "object_moved", "target_instance_id": "obj_1", "description": "Object moved", "severity": "notice", "metadata": {"displacement_m": 1.0}},
        ]
        with open(os.path.join(run_dir, "events.jsonl"), "w") as f:
            for evt in events:
                f.write(json.dumps(evt) + "\n")
        
        # Write validity.jsonl
        validity = [
            {"run_id": "run_test", "validity": "valid", "previous_validity": None, "transition_reason": "Run started", "evaluated_at": "2026-11-10T00:00:00Z", "evaluator_component": "event_recorder", "evidence_summary": "Run started", "invalidating_event_ids": [], "version": "1.0.0"},
            {"run_id": "run_test", "validity": "valid", "previous_validity": "valid", "transition_reason": "Run completed", "evaluated_at": "2026-11-10T00:01:00Z", "evaluator_component": "event_recorder", "evidence_summary": "Run completed", "invalidating_event_ids": [], "version": "1.0.0"},
        ]
        with open(os.path.join(run_dir, "validity.jsonl"), "w") as f:
            for v in validity:
                f.write(json.dumps(v) + "\n")
        
        record = RunRecord.load(run_dir)
        assert record.run_id == "run_test"
        assert record.scenario_id == "test_scenario"
        assert len(record.events) == 2
        assert len(record.validity_history) == 2

def test_validate_run_record():
    with tempfile.TemporaryDirectory() as tmpdir:
        run_dir = os.path.join(tmpdir, "run_test")
        os.makedirs(run_dir)
        
        # Write minimal valid run
        run_meta = {"id": "run_test", "scenario_id": "test", "version": "1.0.0", "agent_id": "a", "started_at": "2026-11-10T00:00:00Z", "ended_at": None, "simulation_time_s": 0, "status": "running", "random_seed": 42}
        with open(os.path.join(run_dir, "run.json"), "w") as f:
            json.dump(run_meta, f)
        with open(os.path.join(run_dir, "events.jsonl"), "w") as f:
            f.write('{"id": "evt_1", "run_id": "run_test", "timestamp_s": 0, "version": "1.0.0", "event_type_id": "run_started", "target_instance_id": "", "description": "", "severity": "info", "metadata": {}}\n')
        with open(os.path.join(run_dir, "validity.jsonl"), "w") as f:
            f.write('{"run_id": "run_test", "validity": "valid", "previous_validity": null, "transition_reason": "", "evaluated_at": "2026-11-10T00:00:00Z", "evaluator_component": "event_recorder", "evidence_summary": "", "invalidating_event_ids": [], "version": "1.0.0"}\n')
        
        record = RunRecord.load(run_dir)
        errors = record.validate()
        assert len(errors) == 0


def test_validate_requires_completed_run_boundaries():
    record = _record(
        events=[_event("agent_action_started", "evt_1")],
        validity_history=[_validity("valid", None)],
    )

    errors = record.validate()

    assert any("run_started" in error for error in errors)
    assert any("run_ended" in error for error in errors)


def test_validate_rejects_discontinuous_terminal_validity_history():
    record = _record(
        events=[_event("run_started", "evt_1"), _event("run_ended", "evt_2")],
        validity_history=[_validity("invalid", None), _validity("valid", "valid")],
    )

    errors = record.validate()

    assert any("previous_validity" in error for error in errors)
    assert any("terminal state" in error for error in errors)
    assert not record.is_valid()


def test_validate_requires_terminal_validity_for_completed_run():
    record = _record(
        events=[_event("run_started", "evt_1"), _event("run_ended", "evt_2")],
        validity_history=[_validity("valid", None)],
    )

    assert any("Terminal validity" in error for error in record.validate())
    assert not record.is_valid()


def test_validate_requires_invalidation_for_aborted_run():
    record = _record(
        events=[_event("run_started", "evt_1")],
        validity_history=[_validity("valid", None)],
        status="aborted",
    )

    assert any("Terminal validity" in error for error in record.validate())

if __name__ == "__main__":
    test_load_run_record()
    test_validate_run_record()
    print("All tests passed!")
