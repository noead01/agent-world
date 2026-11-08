extends Node3D

class_name Room

signal object_landed(instance_id: String)
signal object_collided(instance_id: String, other_id: String)
signal object_impulse_applied(instance_id: String, impulse: Vector3)

@export_group("Room Bounds")
var half_size: Vector3 = Vector3(13.5, 13.5, 13.5)

@export_group("Physics")
var gravity: Vector3 = Vector3(0, -9.8, 0)
var fixed_timestep_hz: float = 60.0

var objects: Array = []
var _sim_time_template = preload("res://src/simulation_time.gd")
var _sim_time
var _light: DirectionalLight3D
var _last_light_hour: float = -1.0

var _demo_timer: float = 0.0
var _demo_duration: float = 10.0
var _last_print_time: float = 0.0
var _landed_count: int = 0
var _impulse_applied: bool = false

var _demo_pause_time: float = 2.0
var _demo_resume_time: float = 4.0
var _demo_scale_time: float = 6.0
var _demo_reset_time: float = 8.0
var _demo_phase: String = "normal"

var _agent
var _ws_client
var _protocol_handler
var _agent_template = preload("res://src/agent.gd")
var _ws_client_template = preload("res://src/websocket_client.gd")
var _protocol_handler_template = preload("res://src/protocol_handler.gd")

func _ready() -> void:
	# Configure project physics settings for Jolt fixed timestep
	ProjectSettings.set_setting("physics/3d/physics_engine", "JoltPhysics")
	ProjectSettings.set_setting("physics/common/physics_fps", fixed_timestep_hz)
	# Set gravity at runtime via PhysicsServer3D (project.godot's default_gravity
	# may be overridden by physics_engine selection at startup)
	var space: RID = get_world_3d().space
	PhysicsServer3D.space_set_param(space, 0, gravity.y)

	_build_room_boundaries()
	_spawn_objects()

	# Create and configure SimulationTime
	_sim_time = _sim_time_template.new()
	add_child(_sim_time)
	_sim_time.time_of_day_changed.connect(_animate_day_night)

	# Find the directional light for day/night animation
	_light = get_node("../DirectionalLight3D")

	# Spawn the embodied agent
	_spawn_agent()

	# Create WebSocketClient for agent service communication
	var ws_client = _ws_client_template.new()
	ws_client.url = "ws://localhost:8765"
	add_child(ws_client)
	ws_client.connect_to_server()

	# Create ProtocolHandler
	var protocol_handler = _protocol_handler_template.new()
	protocol_handler.agent_id = _agent.agent_id
	protocol_handler.run_id = "run_001"
	protocol_handler.set_websocket_client(ws_client)
	add_child(protocol_handler)

	# Store references
	_ws_client = ws_client
	_protocol_handler = protocol_handler

	# Connect ProtocolHandler signals
	_protocol_handler.action_received.connect(_on_action_received)
	_protocol_handler.action_result_received.connect(_on_action_result)
	_protocol_handler.stale_request_rejected.connect(_on_stale_request)

	set_process(true)
	set_physics_process(true)

	print("=== Agent World Physical Room ===")
	print("Gravity: %s m/s^2" % [str(gravity.y)])
	print("Fixed timestep: %d Hz" % [int(fixed_timestep_hz)])
	print("Room half-size: %s m" % [str(half_size)])
	print("Objects spawned: %d" % [objects.size()])
	print("Simulation time: %d Hz fixed step, day cycle %ds" % [int(fixed_timestep_hz), int(_sim_time.day_cycle_duration_s)])
	print("=================================")

