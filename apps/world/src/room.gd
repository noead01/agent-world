extends Node3D
class_name Room

signal object_landed(instance_id: String)
signal object_collided(instance_id: String, other_id: String)
signal object_impulse_applied(instance_id: String, impulse: Vector3)
signal simulation_paused()
signal simulation_resumed()
signal simulation_time_scale_changed(time_scale: float)
signal simulation_reset()
signal observation_ready(msg: Dictionary)

# Configuration loaded from world_config.json
var _config_loader = preload("res://src/config_loader.gd")

# Room bounds (from config, with @export for editor override)
@export_group("Room Bounds")
@export var half_size: Vector3 = Vector3(13.5, 13.5, 13.5)

@export_group("Physics")
@export var gravity: Vector3 = Vector3(0, -9.8, 0)
@export var fixed_timestep_hz: float = 60.0

# Protocol timing controls (from config, with @export for editor override)
@export_group("Protocol")
@export var stale_threshold: int = 5
@export var world_state_interval_ticks: int = 5

# Experiment identification (from config, with @export for editor override)
@export_group("Experiment")
@export var experiment_id: String = "exp_autonomous_discovery_01"
@export var scenario_id: String = "first_benchmark_room"
@export var scenario_version: String = "1.0.0"

var objects: Array = []
var _sim_time_template = preload("res://src/simulation_time.gd")
var _trace_template = preload("res://src/trace.gd")
var _sim_time
var _sim_day_cycle_duration_s: float = 240.0  # Stored from config, applied after _sim_time creation
var _light: DirectionalLight3D
var _last_light_hour: float = -1.0

var _cumulative_run_time: float = 0.0  # Tracks total run time across simulation resets
var _world_revision: int = 0  # Monotonic across simulation resets (unlike simulation_tick)
var _trace

# Agent service policy constants (from config, for fingerprint)
var _agent_service_policy_version: String = "2"
var _agent_service_action_delay_ticks: int = 12
var _agent_service_action_cooldown_ticks: int = 30
var _agent_service_action_delay_probability: float = 0.5
var _agent_service_target_ids: Array = ["obj_wood_cube", "obj_metal_sphere", "obj_glass_box", "obj_rubber_cylinder"]
var _agent_service_interrupt_target_ids: Array = ["obj_wood_cube"]

# Drive policy constants (from config, for fingerprint)
var _drive_policy_version: String = "1"
var _drive_curiosity_explore_threshold: float = 0.7
var _drive_uncertainty_investigate_threshold: float = 0.6
var _drive_integrity_safety_threshold: float = 0.3
var _drive_initial_curiosity: float = 0.5
var _drive_initial_uncertainty: float = 0.5
var _drive_initial_integrity: float = 1.0
var _drive_curiosity_novel_boost: float = 0.15
var _drive_curiosity_moved_boost: float = 0.05
var _drive_curiosity_decay_rate: float = 0.01
var _drive_uncertainty_high_error_boost: float = 0.1
var _drive_uncertainty_medium_error_boost: float = 0.03
var _drive_uncertainty_good_prediction_decay: float = 0.005
var _drive_uncertainty_unexpected_movement_boost: float = 0.05
var _drive_uncertainty_decay_rate: float = 0.005
var _drive_integrity_collision_penalty: float = 0.005
var _drive_integrity_recovery_rate: float = 0.002
var _drive_integrity_collision_distance: float = 0.5
var _drive_prediction_error_high: float = 0.04
var _drive_prediction_error_medium: float = 0.01
var _drive_unexpected_movement_threshold: float = 0.25

var _agent
var _ws_client
var _protocol_handler
var _agent_template = preload("res://src/agent.gd")
var _ws_client_template = preload("res://src/websocket_client.gd")
var _protocol_handler_template = preload("res://src/protocol_handler.gd")
var _event_recorder_template = preload("res://src/event_recorder.gd")
var _mock_controller_template = preload("res://src/mock_controller.gd")
var _event_recorder
var _active_action_context: Dictionary = {}
var _active_action_spans: Dictionary = {}  # command_id -> span
var _agent_session_established: bool = false
var _agent_session_connected: bool = false
var _use_local_mock: bool = false
var _mock_controller

# Health status emission
var _health_timer: float = 0.0
var _health_interval_s: float = 5.0

# Metrics emission (gate to avoid per-tick spam)
var _metrics_timer: float = 0.0
var _metrics_interval_s: float = 1.0  # Emit metrics once per second of wall time

# Verbose logging flag
var _verbose_logging: bool = false

# Demo timing variables (used by _process_demo in subclasses)
var _demo_timer: float = 0.0
var _demo_duration: float = 10.0
var _demo_pause_time: float = 2.0
var _demo_resume_time: float = 4.0
var _demo_scale_time: float = 6.0
var _demo_reset_time: float = 8.0
var _demo_scale_factor: float = 2.0
var _demo_impulse_time: float = 1.0
var _demo_impulse_target_id: String = "obj_metal_sphere"
var _demo_impulse_vector: Vector3 = Vector3(2.0, 0.0, 0.0)
var _demo_step: int = 0
var _impulse_applied: bool = false
var _last_print_time: float = 0.0
var _landed_count: int = 0

