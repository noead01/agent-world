extends Node

class_name ProtocolHandler

signal observation_ready(observation: Dictionary)
signal intention_sent(intention: Dictionary)
signal action_received(action: Dictionary)
signal action_result_received(result: Dictionary)
signal stale_request_rejected(request_id: String, current_revision: int)
signal invalid_command_rejected(request_id: String, reason: String)
signal health_status_ready(health_status: Dictionary)

@export var agent_id: String = "wanderer_01"
@export var run_id: String = "run_001"
@export var experiment_id: String = "exp_autonomous_discovery_01"
@export var scenario_id: String = "first_benchmark_room"
@export var scenario_version: String = "1.0.0"
@export var stale_threshold: int = 5
@export var world_state_interval_ticks: int = 5

var _websocket_client
var _current_world_revision: int = 0
var _current_simulation_tick: int = 0
var _current_simulation_time: float = 0.0
var _tick_counter: int = 0
var _pending_requests: Dictionary = {}  # request_id -> {type, correlation, timestamp}
var _received_commands: Dictionary = {}  # command_id -> {terminal_result}
var _trace_id: String = ""
var _trace

func _log_verbose_message(message: Dictionary) -> void:
	if OS.get_environment("AGENT_WORLD_VERBOSE_LOGS") == "1":
		print("MSG_JSON: %s" % [JSON.stringify(message)])

func set_trace(trace_instance) -> void:
	_trace = trace_instance
	print("ProtocolHandler: Trace set via set_trace()")

func _ready() -> void:
	# Only auto-discover WebSocketClient if not already set via set_websocket_client
	if _websocket_client == null and has_node("../WebSocketClient"):
		set_websocket_client(get_node("../WebSocketClient"))
	print("ProtocolHandler: _ready() called, trace = ", _trace)

func set_websocket_client(client) -> void:
	_websocket_client = client
	if _websocket_client:
		if _websocket_client.has_method("get_trace_id"):
			_trace_id = _websocket_client.get_trace_id()
		if not _websocket_client.message_received.is_connected(_on_message_received):
			_websocket_client.message_received.connect(_on_message_received)
		if not _websocket_client.connected.is_connected(_on_connected):
			_websocket_client.connected.connect(_on_connected)
		if not _websocket_client.disconnected.is_connected(_on_disconnected):
			_websocket_client.disconnected.connect(_on_disconnected)

func _on_connected(server_id: String) -> void:
	print("ProtocolHandler: Connected to agent service: %s" % [server_id])

func _on_disconnected(reason: String) -> void:
	print("ProtocolHandler: Disconnected: %s" % [reason])
	_pending_requests.clear()

