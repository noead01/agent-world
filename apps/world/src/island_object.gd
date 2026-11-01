extends RigidBody3D

class_name IslandObject

signal object_broken(instance_id: String)

@export_group("Instance")
var instance_id: String = ""
var type_id: String = ""

@export_group("Physics (inherited from type)")
var movability: String = "light"
var weight_kg: float = 1.0
var brittleness: float = 0.0
var throwable: bool = true
var stackable: bool = false
var density_kg_per_m3: float = 500.0

@export_group("Per-instance overrides")
var size_scale: float = 1.0
var orientation_degrees: Vector3 = Vector3.ZERO

var kind: String = ""
var name: String = ""

func _ready() -> void:
	mass = weight_kg
	if movability == "fixed":
		mode = RigidBody3D.MODE_STATIC
	else:
		mode = RigidBody3D.MODE_RIGID
	apply_central_impulse(Vector3.ZERO)

func configure(type_def: Dictionary, instance_overrides: Dictionary = {}) -> void:
	type_id = type_def.get("id", "")
	name = type_def.get("name", type_id)
	kind = type_def.get("kind", "artifact")
	instance_id = instance_overrides.get("instance_id", type_id + "_" + str(randi()))

	movability = type_def.get("movability", "light")
	weight_kg = float(type_def.get("weightKg", 1.0))
	brittleness = float(type_def.get("brittleness", 0.0))
	throwable = bool(type_def.get("throwable", true))
	stackable = bool(type_def.get("stackable", false))
	density_kg_per_m3 = float(type_def.get("densityKgPerM3", 500.0))

	var dims: Dictionary = type_def.get("dimensionsM", { "x": 0.5, "y": 0.5, "z": 0.5 })
	size_scale = float(instance_overrides.get("size_scale", 1.0 + (randf() - 0.5) * 0.2))
	orientation_degrees = instance_overrides.get("orientation", Vector3(
		randf_range(0, 360),
		randf_range(0, 360),
		randf_range(0, 360)
	))

	var sx: float = float(dims.get("x", 0.5)) * size_scale
	var sy: float = float(dims.get("y", 0.5)) * size_scale
	var sz: float = float(dims.get("z", 0.5)) * size_scale

	if get_node_or_null("CollisionShape3D"):
		var shape: CollisionShape3D = get_node("CollisionShape3D")
		var box: BoxShape3D = BoxShape3D.new()
		box.size = Vector3(sx, sy, sz)
		shape.shape = box

	position = instance_overrides.get("position", Vector3.ZERO)
	rotation_degrees = orientation_degrees

	if movability == "fixed":
		mode = RigidBody3D.MODE_STATIC
		can_sleep = true
	else:
		mode = RigidBody3D.MODE_RIGID
		mass = weight_kg

func _on_body_entered(body: Node) -> void:
	if brittleness > 0.0 and randf() < brittleness:
		_queue_break()

func _queue_break() -> void:
	object_broken.emit(instance_id)
	queue_free()