func _ready() -> void:
	# Load configuration from JSON file
	_config_loader.load_config()
	_load_config_values()
	
	_verbose_logging = OS.get_environment("AGENT_WORLD_VERBOSE_LOGS") == "1"
	# Configure project physics settings for Jolt fixed timestep
	ProjectSettings.set_setting("physics/3d/physics_engine", "JoltPhysics")
	ProjectSettings.set_setting("physics/common/physics_fps", fixed_timestep_hz)
	# Set gravity at runtime via PhysicsServer3D (project.godot's default_gravity
	# may be overridden by physics_engine selection at startup)
	var space: RID = get_world_3d().space
	PhysicsServer3D.space_set_param(space, 0, gravity.y)
	# Set sleep thresholds so objects settle faster and stop jittering
	# SPACE_PARAM_BODY_LINEAR_VELOCITY_SLEEP_THRESHOLD = 4
	PhysicsServer3D.space_set_param(space, PhysicsServer3D.SPACE_PARAM_BODY_LINEAR_VELOCITY_SLEEP_THRESHOLD, 0.01)
	# SPACE_PARAM_BODY_ANGULAR_VELOCITY_SLEEP_THRESHOLD = 5
	PhysicsServer3D.space_set_param(space, PhysicsServer3D.SPACE_PARAM_BODY_ANGULAR_VELOCITY_SLEEP_THRESHOLD, 0.01)
	# SPACE_PARAM_BODY_TIME_TO_SLEEP = 6 (seconds before sleep)
	PhysicsServer3D.space_set_param(space, PhysicsServer3D.SPACE_PARAM_BODY_TIME_TO_SLEEP, 0.1)
	# Increase solver iterations for better constraint resolution (default ~8-10)
	# SPACE_PARAM_SOLVER_ITERATIONS = 7
	PhysicsServer3D.space_set_param(space, PhysicsServer3D.SPACE_PARAM_SOLVER_ITERATIONS, 20)
	# Tune contact parameters for stability with small/stacked bodies
	# SPACE_PARAM_CONTACT_RECYCLE_RADIUS = 0
	PhysicsServer3D.space_set_param(space, PhysicsServer3D.SPACE_PARAM_CONTACT_RECYCLE_RADIUS, 0.05)
	# SPACE_PARAM_CONTACT_MAX_SEPARATION = 1
	PhysicsServer3D.space_set_param(space, PhysicsServer3D.SPACE_PARAM_CONTACT_MAX_SEPARATION, 0.02)
	# SPACE_PARAM_CONTACT_MAX_ALLOWED_PENETRATION = 2
	PhysicsServer3D.space_set_param(space, PhysicsServer3D.SPACE_PARAM_CONTACT_MAX_ALLOWED_PENETRATION, 0.01)
	# SPACE_PARAM_CONTACT_DEFAULT_BIAS = 3 (bias to correct penetration)
	PhysicsServer3D.space_set_param(space, PhysicsServer3D.SPACE_PARAM_CONTACT_DEFAULT_BIAS, 0.3)

	_build_room_boundaries()
	_spawn_objects()

	# Create and configure SimulationTime
	_sim_time = _sim_time_template.new()
	add_child(_sim_time)
	_sim_time.time_of_day_changed.connect(_animate_day_night)
	# Apply stored simulation config (day_cycle_duration_s from config file)
	_sim_time.day_cycle_duration_s = _sim_day_cycle_duration_s

	# Find the directional light for day/night animation
	_light = get_node_or_null("DirectionalLight3D")

	# Spawn the embodied agent (must be before EventRecorder start_run to have agent_id)
	_spawn_agent()

	# Generate high-precision run_id using timestamp + milliseconds + random component
	var timestamp_sec = Time.get_unix_time_from_system()
	var timestamp_msec = Time.get_ticks_msec()
	var random_component = randi() % 10000
	var run_id = "run_%d_%03d_%04d" % [timestamp_sec, timestamp_msec % 1000, random_component]

	# Derive random_seed from run_id for reproducibility
	var random_seed = hash(run_id) & 0x7FFFFFFF
	var config_fingerprint = _compute_config_fingerprint()
	if config_fingerprint == "":
		push_error("Room: Failed to compute configuration fingerprint")
		get_tree().quit()
		return

	# Check if local mock mode is enabled (for testing without agent service)
	_use_local_mock = OS.get_environment("AGENT_WORLD_LOCAL_MODE") == "1"
	
	if _use_local_mock:
		print("AGENT_WORLD_LOCAL_MODE=1: Using local MockController")
		_setup_local_mock_controller(run_id, random_seed)
		# Mark session as established/connected for local mock mode
		_agent_session_established = true
		_agent_session_connected = true
	else:
		# Create WebSocketClient for agent service communication
		var ws_client = _ws_client_template.new()
		# Allow overriding agent service URL via environment variable for testing
		var agent_service_url = OS.get_environment("AGENT_SERVICE_URL")
		if agent_service_url == "":
			agent_service_url = "ws://localhost:8765"
		ws_client.url = agent_service_url
		ws_client.configure_hello(run_id, _agent.agent_id, _agent.agent_type_id)
		# WebSocketClient signals: connected, disconnected, message_received, error
		ws_client.connected.connect(_on_hello_ack)
		ws_client.message_received.connect(_on_message_received)
		ws_client.error.connect(_on_connection_failed)
		ws_client.disconnected.connect(_on_disconnected)
		add_child(ws_client)
		_ws_client = ws_client
		
		# Create ProtocolHandler for message serialization/deserialization
		var protocol_handler = _protocol_handler_template.new()
		protocol_handler.experiment_id = experiment_id
		protocol_handler.scenario_id = scenario_id
		protocol_handler.scenario_version = scenario_version
		protocol_handler.agent_id = _agent.agent_id
		protocol_handler.stale_threshold = stale_threshold
		protocol_handler.world_state_interval_ticks = world_state_interval_ticks
		protocol_handler.set_websocket_client(ws_client)
		protocol_handler.observation_ready.connect(_send_observation)
		protocol_handler.intention_sent.connect(_send_intention)
		protocol_handler.action_received.connect(_send_action)
		# Note: action_result_received and stale_request_rejected are handled
		# by _on_message_received routing to protocol_handler
		add_child(protocol_handler)
		_protocol_handler = protocol_handler
		
		# Start 3-second connection timeout for fallback to local mock
		# (handled by WebSocketClient internally)

	# Create and configure EventRecorder
	_event_recorder = _event_recorder_template.new()
	add_child(_event_recorder)
	_event_recorder.run_failed.connect(_on_run_failed)

	# Start recording
	var success = _event_recorder.start_run(
		run_id,
		"first_benchmark_room",
		_agent.agent_id,
		random_seed,
		config_fingerprint
	)
	if not success:
		print("ERROR: Failed to start event recorder")
		set_process(false)
		set_physics_process(false)
		get_tree().quit()
		return
	else:
		# Update ProtocolHandler with the run_id
		if _protocol_handler:
			_protocol_handler.run_id = run_id
		# Persist the initial run boundary before any other activity so the
		# authoritative timeline can reconstruct its starting conditions.
		var initial_objects: Array = []
		for obj in objects:
			var meta: Dictionary = obj.get_metadata()
			var p: Vector3 = obj.position
			initial_objects.append({
				"instance_id": meta["instance_id"],
				"type_id": meta.get("type_id", "unknown"),
				"position": {"x": p.x, "y": p.y, "z": p.z},
				"sleeping": obj.is_sleeping(),
			})
		var initial_agent_state = {
			"id": _agent.agent_id,
			"status": _agent.status,
			"position": _agent.position,
			"heading_radians": _agent.heading_radians,
		}
		_append_domain_event("run_started", "", {
			"description": "Simulation started",
			"initial_objects": initial_objects,
			"initial_agent_state": initial_agent_state,
		})

	# Check if local mock mode is enabled (for testing without agent service)
	_use_local_mock = OS.get_environment("AGENT_WORLD_LOCAL_MODE") == "1"
	
	if _use_local_mock:
		print("AGENT_WORLD_LOCAL_MODE=1: Using local MockController")
		_setup_local_mock_controller(run_id, random_seed)
		# Mark session as established/connected for local mock mode
		_agent_session_established = true
		_agent_session_connected = true
	else:
		# Create WebSocketClient for agent service communication
		var ws_client = _ws_client_template.new()
		# Allow overriding agent service URL via environment variable for testing
		var agent_service_url = OS.get_environment("AGENT_SERVICE_URL")
		if agent_service_url == "":
			agent_service_url = "ws://localhost:8765"
		ws_client.url = agent_service_url
		ws_client.configure_hello(run_id, _agent.agent_id, _agent.agent_type_id)
		# WebSocketClient signals: connected, disconnected, message_received, error
		ws_client.connected.connect(_on_hello_ack)
		ws_client.message_received.connect(_on_message_received)
		ws_client.error.connect(_on_connection_failed)
		ws_client.disconnected.connect(_on_disconnected)
		add_child(ws_client)
		_ws_client = ws_client
		
		# Start 3-second connection timeout for fallback to local mock
		# (handled by WebSocketClient internally)

	set_process(true)
	set_physics_process(true)

	print("=== Agent World Physical Room ===")
	print("Gravity: %s m/s^2" % [str(gravity.y)])
	print("Fixed timestep: %d Hz" % [int(fixed_timestep_hz)])
	print("Room half-size: %s m" % [str(half_size)])
	print("Objects spawned: %d" % [objects.size()])
	print("Simulation time: %d Hz fixed step, day cycle %ds" % [int(fixed_timestep_hz), int(_sim_time.day_cycle_duration_s)])
	print("=================================")

