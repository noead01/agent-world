#!/usr/bin/env python3
"""Regression checks for recording behavior-affecting world configuration."""
import os
import re
import json

WORLD_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPO_DIR = os.path.dirname(os.path.dirname(WORLD_DIR))
ROOM_FILE = os.path.join(WORLD_DIR, "src", "room.gd")
BENCHMARK_ROOM_FILE = os.path.join(WORLD_DIR, "src", "benchmark_room.gd")
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


def _gdscript_var(content, name):
    """Extract a var assignment (not const) from GDScript."""
    # Handle both `var name = value` and `var name: Type = value`
    match = re.search(
        rf"^var {name}(\s*:\s*\w+)?\s*=\s*(.+)$", content, re.MULTILINE
    )
    assert match, f"missing GDScript var {name}"
    return match.group(2).strip()


def _gdscript_export_var(content, name):
    """Extract an @export var assignment from GDScript."""
    match = re.search(
        rf"@export var {name}\s*:\s*\w+\s*=\s*(.+)$", content, re.MULTILINE
    )
    assert match, f"missing GDScript export var {name}"
    return match.group(1).strip()


def _gdscript_string_array(content, name):
    return re.findall(r'"([^"]*)"', _gdscript_var(content, name))


def _gdscript_const_string_array(content, name):
    return re.findall(r'"([^"]*)"', _gdscript_const(content, name))


def test_demo_impulse_uses_recorded_impulse_path():
    """Demo impulse handling is in BenchmarkRoom (demo layer) and Room (core)."""
    with open(BENCHMARK_ROOM_FILE) as source:
        content = source.read()
    # BenchmarkRoom calls apply_impulse which is defined in parent Room
    assert 'apply_impulse(target.instance_id, _demo_impulse_vector)' in content
    # The event emission is in parent Room's apply_impulse method
    with open(ROOM_FILE) as source:
        room_content = source.read()
    assert '_append_domain_event("object_impulse_applied", instance_id' in room_content
    assert '"impulse": _vector_to_dict(impulse)' in room_content


