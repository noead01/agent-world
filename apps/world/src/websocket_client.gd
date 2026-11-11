extends Node

class_name WebSocketClient

signal connected(server_id: String)
signal disconnected(reason: String)
signal message_received(message: Dictionary)
signal error(code: String, message: String)

enum ConnectionState { DISCONNECTED, CONNECTING, CONNECTED, RECONNECTING }

@export var url: String = "ws://localhost:8765"
@export var reconnect_max_attempts: int = 10
@export var ping_interval_s: float = 5.0
@export var max_unanswered_pings: int = 3

# Configurable fields for Hello message
var _hello_run_id: String = "run_001"
var _hello_agent_id: String = "wanderer_01"
var _hello_experiment_id: String = "exp_autonomous_discovery_01"
var _hello_scenario_id: String = "first_benchmark_room"
var _hello_scenario_version: String = "1.0.0"

var _peer: WebSocketPeer
var _state: ConnectionState = ConnectionState.DISCONNECTED
var _reconnect_attempt: int = 0
var _ping_timer: float = 0.0
var _pending_messages: Array[Dictionary] = []
var _request_id_counter: int = 0

func _ready() -> void:
	_peer = WebSocketPeer.new()
	set_process(true)
	set_physics_process(false)

func configure_hello(run_id: String, agent_id: String, experiment_id: String = "", scenario_id: String = "", scenario_version: String = "") -> void:
	_hello_run_id = run_id
	_hello_agent_id = agent_id
	if experiment_id != "":
		_hello_experiment_id = experiment_id
	if scenario_id != "":
		_hello_scenario_id = scenario_id
	if scenario_version != "":
		_hello_scenario_version = scenario_version

func _process(delta: float) -> void:
	if _peer == null:
		return
	
	_peer.poll()
	
	# Handle incoming messages
	while _peer.get_available_packet_count() > 0:
		var packet = _peer.get_packet()
		if packet:
			var text = packet.get_string_from_utf8()
			var parse_result = JSON.parse_string(text)
			# In Godot 4, parse_string returns the parsed value on success, or Error code on failure
			if parse_result is Dictionary or parse_result is Array:
				var msg = parse_result
				message_received.emit(msg)
				_handle_incoming(msg)
			else:
				print("WebSocketClient: JSON parse error: %s" % [parse_result])
	
	# Connection state machine
	match _state:
		ConnectionState.CONNECTING:
			if _peer.get_ready_state() == WebSocketPeer.STATE_OPEN:
				_state = ConnectionState.CONNECTED
				_reconnect_attempt = 0
				_ping_timer = 0.0
				_send_hello()
			elif _peer.get_ready_state() == WebSocketPeer.STATE_CLOSED:
				_on_disconnected("Connection closed during handshake")
				
		ConnectionState.CONNECTED:
			# Detect closed peers while connected
			if _peer.get_ready_state() == WebSocketPeer.STATE_CLOSED:
				_on_disconnected("Peer closed unexpectedly")
				break
			
			_ping_timer += delta
			if _ping_timer >= ping_interval_s:
				_send_ping()
				_ping_timer = 0.0
			
			# Check for missed pongs using WebSocket peer's built-in tracking
			var unanswered = _peer.get_pending_pings()
			if unanswered > max_unanswered_pings:
				_on_disconnected("Ping timeout: %d unanswered pings" % [unanswered])
				
		ConnectionState.RECONNECTING:
			# Reconnection handled by _schedule_reconnect
			pass

func _send_hello() -> void:
	var hello = {
		"type": "Hello",
		"protocol_version": "1.0.0",
		"agent_id": _hello_agent_id,
		"run_id": _hello_run_id,
		"capabilities": ["observation", "intention", "action"],
		"reconnect": _reconnect_attempt > 0,
		"correlation": {
			"experiment_id": _hello_experiment_id,
			"scenario_id": _hello_scenario_id,
			"scenario_version": _hello_scenario_version,
			"run_id": _hello_run_id,
			"agent_id": _hello_agent_id,
			"world_revision": 0,
			"simulation_tick": 0,
			"simulation_time": 0.0,
			"component": "world",
			"component_version": "1.0.0"
		}
	}
	_send(hello)
	print("MSG_JSON: %s" % [JSON.stringify(hello)])

func _send_ping() -> void:
	if _peer and _peer.get_ready_state() == WebSocketPeer.STATE_OPEN:
		_peer.send_ping()

func _handle_incoming(msg: Dictionary) -> void:
	var msg_type = msg.get("type", "")
	match msg_type:
		"HelloAck":
			connected.emit(msg.get("server_id", "unknown"))
		"Error":
			error.emit(msg.get("code", "UNKNOWN"), msg.get("message", ""))
		"Goodbye":
			_on_disconnected(msg.get("reason", "Server closed"))
		_:
			# Forward to ProtocolHandler for other types
			pass

func _on_disconnected(reason: String) -> void:
	_state = ConnectionState.DISCONNECTED
	disconnected.emit(reason)
	_schedule_reconnect()

func _schedule_reconnect() -> void:
	if _reconnect_attempt >= reconnect_max_attempts:
		error.emit("MAX_RECONNECT_ATTEMPTS", "Max reconnection attempts reached")
		return
	
	var delay = min(pow(2, _reconnect_attempt), 30.0)  # 1, 2, 4, 8, 16, 30...
	call_deferred("_do_reconnect", delay)
	_reconnect_attempt += 1

func _do_reconnect(delay: float) -> void:
	await get_tree().create_timer(delay).timeout
	# Always attempt reconnection if still disconnected
	if _state == ConnectionState.DISCONNECTED:
		connect_to_server()

func connect_to_server() -> void:
	if _state != ConnectionState.DISCONNECTED and _state != ConnectionState.RECONNECTING:
		return
	_state = ConnectionState.CONNECTING
	var err = _peer.connect_to_url(url)
	if err != OK:
		_on_disconnected("Failed to connect: %s" % [err])

func send_message(message: Dictionary) -> void:
	if _state != ConnectionState.CONNECTED:
		_pending_messages.append(message)
		return
	_send(message)

func _send(message: Dictionary) -> void:
	if _peer == null or _peer.get_ready_state() != WebSocketPeer.STATE_OPEN:
		return
	var text = JSON.stringify(message)
	var err = _peer.send_text(text)
	if err != OK:
		print("WebSocketClient: send failed: %s" % [err])
	print("MSG_JSON: %s" % [text])

func close() -> void:
	if _peer:
		_peer.close()
	_peer = null
	_state = ConnectionState.DISCONNECTED