func _on_message_received(msg: Dictionary) -> void:
	var msg_type = msg.get("type", "")
	var start_msec = Time.get_ticks_msec()
	match msg_type:
		"HelloAck":
			_on_hello_ack(msg)
		"WorldState":
			_on_world_state(msg)
		"Action":
			# Distinguish between Action command (from agent service) and ActionResult (response to our action)
			# Agent service sends Action commands with result="pending"
			# World sends ActionResults with result in ["success", "failure", "partial"]
			var result = msg.get("result", "")
			if result in ["success", "failure", "partial"]:
				# This is an ActionResult response to an action we sent. A
				# terminal result mutates pending state, so validate the same
				# session identity as an incoming command before classification.
				var identity_error := _validate_session_identity(msg)
				if identity_error != "":
					invalid_command_rejected.emit(String(msg.get("id", "")), identity_error)
					return
				# Session validated: now safe to adopt trace context from this message.
				_adopt_trace_context(msg)
				_on_action_result(msg)
			else:
				# This is an Action command from the agent service (result="pending" or missing)
				var identity_error := _validate_session_identity(msg)
				if identity_error != "":
					invalid_command_rejected.emit(String(msg.get("id", "")), identity_error)
					return
				# Session validated: now safe to adopt trace context.
				_adopt_trace_context(msg)
				_on_action_received(msg)
		"Intention":
			# Intention from agent service - treat as action command for touch/inspect
			var identity_error := _validate_session_identity(msg)
			if identity_error != "":
				invalid_command_rejected.emit(String(msg.get("id", "")), identity_error)
				return
			# Session validated: now safe to adopt trace context.
			_adopt_trace_context(msg)
			_on_action_received(msg)
		"Error":
			# Validate session before adopting trace context (especially for STALE_REVISION).
			var identity_error := _validate_session_identity(msg)
			if identity_error != "":
				invalid_command_rejected.emit(String(msg.get("id", "")), identity_error)
				return
			_adopt_trace_context(msg)
			_on_error(msg)
		"Observation":
			observation_ready.emit(msg)
		_:
			pass
	
	# Record inbound protocol metrics
	if _trace:
		var duration_sec = (Time.get_ticks_msec() - start_msec) / 1000.0
		var attrs = {
			"message.type": msg_type,
			"direction": "inbound",
			"outcome": "success",
		}
		_trace.record_counter("agent_world_protocol_message_total", 1, attrs, experiment_id, scenario_id, scenario_version, agent_id, _current_world_revision, _current_simulation_tick, _current_simulation_time)
		_trace.record_histogram("agent_world_protocol_round_trip_seconds", duration_sec, attrs, experiment_id, scenario_id, scenario_version, agent_id, _current_world_revision, _current_simulation_tick, _current_simulation_time)
	
	# Print correlation for demo verification
	if msg.has("correlation"):
		_log_verbose_message(msg)

func _adopt_trace_context(msg: Dictionary) -> void:
	# Safely adopt trace_id/span_id from a validated message's correlation.
	# Validates format before storing to avoid poisoning the session trace.
	var incoming_correlation = msg.get("correlation")
	if not incoming_correlation is Dictionary:
		return
	var incoming_trace_id = incoming_correlation.get("trace_id", "")
	var incoming_span_id = incoming_correlation.get("span_id", "")
	if incoming_trace_id != "" and _is_valid_hex_string(incoming_trace_id, 32):
		_trace_id = incoming_trace_id
	if incoming_span_id != "" and _is_valid_hex_string(incoming_span_id, 16):
		# span_id is not stored globally but used for outgoing spans
		pass

func _is_valid_hex_string(s: String, expected_length: int) -> bool:
	if s.length() != expected_length:
		return false
	for c in s:
		if not (c >= "0" and c <= "9") and not (c >= "a" and c <= "f") and not (c >= "A" and c <= "F"):
			return false
	return true

func _on_hello_ack(msg: Dictionary) -> void:
	var correlation = msg.get("correlation", {})
	_current_world_revision = correlation.get("world_revision", 0)
	_current_simulation_tick = correlation.get("simulation_tick", 0)
	_current_simulation_time = correlation.get("simulation_time", 0.0)
	
	# Send any queued messages
	pass

func _on_world_state(msg: Dictionary) -> void:
	var correlation = msg.get("correlation", {})
	_current_world_revision = correlation.get("world_revision", _current_world_revision)
	_current_simulation_tick = correlation.get("simulation_tick", _current_simulation_tick)
	_current_simulation_time = correlation.get("simulation_time", _current_simulation_time)

func _on_action_result(msg: Dictionary) -> void:
	var request_id = msg.get("id", "")
	if request_id in _pending_requests:
		_pending_requests.erase(request_id)
	action_result_received.emit(msg)

