extends SceneTree

const EventRecorderScript = preload("res://src/event_recorder.gd")

func _initialize() -> void:
	call_deferred("_run_recorder_ordering")

func _run_recorder_ordering() -> void:
	var recorder = EventRecorderScript.new()
	recorder.runs_directory = OS.get_environment("AGENT_WORLD_TEST_RUNS_DIR")
	root.add_child(recorder)
	if not recorder.start_run("run_ordering_test", "scenario_test", "agent_test", 42):
		quit(1)
		return
	if not recorder.append_event(_event("evt_started", 10.0, "run_started")):
		quit(1)
		return
	# A decreasing timestamp violates the ordered-stream contract and must be
	# rejected immediately rather than persisted until readback validation.
	if recorder.append_event(_event("evt_out_of_order", 5.0, "information_received")):
		quit(1)
		return
	quit(0)

func _event(event_id: String, timestamp_s: float, event_type_id: String) -> Dictionary:
	return {
		"id": event_id,
		"run_id": "run_ordering_test",
		"timestamp_s": timestamp_s,
		"version": "1.0.0",
		"event_type_id": event_type_id,
		"target_instance_id": "",
		"description": "Out-of-order timestamp probe",
		"severity": "info",
		"metadata": {},
	}
