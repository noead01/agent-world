#!/usr/bin/env python3
"""Regression checks for recording behavior-affecting world configuration."""
import os
import re

WORLD_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPO_DIR = os.path.dirname(os.path.dirname(WORLD_DIR))
ROOM_FILE = os.path.join(WORLD_DIR, "src", "room.gd")
MOCK_AGENT_FILE = os.path.join(REPO_DIR, "services", "agent", "src", "mock_agent.py")
AGENT_SERVICE_FILE = os.path.join(REPO_DIR, "services", "agent", "src", "agent_service.py")


def _read(path):
    with open(path) as source:
        return source.read()


def _gdscript_const(content, name):
    match = re.search(
        rf"^const {name}\s*(?::[^=\n]*)?=\s*(.+)$", content, re.MULTILINE
    )
    assert match, f"missing GDScript constant {name}"
    return match.group(1).strip()


def _gdscript_string_array(content, name):
    return re.findall(r'"([^"]*)"', _gdscript_const(content, name))


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
        "stale_threshold",
        "world_state_interval_ticks",
    ):
        assert control in fingerprint


def test_fingerprint_includes_agent_service_behavior_policy():
    """World-only settings cannot distinguish runs whose agent behavior differs."""
    with open(ROOM_FILE) as source:
        content = source.read()
    fingerprint = content.split("func _compute_config_fingerprint()", 1)[1].split(
        "func _canonicalize_config", 1
    )[0]
    for control in (
        "agent_service",
        "policy_version",
        "target_sequence",
        "action_delay_ticks",
        "action_cooldown_ticks",
        "action_delay_probability",
        "drive_policy",
    ):
        assert control in fingerprint


def test_fingerprint_includes_drive_policy():
    """Drive policy (thresholds, initial values, update rates) must be in fingerprint."""
    with open(ROOM_FILE) as source:
        content = source.read()
    fingerprint = content.split("func _compute_config_fingerprint()", 1)[1].split(
        "func _canonicalize_config", 1
    )[0]
    for control in (
        "drive_policy",
        "version",
        "thresholds",
        "curiosity_explore",
        "uncertainty_investigate",
        "integrity_safety",
        "initial_values",
        "update_rates",
        "prediction_error_thresholds",
    ):
        assert control in fingerprint


def test_agent_service_policy_constants_match_service_sources():
    """The fingerprinted policy must stay identical to the Python implementation."""
    room = _read(ROOM_FILE)
    mock_agent = _read(MOCK_AGENT_FILE)
    service = _read(AGENT_SERVICE_FILE)

    delay = re.search(r"ACTION_DELAY_TICKS = (\d+)", mock_agent)
    cooldown = re.search(r"ACTION_COOLDOWN_TICKS = (\d+)", mock_agent)
    probability = re.search(r"self\._rng\.random\(\) < ([\d.]+)", mock_agent)
    target_ids = re.search(r"target_ids = \[(.*?)\]", service, re.DOTALL)
    interrupt_target = re.search(r'is_first = \(tid == "([^"]+)"\)', service)
    assert delay and cooldown and probability and target_ids and interrupt_target

    assert _gdscript_const(room, "AGENT_SERVICE_POLICY_VERSION").strip('"')
    assert int(_gdscript_const(room, "AGENT_SERVICE_ACTION_DELAY_TICKS")) == int(
        delay.group(1)
    )
    assert int(_gdscript_const(room, "AGENT_SERVICE_ACTION_COOLDOWN_TICKS")) == int(
        cooldown.group(1)
    )
    assert float(
        _gdscript_const(room, "AGENT_SERVICE_ACTION_DELAY_PROBABILITY")
    ) == float(probability.group(1))
    assert _gdscript_string_array(room, "AGENT_SERVICE_TARGET_IDS") == re.findall(
        r'"([^"]+)"', target_ids.group(1)
    )
    assert _gdscript_string_array(
        room, "AGENT_SERVICE_INTERRUPT_TARGET_IDS"
    ) == [interrupt_target.group(1)]