# Virtual method - subclasses should override to spawn their specific objects
func _spawn_objects() -> void:
	# Base implementation does nothing - subclasses must implement
	pass

# Virtual method - subclasses can override to run demo sequences
func _process_demo(delta: float) -> void:
	# Base implementation does nothing - subclasses can implement demo logic
	pass

func _load_config_values() -> void:
	# Load room config
	var room_config = _config_loader.get_room()
	if room_config:
		half_size = Vector3(room_config.get("half_size", {}).get("x", 13.5), 
						   room_config.get("half_size", {}).get("y", 13.5), 
						   room_config.get("half_size", {}).get("z", 13.5))
		gravity = Vector3(room_config.get("gravity", {}).get("x", 0.0),
						 room_config.get("gravity", {}).get("y", -9.8),
						 room_config.get("gravity", {}).get("z", 0.0))
		fixed_timestep_hz = room_config.get("fixed_timestep_hz", 60.0)
	
	# Load protocol config
	var protocol_config = _config_loader.get_protocol()
	if protocol_config:
		stale_threshold = protocol_config.get("stale_threshold", 5)
		world_state_interval_ticks = protocol_config.get("world_state_interval_ticks", 5)
	
	# Load experiment config
	var exp_config = _config_loader.get_experiment()
	if exp_config:
		experiment_id = exp_config.get("experiment_id", "exp_autonomous_discovery_01")
		scenario_id = exp_config.get("scenario_id", "first_benchmark_room")
		scenario_version = exp_config.get("scenario_version", "1.0.0")
	
	# Load agent config
	var agent_config = _config_loader.get_agent()
	if agent_config:
		# These are used for fingerprint, agent.gd has its own exports
		pass
	
	# Load agent service policy
	var svc_config = _config_loader.get_agent_service()
	if svc_config:
		_agent_service_policy_version = str(svc_config.get("policy_version", "2"))
		_agent_service_action_delay_ticks = svc_config.get("action_delay_ticks", 12)
		_agent_service_action_cooldown_ticks = svc_config.get("action_cooldown_ticks", 30)
		_agent_service_action_delay_probability = svc_config.get("action_delay_probability", 0.5)
		_agent_service_target_ids = svc_config.get("target_ids", ["obj_wood_cube", "obj_metal_sphere", "obj_glass_box", "obj_rubber_cylinder"])
		_agent_service_interrupt_target_ids = svc_config.get("interrupt_target_ids", ["obj_wood_cube"])
	
	# Load drive policy
	var drive_config = _config_loader.get_drive_policy()
	if drive_config:
		_drive_policy_version = str(drive_config.get("version", "1"))
		var thresholds = drive_config.get("thresholds", {})
		_drive_curiosity_explore_threshold = thresholds.get("curiosity_explore", 0.7)
		_drive_uncertainty_investigate_threshold = thresholds.get("uncertainty_investigate", 0.6)
		_drive_integrity_safety_threshold = thresholds.get("integrity_safety", 0.3)
		
		var initial = drive_config.get("initial_values", {})
		_drive_initial_curiosity = initial.get("curiosity", 0.5)
		_drive_initial_uncertainty = initial.get("uncertainty", 0.5)
		_drive_initial_integrity = initial.get("physical_integrity", 1.0)
		
		var rates = drive_config.get("update_rates", {})
		var curiosity_rates = rates.get("curiosity", {})
		_drive_curiosity_novel_boost = curiosity_rates.get("novel_object_boost", 0.15)
		_drive_curiosity_moved_boost = curiosity_rates.get("moved_object_boost", 0.05)
		_drive_curiosity_decay_rate = curiosity_rates.get("decay_rate", 0.01)
		
		var uncertainty_rates = rates.get("uncertainty", {})
		_drive_uncertainty_high_error_boost = uncertainty_rates.get("high_prediction_error_boost", 0.1)
		_drive_uncertainty_medium_error_boost = uncertainty_rates.get("medium_prediction_error_boost", 0.03)
		_drive_uncertainty_good_prediction_decay = uncertainty_rates.get("good_prediction_decay", 0.005)
		_drive_uncertainty_unexpected_movement_boost = uncertainty_rates.get("unexpected_movement_boost", 0.05)
		_drive_uncertainty_decay_rate = uncertainty_rates.get("decay_rate", 0.005)
		
		var integrity_rates = rates.get("physical_integrity", {})
		_drive_integrity_collision_penalty = integrity_rates.get("collision_risk_penalty", 0.005)
		_drive_integrity_recovery_rate = integrity_rates.get("recovery_rate", 0.002)
		_drive_integrity_collision_distance = integrity_rates.get("collision_distance_threshold", 0.5)
		
		var pred_thresholds = drive_config.get("prediction_error_thresholds", {})
		_drive_prediction_error_high = pred_thresholds.get("high", 0.04)
		_drive_prediction_error_medium = pred_thresholds.get("medium", 0.01)
		_drive_unexpected_movement_threshold = pred_thresholds.get("unexpected_movement", 0.25)
	
	# Store simulation config for later application (after _sim_time is created)
	var sim_config = _config_loader.get_simulation()
	if sim_config:
		_sim_day_cycle_duration_s = sim_config.get("day_cycle_duration_s", 240.0)
	
	# Load metrics config
	var metrics_config = _config_loader.get_metrics()
	if metrics_config:
		_health_interval_s = metrics_config.get("health_interval_s", 5.0)
		_metrics_interval_s = metrics_config.get("metrics_interval_s", 1.0)
		_verbose_logging = _verbose_logging or metrics_config.get("verbose_logs", false)