func _on_action_received(action: Dictionary) -> void:
	var request_id: String = String(action.get("id", ""))
	var validation_error := _validate_incoming_command(action)
	if validation_error != "":
		# Reply so the sender can clear or retry instead of waiting forever on
		# a command the world will never execute.
		if _websocket_client:
			_websocket_client.send_message({
				"type": "Error",
				"code": "INVALID_COMMAND",
				"message": validation_error,
				"request_id": request_id,
				"correlation": _make_correlation(),
			})
		invalid_command_rejected.emit(request_id, validation_error)
		return

	if request_id != "" and _received_commands.has(request_id):
		# A reconnect may resend a command already accepted by this world. Leave
		# an active command alone, or replay its terminal result if it completed.
		var received: Dictionary = _received_commands[request_id]
		if received.has("terminal_result"):
			send_action(received["terminal_result"])
		return

	# Check for stale request
	var request_revision = action.get("request_world_revision", 0)
	if request_revision < _current_world_revision - stale_threshold:
		# Send STALE_REVISION error
		var error_msg = {
			"type": "Error",
			"code": "STALE_REVISION",
			"message": "Request based on obsolete world revision %d, current is %d" % [request_revision, _current_world_revision],
			"request_id": action.get("id", ""),
			"current_revision": _current_world_revision,
			"correlation": _make_correlation()
		}
		if _websocket_client:
			_websocket_client.send_message(error_msg)
		print("ProtocolHandler: Rejected stale request %s (request_rev=%d, current_rev=%d)" % [action.get("id", ""), request_revision, _current_world_revision])
		stale_request_rejected.emit(action.get("id", ""), _current_world_revision)
		return
	
	if request_id != "":
		_received_commands[request_id] = {}
	# Emit signal for Room to handle - Room will call Agent.execute_action()
	print("ProtocolHandler: Received action/intention: %s" % [action])
	action_received.emit(action)

func _validate_incoming_command(message: Dictionary) -> String:
	var command_type = message.get("type", "")
	if command_type not in ["Action", "Intention"]:
		return "Unsupported command type"
	var identity_error := _validate_session_identity(message)
	if identity_error != "":
		return identity_error

	var request_revision = _normalize_world_revision(message.get("request_world_revision"))
	var correlation = message.get("correlation")
	var correlation_revision = _normalize_world_revision(correlation.get("world_revision"))
	if request_revision < 0 or correlation_revision != request_revision:
		return "Command world revision is invalid or inconsistent"
	var kind_field = "action_type_id" if command_type == "Action" else "intention_type_id"
	var timestamp = message.get("timestamp_s")
	if message.get("id", "") == "" or message.get("version", "") == "" \
			or message.get(kind_field, "") == "":
		return "Command identity, version, or kind is missing"
	if (not timestamp is int and not timestamp is float) or timestamp < 0:
		return "Command timestamp is invalid"
	return ""

func _validate_session_identity(message: Dictionary) -> String:
	# Shared by commands and terminal results: a message may only mutate this
	# session's request state when every identity field matches.
	if message.get("run_id", "") != run_id or message.get("agent_id", "") != agent_id:
		return "Message run_id or agent_id does not match this session"

	var correlation = message.get("correlation")
	if not correlation is Dictionary:
		return "Message correlation context is missing"
	if correlation.get("experiment_id", "") != experiment_id \
			or correlation.get("scenario_id", "") != scenario_id \
			or correlation.get("scenario_version", "") != scenario_version \
			or correlation.get("run_id", "") != run_id \
			or correlation.get("agent_id", "") != agent_id:
		return "Message correlation context does not match this session"
	if not correlation.has_all(["world_revision", "simulation_tick", "simulation_time", "component"]):
		return "Message correlation context is incomplete"
	return ""

func _normalize_world_revision(value: Variant) -> int:
	if (not value is int and not value is float) or value < 0 or floor(value) != value:
		return -1
	return int(value)

func _on_error(msg: Dictionary) -> void:
	var code = msg.get("code", "")
	if code == "STALE_REVISION":
		var request_id = msg.get("request_id", "")
		var current_rev = msg.get("current_revision", _current_world_revision)
		stale_request_rejected.emit(request_id, current_rev)
		if request_id in _pending_requests:
			_pending_requests.erase(request_id)

