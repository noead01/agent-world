extends RigidBody3D

class_name RigidObject

signal object_landed(instance_id: String)

var instance_id: String = ""
var type_id: String = ""
var object_name: String = ""
var kind: String = ""
var mass_kg: float = 1.0
var brittleness: float = 0.0
var throwable: bool = true
var stackable: bool = false
var friction: float = 0.5
var bounciness: float = 0.5
var density_kg_per_m3: float = 500.0
var dimensions_m: Dictionary = { "x": 0.5, "y": 0.5, "z": 0.5 }

var _has_landed: bool = false
var _was_moving: bool = false

func configure(defn: Dictionary) -> void:
	instance_id = String(defn.get("instance_id", ""))
	type_id = String(defn.get("type_id", ""))
	object_name = String(defn.get("name", instance_id))
	kind = String(defn.get("kind", "artifact"))
	mass_kg = float(defn.get("mass_kg", 1.0))
	brittleness = float(defn.get("brittleness", 0.0))
	throwable = bool(defn.get("throwable", true))
	stackable = bool(defn.get("stackable", false))
	friction = float(defn.get("friction", 0.5))
	bounciness = float(defn.get("bounciness", 0.5))
	density_kg_per_m3 = float(defn.get("density_kg_per_m3", 500.0))
	dimensions_m = defn.get("dimensions_m", { "x": 0.5, "y": 0.5, "z": 0.5 })

	# Apply physics properties
	mass = mass_kg
	gravity_scale = 1.0
	can_sleep = true
	# Assign a PhysicsMaterial so friction and bounciness affect simulation
	var material: PhysicsMaterial = PhysicsMaterial.new()
	material.friction = friction
	material.bounce = bounciness
	physics_material_override = material

	var dims: Dictionary = dimensions_m
	var sx: float = float(dims.get("x", 0.5))
	var sy: float = float(dims.get("y", 0.5))
	var sz: float = float(dims.get("z", 0.5))

	var shape: CollisionShape3D = CollisionShape3D.new()
	var box: BoxShape3D = BoxShape3D.new()
	box.size = Vector3(sx, sy, sz)
	shape.shape = box
	add_child(shape)

	# Store metadata on the node for lookup
	set_meta("instance_id", instance_id)
	set_meta("type_id", type_id)
	set_meta("mass_kg", mass_kg)
	set_meta("friction", friction)
	set_meta("bounciness", bounciness)

func get_metadata() -> Dictionary:
	return {
		"instance_id": instance_id,
		"type_id": type_id,
		"name": object_name,
		"kind": kind,
		"mass_kg": mass_kg,
		"brittleness": brittleness,
		"throwable": throwable,
		"stackable": stackable,
		"friction": friction,
		"bounciness": bounciness,
		"density_kg_per_m3": density_kg_per_m3,
		"dimensions_m": dimensions_m,
		"position": {
			"x": position.x,
			"y": position.y,
			"z": position.z,
		},
		"is_sleeping": is_sleeping(),
	}

func _integrate_forces(state: PhysicsDirectBodyState3D) -> void:
	var linear_vel: Vector3 = state.linear_velocity
	# Track that object has been in motion
	if linear_vel.length() > 0.5:
		_was_moving = true
	# Detect landing: object was moving, now settled (sleeping)
	if _was_moving and not _has_landed and is_sleeping():
		_has_landed = true
		object_landed.emit(instance_id)