func _compute_config_fingerprint() -> String:
	var object_configs: Array = []
	for obj in objects:
		var object_config: Dictionary = obj.get_metadata()
		object_config.erase("is_sleeping")
		object_configs.append(object_config)

	var config = {
		"scenario_id": "first_benchmark_room",
		"scenario_version": "1.0.0",
		"world": {
			"half_size": {"x": half_size.x, "y": half_size.y, "z": half_size.z},
			"gravity": {"x": gravity.x, "y": gravity.y, "z": gravity.z},
			"fixed_timestep_hz": fixed_timestep_hz,
			"physics_engine": "JoltPhysics",
			"boundary_thickness_m": 0.2,
			"stale_threshold": stale_threshold,
			"world_state_interval_ticks": world_state_interval_ticks,
		},
		"agent": {
			"agent_id": _agent.agent_id,
			"agent_type_id": _agent.agent_type_id,
			"move_speed": _agent.move_speed,
			"turn_speed": _agent.turn_speed,
			"reach_distance": _agent.reach_distance,
			"spawn_position": {
				"x": _agent.spawn_position.x,
				"y": _agent.spawn_position.y,
				"z": _agent.spawn_position.z,
			},
			"collision_shape": {"type": "capsule", "radius_m": 0.3, "height_m": 1.0},
		},
		"objects": object_configs,
		"agent_service": {
			"policy_version": _agent_service_policy_version,
			"action_delay_ticks": _agent_service_action_delay_ticks,
			"action_cooldown_ticks": _agent_service_action_cooldown_ticks,
			"action_delay_probability": _agent_service_action_delay_probability,
			"target_sequence": _agent_service_target_sequence(),
			"drive_policy": {
				"version": _drive_policy_version,
				"thresholds": {
					"curiosity_explore": _drive_curiosity_explore_threshold,
					"uncertainty_investigate": _drive_uncertainty_investigate_threshold,
					"integrity_safety": _drive_integrity_safety_threshold
				},
				"initial_values": {
					"curiosity": _drive_initial_curiosity,
					"uncertainty": _drive_initial_uncertainty,
					"physical_integrity": _drive_initial_integrity
				},
				"update_rates": {
					"curiosity": {
						"novel_object_boost": _drive_curiosity_novel_boost,
						"moved_object_boost": _drive_curiosity_moved_boost,
						"decay_rate": _drive_curiosity_decay_rate
					},
					"uncertainty": {
						"high_prediction_error_boost": _drive_uncertainty_high_error_boost,
						"medium_prediction_error_boost": _drive_uncertainty_medium_error_boost,
						"good_prediction_decay": _drive_uncertainty_good_prediction_decay,
						"unexpected_movement_boost": _drive_uncertainty_unexpected_movement_boost,
						"decay_rate": _drive_uncertainty_decay_rate
					},
					"physical_integrity": {
						"collision_risk_penalty": _drive_integrity_collision_penalty,
						"recovery_rate": _drive_integrity_recovery_rate,
						"collision_distance_threshold": _drive_integrity_collision_distance
					}
				},
				"prediction_error_thresholds": {
					"high": _drive_prediction_error_high,
					"medium": _drive_prediction_error_medium,
					"unexpected_movement": _drive_unexpected_movement_threshold
				}
			}
		},
		"simulation": {
			"day_cycle_duration_s": _sim_time.day_cycle_duration_s,
		},
	}
	var canonical_json: String = JSON.stringify(_canonicalize_config(config))
	var hashing_context := HashingContext.new()
	if hashing_context.start(HashingContext.HASH_SHA256) != OK:
		return ""
	hashing_context.update(canonical_json.to_utf8_buffer())
	return hashing_context.finish().hex_encode()

