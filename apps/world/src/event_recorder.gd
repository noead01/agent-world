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

func _init() -> void:
	# Pre-compile regex patterns so validation works even if start_run/append_event
	# is called before the node enters the tree (before _ready()).
	_id_regex = RegEx.new()
	_id_regex.compile("^[a-z][a-z0-9_-]*$")
	_version_regex = RegEx.new()
	_version_regex.compile("^\\d+\\.\\d+\\.\\d+$")

func _ready() -> void:
	# Ensure runs directory exists
	var dir = DirAccess.open(runs_directory)
	if dir == null:
		if DirAccess.make_dir_recursive_absolute(runs_directory) != OK:
			push_error("EventRecorder: Failed to create runs directory: %s" % [runs_directory])

func _get_utc_timestamp() -> String:
	# Get UTC time in ISO 8601 format with Z suffix (RFC3339).
	# get_datetime_dict_from_system(true) returns UTC; the default returns local time.
	var dt = Time.get_datetime_dict_from_system(true)
	return "%04d-%02d-%02dT%02d:%02d:%02dZ" % [dt["year"], dt["month"], dt["day"], dt["hour"], dt["minute"], dt["second"]]

func start_run(run_id: String, scenario_id: String, agent_id: String, random_seed: int, config_fingerprint: String = "") -> bool:
	if _current_run_id != "":
		push_error("EventRecorder: Run already in progress: %s" % [_current_run_id])
		return false

	var run_path = "%s/%s" % [runs_directory, run_id]

	# Refuse to reuse an existing run directory: opening events.jsonl with WRITE
	# would truncate an already-persisted authoritative run record.
	if DirAccess.open(run_path) != null:
		push_error("EventRecorder: Refusing to overwrite existing run record: %s" % [run_path])
		return false

	_current_run_id = run_id
	_current_run_path = run_path

	# Create run directory
	var dir_error = DirAccess.make_dir_recursive_absolute(_current_run_path)
	if dir_error != OK:
		push_error("EventRecorder: Failed to create run directory: %s (error %d)" % [_current_run_path, dir_error])
		_current_run_id = ""
		_current_run_path = ""
		return false

	# Open events file for append-only writing
	var events_path = "%s/events.jsonl" % [_current_run_path]
	_events_file = FileAccess.open(events_path, FileAccess.WRITE)
	if _events_file == null:
		_fail_run("Failed to open events file: %s" % [events_path])
		return false

	# Initialize run metadata (config_fingerprint not in run.schema.json)
	var now_str = _get_utc_timestamp()
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

	# Write run metadata and verify the write actually succeeded
	var metadata_path = "%s/run.json" % [_current_run_path]
	var run_file = FileAccess.open(metadata_path, FileAccess.WRITE)
	if run_file == null:
		_fail_run("Failed to open run metadata file: %s" % [metadata_path])
		return false
	run_file.store_string(JSON.stringify(_run_metadata, "\t"))
	run_file.flush()
	var metadata_error = run_file.get_error()
	run_file.close()
	if metadata_error != OK:
		_fail_run("Failed to write run metadata: %s (error %d)" % [metadata_path, metadata_error])
		return false

	# Write initial validity record (previous_validity = null for initial)
	if not _write_validity("valid", null, "Run started", "event_recorder"):
		_fail_run("Failed to write initial validity record")
		return false

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
	
	# Ensure required correlation fields before validation so events that omit
	# them are still schema-valid once the recorder fills them in.
	var event_copy = event.duplicate(true)
	if not event_copy.has("run_id"):
		event_copy["run_id"] = _current_run_id
	if not event_copy.has("timestamp_s") and _run_metadata.has("simulation_time_s"):
		event_copy["timestamp_s"] = _run_metadata["simulation_time_s"]
	
	# Validate event against schema if enabled
	if validate_events:
		if not _validate_event(event_copy):
			_fail_run("Event schema validation failed: %s" % [JSON.stringify(event_copy)])
			return false
	
	# Write event as JSONL line
	var event_json = JSON.stringify(event_copy)
	_events_file.store_line(event_json)
	if _events_file.get_error() != OK:
		push_error("EventRecorder: Failed to write event to file: %s" % [_events_file.get_error()])
		_fail_run("Event write failed: %s" % [_events_file.get_error()])
		return false
	
	_event_count += 1
	
	event_appended.emit(event_copy)
	return true

