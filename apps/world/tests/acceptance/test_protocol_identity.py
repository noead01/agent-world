#!/usr/bin/env python3
"""Acceptance test for session-identity validation of terminal action results."""
import tempfile
from pathlib import Path

from test_run_recording import _run_godot


def test_terminal_action_results_validate_session_identity():
    """A foreign result must not clear a pending request or be surfaced."""
    with tempfile.TemporaryDirectory() as temp_dir:
        data_home = Path(temp_dir) / "godot-data"
        _run_godot(
            data_home,
            "--script",
            "res://tests/acceptance/protocol_result_identity_harness.gd",
            timeout=15,
        )
