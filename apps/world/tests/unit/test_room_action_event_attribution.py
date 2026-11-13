#!/usr/bin/env python3
"""Regression tests for recording action lifecycle event context."""
import os

WORLD_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROOM_FILE = os.path.join(WORLD_DIR, "src", "room.gd")


def test_terminal_action_events_restore_active_target_and_command_id():
    with open(ROOM_FILE) as source:
        content = source.read()

    assert "_active_action_context" in content
    for handler in (
        "_on_agent_action_completed",
        "_on_agent_action_failed",
        "_on_agent_action_interrupted",
    ):
        assert f"func {handler}" in content
    assert '"command_id": command_id' in content
    assert '_append_domain_event("agent_action_completed", context["target_instance_id"]' in content
    assert '_append_domain_event("agent_action_failed", context["target_instance_id"]' in content
    assert '_append_domain_event("agent_action_interrupted", context["target_instance_id"]' in content