func _agent_service_target_sequence() -> Array:
	# Mirror AgentService._handle_hello's deterministic target sequence. The
	# fingerprint records the effective policy; keep this in lockstep with
	# services/agent/src/agent_service.py (checked by a cross-language test).
	var targets: Array = [
		{"target_id": "obj_nonexistent", "action_type": "touch"},
		{"target_id": "", "action_type": "wait"},
	]
	for target_id in _agent_service_target_ids:
		targets.append({"target_id": target_id, "action_type": "move"})
		var touch := {"target_id": target_id, "action_type": "touch"}
		if target_id in _agent_service_interrupt_target_ids:
			touch["interrupt_after"] = true
		targets.append(touch)
	return targets

func _canonicalize_config(config: Variant) -> Variant:
	# Sort keys recursively for deterministic JSON output
	if config is Dictionary:
		var sorted: Dictionary = {}
		var keys: Array = config.keys()
		keys.sort()
		for key in keys:
			sorted[key] = _canonicalize_config(config[key])
		return sorted
	elif config is Array:
		var sorted: Array = []
		for item in config:
			sorted.append(_canonicalize_config(item))
		return sorted
	else:
		return config

# === Core room functionality (physics, boundaries, agent, WebSocket) ===

func _build_room_boundaries() -> void:
	# Floor - match visual floor in main.tscn (position y=-13.43, height=0.05, top at -13.405)
	# Collision floor height=0.2, so center at -13.405 - 0.1 = -13.505
	var floor = _create_boundary_box("Floor", Vector3(half_size.x * 2 + 1, 0.2, half_size.z * 2 + 1), Vector3(0, -13.505, 0))
	# Ceiling
	var ceiling = _create_boundary_box("Ceiling", Vector3(half_size.x * 2 + 1, 0.2, half_size.z * 2 + 1), Vector3(0, half_size.y + 0.1, 0))
	# Walls
	var wall_north = _create_boundary_box("WallNorth", Vector3(half_size.x * 2 + 1, half_size.y * 2, 0.2), Vector3(0, 0, -half_size.z - 0.1))
	var wall_south = _create_boundary_box("WallSouth", Vector3(half_size.x * 2 + 1, half_size.y * 2, 0.2), Vector3(0, 0, half_size.z + 0.1))
	var wall_east = _create_boundary_box("WallEast", Vector3(0.2, half_size.y * 2, half_size.z * 2), Vector3(half_size.x + 0.1, 0, 0))
	var wall_west = _create_boundary_box("WallWest", Vector3(0.2, half_size.y * 2, half_size.z * 2), Vector3(-half_size.x - 0.1, 0, 0))