# Called by Room each physics tick
func tick_world_state(world_revision: int, simulation_tick: int, simulation_time: float, agent_dict: Dictionary, nearby_objects: Array) -> void:
	_current_world_revision = world_revision
	_current_simulation_tick = simulation_tick
	_current_simulation_time = simulation_time
	
	_tick_counter += 1
	if _tick_counter >= world_state_interval_ticks:
		_tick_counter = 0
		_send_world_state(agent_dict, nearby_objects)

func _send_world_state(agent_dict: Dictionary, nearby_objects: Array) -> void:
	if not _websocket_client:
		return
		
	# Trace: world.perception.collect (collecting nearby objects, agent state)
	var collect_span = _trace.start_span(
		"world.perception.collect",
		{},
		_trace.bounded_attributes(
			experiment_id, scenario_id, scenario_version, agent_id,
			_current_world_revision, _current_simulation_tick,
			_current_simulation_time, "world", "1.0.0",
		),
	)
	
	var correlation = _make_correlation()
	
	# Trace: world.observation.publish (publishing WorldState)
	var publish_span = _trace.start_span(
		"world.observation.publish",
		{},
		_trace.bounded_attributes(
			experiment_id, scenario_id, scenario_version, agent_id,
			_current_world_revision, _current_simulation_tick,
			_current_simulation_time, "world", "1.0.0",
		),
	)
	
	# Update correlation with the publish span's trace context
	correlation["trace_id"] = publish_span.get("trace_id", "")
	correlation["span_id"] = publish_span.get("span_id", "")
	
	var state = {
		"type": "WorldState",
		"world_revision": _current_world_revision,
		"simulation_tick": _current_simulation_tick,
		"simulation_time": _current_simulation_time,
		"agent_id": agent_id,
		"agent_position": agent_dict.get("position", {"x": 0, "y": 0, "z": 0}),
		"agent_heading_radians": agent_dict.get("heading_radians", 0.0),
		"nearby_objects": nearby_objects,
		"correlation": correlation,
	}
	_websocket_client.send_message(state)
	_log_verbose_message(state)
	
	# Record outbound WorldState protocol metrics
	if _trace:
		var attrs = {
			"message.type": "WorldState",
			"direction": "outbound",
			"outcome": "success",
		}
		_trace.record_counter("agent_world_protocol_message_total", 1, attrs, experiment_id, scenario_id, scenario_version, agent_id, _current_world_revision, _current_simulation_tick, _current_simulation_time)
		_trace.record_histogram("agent_world_protocol_message_size_bytes", len(JSON.stringify(state)), attrs, experiment_id, scenario_id, scenario_version, agent_id, _current_world_revision, _current_simulation_tick, _current_simulation_time)
	
	_trace.end_span(collect_span)
	_trace.end_span(publish_span)

func send_observation(observation: Dictionary) -> void:
	var msg = observation.duplicate()
	# Start the publish span BEFORE creating correlation, so the span ID
	# matches the outgoing message's correlation.
	var span = _trace.start_span(
		"world.observation.publish",
		{},
		_trace.bounded_attributes(
			experiment_id, scenario_id, scenario_version, agent_id,
			_current_world_revision, _current_simulation_tick,
			_current_simulation_time, "world", "1.0.0",
		),
	)
	var correlation = _make_correlation()
	correlation["trace_id"] = span.get("trace_id", "")
	correlation["span_id"] = span.get("span_id", "")
	msg["correlation"] = correlation
	_websocket_client.send_message(msg)
	observation_ready.emit(msg)
	
	# Record outbound Observation protocol metrics
	if _trace:
		var attrs = {
			"message.type": "Observation",
			"direction": "outbound",
			"outcome": "success",
		}
		_trace.record_counter("agent_world_protocol_message_total", 1, attrs, experiment_id, scenario_id, scenario_version, agent_id, _current_world_revision, _current_simulation_tick, _current_simulation_time)
		_trace.record_histogram("agent_world_protocol_message_size_bytes", len(JSON.stringify(msg)), attrs, experiment_id, scenario_id, scenario_version, agent_id, _current_world_revision, _current_simulation_tick, _current_simulation_time)
	
	_trace.end_span(span)