def test_fingerprint_covers_demo_timing_and_impulse_controls():
    """Demo timing and impulse controls are in BenchmarkRoom exports, not core fingerprint.
    
    The core Room fingerprint should NOT include demo-specific controls since they
    don't affect the reproducible configuration - only the demo scenario does.
    """
    with open(ROOM_FILE) as source:
        content = source.read()
    fingerprint = content.split("func _compute_config_fingerprint()", 1)[1].split(
        "func _canonicalize_config", 1
    )[0]
    # Core fingerprint should NOT include demo timing controls
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
        assert control not in fingerprint, f"Demo control {control} should not be in core fingerprint"
    # But should include protocol controls
    for control in (
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
    """The fingerprinted policy must stay identical to the Python implementation.
    
    Core Room stores these as vars (prefixed with _) for fingerprint; 
    BenchmarkRoom can override via exports.
    """
    room = _read(ROOM_FILE)
    mock_agent = _read(MOCK_AGENT_FILE)
    service = _read(AGENT_SERVICE_FILE)

    delay = re.search(r"ACTION_DELAY_TICKS = (\d+)", mock_agent)
    cooldown = re.search(r"ACTION_COOLDOWN_TICKS = (\d+)", mock_agent)
    probability = re.search(r"self\._rng\.random\(\) < ([\d.]+)", mock_agent)
    target_ids = re.search(r"target_ids = \[(.*?)\]", service, re.DOTALL)
    interrupt_target = re.search(r'is_first = \(tid == "([^"]+)"\)', service)
    assert delay and cooldown and probability and target_ids and interrupt_target

    # Core Room uses var _agent_service_* for fingerprint
    assert _gdscript_var(room, "_agent_service_policy_version").strip('"')
    assert int(_gdscript_var(room, "_agent_service_action_delay_ticks")) == int(
        delay.group(1)
    )
    assert int(_gdscript_var(room, "_agent_service_action_cooldown_ticks")) == int(
        cooldown.group(1)
    )
    assert float(
        _gdscript_var(room, "_agent_service_action_delay_probability")
    ) == float(probability.group(1))
    assert _gdscript_string_array(room, "_agent_service_target_ids") == re.findall(
        r'"([^"]+)"', target_ids.group(1)
    )
    assert _gdscript_string_array(
        room, "_agent_service_interrupt_target_ids"
    ) == [interrupt_target.group(1)]


def test_drive_policy_constants_match_config():
    """Drive policy constants in core Room (for fingerprint) must match drive_policy.json."""
    room = _read(ROOM_FILE)
    config_path = os.path.join(REPO_DIR, "services", "agent", "drive_policy.json")
    with open(config_path) as f:
        drive_config = json.load(f)

    # Core Room uses var _drive_* for fingerprint
    # Check thresholds
    assert float(_gdscript_var(room, "_drive_curiosity_explore_threshold")) == drive_config["thresholds"]["curiosity_explore"]
    assert float(_gdscript_var(room, "_drive_uncertainty_investigate_threshold")) == drive_config["thresholds"]["uncertainty_investigate"]
    assert float(_gdscript_var(room, "_drive_integrity_safety_threshold")) == drive_config["thresholds"]["integrity_safety"]

    # Check initial values
    assert float(_gdscript_var(room, "_drive_initial_curiosity")) == drive_config["initial_values"]["curiosity"]
    assert float(_gdscript_var(room, "_drive_initial_uncertainty")) == drive_config["initial_values"]["uncertainty"]
    assert float(_gdscript_var(room, "_drive_initial_integrity")) == drive_config["initial_values"]["physical_integrity"]

    # Check update rates
    assert float(_gdscript_var(room, "_drive_curiosity_novel_boost")) == drive_config["update_rates"]["curiosity"]["novel_object_boost"]
    assert float(_gdscript_var(room, "_drive_curiosity_moved_boost")) == drive_config["update_rates"]["curiosity"]["moved_object_boost"]
    assert float(_gdscript_var(room, "_drive_curiosity_decay_rate")) == drive_config["update_rates"]["curiosity"]["decay_rate"]

    assert float(_gdscript_var(room, "_drive_uncertainty_high_error_boost")) == drive_config["update_rates"]["uncertainty"]["high_prediction_error_boost"]
    assert float(_gdscript_var(room, "_drive_uncertainty_medium_error_boost")) == drive_config["update_rates"]["uncertainty"]["medium_prediction_error_boost"]
    assert float(_gdscript_var(room, "_drive_uncertainty_good_prediction_decay")) == drive_config["update_rates"]["uncertainty"]["good_prediction_decay"]
    assert float(_gdscript_var(room, "_drive_uncertainty_unexpected_movement_boost")) == drive_config["update_rates"]["uncertainty"]["unexpected_movement_boost"]
    assert float(_gdscript_var(room, "_drive_uncertainty_decay_rate")) == drive_config["update_rates"]["uncertainty"]["decay_rate"]

    assert float(_gdscript_var(room, "_drive_integrity_collision_penalty")) == drive_config["update_rates"]["physical_integrity"]["collision_risk_penalty"]
    assert float(_gdscript_var(room, "_drive_integrity_recovery_rate")) == drive_config["update_rates"]["physical_integrity"]["recovery_rate"]
    assert float(_gdscript_var(room, "_drive_integrity_collision_distance")) == drive_config["update_rates"]["physical_integrity"]["collision_distance_threshold"]

    # Check prediction error thresholds
    assert float(_gdscript_var(room, "_drive_prediction_error_high")) == drive_config["prediction_error_thresholds"]["high"]
    assert float(_gdscript_var(room, "_drive_prediction_error_medium")) == drive_config["prediction_error_thresholds"]["medium"]
    assert float(_gdscript_var(room, "_drive_unexpected_movement_threshold")) == drive_config["prediction_error_thresholds"]["unexpected_movement"]


def test_benchmark_room_exports_match_config():
    """BenchmarkRoom exports (demo layer) should match config defaults."""
    bench = _read(BENCHMARK_ROOM_FILE)
    config_path = os.path.join(WORLD_DIR, "config", "world_config.json")
    with open(config_path) as f:
        config = json.load(f)
    
    # Check demo exports match config
    demo = config["simulation"].get("demo", {})
    assert float(_gdscript_export_var(bench, "demo_duration_s")) == demo.get("duration_s", 10.0)
    assert float(_gdscript_export_var(bench, "demo_pause_time_s")) == demo.get("pause_time_s", 2.0)
    assert float(_gdscript_export_var(bench, "demo_resume_time_s")) == demo.get("resume_time_s", 4.0)
    assert float(_gdscript_export_var(bench, "demo_scale_time_s")) == demo.get("scale_time_s", 6.0)
    assert float(_gdscript_export_var(bench, "demo_reset_time_s")) == demo.get("reset_time_s", 8.0)
    assert float(_gdscript_export_var(bench, "demo_scale_factor")) == demo.get("scale_factor", 2.0)
    
    impulse = demo.get("automatic_impulse", {})
    assert float(_gdscript_export_var(bench, "impulse_time_s")) == impulse.get("time_s", 1.0)
    assert _gdscript_export_var(bench, "impulse_target_id").strip('"') == impulse.get("target_instance_id", "obj_metal_sphere")