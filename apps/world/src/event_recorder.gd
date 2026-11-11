extends Node

class_name EventRecorder

signal run_started(run_id: String)
signal event_appended(event: Dictionary)
signal run_ended(run_id: String, status: String)
signal run_failed(run_id: String, reason: String)
signal validity_changed(run_id: String, validity: String, reason: String)

@export var runs_directory: String = "user://runs"
@export var validate_events: bool = true

var _current_run_id: String = ""
var _current_run_path: String = ""
var _events_file = null
var _run_metadata: Dictionary = {}
var _validity: String = "valid"
var _event_count: int = 0
var _id_regex: RegEx
var _version_regex: RegEx

func _ready() -> void:
	# Ensure runs directory exists
	var dir = DirAccess.open(runs_directory)
	if dir == null:
		if not DirAccess.make_dir_recursive_absolute(runs_directory):
			push_error("EventRecorder: Failed to create runs directory: %s" % [runs_directory])

	# Pre-compile regex patterns for validation
	_id_regex = RegEx.new()
	_id_regex.compile("^[a-z][a-z0-9_-]*$")
	_version_regex = RegEx.new()
	_version_regex.compile("^\\d+\\.\\d+\\.\\d+$")

func start_run(run_id: String, scenario_id: String, agent_id: String, random_seed: int, config_fingerprint: String = "") -> bool:
	if _current_run_id != "":
		push_error("EventRecorder: Run already in progress: %s" % [_current_run_id])
		return false
	
	_current_run_id = run_id
	_current_run_path = "%s/%s" % [runs_directory, run_id]
	
	# Create run directory
	var dir = DirAccess.open(_current_run_path)
	if dir == null:
		dir = DirAccess.make_dir_recursive_absolute(_current_run_path)
	if dir == null:
		_fail_run("Failed to create run directory: %s" % [_current_run_path])
		return false
	
	# Open events file for append-only writing
	var events_path = "%s/events.jsonl" % [_current_run_path]
	_events_file = FileAccess.open(events_path, FileAccess.WRITE)
	if _events_file == null:
		_fail_run("Failed to open events file: %s" % [events_path])
		return false
	
	# Initialize run metadata (config_fingerprint not in run.schema.json)
	var now_str = Time.get_datetime_string_from_system()
	_run_metadata = {
		"id": run_id,
		"scenario_id": scenario_id,
		"version": "1.0.0",
		"agent_id": agent_id,
		"started_at": now_str,
		"ended_at": null,
		"simulation_time_s": 0.0,
		"status": "running",
		"random_seed": random_seed,
	}
	
	# Write run metadata
	var run_path = "%s/run.json" % [_current_run_path]
	var run_file = FileAccess.open(run_path, FileAccess.WRITE)
	if run_file == null:
		_fail_run("Failed to open run metadata file: %s" % [run_path])
		return false
	run_file.store_string(JSON.stringify(_run_metadata, "\t"))
	run_file.close()
	
	# Write initial validity record (previous_validity = null for initial)
	_write_validity("valid", null, "Run started", "event_recorder")
	
	_validity = "valid"
	_event_count = 0
	run_started.emit(run_id)
	return true

func append_event(event: Dictionary) -> bool:
	if _current_run_id == "":
		push_error("EventRecorder: No active run")
		return false
	
	if _events_file == null:
		_fail_run("Events file not open")
		return false
	
	# Validate event against schema if enabled
	if validate_events:
		if not _validate_event(event):
			_fail_run("Event schema validation failed: %s" % [JSON.stringify(event)])
			return false
	
	# Ensure required correlation fields
	var event_copy = event.duplicate(true)
	if not event_copy.has("run_id"):
		event_copy["run_id"] = _current_run_id
	if not event_copy.has("timestamp_s") and _run_metadata.has("simulation_time_s"):
		event_copy["timestamp_s"] = _run_metadata["simulation_time_s"]
	
	# Write event as JSONL line
	var event_json = JSON.stringify(event_copy)
	_events_file.store_line(event_json)
	_event_count += 1
	
	event_appended.emit(event_copy)
	return true