func _physics_process(delta: float) -> void:
	# Advance simulation time through fixed physics steps
	_sim_time.tick(delta)

	# Send world state via ProtocolHandler
	if _protocol_handler:
		_protocol_handler.tick_world_state(
			_sim_time.simulation_tick,  # Using tick as world_revision
			_sim_time.simulation_tick,
			_sim_time.simulation_time,
			_agent.get_agent_dict(),
			_get_nearby_objects()
		)

	# Demo sequence: pause/resume/time-scale/reset at scheduled times
	_demo_timer += delta
	if _demo_phase == "normal" and _demo_timer >= _demo_pause_time:
		_sim_time.pause()
		_demo_phase = "paused"
		print("  SIM PAUSED at t=%.1fs (sim_time=%.3f, tick=%d)" % [_demo_timer, _sim_time.simulation_time, _sim_time.simulation_tick])
	elif _demo_phase == "paused" and _demo_timer >= _demo_resume_time:
		_sim_time.resume()
		_demo_phase = "normal"
		print("  SIM RESUMED at t=%.1fs (sim_time=%.3f, tick=%d)" % [_demo_timer, _sim_time.simulation_time, _sim_time.simulation_tick])
	elif _demo_phase == "normal" and _demo_timer >= _demo_scale_time:
		_sim_time.set_time_scale(2.0)
		_demo_phase = "scaled"
		print("  TIME SCALE 2.0 at t=%.1fs (sim_time=%.3f, tick=%d)" % [_demo_timer, _sim_time.simulation_time, _sim_time.simulation_tick])
	elif _demo_phase == "scaled" and _demo_timer >= _demo_reset_time:
		_sim_time.reset()
		_sim_time.set_time_scale(1.0)
		_demo_phase = "reset"
		print("  SIM RESET at t=%.1fs (sim_time=%.3f, tick=%d)" % [_demo_timer, _sim_time.simulation_time, _sim_time.simulation_tick])

	# Apply gravity only when not paused (pause freezes behavior without corrupting state)
	if not _sim_time.is_paused:
		for obj in objects:
			if not obj.is_sleeping():
				obj.apply_central_force(gravity * obj.mass)
	else:
		# During pause, zero velocities to truly freeze simulation behavior
		for obj in objects:
			obj.linear_velocity = Vector3(0, 0, 0)
			obj.angular_velocity = Vector3(0, 0, 0)

	# Apply an impulse to obj_metal_sphere at t=1s (before pause) to demonstrate impulse response
	if not _impulse_applied and _demo_timer >= 1.0:
		var target = _find_object("obj_metal_sphere")
		if target:
			target.apply_central_impulse(Vector3(2.0, 0.0, 0.0))
			_impulse_applied = true
			print("  IMPULSE applied to obj_metal_sphere at t=%.1fs" % [_demo_timer])

	# Print status once per second with simulation time
	if _demo_timer - _last_print_time >= 1.0:
		_last_print_time = _demo_timer
		var settled: Array[String] = get_settled_objects()
		print("T+: wall=%.1fs sim=%.3f tick=%d paused=%s scale=%.1f tod=%.1f settled=%d/%d landed=%d" % [
			_demo_timer, _sim_time.simulation_time, _sim_time.simulation_tick,
			str(_sim_time.is_paused), _sim_time.time_scale, _sim_time.get_time_of_day(),
			settled.size(), objects.size(), _landed_count
		])
		for obj in objects:
			var p: Vector3 = obj.position
			var meta: Dictionary = obj.get_metadata()
			print("  %s: (%.2f, %.2f, %.2f) sleeping=%s mass=%.1f friction=%.1f bounciness=%.1f shape=%s dims=(%.2f,%.2f,%.2f)" % [
				meta["instance_id"], p.x, p.y, p.z, str(obj.is_sleeping()), meta["mass_kg"], meta["friction"], meta["bounciness"],
				meta.get("shape_type", "unknown"), meta["dimensions_m"]["x"], meta["dimensions_m"]["y"], meta["dimensions_m"]["z"]
			])

		# Print agent state
		if _agent != null:
			var agent_dict: Dictionary = _agent.get_agent_dict()
			print("  AGENT: id=%s status=%s pos=(%.2f, %.2f, %.2f) heading=%.2f world_time=%.3f goal=%s" % [
				agent_dict["id"], agent_dict["status"],
				agent_dict["position"]["x"], agent_dict["position"]["y"], agent_dict["position"]["z"],
				agent_dict["heading_radians"], agent_dict["world_time_s"], agent_dict["current_goal"]
			])

	if _demo_timer >= _demo_duration:
		print("=== Final Object States ===")
		for obj in objects:
			var meta: Dictionary = obj.get_metadata()
			var p: Vector3 = obj.position
			print("  %s: sleeping=%s position=(%.3f, %.3f, %.3f) mass=%.1f friction=%.1f bounciness=%.1f shape=%s dims=(%.2f,%.2f,%.2f)" % [
				meta["instance_id"], str(obj.is_sleeping()), p.x, p.y, p.z, meta["mass_kg"], meta["friction"], meta["bounciness"],
				meta.get("shape_type", "unknown"), meta["dimensions_m"]["x"], meta["dimensions_m"]["y"], meta["dimensions_m"]["z"]
			])
		print("=== Final Simulation State ===")
		print("  wall=%.3fs sim=%.3fs tick=%d paused=%s scale=%.1f tod=%.1f" % [
			_demo_timer, _sim_time.simulation_time, _sim_time.simulation_tick,
			str(_sim_time.is_paused), _sim_time.time_scale, _sim_time.get_time_of_day()
		])
		if _agent != null:
			var agent_dict: Dictionary = _agent.get_agent_dict()
			print("  AGENT: id=%s status=%s pos=(%.3f, %.3f, %.3f) heading=%.2f world_time=%.3f goal=%s" % [
				agent_dict["id"], agent_dict["status"],
				agent_dict["position"]["x"], agent_dict["position"]["y"], agent_dict["position"]["z"],
				agent_dict["heading_radians"], agent_dict["world_time_s"], agent_dict["current_goal"]
			])
		print("==========================")
		get_tree().quit()