func _create_boundary_box(name: String, size: Vector3, position: Vector3) -> StaticBody3D:
	var body = StaticBody3D.new()
	body.name = name
	var shape = CollisionShape3D.new()
	var box = BoxShape3D.new()
	box.size = size
	shape.shape = box
	body.add_child(shape)
	# Add physics material with 0 bounce to prevent micro-bouncing
	if name == "Floor":
		var material: PhysicsMaterial = PhysicsMaterial.new()
		material.friction = 0.9
		material.bounce = 0.0
		body.physics_material_override = material
	body.global_position = position
	add_child(body)
	return body

func _spawn_agent() -> void:
	_agent = _agent_template.new()
	_agent.name = "Agent"
	_agent.global_position = Vector3(0, -12.9, 1.5)
	
	# Add collision shape (capsule) so agent stands on floor
	# Capsule height=1.12 (extends from y=-0.56 to y=+0.56), radius=0.3
	# Spawn y=-12.9 aligns capsule bottom with floor at y=-13.5
	var collision_shape = CollisionShape3D.new()
	var capsule = CapsuleShape3D.new()
	capsule.height = 1.12
	capsule.radius = 0.3
	collision_shape.shape = capsule
	_agent.add_child(collision_shape)
	
	add_child(_agent)
	
	# Add first-person camera at agent's forehead (eye level, slightly forward)
	# Agent capsule: height=1.12 (y: -0.56 to 0.56), radius=0.3
	# Forehead/eye position: y=0.35 (eye level), z=-0.35 (forward, -Z is forward when heading=PI)
	# Agent navigate_toward uses heading=0 -> world +Z, but Camera3D looks along local -Z
	# So we rotate the camera by PI (180 degrees) to face the travel direction
	# Pitch down ~30 degrees (-0.52 rad) to see objects on the floor
	var agent_camera = Camera3D.new()
	agent_camera.name = "AgentCamera"
	agent_camera.current = true
	# Position at forehead: slightly below top (0.56), slightly forward of center (-radius)
	agent_camera.position = Vector3(0, 0.35, -0.35)
	# Rotate 180 degrees around Y so camera faces travel direction
	# (Agent heading=0 moves toward +Z, camera looks along -Z local)
	# Pitch down -0.52 rad (~ -30 deg) to see floor/objects
	agent_camera.rotation = Vector3(-0.52, PI, 0)
	_agent.add_child(agent_camera)

func _animate_day_night(hour: float) -> void:
	if _light and abs(hour - _last_light_hour) > 0.1:
		_last_light_hour = hour
		var sun_angle = (hour / 24.0) * TAU - PI * 0.5
		_light.global_rotation = Vector3(-sun_angle, 0, 0)
		var intensity = max(0.1, cos(sun_angle))
		_light.light_energy = intensity * 2.0
		_light.light_color = Color(1.0, 0.95, 0.85) if intensity > 0.5 else Color(0.2, 0.2, 0.4)

func _find_object(instance_id: String):
	for obj in objects:
		var meta = obj.get_metadata()
		if meta["instance_id"] == instance_id:
			return obj
	return null

func apply_impulse(instance_id: String, impulse: Vector3) -> void:
	var target = _find_object(instance_id)
	if target:
		target.apply_central_impulse(impulse)
		_append_domain_event("object_impulse_applied", instance_id, {
			"impulse": _vector_to_dict(impulse),
		})
		object_impulse_applied.emit(instance_id, impulse)

func get_settled_objects() -> Array[String]:
	var settled: Array[String] = []
	for obj in objects:
		if obj.is_sleeping():
			var meta = obj.get_metadata()
			settled.append(meta["instance_id"])
	return settled

