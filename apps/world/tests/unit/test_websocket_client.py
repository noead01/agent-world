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