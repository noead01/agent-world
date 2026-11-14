#!/usr/bin/env python3
"""Regression checks for recording behavior-affecting world configuration."""
import os

WORLD_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROOM_FILE = os.path.join(WORLD_DIR, "src", "room.gd")


def test_demo_impulse_uses_recorded_impulse_path():
    with open(ROOM_FILE) as source:
        content = source.read()
    assert 'apply_impulse(target.instance_id, _demo_impulse_vector)' in content
    assert '_append_domain_event("object_impulse_applied", instance_id' in content
    assert '"impulse": _vector_to_dict(impulse)' in content


def test_fingerprint_covers_demo_timing_and_impulse_controls():
    with open(ROOM_FILE) as source:
        content = source.read()
    fingerprint = content.split("func _compute_config_fingerprint()", 1)[1].split(
        "func _canonicalize_config", 1
    )[0]
    for control in (
        "_demo_duration",
        "_demo_pause_time",
        "_demo_resume_time",
        "_demo_scale_time",
        "_demo_reset_time",
        "_demo_scale_factor",
        "_demo_impulse_time",
        "_demo_impulse_target_id",
        "_demo_impulse_vector",
    ):
        assert control in fingerprint
