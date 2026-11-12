extends Node

class_name ProtocolHandler

signal observation_ready(observation: Dictionary)
signal intention_sent(intention: Dictionary)
signal action_received(action: Dictionary)
signal action_result_received(result: Dictionary)
signal stale_request_rejected(request_id: String, current_revision: int)

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

func _ready() -> void:
	# Only auto-discover WebSocketClient if not already set via set_websocket_client
	if _websocket_client == null and has_node("../WebSocketClient"):
		set_websocket_client(get_node("../WebSocketClient"))

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
				# This is an ActionResult response to an action we sent
				_on_action_result(msg)
			else:
				# This is an Action command from the agent service (result="pending" or missing)
				_on_action_received(msg)
		"Intention":
			# Intention from agent service - treat as action command for touch/inspect
			_on_action_received(msg)
		"Error":
			_on_error(msg)
		"Observation":
			observation_ready.emit(msg)
		_:
			pass
	
	# Print correlation for demo verification
	if msg.has("correlation"):
		var corr = msg["correlation"]
		print("MSG_JSON: %s" % [JSON.stringify(msg)])

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
		
	var correlation = _make_correlation()
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
	print("MSG_JSON: %s" % [JSON.stringify(state)])

func send_observation(observation: Dictionary) -> void:
	var msg = observation.duplicate()
	msg["correlation"] = _make_correlation()
	_websocket_client.send_message(msg)
	observation_ready.emit(msg)

func send_intention(intention: Dictionary) -> void:
	var msg = intention.duplicate()
	var correlation = _make_correlation()
	msg["correlation"] = correlation
	msg["request_world_revision"] = _current_world_revision
	_pending_requests[msg["id"]] = {"type": "intention", "correlation": correlation, "timestamp": Time.get_ticks_msec() / 1000.0}
	_websocket_client.send_message(msg)
	intention_sent.emit(msg)
	print("MSG_JSON: %s" % [JSON.stringify(msg)])

func send_action(action: Dictionary) -> void:
	var msg = action.duplicate()
	var correlation = _make_correlation()
	msg["correlation"] = correlation
	msg["request_world_revision"] = _current_world_revision
	_pending_requests[msg["id"]] = {"type": "action", "correlation": correlation, "timestamp": Time.get_ticks_msec() / 1000.0}
	if _received_commands.has(msg["id"]) and msg.get("result", "") != "pending":
		_received_commands[msg["id"]]["terminal_result"] = msg.duplicate(true)
	_websocket_client.send_message(msg)
	print("MSG_JSON: %s" % [JSON.stringify(msg)])

func _make_correlation() -> Dictionary:
	# Resolve lazily as well as in set_websocket_client(), because sibling node
	# _ready() order can expose the client before its trace ID is initialized.
	if _trace_id == "" and _websocket_client and _websocket_client.has_method("get_trace_id"):
		_trace_id = _websocket_client.get_trace_id()
	if _trace_id == "":
		_trace_id = Crypto.new().generate_random_bytes(16).hex_encode()
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
