extends SceneTree

const EventRecorderScript = preload("res://src/event_recorder.gd")

func _initialize() -> void:
	call_deferred("_run_duplicate_id_case")

func _run_duplicate_id_case() -> void:
	var recorder = EventRecorderScript.new()
	recorder.runs_directory = OS.get_environment("AGENT_WORLD_TEST_RUNS_DIR")
	root.add_child(recorder)
	if not recorder.start_run("run_duplicate_id_test", "scenario_test", "agent_test", 42):
		quit(1)
		return
	if not recorder.append_event(_event("evt_repeated", 1.0, "run_started")):
		quit(1)
		return
	# `event.id` is the stable key consumers index by, so a reused id must be
	# rejected before it reaches the persisted stream.
	if recorder.append_event(_event("evt_repeated", 2.0, "information_received")):
		quit(1)
		return
	quit(0)

func _event(event_id: String, timestamp_s: float, event_type_id: String) -> Dictionary:
	return {
		"id": event_id,
		"run_id": "run_duplicate_id_test",
		"timestamp_s": timestamp_s,
		"version": "1.0.0",
		"event_type_id": event_type_id,
		"target_instance_id": "",
		"description": "",
		"severity": "info",
		"metadata": {},
	}