func _process(delta: float) -> void:
	# Update demo timer
	var demo_timer: float = 0.0
	if _sim_time:
		demo_timer = _sim_time.simulation_time
	
	# Run demo sequence (virtual, subclasses can override)
	_process_demo(delta)
	
	# Apply gravity only when not paused (pause freezes behavior without corrupting state)
	if _sim_time and not _sim_time.is_paused:
		for obj in objects:
			if not obj.is_sleeping():
				obj.apply_central_force(gravity * obj.mass)
	else:
		# During pause, zero velocities to truly freeze simulation behavior
		for obj in objects:
			obj.linear_velocity = Vector3(0, 0, 0)
			obj.angular_velocity = Vector3(0, 0, 0)
	
	# Emit health status periodically
	if _sim_time:
		_health_timer += delta
		if _health_timer >= _health_interval_s:
			_health_timer = 0.0
			_emit_health_status()
	
	# Emit metrics periodically
	if _trace and _metrics_timer >= _metrics_interval_s:
		_metrics_timer = 0.0
		_emit_metrics()
	else:
		_metrics_timer += delta

func _physics_process(delta: float) -> void:
	# Physics is handled by Jolt at fixed timestep
	# This is here for any custom physics logic
	pass

func _emit_health_status() -> void:
	if not _ws_client or _ws_client.get_connection_state() != WebSocketClient.ConnectionState.CONNECTED:
		return
	var health = {
		"type": "HealthStatus",
		"run_id": _event_recorder.run_id if _event_recorder else "",
		"agent_id": _agent.agent_id,
		"timestamp_s": _sim_time.simulation_time if _sim_time else 0.0,
		"world_revision": _world_revision,
		"status": "healthy" if _agent_session_established else "degraded",
		"details": {
			"objects_count": objects.size(),
			"settled_count": get_settled_objects().size(),
			"simulation_tick": _sim_time.simulation_tick if _sim_time else 0,
			"simulation_time": _sim_time.simulation_time if _sim_time else 0.0,
			"paused": _sim_time.is_paused if _sim_time else false,
			"time_scale": _sim_time.time_scale if _sim_time else 1.0,
		}
	}
	_ws_client.send_message(health)

func _emit_metrics() -> void:
	# Emit world-level metrics
	if _trace:
		var attrs = _trace.bounded_attributes(
			experiment_id, scenario_id, scenario_version, _agent.agent_id,
			"world", "1.0.0"
		)
		attrs["objects_count"] = objects.size()
		attrs["settled_count"] = get_settled_objects().size()
		if _sim_time:
			attrs["simulation_tick"] = _sim_time.simulation_tick
			attrs["simulation_time"] = _sim_time.simulation_time
			attrs["time_scale"] = _sim_time.time_scale
		_trace.set_gauge("agent_world_objects_total", objects.size(), attrs)
		_trace.set_gauge("agent_world_objects_settled", get_settled_objects().size(), attrs)
		if _sim_time:
			_trace.set_gauge("agent_world_simulation_time_scale", _sim_time.time_scale, attrs)

func _vector_to_dict(v: Vector3) -> Dictionary:
	return {"x": v.x, "y": v.y, "z": v.z}

func _append_domain_event(event_family: String, instance_id: String, payload: Dictionary) -> void:
	if _event_recorder:
		var event: Dictionary = {
			"event_family": event_family,
			"instance_id": instance_id,
			"payload": payload,
			"world_revision": _world_revision,
			"run_id": _event_recorder._current_run_id if _event_recorder else "",
			"timestamp_s": _sim_time.simulation_time if _sim_time else 0.0,
		}
		_event_recorder.append_event(event)

func _on_hello_ack(server_id: String) -> void:
	_agent_session_established = true
	_agent_session_connected = true
	print("Agent session established: %s" % [server_id])

func _on_message_received(msg: Dictionary) -> void:
	# Route incoming messages to ProtocolHandler
	if _protocol_handler:
		_protocol_handler._on_message_received(msg)

func _on_connection_failed(code: String, message: String) -> void:
	print("WebSocket connection failed")
	_fallback_to_local_mock()

func _on_disconnected(reason: String) -> void:
	print("WebSocket disconnected: %s" % [reason])
	_agent_session_connected = false

func _fallback_to_local_mock() -> void:
	if _use_local_mock or _mock_controller != null:
		return  # Already using mock
	if _ws_client != null and _ws_client.get_connection_state() == WebSocketClient.ConnectionState.CONNECTED:
		return  # Connected successfully, don't fallback
	print("WebSocket connection failed, falling back to local MockController")
	_use_local_mock = true
	# Do NOT mark session as established/connected for fallback.
	# Fallback uses different policy (2s cooldown, no seeded delay) than external
	# service (30-tick cooldown, 50% seeded delay). Marking connected would
	# create identical run fingerprints for different behaviors.
	if _ws_client != null:
		_ws_client.queue_free()
		_ws_client = null
	if _protocol_handler != null:
		_protocol_handler.queue_free()
		_protocol_handler = null
	_setup_local_mock_controller(_event_recorder.run_id, hash(_event_recorder.run_id) & 0x7FFFFFFF)