func send_intention(intention: Dictionary) -> void:
	var msg = intention.duplicate()
	# Start the action execute span BEFORE creating correlation.
	var span = _trace.start_span(
		"world.action.execute",
		{},
		_trace.bounded_attributes(
			experiment_id, scenario_id, scenario_version, agent_id,
			_current_world_revision, _current_simulation_tick,
			_current_simulation_time, "world", "1.0.0",
		),
	)
	var correlation = _make_correlation()
	correlation["trace_id"] = span.get("trace_id", "")
	correlation["span_id"] = span.get("span_id", "")
	msg["correlation"] = correlation
	msg["request_world_revision"] = _current_world_revision
	_pending_requests[msg["id"]] = {"type": "intention", "correlation": correlation, "timestamp": Time.get_ticks_msec() / 1000.0}
	_websocket_client.send_message(msg)
	intention_sent.emit(msg)
	_log_verbose_message(msg)
	
	# Record outbound Intention protocol metrics
	if _trace:
		var attrs = {
			"message.type": "Intention",
			"direction": "outbound",
			"outcome": "success",
		}
		_trace.record_counter("agent_world_protocol_message_total", 1, attrs, experiment_id, scenario_id, scenario_version, agent_id, _current_world_revision, _current_simulation_tick, _current_simulation_time)
		_trace.record_histogram("agent_world_protocol_message_size_bytes", len(JSON.stringify(msg)), attrs, experiment_id, scenario_id, scenario_version, agent_id, _current_world_revision, _current_simulation_tick, _current_simulation_time)
	
	_trace.end_span(span)

func send_action(action: Dictionary) -> void:
	var msg = action.duplicate()
	# Start the action execute span BEFORE creating correlation.
	var span = _trace.start_span(
		"world.action.execute",
		{},
		_trace.bounded_attributes(
			experiment_id, scenario_id, scenario_version, agent_id,
			_current_world_revision, _current_simulation_tick,
			_current_simulation_time, "world", "1.0.0",
		),
	)
	var correlation = _make_correlation()
	correlation["trace_id"] = span.get("trace_id", "")
	correlation["span_id"] = span.get("span_id", "")
	msg["correlation"] = correlation
	msg["request_world_revision"] = _current_world_revision
	_pending_requests[msg["id"]] = {"type": "action", "correlation": correlation, "timestamp": Time.get_ticks_msec() / 1000.0}
	if _received_commands.has(msg["id"]) and msg.get("result", "") != "pending":
		_received_commands[msg["id"]]["terminal_result"] = msg.duplicate(true)
	_websocket_client.send_message(msg)
	
	# Record outbound Action protocol metrics
	if _trace:
		var attrs = {
			"message.type": "Action",
			"direction": "outbound",
			"outcome": "success",
		}
		_trace.record_counter("agent_world_protocol_message_total", 1, attrs, experiment_id, scenario_id, scenario_version, agent_id, _current_world_revision, _current_simulation_tick, _current_simulation_time)
		_trace.record_histogram("agent_world_protocol_message_size_bytes", len(JSON.stringify(msg)), attrs, experiment_id, scenario_id, scenario_version, agent_id, _current_world_revision, _current_simulation_tick, _current_simulation_time)
	
	_trace.end_span(span)
	_log_verbose_message(msg)

