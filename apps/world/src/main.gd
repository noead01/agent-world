extends Node3D

@onready var physics_engine: String = ProjectSettings.get_setting("physics/3d/physics_engine")
@onready var physics_fps: Variant = ProjectSettings.get_setting("physics/common/physics_fps")

func _ready() -> void:
	var version_info: Dictionary = Engine.get_version_info()
	var godot_version: String = version_info["string"] if version_info.has("string") else "unknown"

	print("=== Agent World Godot Runtime ===")
	print("Runtime: Godot %s" % [godot_version])
	print("Physics engine: %s" % [physics_engine])
	print("Fixed timestep: %s Hz" % [str(physics_fps)])
	print("=================================")