func _setup_local_mock_controller(run_id: String, random_seed: int) -> void:
	# Create and configure MockController for local testing
	_mock_controller = _mock_controller_template.new()
	_mock_controller.agent = _agent
	add_child(_mock_controller)
	
	# Set up deterministic target sequence matching agent service policy
	var targets: Array = [
		{"target_id": "obj_nonexistent", "action_type": "touch"},
		{"target_id": "", "action_type": "wait"},
	]
	for target_id in _agent_service_target_ids:
		targets.append({"target_id": target_id, "action_type": "move"})
		var touch := {"target_id": target_id, "action_type": "touch"}
		if target_id in _agent_service_interrupt_target_ids:
			touch["interrupt_after"] = true
		targets.append(touch)
	
	_mock_controller.set_targets(targets)
	_mock_controller.action_cooldown_s = 2.0  # Slower for visibility
	
	# Connect MockController signals to same handlers as ProtocolHandler
	_mock_controller.controller_action_issued.connect(_on_mock_action_issued)
	print("Local MockController configured with %d targets" % [targets.size()])

func _on_mock_action_issued(action_type_id: String, target_instance_id: String) -> void:
	# Observational only - MockController already executed the action before emitting.
	# This handler is for logging/metrics correlation, not for re-executing actions.
	print("MOCK_ACTION_ISSUED: action=%s target=%s" % [action_type_id, target_instance_id])

func _send_observation(observation: Dictionary) -> void:
	if not _ws_client or _ws_client.get_connection_state() != WebSocketClient.ConnectionState.CONNECTED:
		return
	var msg = observation.duplicate()
	# Start the publish span BEFORE creating correlation, so the span ID
	# matches the outgoing message's correlation.
	var span = _trace.start_span(
		"world.observation.publish",
		{},
		_trace.bounded_attributes(
			experiment_id, scenario_id, scenario_version, _agent.agent_id,
			"world", "1.0.0"
		),
	)
	var correlation = _make_correlation()
	correlation["trace_id"] = span.get("trace_id", "")
	correlation["span_id"] = span.get("span_id", "")
	msg["correlation"] = correlation
	_ws_client.send_message(msg)
	observation_ready.emit(msg)
	
	# Record outbound Observation protocol metrics
	if _trace:
		var attrs = {
			"message.type": "Observation",
			"direction": "outbound",
			"outcome": "success",
		}
		_trace.record_counter("agent_world_protocol_message_total", 1, attrs, experiment_id, scenario_id, scenario_version, _agent.agent_id, _world_revision, _sim_time.simulation_tick if _sim_time else 0, _sim_time.simulation_time if _sim_time else 0.0)

func _make_correlation() -> Dictionary:
	return {
		"experiment_id": experiment_id,
		"scenario_id": scenario_id,
		"scenario_version": scenario_version,
		"run_id": _event_recorder.run_id if _event_recorder else "",
		"agent_id": _agent.agent_id,
		"world_revision": _world_revision,
		"simulation_tick": _sim_time.simulation_tick if _sim_time else 0,
		"simulation_time": _sim_time.simulation_time if _sim_time else 0.0,
		"component": "world",
		"component_version": "1.0.0",
	}

func _on_observation_received(observation: Dictionary) -> void:
	# Handle incoming observation (world state update)
	if _protocol_handler:
		_protocol_handler.handle_observation(observation)

func _send_intention(intention: Dictionary) -> void:
	if not _ws_client or _ws_client.get_connection_state() != WebSocketClient.ConnectionState.CONNECTED:
		return
	var msg = intention.duplicate()
	var span = _trace.start_span(
		"world.intention.publish",
		{},
		_trace.bounded_attributes(
			experiment_id, scenario_id, scenario_version, _agent.agent_id,
			"world", "1.0.0"
		),
	)
	var correlation = _make_correlation()
	correlation["trace_id"] = span.get("trace_id", "")
	correlation["span_id"] = span.get("span_id", "")
	msg["correlation"] = correlation
	_ws_client.send_message(msg)

func _send_action(action: Dictionary) -> void:
	if not _ws_client or _ws_client.get_connection_state() != WebSocketClient.ConnectionState.CONNECTED:
		return
	var msg = action.duplicate()
	var span = _trace.start_span(
		"world.action.execute",
		{},
		_trace.bounded_attributes(
			experiment_id, scenario_id, scenario_version, _agent.agent_id,
			"world", "1.0.0"
		),
	)
	var correlation = _make_correlation()
	correlation["trace_id"] = span.get("trace_id", "")
	correlation["span_id"] = span.get("span_id", "")
	msg["correlation"] = correlation
	msg["request_world_revision"] = _world_revision
	_ws_client.send_message(msg)

func _on_action_result(result: Dictionary) -> void:
	if _protocol_handler:
		_protocol_handler.handle_action_result(result)
	
	# Emit action result event
	_append_domain_event("action_result", "", {
		"action_id": result.get("id", ""),
		"action_type": result.get("action_type_id", ""),
		"target_id": result.get("target_instance_id", ""),
		"result": result.get("result", "unknown"),
		"simulation_tick": _sim_time.simulation_tick if _sim_time else 0,
	})

func _on_stale_request(request_id: String) -> void:
	_append_domain_event("stale_request_rejected", "", {
		"request_id": request_id,
		"world_revision": _world_revision,
		"simulation_tick": _sim_time.simulation_tick if _sim_time else 0,
	})

func _on_run_failed(reason: String) -> void:
	print("RUN FAILED: %s - %s" % [_event_recorder.run_id if _event_recorder else "unknown", reason])
	set_process(false)
	set_physics_process(false)
