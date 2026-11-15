#!/usr/bin/env python3
"""Acceptance test for WebSocketClient shutdown behavior."""
import tempfile
from pathlib import Path

from test_run_recording import _run_godot


def test_close_cancels_pending_reconnects():
    """A close during backoff must not reconnect the released peer."""
    with tempfile.TemporaryDirectory() as temp_dir:
        data_home = Path(temp_dir) / "godot-data"
        _run_godot(
            data_home,
            "--script",
            "res://tests/acceptance/websocket_close_harness.gd",
            timeout=15,
        )
