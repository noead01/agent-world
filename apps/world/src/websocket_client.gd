extends Node

class_name WebSocketClient

signal connected(server_id: String)
signal disconnected(reason: String)
signal message_received(message: Dictionary)
signal error(code: String, message: String)

enum ConnectionState { DISCONNECTED, CONNECTING, CONNECTED, RECONNECTING }

@export var url: String = "ws://localhost:8765"
@export var reconnect_max_attempts: int = 10
@export var heartbeat_interval_s: float = 5.0

var _peer: WebSocketPeer
var _state: ConnectionState = ConnectionState.DISCONNECTED
var _reconnect_attempt: int = 0
var _heartbeat_timer: float = 0.0
var _last_pong: float = 0.0
var _pending_messages: Array[Dictionary] = []
var _request_id_counter: int = 0

func _ready() -> void:
	_peer = WebSocketPeer.new()
	set_process(true)
	set_physics_process(false)

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
				_heartbeat_timer = 0.0
				_last_pong = Time.get_ticks_msec() / 1000.0
				_send_hello()
			elif _peer.get_ready_state() == WebSocketPeer.STATE_CLOSED:
				_on_disconnected("Connection closed during handshake")
				
		ConnectionState.CONNECTED:
			_heartbeat_timer += delta
			if _heartbeat_timer >= heartbeat_interval_s:
				_send_heartbeat()
				_heartbeat_timer = 0.0
				
			# Check for missed pongs (3 intervals = 15s)
			var now = Time.get_ticks_msec() / 1000.0
			if now - _last_pong > heartbeat_interval_s * 3:
				_on_disconnected("Heartbeat timeout")
				
		ConnectionState.RECONNECTING:
			# Reconnection handled by _schedule_reconnect
			pass

func _send_hello() -> void:
	var hello = {
		"type": "Hello",
		"protocol_version": "1.0.0",
		"agent_id": "wanderer_01",  # Will be overridden by ProtocolHandler
		"run_id": "run_001",
		"capabilities": ["observation", "intention", "action"],
		"reconnect": _reconnect_attempt > 0,
		"correlation": {
			"experiment_id": "exp_autonomous_discovery_01",
			"scenario_id": "first_benchmark_room",
			"scenario_version": "1.0.0",
			"run_id": "run_001",
			"agent_id": "wanderer_01",
			"world_revision": 0,
			"simulation_tick": 0,
			"simulation_time": 0.0,
			"component": "world",
			"component_version": "1.0.0"
		}
	}
	_send(hello)

func _send_heartbeat() -> void:
	var hb = {"type": "Heartbeat", "timestamp_s": Time.get_ticks_msec() / 1000.0}
	_send(hb)

func _handle_incoming(msg: Dictionary) -> void:
	var msg_type = msg.get("type", "")
	match msg_type:
		"HelloAck":
			connected.emit(msg.get("server_id", "unknown"))
		"Heartbeat":
			_last_pong = Time.get_ticks_msec() / 1000.0
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
	if _state == ConnectionState.DISCONNECTED:
		_state = ConnectionState.RECONNECTING
		connect_to_server()

func connect_to_server() -> void:
	if _state != ConnectionState.DISCONNECTED:
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

func close() -> void:
	if _peer:
		_peer.close()
	_peer = null
	_state = ConnectionState.DISCONNECTED