# ProtocolHandler signal handlers
func _on_action_received(action: Dictionary) -> void:
	# Agent service sent an Action or Intention command - execute it via Agent
	if _agent:
		# Handle both Action (action_type_id) and Intention (intention_type_id) message formats
		var action_type = action.get("action_type_id", action.get("intention_type_id", ""))
		var target_id = action.get("target_instance_id", "")
		_agent.execute_action(action_type, target_id)

func _on_action_result(result: Dictionary) -> void:
	# ActionResult received (response to action we sent) - currently not used since agent service drives actions
	print("Room: ActionResult received: %s" % [result])

func _on_stale_request(request_id: String, current_revision: int) -> void:
	print("Room: Stale request rejected, current_revision=%d" % [current_revision])
	# Agent will re-plan automatically via agent service

func _get_nearby_objects() -> Array:
	var nearby = []
	for obj in objects:
		var meta = obj.get_metadata()
		nearby.append({
			"instance_id": meta["instance_id"],
			"type_id": meta.get("type_id", "unknown"),
			"position": {
				"x": obj.position.x,
				"y": obj.position.y,
				"z": obj.position.z
			}
		})
	return nearby

func _build_room_boundaries() -> void:
	_create_static_body("floor", Vector3(0, -half_size.y, 0), Vector3(half_size.x * 2, 0.2, half_size.z * 2))
	_create_static_body("ceiling", Vector3(0, half_size.y, 0), Vector3(half_size.x * 2, 0.2, half_size.z * 2))
	_create_static_body("wall_west", Vector3(-half_size.x, 0, 0), Vector3(0.2, half_size.y * 2, half_size.z * 2))
	_create_static_body("wall_east", Vector3(half_size.x, 0, 0), Vector3(0.2, half_size.y * 2, half_size.z * 2))
	_create_static_body("wall_north", Vector3(0, 0, -half_size.z), Vector3(half_size.x * 2, half_size.y * 2, 0.2))
	_create_static_body("wall_south", Vector3(0, 0, half_size.z), Vector3(half_size.x * 2, half_size.y * 2, 0.2))

func _create_static_body(name: String, position: Vector3, size: Vector3) -> void:
	var body: StaticBody3D = StaticBody3D.new()
	body.name = name
	body.position = position
	add_child(body)

	var shape: CollisionShape3D = CollisionShape3D.new()
	var box: BoxShape3D = BoxShape3D.new()
	box.size = size
	shape.shape = box
	body.add_child(shape)

