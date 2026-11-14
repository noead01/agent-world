#!/usr/bin/env python3
"""Unit tests for event_recorder.gd source validation."""
import os

WORLD_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC_FILE = os.path.join(WORLD_DIR, "src", "event_recorder.gd")

def test_file_exists():
    assert os.path.exists(SRC_FILE), "event_recorder.gd must exist"

def test_class_name():
    with open(SRC_FILE) as f:
        content = f.read()
    assert "class_name EventRecorder" in content

def test_extends_node():
    with open(SRC_FILE) as f:
        content = f.read()
    assert content.strip().startswith("extends Node")

def test_signals():
    with open(SRC_FILE) as f:
        content = f.read()
    required = ["run_started", "event_appended", "run_ended", "run_failed", "validity_changed"]
    for sig in required:
        assert f"signal {sig}" in content, f"Missing signal: {sig}"

def test_methods():
    with open(SRC_FILE) as f:
        content = f.read()
    required = ["start_run", "append_event", "end_run", "fail_run", "get_run_status", "get_events_path"]
    for method in required:
        assert f"func {method}" in content, f"Missing method: {method}"

def test_schema_validation():
    with open(SRC_FILE) as f:
        content = f.read()
    assert "validate" in content.lower()
    assert "schema" in content.lower()

def test_append_only_writing():
    with open(SRC_FILE) as f:
        content = f.read()
    assert "append" in content.lower() or "Append" in content

def test_aborted_run_preserves_elapsed_simulation_time():
    # _fail_run persists _run_metadata, so the clock must be advanced while
    # events are appended; otherwise an aborted run reports simulation_time_s 0.
    with open(SRC_FILE) as f:
        content = f.read()
    assert "func _update_simulation_clock" in content
    assert "_update_simulation_clock(event_copy.get(\"timestamp_s\"))" in content
    assert "simulation_time_s" in content

def test_event_type_id_is_required():
    with open(SRC_FILE) as f:
        content = f.read()
    assert '"event_type_id"' in content
    assert 'event["event_type_id"] == ""' in content

def test_end_run_preserves_tracked_clock_by_default():
    # The null default must keep the clock advanced by _update_simulation_clock
    # instead of overwriting it with zero.
    with open(SRC_FILE) as f:
        content = f.read()
    assert "func end_run(simulation_time_s = null) -> bool:" in content
    assert "if simulation_time_s != null:" in content
    assert 'simulation_time_s"] = float(simulation_time_s)' in content

if __name__ == "__main__":
    import sys
    tests = [
        test_file_exists,
        test_class_name,
        test_extends_node,
        test_signals,
        test_methods,
        test_schema_validation,
        test_append_only_writing,
        test_aborted_run_preserves_elapsed_simulation_time,
        test_event_type_id_is_required,
        test_end_run_preserves_tracked_clock_by_default,
    ]
    failed = 0
    for test in tests:
        try:
            test()
            print(f"PASS: {test.__name__}")
        except AssertionError as e:
            print(f"FAIL: {test.__name__} - {e}")
            failed += 1
    sys.exit(1 if failed else 0)
