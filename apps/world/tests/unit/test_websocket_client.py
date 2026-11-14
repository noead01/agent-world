#!/usr/bin/env python3
"""Unit tests for websocket_client.gd source validation."""
import os
import re

WORLD_SRC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src")
SRC_FILE = os.path.join(WORLD_SRC_DIR, "websocket_client.gd")

def test_file_exists():
    assert os.path.exists(SRC_FILE), "websocket_client.gd must exist"

def test_class_name():
    with open(SRC_FILE) as f:
        content = f.read()
    assert "class_name WebSocketClient" in content, "Must declare class_name WebSocketClient"

def test_extends_node():
    with open(SRC_FILE) as f:
        content = f.read()
    assert content.strip().startswith("extends Node"), "Must extend Node"

def test_signals():
    with open(SRC_FILE) as f:
        content = f.read()
    required_signals = ["connected", "disconnected", "message_received", "error"]
    for sig in required_signals:
        assert f"signal {sig}" in content, f"Missing signal: {sig}"

def test_exported_config():
    with open(SRC_FILE) as f:
        content = f.read()
    assert '@export var url: String = "ws://localhost:8765"' in content
    assert "@export var reconnect_max_attempts: int = 10" in content
    assert "@export var heartbeat_interval_s: float = 5.0" in content

def test_methods():
    with open(SRC_FILE) as f:
        content = f.read()
    required_methods = ["connect_to_server", "send_message", "close"]
    for method in required_methods:
        assert f"func {method}" in content, f"Missing method: {method}"

def test_state_machine():
    with open(SRC_FILE) as f:
        content = f.read()
    # Check for connection state handling
    assert "_state" in content or "state" in content.lower(), "Should track connection state"
    assert "CONNECTING" in content or "connecting" in content.lower(), "Should have CONNECTING state"
    assert "CONNECTED" in content or "connected" in content.lower(), "Should have CONNECTED state"
    assert "DISCONNECTED" in content or "disconnected" in content.lower(), "Should have DISCONNECTED state"

def test_commands_are_forwarded_only_after_handshake():
    with open(SRC_FILE) as f:
        content = f.read()
    assert "if _can_forward_message(msg):" in content
    assert "func _can_forward_message(msg: Dictionary) -> bool:" in content
    assert "_state == ConnectionState.CONNECTED" in content

def test_hello_ack_is_validated_before_connecting():
    with open(SRC_FILE) as f:
        content = f.read()
    validation = content.index("var validation_error = _validate_hello_ack(msg)")
    connected = content.index("_state = ConnectionState.CONNECTED")
    assert validation < connected
    assert 'msg.get("protocol_version", "")' in content
    assert 'msg.get("accepted_capabilities", [])' in content
    assert '_on_disconnected("Invalid HelloAck' in content

def test_queued_world_states_are_coalesced():
    with open(SRC_FILE) as f:
        content = f.read()
    # Only the newest WorldState may stay queued while disconnected; other
    # lifecycle messages must keep being appended.
    assert "func _queue_pending_message(message: Dictionary) -> void:" in content
    assert "func _drop_queued_world_states() -> void:" in content
    assert 'if message.get("type", "") == "WorldState":' in content
    assert "_drop_queued_world_states()" in content
    assert "_pending_messages.remove_at(index)" in content
    assert "_pending_messages.append(message)" in content


if __name__ == "__main__":
    import sys
    tests = [
        test_file_exists,
        test_class_name,
        test_extends_node,
        test_signals,
        test_exported_config,
        test_methods,
        test_state_machine,
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
