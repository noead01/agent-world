extends CharacterBody3D

class_name Agent

signal action_started(action_type_id: String, target_instance_id: String)
signal action_completed(action_type_id: String, result: String)
signal action_failed(action_type_id: String, reason: String)
signal action_interrupted(action_type_id: String)

@export_group("Agent")
var agent_id: String = "wanderer_01"
var agent_type_id: String = "exploration_agent"
var agent_name: String = "Wanderer"
var move_speed: float = 2.0
var turn_speed: float = 1.5
var reach_distance: float = 0.5
var spawn_position: Vector3 = Vector3(0, 0.56, 1.5)
var heading_radians: float = 0.0

@export_group("State")
var status: String = "idle"
var current_goal: String = ""
var world_time_s: float = 0.0

var _current_action: Dictionary = {}
var _target_object: Node
var _room: Node
var _sim_time: Object

func _ready() -> void:
	global_position = spawn_position
	rotation.y = heading_radians
	status = "idle"
	current_goal = ""

func _physics_process(delta: float) -> void:
	# Update world_time_s from the room's SimulationTime (single source of truth)
	if _sim_time != null and _sim_time.has_method("get_simulation_time"):
		world_time_s = float(_sim_time.get_simulation_time())

	# Execute current action if one is in progress
	if _current_action.has("action_type_id"):
		_execute_current_action(delta)
		return

	# Otherwise maintain position (hold heading)
	velocity = Vector3(0, 0, 0)
	move_and_slide()

func set_room(room: Node, sim_time: Object) -> void:
	_room = room
	_sim_time = sim_time

func navigate_toward(target: Vector3, delta: float) -> void:
	var direction: Vector3 = (target - global_position).normalized()
	if direction.length() > 0.001:
		heading_radians = atan2(direction.x, direction.z)
		rotation.y = heading_radians
		velocity = direction * move_speed
		move_and_slide()
		status = "moving"

func turn_toward(target: Vector3, delta: float) -> void:
	var to_target: Vector3 = (target - global_position).normalized()
	if to_target.length() > 0.001:
		var target_angle: float = atan2(to_target.x, to_target.z)
		var diff: float = target_angle - heading_radians
		# Wrap diff to [-PI, PI]
		while diff > PI:
			diff -= TAU
		while diff < -PI:
			diff += TAU
		var step: float = turn_speed * delta
		if abs(diff) <= step:
			heading_radians = target_angle
		else:
			heading_radians += step * sign(diff)
		rotation.y = heading_radians
		status = "turning"

func can_reach(target_instance_id: String) -> bool:
	if _room == null:
		return false
	var target: Node = _find_object_in_room(_room, target_instance_id)
	if target == null:
		return false
	var distance: float = global_position.distance_to(target.global_position)
	return distance <= reach_distance

func _find_object_in_room(node: Node, instance_id: String):
	if node.has_meta("instance_id") and node.get_meta("instance_id") == instance_id:
		return node
	for child in node.get_children():
		var found: Node = _find_object_in_room(child, instance_id)
		if found != null:
			return found
	return null

func execute_action(action_type_id: String, target_instance_id: String = "") -> void:
	# Interrupt any current action
	if _current_action.has("action_type_id"):
		action_interrupted.emit(_current_action["action_type_id"])
		print("AGENT_ACTION: interrupted=%s" % [_current_action["action_type_id"]])

	_current_action = {
		"action_type_id": action_type_id,
		"target_instance_id": target_instance_id,
		"started": false,
	}
	action_started.emit(action_type_id, target_instance_id)
	print("AGENT_ACTION: started=%s target=%s" % [action_type_id, target_instance_id])
	status = "acting"

func _execute_current_action(delta: float) -> void:
	var action_type: String = _current_action["action_type_id"]
	var target_id: String = _current_action["target_instance_id"]

	if not _current_action["started"]:
		_current_action["started"] = true

	# Resolve target object
	if _target_object == null and target_id != "":
		if _room != null:
			_target_object = _find_object_in_room(_room, target_id)

	# Check reach constraint for touch/inspect actions
	if action_type in ["touch", "inspect"]:
		if _target_object == null:
			_current_action = {}
			action_failed.emit(action_type, "target_not_found")
			print("AGENT_ACTION: failed=%s reason=target_not_found" % [action_type])
			status = "idle"
			return
		if not can_reach(target_id):
			_current_action = {}
			action_failed.emit(action_type, "unreachable")
			print("AGENT_ACTION: failed=%s reason=unreachable" % [action_type])
			status = "idle"
			return
		# Move close to target first
		navigate_toward(_target_object.global_position, delta)
		if global_position.distance_to(_target_object.global_position) <= reach_distance:
			_current_action = {}
			_target_object = null
			action_completed.emit(action_type, "success")
			print("AGENT_ACTION: completed=%s result=success" % [action_type])
			status = "idle"
		return

	# For move actions, keep moving
	if action_type == "move":
		if _target_object != null:
			navigate_toward(_target_object.global_position, delta)
			var dist: float = global_position.distance_to(_target_object.global_position)
			if dist <= 0.1:
				_current_action = {}
				_target_object = null
				action_completed.emit(action_type, "success")
				print("AGENT_ACTION: completed=%s result=success" % [action_type])
				status = "idle"
		else:
			_current_action = {}
			action_completed.emit(action_type, "success")
			print("AGENT_ACTION: completed=%s result=success" % [action_type])
			status = "idle"
		return

	# Unknown action type
	_current_action = {}
	action_failed.emit(action_type, "unknown_action_type")
	print("AGENT_ACTION: failed=%s reason=unknown_action_type" % [action_type])
	status = "idle"

func interrupt_current_action() -> void:
	if _current_action.has("action_type_id"):
		var interrupted_type: String = _current_action["action_type_id"]
		_current_action = {}
		_target_object = null
		action_interrupted.emit(interrupted_type)
		print("AGENT_ACTION: interrupted=%s" % [interrupted_type])
		status = "idle"

func get_agent_dict() -> Dictionary:
	return {
		"id": agent_id,
		"version": "1.0.0",
		"agent_type_id": agent_type_id,
		"name": agent_name,
		"position": {
			"x": global_position.x,
			"y": global_position.y,
			"z": global_position.z,
		},
		"heading_radians": heading_radians,
		"status": status,
		"current_goal": current_goal,
		"world_time_s": world_time_s,
	}
