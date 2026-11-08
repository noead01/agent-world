extends Node

class_name MockController

signal controller_action_issued(action_type_id: String, target_instance_id: String)

@export_group("Controller")
var agent
var targets: Array[Dictionary] = []
var action_cooldown_s: float = 0.5
var current_target_index: int = 0

var _cooldown_timer: float = 0.0
var _action_start_time: float = 0.0
var _interrupt_issued: bool = false

func _ready() -> void:
	if agent == null:
		print("MockController: no agent assigned")

func _physics_process(delta: float) -> void:
	if agent == null:
		return

	# Respect simulation pause - don't issue actions while world is paused
	if agent._sim_time != null and agent._sim_time.is_paused:
		return

	# Update cooldown timer
	if _cooldown_timer > 0:
		_cooldown_timer -= delta
		if _cooldown_timer < 0:
			_cooldown_timer = 0

	# Track action start time for interrupt logic
	var has_current_action: bool = agent._current_action.has("action_type_id")
	if has_current_action:
		if _action_start_time == 0.0:
			_action_start_time = delta  # First frame of action
		else:
			_action_start_time += delta  # Accumulate
	else:
		_action_start_time = 0.0
		_interrupt_issued = false

	# Issue interrupt action after a short delay during a move action
	# This demonstrates action interruption observability
	if has_current_action and not _interrupt_issued and _action_start_time > 0.3:
		var current_action_type: String = agent._current_action["action_type_id"]
		if current_action_type == "move" and current_target_index < targets.size():
			var next_target: Dictionary = targets[current_target_index]
			var next_action_type: String = String(next_target.get("action_type", "move"))
			var next_target_id: String = String(next_target.get("target_id", ""))
			# Interrupt the move with the next action (e.g., touch)
			agent.execute_action(next_action_type, next_target_id)
			controller_action_issued.emit(next_action_type, next_target_id)
			current_target_index += 1
			_interrupt_issued = true
			_cooldown_timer = action_cooldown_s
			return

	# Only issue a new action when the agent has no current action in progress
	if not has_current_action:
		if _cooldown_timer > 0:
			return
		if current_target_index < targets.size():
			var target: Dictionary = targets[current_target_index]
			var action_type: String = String(target.get("action_type", "move"))
			var target_id: String = String(target.get("target_id", ""))
			agent.execute_action(action_type, target_id)
			controller_action_issued.emit(action_type, target_id)
			current_target_index += 1
			_cooldown_timer = action_cooldown_s
			_action_start_time = 0.0  # Will be set on next frame
		else:
			# All targets completed
			agent.status = "idle"

func add_target(instance_id: String, action_type: String = "move") -> void:
	targets.append({
		"target_id": instance_id,
		"action_type": action_type,
	})

func set_targets(target_list: Array[Dictionary]) -> void:
	targets = target_list.duplicate()
	current_target_index = 0

func reset() -> void:
	current_target_index = 0
	_cooldown_timer = 0.0
	if agent != null:
		agent.interrupt_current_action()