func end_run(simulation_time_s: float = 0.0) -> bool:
	if _current_run_id == "":
		push_error("EventRecorder: No active run")
		return false
	
	# Update run metadata
	var now_str = _get_utc_timestamp()
	_run_metadata["ended_at"] = now_str
	_run_metadata["simulation_time_s"] = simulation_time_s
	_run_metadata["status"] = "completed"
	
	var run_path = "%s/run.json" % [_current_run_path]
	var run_file = FileAccess.open(run_path, FileAccess.WRITE)
	if run_file == null:
		_fail_run("Failed to update run metadata: %s" % [run_path])
		return false
	run_file.store_string(JSON.stringify(_run_metadata, "\t"))
	run_file.flush()
	var metadata_error = run_file.get_error()
	run_file.close()
	if metadata_error != OK:
		_fail_run("Failed to write run metadata: %s (error %d)" % [run_path, metadata_error])
		return false

	# Write final validity record; a failure here must abort the run rather than
	# reporting a completed run whose authoritative history is incomplete.
	if not _write_validity("valid", _validity, "Run completed successfully", "event_recorder"):
		_fail_run("Failed to write final validity record")
		return false
	
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
	var now_str = _get_utc_timestamp()
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

func _write_validity(validity: String, previous, reason: String, evaluator: String) -> bool:
	if _current_run_path == "":
		return false
	
	var validity_record = {
		"run_id": _current_run_id,
		"validity": validity,
		"previous_validity": previous,
		"transition_reason": reason,
		"evaluated_at": _get_utc_timestamp(),
		"evaluator_component": evaluator,
		"evidence_summary": reason,
		"invalidating_event_ids": [],
		"version": "1.0.0",
	}
	
	var validity_path = "%s/validity.jsonl" % [_current_run_path]
	# Append without truncating: READ_WRITE opens an existing file without
	# truncation, while WRITE creates it the first time. (WRITE_READ truncates.)
	var validity_file = null
	if FileAccess.file_exists(validity_path):
		validity_file = FileAccess.open(validity_path, FileAccess.READ_WRITE)
	else:
		validity_file = FileAccess.open(validity_path, FileAccess.WRITE)
	if validity_file == null:
		push_error("EventRecorder: Failed to open validity file: %s" % [validity_path])
		return false
	
	validity_file.seek_end()
	validity_file.store_line(JSON.stringify(validity_record))
	validity_file.flush()
	var write_error = validity_file.get_error()
	validity_file.close()
	if write_error != OK:
		push_error("EventRecorder: Failed to write validity record: %s (error %d)" % [validity_path, write_error])
		return false
	
	_validity = validity
	validity_changed.emit(_current_run_id, validity, reason)
	return true

func _validate_event(event: Dictionary) -> bool:
	# Mirror event.schema.json before persisting: required fields, types,
	# patterns, severity enum, additionalProperties=false, plus run_id
	# consistency with the active run.
	var allowed_fields = [
		"id", "run_id", "agent_id", "timestamp_s", "version",
		"event_type_id", "target_instance_id", "description", "severity", "metadata",
	]
	for field in event.keys():
		if field not in allowed_fields:
			push_error("EventRecorder: Unknown event field '%s'" % [field])
			return false

	var required_fields = ["id", "run_id", "timestamp_s", "version"]
	for field in required_fields:
		if not event.has(field):
			push_error("EventRecorder: Missing required field '%s' in event" % [field])
			return false

	# Optional/required string fields must actually be strings.
	var string_fields = ["id", "run_id", "agent_id", "version", "event_type_id", "target_instance_id", "description"]
	for field in string_fields:
		if event.has(field) and not (event[field] is String):
			push_error("EventRecorder: Field '%s' must be a string" % [field])
			return false

	# Validate id pattern using pre-compiled RegEx (String.match uses wildcard, not regex)
	if not _id_regex.search(event["id"]):
		push_error("EventRecorder: Invalid event id format: %s" % [event["id"]])
		return false

	# Validate version pattern using pre-compiled RegEx
	if not _version_regex.search(event["version"]):
		push_error("EventRecorder: Invalid version format: %s" % [event["version"]])
		return false

	# timestamp_s: number with minimum 0
	var timestamp = event["timestamp_s"]
	if not (timestamp is int or timestamp is float):
		push_error("EventRecorder: timestamp_s must be a number")
		return false
	if float(timestamp) < 0.0:
		push_error("EventRecorder: timestamp_s must be >= 0")
		return false

	# Events persisted under a run must reference that run.
	if event["run_id"] != _current_run_id:
		push_error("EventRecorder: Event run_id '%s' does not match active run '%s'" % [event["run_id"], _current_run_id])
		return false

	# Validate severity if present
	if event.has("severity"):
		var valid_severities = ["info", "notice", "warning", "error"]
		if not (event["severity"] is String) or event["severity"] not in valid_severities:
			push_error("EventRecorder: Invalid severity: %s" % [event["severity"]])
			return false

	# metadata must be an object when present
	if event.has("metadata") and not (event["metadata"] is Dictionary):
		push_error("EventRecorder: metadata must be an object")
		return false

	return true
