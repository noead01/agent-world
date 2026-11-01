extends Resource

class_name ObjectCatalog

@export var object_types: Array[Dictionary] = []

var type_lookup: Dictionary = {}

func load_from_json(json_text: String) -> void:
	var parser: JSON = JSON.new()
	var result: Variant = parser.parse(json_text)
	if typeof(result) != TYPE_DICTIONARY:
		push_error("ObjectCatalog: invalid JSON payload")
		return

	var raw_types: Array = result.get("objectTypes", result.get("object_types", []))
	type_lookup.clear()
	object_types.clear()

	for entry in raw_types:
		if typeof(entry) == TYPE_DICTIONARY:
			var id: String = String(entry.get("id", ""))
			type_lookup[id] = entry
			object_types.append(entry)

func get_type(type_id: String) -> Dictionary:
	return type_lookup.get(type_id, {})

func has_type(type_id: String) -> bool:
	return type_lookup.has(type_id)

func get_all_type_ids() -> Array[String]:
	return type_lookup.keys()
