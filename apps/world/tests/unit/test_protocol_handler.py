#!/usr/bin/env python3
"""Unit tests for protocol_handler.gd source validation."""
import os

WORLD_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC_FILE = os.path.join(WORLD_DIR, "src", "protocol_handler.gd")

def test_file_exists():
    assert os.path.exists(SRC_FILE), "protocol_handler.gd must exist"

def test_class_name():
    with open(SRC_FILE) as f:
        content = f.read()
    assert "class_name ProtocolHandler" in content

def test_extends_node():
    with open(SRC_FILE) as f:
        content = f.read()
    assert content.strip().startswith("extends Node")

def test_signals():
    with open(SRC_FILE) as f:
        content = f.read()
    required = ["observation_ready", "intention_sent", "action_result_received", "stale_request_rejected"]
    for sig in required:
        assert f"signal {sig}" in content, f"Missing signal: {sig}"

def test_methods():
    with open(SRC_FILE) as f:
        content = f.read()
    required = ["tick_world_state", "send_observation", "send_intention", "send_action"]
    for method in required:
        assert f"func {method}" in content, f"Missing method: {method}"

def test_correlation_injection():
    with open(SRC_FILE) as f:
        content = f.read()
    assert "correlation" in content.lower()
    assert "world_revision" in content
    assert "simulation_tick" in content
    assert "simulation_time" in content

def test_staleness_check():
    with open(SRC_FILE) as f:
        content = f.read()
    assert "stale" in content.lower() or "STALE" in content
    assert "world_revision" in content

def test_incoming_commands_validate_session_context_before_execution():
    with open(SRC_FILE) as f:
        content = f.read()
    assert "_validate_incoming_command(action)" in content
    assert "correlation.get(\"run_id\", \"\") != run_id" in content
    assert "correlation.get(\"agent_id\", \"\") != agent_id" in content

def test_incoming_command_revision_accepts_integral_json_float():
    with open(SRC_FILE) as f:
        content = f.read()
    assert "request_revision = _normalize_world_revision(message.get(\"request_world_revision\"))" in content
    assert "correlation_revision = _normalize_world_revision(correlation.get(\"world_revision\"))" in content
    assert "floor(value) != value" in content

if __name__ == "__main__":
    import sys
    tests = [
        test_file_exists,
        test_class_name,
        test_extends_node,
        test_signals,
        test_methods,
        test_correlation_injection,
        test_staleness_check,
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
