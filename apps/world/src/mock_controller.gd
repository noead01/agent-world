extends Node

class_name MockController

signal controller_action_issued(action_type_id: String, target_instance_id: String)

@export_group("Controller")
var agent
var targets: Array[Dictionary] = []
var action_cooldown_s: float = 0.5
var current_target_index: int = 0

var _cooldown_timer: float = 0.0

func _ready() -> void:
	if agent == null:
		print("MockController: no agent assigned")

func _physics_process(delta: float) -> void:
	if agent == null:
		return

	# Update cooldown timer
	if _cooldown_timer > 0:
		_cooldown_timer -= delta
		if _cooldown_timer < 0:
			_cooldown_timer = 0

	# Only issue a new action when the agent has no current action in progress
	if not agent._current_action.has("action_type_id"):
		if _cooldown_timer > 0:
			return
		if current_target_index < targets.size():
			var target: Dictionary = targets[current_target_index]
			var action_type: String = String(target.get("action_type", "move"))
			var target_id: String = String(target.get("instance_id", ""))
			agent.execute_action(action_type, target_id)
			controller_action_issued.emit(action_type, target_id)
			current_target_index += 1
			_cooldown_timer = action_cooldown_s
		else:
			# All targets completed
			agent.status = "idle"

func add_target(instance_id: String, action_type: String = "move") -> void:
	targets.append({
		"instance_id": instance_id,
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