def test_drive_policy_constants_match_config():
    """Drive policy constants in room.gd must match drive_policy.json."""
    import json
    room = _read(ROOM_FILE)
    config_path = os.path.join(REPO_DIR, "services", "agent", "drive_policy.json")
    with open(config_path) as f:
        drive_config = json.load(f)

    # Check thresholds
    assert float(_gdscript_const(room, "DRIVE_CURIOSITY_EXPLORE_THRESHOLD")) == drive_config["thresholds"]["curiosity_explore"]
    assert float(_gdscript_const(room, "DRIVE_UNCERTAINTY_INVESTIGATE_THRESHOLD")) == drive_config["thresholds"]["uncertainty_investigate"]
    assert float(_gdscript_const(room, "DRIVE_INTEGRITY_SAFETY_THRESHOLD")) == drive_config["thresholds"]["integrity_safety"]

    # Check initial values
    assert float(_gdscript_const(room, "DRIVE_INITIAL_CURIOSITY")) == drive_config["initial_values"]["curiosity"]
    assert float(_gdscript_const(room, "DRIVE_INITIAL_UNCERTAINTY")) == drive_config["initial_values"]["uncertainty"]
    assert float(_gdscript_const(room, "DRIVE_INITIAL_INTEGRITY")) == drive_config["initial_values"]["physical_integrity"]

    # Check update rates
    assert float(_gdscript_const(room, "DRIVE_CURIOSITY_NOVEL_BOOST")) == drive_config["update_rates"]["curiosity"]["novel_object_boost"]
    assert float(_gdscript_const(room, "DRIVE_CURIOSITY_MOVED_BOOST")) == drive_config["update_rates"]["curiosity"]["moved_object_boost"]
    assert float(_gdscript_const(room, "DRIVE_CURIOSITY_DECAY_RATE")) == drive_config["update_rates"]["curiosity"]["decay_rate"]

    assert float(_gdscript_const(room, "DRIVE_UNCERTAINTY_HIGH_ERROR_BOOST")) == drive_config["update_rates"]["uncertainty"]["high_prediction_error_boost"]
    assert float(_gdscript_const(room, "DRIVE_UNCERTAINTY_MEDIUM_ERROR_BOOST")) == drive_config["update_rates"]["uncertainty"]["medium_prediction_error_boost"]
    assert float(_gdscript_const(room, "DRIVE_UNCERTAINTY_GOOD_PREDICTION_DECAY")) == drive_config["update_rates"]["uncertainty"]["good_prediction_decay"]
    assert float(_gdscript_const(room, "DRIVE_UNCERTAINTY_UNEXPECTED_MOVEMENT_BOOST")) == drive_config["update_rates"]["uncertainty"]["unexpected_movement_boost"]
    assert float(_gdscript_const(room, "DRIVE_UNCERTAINTY_DECAY_RATE")) == drive_config["update_rates"]["uncertainty"]["decay_rate"]

    assert float(_gdscript_const(room, "DRIVE_INTEGRITY_COLLISION_PENALTY")) == drive_config["update_rates"]["physical_integrity"]["collision_risk_penalty"]
    assert float(_gdscript_const(room, "DRIVE_INTEGRITY_RECOVERY_RATE")) == drive_config["update_rates"]["physical_integrity"]["recovery_rate"]
    assert float(_gdscript_const(room, "DRIVE_INTEGRITY_COLLISION_DISTANCE")) == drive_config["update_rates"]["physical_integrity"]["collision_distance_threshold"]

    # Check prediction error thresholds
    assert float(_gdscript_const(room, "DRIVE_PREDICTION_ERROR_HIGH")) == drive_config["prediction_error_thresholds"]["high"]
    assert float(_gdscript_const(room, "DRIVE_PREDICTION_ERROR_MEDIUM")) == drive_config["prediction_error_thresholds"]["medium"]
    assert float(_gdscript_const(room, "DRIVE_UNEXPECTED_MOVEMENT_THRESHOLD")) == drive_config["prediction_error_thresholds"]["unexpected_movement"]
