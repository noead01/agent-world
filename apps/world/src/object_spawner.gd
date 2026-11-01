extends Node3D

class_name ObjectSpawner

@export var catalog: ObjectCatalog
@export var catalog_path: String = "res://schemas/island-object-types.json"
@export var object_scene: PackedScene

var spawned: Array[IslandObject] = []

func _ready() -> void:
	if catalog == null:
		catalog = ObjectCatalog.new()
		var file: FileAccess = FileAccess.open(catalog_path, FileAccess.READ)
		if file:
			catalog.load_from_json(file.get_as_text())
			file.close()

func _instantiate_object() -> IslandObject:
	if object_scene:
		return object_scene.instantiate()
	return IslandObject.new()

func spawn(type_id: String, position: Vector3 = Vector3.ZERO, overrides: Dictionary = {}) -> IslandObject:
	if not catalog.has_type(type_id):
		push_error("ObjectSpawner: unknown type_id '%s'" % type_id)
		return null

	var type_def: Dictionary = catalog.get_type(type_id)
	var instance: IslandObject = _instantiate_object()
	add_child(instance)

	var instance_overrides: Dictionary = {
		"instance_id": overrides.get("instance_id", type_id),
		"position": position,
	}

	if overrides.has("size_scale"):
		instance_overrides["size_scale"] = overrides["size_scale"]
	else:
		instance_overrides["size_scale"] = 1.0 + (randf() - 0.5) * 0.3

	if overrides.has("orientation"):
		instance_overrides["orientation"] = overrides["orientation"]
	else:
		instance_overrides["orientation"] = Vector3(
			randf_range(0, 360),
			randf_range(0, 360),
			randf_range(0, 360)
		)

	instance.configure(type_def, instance_overrides)
	spawned.append(instance)
	return instance

func spawn_batch(type_id: String, count: int, center: Vector3 = Vector3.ZERO, spread: float = 5.0, overrides: Dictionary = {}) -> Array[IslandObject]:
	var results: Array[IslandObject] = []
	for i in range(count):
		var jitter: Vector3 = Vector3(
			randf_range(-spread, spread),
			0,
			randf_range(-spread, spread)
		)
		var inst_overrides: Dictionary = overrides.duplicate()
		inst_overrides["instance_id"] = "%s_%d" % [type_id, i]
		var inst: IslandObject = spawn(type_id, center + jitter, inst_overrides)
		if inst:
			results.append(inst)
	return results

func despawn_all() -> void:
	for inst in spawned:
		if inst.is_inside_tree():
			inst.queue_free()
	spawned.clear()

func get_spawned() -> Array[IslandObject]:
	return spawned.duplicate()