func end_run(simulation_time_s: float = 0.0) -> bool:
	if _current_run_id == "":
		push_error("EventRecorder: No active run")
		return false
	
	# Update run metadata
	var now_str = Time.get_datetime_string_from_system()
	_run_metadata["ended_at"] = now_str
	_run_metadata["simulation_time_s"] = simulation_time_s
	_run_metadata["status"] = "completed"
	
	var run_path = "%s/run.json" % [_current_run_path]
	var run_file = FileAccess.open(run_path, FileAccess.WRITE)
	if run_file == null:
		_fail_run("Failed to update run metadata: %s" % [run_path])
		return false
	run_file.store_string(JSON.stringify(_run_metadata, "\t"))
	run_file.close()
	
	# Write final validity record
	_write_validity("valid", _validity, "Run completed successfully", "event_recorder")
	
	# Close events file
	if _events_file:
		_events_file.close()
		_events_file = null
	
	var run_id = _current_run_id
	_current_run_id = ""
	_current_run_path = ""
	
	run_ended.emit(run_id, "completed")
	return true

func fail_run(reason: String) -> void:
	_fail_run(reason)

func _fail_run(reason: String) -> void:
	if _current_run_id == "":
		return
	
	# Update run metadata to aborted
	var now_str = Time.get_datetime_string_from_system()
	_run_metadata["ended_at"] = now_str
	_run_metadata["status"] = "aborted"
	
	var run_path = "%s/run.json" % [_current_run_path]
	var run_file = FileAccess.open(run_path, FileAccess.WRITE)
	if run_file:
		run_file.store_string(JSON.stringify(_run_metadata, "\t"))
		run_file.close()
	
	# Write invalid validity record
	_write_validity("invalid", _validity, reason, "event_recorder")
	
	# Close events file
	if _events_file:
		_events_file.close()
		_events_file = null
	
	var run_id = _current_run_id
	_current_run_id = ""
	_current_run_path = ""
	_validity = "invalid"
	
	run_failed.emit(run_id, reason)

func get_run_status() -> Dictionary:
	return {
		"run_id": _current_run_id,
		"validity": _validity,
		"event_count": _event_count,
		"path": _current_run_path,
	}

func get_events_path() -> String:
	if _current_run_path == "":
		return ""
	return "%s/events.jsonl" % [_current_run_path]

func _write_validity(validity: String, previous: String, reason: String, evaluator: String) -> void:
	if _current_run_path == "":
		return
	
	var validity_record = {
		"run_id": _current_run_id,
		"validity": validity,
		"previous_validity": previous,
		"transition_reason": reason,
		"evaluated_at": Time.get_datetime_string_from_system(),
		"evaluator_component": evaluator,
		"evidence_summary": reason,
		"invalidating_event_ids": [],
		"version": "1.0.0",
	}
	
	var validity_path = "%s/validity.jsonl" % [_current_run_path]
	# Use WRITE mode with append by seeking to end - avoids truncation of WRITE_READ
	var validity_file = FileAccess.open(validity_path, FileAccess.WRITE)
	if validity_file == null:
		push_error("EventRecorder: Failed to open validity file: %s" % [validity_path])
		return
	
	validity_file.seek_end()
	validity_file.store_line(JSON.stringify(validity_record))
	validity_file.close()
	
	_validity = validity
	validity_changed.emit(_current_run_id, validity, reason)

func _validate_event(event: Dictionary) -> bool:
	# Basic validation - check required fields from event.schema.json
	var required_fields = ["id", "run_id", "timestamp_s", "version", "event_type_id"]
	for field in required_fields:
		if not event.has(field):
			push_error("EventRecorder: Missing required field '%s' in event" % [field])
			return false
	
	# Validate id pattern using pre-compiled RegEx (String.match uses wildcard, not regex)
	if not _id_regex.search(event["id"]):
		push_error("EventRecorder: Invalid event id format: %s" % [event["id"]])
		return false
	
	# Validate version pattern using pre-compiled RegEx
	if not _version_regex.search(event["version"]):
		push_error("EventRecorder: Invalid version format: %s" % [event["version"]])
		return false
	
	# Validate severity if present
	if event.has("severity"):
		var valid_severities = ["info", "notice", "warning", "error"]
		if event["severity"] not in valid_severities:
			push_error("EventRecorder: Invalid severity: %s" % [event["severity"]])
			return false
	
	return true
