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
var _demo_timer: float = 0.0
var _demo_duration: float = 10.0
func _ready() -> void:
	# Configure project physics settings for Jolt fixed timestep
	ProjectSettings.set_setting("physics/3d/physics_engine", "JoltPhysics")
	ProjectSettings.set_setting("physics/common/physics_fps", fixed_timestep_hz)
	ProjectSettings.set_setting("physics/3d/default_gravity", gravity)

	_build_room_boundaries()
	_spawn_objects()

	set_process(true)
	set_physics_process(true)

	print("=== Agent World Physical Room ===")
	print("Gravity: %s m/s^2" % [str(gravity.y)])
	print("Fixed timestep: %d Hz" % [int(fixed_timestep_hz)])
	print("Room half-size: %s m" % [str(half_size)])
	print("Objects spawned: %d" % [objects.size()])
	print("=================================")

func _physics_process(delta: float) -> void:
	# Apply explicit gravity to each object
	for obj in objects:
		obj.apply_central_impulse(gravity * obj.mass * delta)

	_demo_timer += delta
	if _demo_timer >= 1.0:
		_demo_timer = 0.0
		var settled: Array[String] = get_settled_objects()
		print("T+: settled=%d/%d" % [settled.size(), objects.size()])
		for obj in objects:
			var p: Vector3 = obj.position
			var meta: Dictionary = obj.get_metadata()
			print("  %s: (%.2f, %.2f, %.2f) sleeping=%s mass=%.1f friction=%.1f bounciness=%.1f" % [
				meta["instance_id"], p.x, p.y, p.z, str(obj.is_sleeping()), meta["mass_kg"], meta["friction"], meta["bounciness"]
			])

	if _demo_timer >= _demo_duration:
		print("=== Final Object States ===")
		for obj in objects:
			var meta: Dictionary = obj.get_metadata()
			var p: Vector3 = obj.position
			print("  %s: sleeping=%s position=(%.3f, %.3f, %.3f) mass=%.1f friction=%.1f bounciness=%.1f" % [
				meta["instance_id"], str(obj.is_sleeping()), p.x, p.y, p.z, meta["mass_kg"], meta["friction"], meta["bounciness"]
			])
		print("==========================")
		get_tree().quit()

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
		add_child(obj)
		objects.append(obj)

		obj.body_entered.connect(func(other_body): _on_object_body_entered(obj, other_body))
		obj.object_landed.connect(func(instance_id): object_landed.emit(instance_id))

func _on_object_body_entered(obj, other_body: Node) -> void:
	var other_id: String = ""
	if other_body.has_meta("instance_id"):
		other_id = other_body.get_meta("instance_id")
	elif other_body.name:
		other_id = other_body.name
	object_collided.emit(obj.instance_id, other_id)

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
