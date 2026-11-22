extends Resource
class_name ConfigLoader

## Loads and provides access to world configuration from JSON file.
## Centralizes all configurable parameters for the benchmark room.

static var _config: Dictionary = {}
static var _loaded: bool = false

static func load_config(config_path: String = "res://config/world_config.json") -> void:
	if _loaded:
		return
	var file = FileAccess.open(config_path, FileAccess.READ)
	if file == null:
		push_error("ConfigLoader: Failed to open config file: " + config_path)
		return
	var json_text = file.get_as_text()
	file.close()
	var parse_result = JSON.parse_string(json_text)
	if not parse_result.error == OK:
		push_error("ConfigLoader: Failed to parse JSON: " + parse_result.error_string)
		return
	_config = parse_result
	_loaded = true

static func get_value(path: String, default = null):
	if not _loaded:
		load_config()
	var keys = path.split(".")
	var current = _config
	for key in keys:
		if current.has(key):
			current = current[key]
		else:
			return default
	return current

static func get_room() -> Dictionary:
	return get_value("room", {})

static func get_protocol() -> Dictionary:
	return get_value("protocol", {})

static func get_experiment() -> Dictionary:
	return get_value("experiment", {})

static func get_agent() -> Dictionary:
	return get_value("agent", {})

static func get_agent_service() -> Dictionary:
	return get_value("agent_service", {})

static func get_drive_policy() -> Dictionary:
	return get_value("drive_policy", {})

static func get_simulation() -> Dictionary:
	return get_value("simulation", {})

static func get_metrics() -> Dictionary:
	return get_value("metrics", {})