# Send a terminal action result using an existing execution span's trace context.
# This keeps the physical outcome and its publication in the same trace.
func send_terminal_result(action: Dictionary, parent_span: Dictionary = {}) -> void:
	var msg = action.duplicate()
	var correlation = _make_correlation()
	if parent_span:
		correlation["trace_id"] = parent_span.get("trace_id", "")
		correlation["span_id"] = parent_span.get("span_id", "")
	else:
		# Fallback: create a new span if no parent provided (should not happen in normal flow)
		var fallback_span = _trace.start_span(
			"world.action.execute",
			{},
			_trace.bounded_attributes(
				experiment_id, scenario_id, scenario_version, agent_id,
				_current_world_revision, _current_simulation_tick,
				_current_simulation_time, "world", "1.0.0",
			),
		)
		correlation["trace_id"] = fallback_span.get("trace_id", "")
		correlation["span_id"] = fallback_span.get("span_id", "")
		_trace.end_span(fallback_span)
	msg["correlation"] = correlation
	msg["request_world_revision"] = _current_world_revision
	_websocket_client.send_message(msg)
	_log_verbose_message(msg)
	
	# Record outbound terminal Action protocol metrics
	if _trace:
		var attrs = {
			"message.type": "Action",
			"direction": "outbound",
			"outcome": "success",
		}
		_trace.record_counter("agent_world_protocol_message_total", 1, attrs, experiment_id, scenario_id, scenario_version, agent_id, _current_world_revision, _current_simulation_tick, _current_simulation_time)
		_trace.record_histogram("agent_world_protocol_message_size_bytes", len(JSON.stringify(msg)), attrs, experiment_id, scenario_id, scenario_version, agent_id, _current_world_revision, _current_simulation_tick, _current_simulation_time)

func _make_correlation() -> Dictionary:
	# Resolve lazily as well as in set_websocket_client(), because sibling node
	# _ready() order can expose the client before its trace ID is initialized.
	if _trace_id == "" and _websocket_client and _websocket_client.has_method("get_trace_id"):
		_trace_id = _websocket_client.get_trace_id()
	if _trace_id == "":
		_trace_id = _trace.get_trace_id()
	return {
		"experiment_id": experiment_id,
		"scenario_id": scenario_id,
		"scenario_version": scenario_version,
		"run_id": run_id,
		"agent_id": agent_id,
		"world_revision": _current_world_revision,
		"simulation_tick": _current_simulation_tick,
		"simulation_time": _current_simulation_time,
		"trace_id": _trace_id,
		"span_id": Crypto.new().generate_random_bytes(8).hex_encode(),
		"component": "world",
		"component_version": "1.0.0",
	}

# Build and send a HealthStatus message per health_status.schema.json
func build_health_status() -> Dictionary:
	var physics_healthy = _trace != null && _current_simulation_tick > 0
	var recorder_healthy = true  # EventRecorder doesn't expose failure state yet
	var telemetry_healthy = _trace != null
	
	var components = {
		"physics": {
			"status": "healthy" if physics_healthy else "degraded",
			"advancing": physics_healthy,
			"tick_overrun_count": 0,
			"active_body_count": 0,
			"contact_count": 0,
		},
		"recorder": {
			"status": "healthy" if recorder_healthy else "degraded",
			"writable": recorder_healthy,
			"pending_events": 0,
		},
		"telemetry_exporter": {
			"status": "healthy" if telemetry_healthy else "degraded",
			"last_export_timestamp": Time.get_unix_time_from_system() if telemetry_healthy else 0,
		},
		"artifact_store": {
			"status": "healthy",
			"writable": true,
		},
		"evaluator": {
			"status": "healthy",
			"scenario_loaded": true,
		},
	}
	
	# Overall status
	var overall = "healthy"
	for comp in components.values():
		if comp.status == "failed":
			overall = "failed"
			break
		elif comp.status == "degraded" and overall == "healthy":
			overall = "degraded"
	
	return {
		"type": "HealthStatus",
		"run_id": run_id,
		"timestamp_s": _current_simulation_time,
		"version": "1.0.0",
		"overall": overall,
		"components": components,
	}

func send_health_status() -> void:
	var msg = build_health_status()
	if _websocket_client:
		_websocket_client.send_message(msg)
		_log_verbose_message(msg)
	health_status_ready.emit(msg)