func _spawn_objects() -> void:
	var definitions: Array[Dictionary] = [
		{
			"instance_id": "obj_wood_cube",
			"type_id": "wood_cube",
			"name": "Wood Cube",
			"kind": "artifact",
			"shape_type": "box",
			"mass_kg": 2.0,
			"brittleness": 0.1,
			"throwable": true,
			"stackable": false,
			"friction": 0.8,
			"bounciness": 0.3,
			"density_kg_per_m3": 650,
			"dimensions_m": { "x": 0.6, "y": 0.6, "z": 0.6 },
			"position": Vector3(0, 5, 0),
		},
		{
			"instance_id": "obj_metal_sphere",
			"type_id": "metal_sphere",
			"name": "Metal Sphere",
			"kind": "mineral",
			"shape_type": "sphere",
			"mass_kg": 5.0,
			"brittleness": 0.05,
			"throwable": true,
			"stackable": false,
			"friction": 0.4,
			"bounciness": 0.8,
			"density_kg_per_m3": 7800,
			"dimensions_m": { "x": 0.4, "y": 0.4, "z": 0.4 },
			"position": Vector3(2, 5, 0),
		},
		{
			"instance_id": "obj_glass_box",
			"type_id": "glass_box",
			"name": "Glass Box",
			"kind": "artifact",
			"shape_type": "box",
			"mass_kg": 1.0,
			"brittleness": 0.9,
			"throwable": true,
			"stackable": false,
			"friction": 0.9,
			"bounciness": 0.5,
			"density_kg_per_m3": 2500,
			"dimensions_m": { "x": 0.5, "y": 0.5, "z": 0.5 },
			"position": Vector3(-2, 5, 0),
		},
		{
			"instance_id": "obj_rubber_cylinder",
			"type_id": "rubber_cylinder",
			"name": "Rubber Cylinder",
			"kind": "organic",
			"shape_type": "cylinder",
			"mass_kg": 3.0,
			"brittleness": 0.2,
			"throwable": true,
			"stackable": false,
			"friction": 0.7,
			"bounciness": 0.7,
			"density_kg_per_m3": 1100,
			"dimensions_m": { "x": 0.4, "y": 0.8, "z": 0.4 },
			"position": Vector3(0, 5, 2),
		},
	]

	for defn in definitions:
		var obj = load("res://src/rigid_object.gd").new()
		obj.configure(defn)
		obj.position = defn["position"]
		# Enable contact monitoring so body_entered signals fire on collisions
		obj.contact_monitor = true
		obj.max_contacts_reported = 1
		add_child(obj)
		objects.append(obj)

		obj.body_entered.connect(func(other_body): _on_object_body_entered(obj, other_body))
		obj.object_landed.connect(func(instance_id): _on_object_landed(instance_id))

func _on_object_body_entered(obj, other_body: Node) -> void:
	var other_id: String = ""
	if other_body.has_meta("instance_id"):
		other_id = other_body.get_meta("instance_id")
	elif other_body.name:
		other_id = other_body.name
	object_collided.emit(obj.instance_id, other_id)

func _on_object_landed(instance_id: String) -> void:
	_landed_count += 1
	object_landed.emit(instance_id)

func apply_impulse(instance_id: String, impulse: Vector3) -> void:
	var obj = _find_object(instance_id)
	if obj:
		obj.apply_central_impulse(impulse)
		object_impulse_applied.emit(instance_id, impulse)

func _find_object(instance_id: String):
	for obj in objects:
		if obj.instance_id == instance_id:
			return obj
	return null

func get_object_metadata() -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	for obj in objects:
		result.append(obj.get_metadata())
	return result

func get_settled_objects() -> Array[String]:
	var result: Array[String] = []
	for obj in objects:
		if obj.is_sleeping():
			result.append(obj.instance_id)
	return result

func _animate_day_night(hour: float) -> void:
	if _light == null:
		return
	# Map time_of_day (0-24) to light rotation and energy
	# 6h = sunrise (low east), 12h = noon (overhead), 18h = sunset (low west), 0h = midnight (below horizon)
	var angle: float = (hour - 6.0) / 24.0 * TAU  # radians, 0 at sunrise
	var elevation: float = sin(angle)  # 1 at noon, -1 at midnight
	var azimuth: float = cos(angle)    # 1 at sunrise/noon side, -1 at sunset side
	_light.rotation_degrees = Vector3(-90.0 + elevation * 45.0, azimuth * 30.0, 0.0)
	# Energy: full at noon, dim at dawn/dusk, minimal at night
	var energy: float = clamp(0.2 + 0.8 * max(0.0, sin(angle)), 0.1, 1.0)
	_light.energy = energy

func _spawn_agent() -> void:
	# Create and configure Agent
	_agent = _agent_template.new()
	add_child(_agent)
	_agent.set_room(self, _sim_time)

	# Add a collision shape so move_and_slide() can test against walls/objects
	var agent_shape = CollisionShape3D.new()
	var agent_capsule = CapsuleShape3D.new()
	agent_capsule.radius = 0.3
	agent_capsule.height = 1.0
	agent_shape.shape = agent_capsule
	_agent.add_child(agent_shape)

	# Add visible geometry so the agent is visible in rendered output
	var agent_mesh = MeshInstance3D.new()
	var capsule_mesh = CapsuleMesh.new()
	capsule_mesh.radius = 0.3
	capsule_mesh.height = 1.0
	agent_mesh.mesh = capsule_mesh
	_agent.add_child(agent_mesh)

	# The external agent service now drives the agent by sending Action messages.
	# ProtocolHandler receives Action messages and Room forwards them to Agent.execute_action().
	# MockController has been removed.

	print("Agent spawned: id=%s at %s" % [_agent.agent_id, str(_agent.global_position)])
