extends SceneTree

const EventRecorderScript = preload("res://src/event_recorder.gd")

func _initialize() -> void:
	call_deferred("_run_recorder_failure")

func _run_recorder_failure() -> void:
	var recorder = EventRecorderScript.new()
	recorder.runs_directory = OS.get_environment("AGENT_WORLD_TEST_RUNS_DIR")
	root.add_child(recorder)
	if not recorder.start_run("run_failure_test", "scenario_test", "agent_test", 42):
		quit(1)
		return
	var started_event = {
		"id": "evt_started",
		"run_id": "run_failure_test",
		"timestamp_s": 0.0,
		"version": "1.0.0",
		"event_type_id": "run_started",
		"target_instance_id": "",
		"description": "Run started",
		"severity": "info",
		"metadata": {},
	}
	if not recorder.append_event(started_event):
		quit(1)
		return
	var invalid_event = started_event.duplicate(true)
	invalid_event["id"] = "evt_invalid"
	invalid_event["severity"] = "invalid"
	if recorder.append_event(invalid_event):
		quit(1)
		return
	quit(0)
