extends SceneTree

const EventRecorderScript = preload("res://src/event_recorder.gd")

var _runs_directory := ""

func _initialize() -> void:
	call_deferred("_run_boundary_cases")

func _run_boundary_cases() -> void:
	_runs_directory = OS.get_environment("AGENT_WORLD_TEST_RUNS_DIR")

	if not _reject_non_initial_event():
		quit(1)
		return
	if not _reject_second_run_started():
		quit(1)
		return
	if not _reject_event_after_run_ended():
		quit(1)
		return
	if not _reject_completion_without_run_ended():
		quit(1)
		return
	quit(0)

func _reject_non_initial_event() -> bool:
	var run_id := "run_boundary_first_test"
	var recorder = _start(run_id)
	if recorder == null:
		return false
	# Readback requires the stream to begin with run_started.
	return not recorder.append_event(_event(run_id, "evt_first", 1.0, "information_received"))

func _reject_second_run_started() -> bool:
	var run_id := "run_boundary_duplicate_start_test"
	var recorder = _start(run_id)
	if recorder == null:
		return false
	if not recorder.append_event(_event(run_id, "evt_started", 1.0, "run_started")):
		return false
	# Exactly one run_started event may exist in a stream.
	return not recorder.append_event(_event(run_id, "evt_started_again", 2.0, "run_started"))

func _reject_event_after_run_ended() -> bool:
	var run_id := "run_boundary_after_end_test"
	var recorder = _start(run_id)
	if recorder == null:
		return false
	if not recorder.append_event(_event(run_id, "evt_started", 1.0, "run_started")):
		return false
	if not recorder.append_event(_event(run_id, "evt_ended", 2.0, "run_ended")):
		return false
	# run_ended is terminal for the event stream.
	return not recorder.append_event(_event(run_id, "evt_after_end", 3.0, "information_received"))

func _reject_completion_without_run_ended() -> bool:
	var run_id := "run_boundary_missing_end_event_test"
	var recorder = _start(run_id)
	if recorder == null:
		return false
	if not recorder.append_event(_event(run_id, "evt_started", 1.0, "run_started")):
		return false
	# A completed run must end with exactly one run_ended event.
	return not recorder.end_run(1.0)

func _start(run_id: String):
	var recorder = EventRecorderScript.new()
	recorder.runs_directory = _runs_directory
	root.add_child(recorder)
	if not recorder.start_run(run_id, "scenario_test", "agent_test", 42):
		return null
	return recorder

func _event(run_id: String, event_id: String, timestamp_s: float, event_type_id: String) -> Dictionary:
	return {
		"id": event_id,
		"run_id": run_id,
		"timestamp_s": timestamp_s,
		"version": "1.0.0",
		"event_type_id": event_type_id,
		"target_instance_id": "",
		"description": "",
		"severity": "info",
		"metadata": {},
	}
