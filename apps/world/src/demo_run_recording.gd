extends Node3D

class_name DemoRunRecording

# Demonstration of TODO-0010: Append-Only Run Recording.
#
# Runs a self-contained physics scene (no external agent service required) and
# persists every behaviorally significant event to a run directory via
# EventRecorder. An on-screen HUD shows the live event stream so the recording
# can be observed in real time. When the demo ends it prints the run directory
# so the persisted run.json / events.jsonl / validity.jsonl can be inspected.

@export var _demo_duration: float = 10.0
@export var runs_directory: String = ""
@export var show_hud: bool = true

# Demo schedule (wall-clock seconds into the demo).
var _demo_impulse_time: float = 1.0
var _demo_pause_time: float = 2.0
var _demo_resume_time: float = 4.0
var _demo_scale_time: float = 6.0
var _demo_reset_time: float = 8.0

var _demo_timer: float = 0.0
var _demo_step: int = 0
var _cumulative_run_time: float = 0.0

var objects: Array = []
var _sim_time
var _event_recorder
var _agent
var _light
var _run_path: String = ""

# HUD nodes
var _hud_canvas: CanvasLayer
var _hud_title: Label
var _hud_status: Label
var _hud_clock: Label
var _hud_event_count: Label
var _hud_event_log: Label
var _event_log_lines: Array = []

func _ready() -> void:
	# Deterministic fixed timestep for replayable demos.
	ProjectSettings.set_setting("physics/3d/physics_engine", "JoltPhysics")
	ProjectSettings.set_setting("physics/common/physics_fps", 60.0)
	var space: RID = get_world_3d().space
	PhysicsServer3D.space_set_param(space, 0, -9.8)

	# Lighting (day/night driven by SimulationTime) - use the scene light if present.
	var light = get_node_or_null("DemoLight")
	if light == null:
		light = DirectionalLight3D.new()
		light.name = "DemoLight"
		light.rotation_degrees = Vector3(-45, -30, 0)
		add_child(light)
	_light = light

	# Build room bounds.
	_build_room_boundaries()

	# Spawn physical objects.
	_spawn_objects()

	# Spawn the embodied agent (idles in place; no external service needed).
	_spawn_agent()

	# Simulation time (single source of truth for clocks and event timestamps).
	var sim_time = SimulationTime.new()
	sim_time.day_cycle_duration_s = 300.0
	add_child(sim_time)
	_sim_time = sim_time
	_sim_time.time_of_day_changed.connect(_animate_day_night)

	# Event recorder - the component under demonstration.
	var recorder = EventRecorder.new()
	recorder.runs_directory = _effective_runs_directory()
	recorder.validate_events = true
	add_child(recorder)
	_event_recorder = recorder

	# Build a stable, unique run id so repeated demos never collide.
	var timestamp_sec = Time.get_unix_time_from_system()
	var timestamp_msec = Time.get_ticks_msec()
	var random_component = randi() % 10000
	var run_id = "demo_run_%d_%03d_%04d" % [timestamp_sec, timestamp_msec % 1000, random_component]
	var random_seed = hash(run_id) & 0x7FFFFFFF

	print("=== DemoRunRecording (TODO-0010 visual demo) ===")
	print("Run ID: %s" % [run_id])
	print("Runs directory: %s" % [_event_recorder.runs_directory])

	var config_fingerprint = ""
	# Minimal fingerprint for the demo (world settings only).
	config_fingerprint = _compute_demo_fingerprint()

	var success = _event_recorder.start_run(
		run_id,
		"first_benchmark_room",
		_agent.agent_id,
		random_seed,
		config_fingerprint
	)
	if not success:
		push_error("Demo: Failed to start event recorder")
		get_tree().quit()
		return

	# Capture the run directory before end_run() clears the recorder's active-path state.
	_run_path = _event_recorder.get_run_status().get("path", "")

	# Persist initial conditions as the first domain event.
	var initial_objects: Array = []
	for obj in objects:
		var meta: Dictionary = obj.get_metadata()
		var p: Vector3 = obj.position
		initial_objects.append({
			"instance_id": meta["instance_id"],
			"type_id": meta.get("type_id", "unknown"),
			"position": {"x": p.x, "y": p.y, "z": p.z},
			"sleeping": obj.is_sleeping(),
		})
	_append_domain_event("run_started", "", {
		"description": "Simulation started",
		"initial_objects": initial_objects,
		"initial_agent_state": {
			"id": _agent.agent_id,
			"status": _agent.status,
			"position": _agent.global_position,
		},
	})

	# Connect recorder signals so the HUD reflects the live stream.
	_event_recorder.event_appended.connect(_on_event_appended)
	_event_recorder.run_ended.connect(_on_run_ended)
	_event_recorder.run_failed.connect(_on_run_failed)

	# On-screen HUD.
	if show_hud:
		_build_hud(run_id)

	set_process(true)
	set_physics_process(true)

	print("=================================")

func _effective_runs_directory() -> String:
	if runs_directory != "":
		return runs_directory
	# Default to a writable location outside the repository checkout so the
	# persisted run directory is easy to locate after the demo exits.
	var user_dir = OS.get_user_data_dir()
	var demo_dir = "demo-runs"
	var full = "user://demo-runs"
	# user:// is abstract; resolve once so we can print the real path.
	var resolved = OS.get_user_data_dir() + "/demo-runs"
	DirAccess.make_dir_recursive_absolute(resolved)
	return resolved

func _build_hud(run_id: String) -> void:
	var canvas = CanvasLayer.new()
	canvas.layer = 100
	add_child(canvas)
	_hud_canvas = canvas

	var container = VBoxContainer.new()
	canvas.add_child(container)

	var panel = ColorRect.new()
	panel.color = Color(0, 0, 0, 0.6)
	panel.size = Vector2(340, 260)
	container.add_child(panel)

	var margin = MarginContainer.new()
	container.add_child(margin)

	var vbox = VBoxContainer.new()
	margin.add_child(vbox)

	_hud_title = Label.new()
	_hud_title.text = "TODO-0010: Append-Only Run Recording"
	_hud_title.add_theme_font_size_override("font_size", 16)
	_hud_title.add_theme_color_override("font_color", Color(1, 1, 1))
	vbox.add_child(_hud_title)

	var run_label = Label.new()
	run_label.text = "Run: %s" % [run_id]
	run_label.add_theme_font_size_override("font_size", 12)
	run_label.add_theme_color_override("font_color", Color(0.8, 0.8, 0.8))
	vbox.add_child(run_label)

	_hud_status = Label.new()
	_hud_status.text = "Status: running"
	_hud_status.add_theme_font_size_override("font_size", 13)
	_hud_status.add_theme_color_override("font_color", Color(0.5, 1, 0.5))
	vbox.add_child(_hud_status)

	_hud_clock = Label.new()
	_hud_clock.text = "Sim time: 0.000s  |  paused: no  |  scale: 1.0x"
	_hud_clock.add_theme_font_size_override("font_size", 12)
	_hud_clock.add_theme_color_override("font_color", Color(1, 1, 1))
	vbox.add_child(_hud_clock)

	_hud_event_count = Label.new()
	_hud_event_count.text = "Events recorded: 0"
	_hud_event_count.add_theme_font_size_override("font_size", 12)
	_hud_event_count.add_theme_color_override("font_color", Color(1, 1, 0.5))
	vbox.add_child(_hud_event_count)

	var log_label_title = Label.new()
	log_label_title.text = "Live event stream:"
	log_label_title.add_theme_font_size_override("font_size", 11)
	log_label_title.add_theme_color_override("font_color", Color(0.7, 0.7, 1))
	vbox.add_child(log_label_title)

	_hud_event_log = Label.new()
	_hud_event_log.add_theme_font_size_override("font_size", 11)
	_hud_event_log.add_theme_color_override("font_color", Color(0.9, 0.9, 0.9))
	_hud_event_log.text = "Waiting for first event..."
	vbox.add_child(_hud_event_log)

func _build_room_boundaries() -> void:
	var bounds = [
		{"name": "floor", "position": Vector3(0, -13.5, 0), "size": Vector3(27, 0.2, 27)},
		{"name": "ceiling", "position": Vector3(0, 13.5, 0), "size": Vector3(27, 0.2, 27)},
		{"name": "wall_west", "position": Vector3(-13.5, 0, 0), "size": Vector3(0.2, 27, 27)},
		{"name": "wall_east", "position": Vector3(13.5, 0, 0), "size": Vector3(0.2, 27, 27)},
		{"name": "wall_north", "position": Vector3(0, 0, -13.5), "size": Vector3(27, 27, 0.2)},
		{"name": "wall_south", "position": Vector3(0, 0, 13.5), "size": Vector3(27, 27, 0.2)},
	]
	for b in bounds:
		var body = StaticBody3D.new()
		body.name = b["name"]
		body.position = b["position"]
		add_child(body)
		var shape_node = CollisionShape3D.new()
		var box = BoxShape3D.new()
		box.size = b["size"]
		shape_node.shape = box
		body.add_child(shape_node)

func _spawn_objects() -> void:
	var definitions = [
		{"instance_id": "obj_wood_cube", "type_id": "wood_cube", "name": "Wood Cube", "kind": "artifact",
		 "shape_type": "box", "mass_kg": 2.0, "friction": 0.8, "bounciness": 0.3,
		 "dimensions_m": {"x": 0.6, "y": 0.6, "z": 0.6},
		 "position": Vector3(0, 5, 0), "color": Color(0.54, 0.37, 0.24)},
		{"instance_id": "obj_metal_sphere", "type_id": "metal_sphere", "name": "Metal Sphere", "kind": "mineral",
		 "shape_type": "sphere", "mass_kg": 5.0, "friction": 0.4, "bounciness": 0.8,
		 "dimensions_m": {"x": 0.4, "y": 0.4, "z": 0.4},
		 "position": Vector3(2, 5, 0), "color": Color(0.6, 0.65, 0.7)},
		{"instance_id": "obj_glass_box", "type_id": "glass_box", "name": "Glass Box", "kind": "artifact",
		 "shape_type": "box", "mass_kg": 1.0, "friction": 0.9, "bounciness": 0.5,
		 "dimensions_m": {"x": 0.5, "y": 0.5, "z": 0.5},
		 "position": Vector3(-2, 5, 0), "color": Color(0.2, 0.7, 0.8)},
		{"instance_id": "obj_rubber_cylinder", "type_id": "rubber_cylinder", "name": "Rubber Cylinder", "kind": "organic",
		 "shape_type": "cylinder", "mass_kg": 3.0, "friction": 0.7, "bounciness": 0.7,
		 "dimensions_m": {"x": 0.4, "y": 0.8, "z": 0.4},
		 "position": Vector3(0, 5, 2), "color": Color(0.9, 0.4, 0.6)},
	]

	for defn in definitions:
		var obj = RigidObject.new()
		obj.configure(defn)
		obj.position = defn["position"]
		obj.contact_monitor = true
		obj.max_contacts_reported = 1
		add_child(obj)
		objects.append(obj)

		# Visible mesh (rigid_object.gd only adds a collision shape).
		var mesh_instance = MeshInstance3D.new()
		var color = defn["color"]
		if defn["shape_type"] == "box":
			var mesh = BoxMesh.new()
			mesh.size = Vector3(
				float(defn["dimensions_m"]["x"]),
				float(defn["dimensions_m"]["y"]),
				float(defn["dimensions_m"]["z"]),
			)
			mesh_instance.mesh = mesh
		elif defn["shape_type"] == "sphere":
			var mesh = SphereMesh.new()
			mesh.radius = float(defn["dimensions_m"]["x"]) / 2.0
			mesh_instance.mesh = mesh
		elif defn["shape_type"] == "cylinder":
			var mesh = CylinderMesh.new()
			mesh.height = float(defn["dimensions_m"]["y"])
			mesh_instance.mesh = mesh
		var material = StandardMaterial3D.new()
		material.albedo_color = color
		mesh_instance.material_override = material
		obj.add_child(mesh_instance)

		obj.body_entered.connect(func(other_body): _on_object_body_entered(obj, other_body))
		obj.object_landed.connect(func(instance_id): _on_object_landed(instance_id))

func _spawn_agent() -> void:
	var agent = Agent.new()
	agent.agent_id = "wanderer_01"
	agent.agent_type_id = "exploration_agent"
	agent.spawn_position = Vector3(0, -12.94, 1.5)
	add_child(agent)
	agent.set_room(self, _sim_time)
	_agent = agent

	# Visible agent capsule (with collision shape for move_and_slide).
	var agent_shape = CollisionShape3D.new()
	var capsule = CapsuleShape3D.new()
	capsule.radius = 0.3
	capsule.height = 1.0
	agent_shape.shape = capsule
	agent.add_child(agent_shape)
	var agent_mesh = MeshInstance3D.new()
	var agent_capsule_mesh = CapsuleMesh.new()
	agent_capsule_mesh.radius = 0.3
	agent_capsule_mesh.height = 1.0
	agent_mesh.mesh = agent_capsule_mesh
	var agent_material = StandardMaterial3D.new()
	agent_material.albedo_color = Color(0.2, 0.6, 1.0)
	agent_mesh.material_override = agent_material
	agent.add_child(agent_mesh)

	# Connect agent action signals (recorded even without an agent service).
	_agent.action_started.connect(_on_agent_action_started)
	_agent.action_completed.connect(_on_agent_action_completed)
	_agent.action_failed.connect(_on_agent_action_failed)
	_agent.action_interrupted.connect(_on_agent_action_interrupted)

func _compute_demo_fingerprint() -> String:
	# Minimal deterministic fingerprint for the demo scene.
	var config = {
		"scenario_id": "first_benchmark_room",
		"scenario_version": "1.0.0",
		"world": {
			"half_size": {"x": 13.5, "y": 13.5, "z": 13.5},
			"gravity": {"x": 0, "y": -9.8, "z": 0},
			"fixed_timestep_hz": 60.0,
			"physics_engine": "JoltPhysics",
		},
		"agent": {
			"agent_id": "wanderer_01",
			"move_speed": _agent.move_speed,
			"spawn_position": {"x": 0, "y": -12.94, "z": 1.5},
		},
		"objects": _metadata_array(objects),
	}
	var canonical = _canonicalize_config(config)
	var json_text = JSON.stringify(canonical)
	var hashing = HashingContext.new()
	hashing.start(HashingContext.HASH_SHA256)
	hashing.update(json_text.to_utf8_buffer())
	return hashing.finish().hex_encode()

func _canonicalize_config(value: Variant) -> Variant:
	if value is Dictionary:
		var canonical = {}
		var keys = value.keys()
		keys.sort()
		for key in keys:
			canonical[key] = _canonicalize_config(value[key])
		return canonical
	if value is Array:
		var canonical = []
		for item in value:
			canonical.append(_canonicalize_config(item))
		return canonical
	return value

func _vector_to_dict(vector: Vector3) -> Dictionary:
	return {"x": vector.x, "y": vector.y, "z": vector.z}

func _metadata_array(objs: Array) -> Array:
	var result = []
	for obj in objs:
		result.append(obj.get_metadata())
	return result

# --- Demo sequence (one-shot control transitions) --------------------------

func _physics_process(delta: float) -> void:
	_sim_time.tick(delta)
	_demo_timer += delta
	_update_hud()

	# Gravity only when not paused.
	if not _sim_time.is_paused:
		for obj in objects:
			if not obj.is_sleeping():
				obj.apply_central_force(Vector3(0, -9.8, 0) * obj.mass)
	else:
		for obj in objects:
			obj.linear_velocity = Vector3(0, 0, 0)
			obj.angular_velocity = Vector3(0, 0, 0)

	# One-shot demo transitions.
	if _demo_step == 0 and _demo_timer >= _demo_impulse_time:
		var target = _find_object("obj_metal_sphere")
		if target:
			target.apply_central_impulse(Vector3(2.0, 0.0, 0.0))
			_append_domain_event("object_impulse_applied", "obj_metal_sphere", {
				"impulse": {"x": 2.0, "y": 0.0, "z": 0.0},
				"description": "Applied impulse to obj_metal_sphere",
			})
			print("  IMPULSE applied at t=%.1fs" % [_demo_timer])
		_demo_step = 1

	elif _demo_step == 1 and _demo_timer >= _demo_pause_time:
		_sim_time.pause()
		_append_domain_event("simulation_paused", "", {
			"description": "Simulation paused by demo control",
			"reason": "demo_schedule",
			"simulation_tick": _sim_time.simulation_tick,
		})
		print("  SIM PAUSED at t=%.1fs" % [_demo_timer])
		_demo_step = 2

	elif _demo_step == 2 and _demo_timer >= _demo_resume_time:
		_sim_time.resume()
		_append_domain_event("simulation_resumed", "", {
			"description": "Simulation resumed by demo control",
			"reason": "demo_schedule",
			"simulation_tick": _sim_time.simulation_tick,
		})
		print("  SIM RESUMED at t=%.1fs" % [_demo_timer])
		_demo_step = 3

	elif _demo_step == 3 and _demo_timer >= _demo_scale_time:
		_sim_time.set_time_scale(2.0)
		_append_domain_event("simulation_time_scale_changed", "", {
			"description": "Simulation time scale changed by demo control",
			"reason": "demo_schedule",
			"time_scale": 2.0,
			"simulation_tick": _sim_time.simulation_tick,
		})
		print("  TIME SCALE 2.0 at t=%.1fs" % [_demo_timer])
		_demo_step = 4

	elif _demo_step == 4 and _demo_timer >= _demo_reset_time:
		# Accumulate sim time before reset so post-reset timestamps stay monotonic.
		_cumulative_run_time += _sim_time.simulation_time
		_sim_time.reset()
		_sim_time.set_time_scale(1.0)
		_append_domain_event("simulation_reset", "", {
			"description": "Simulation reset by demo control",
			"reason": "demo_schedule",
		})
		print("  SIM RESET at t=%.1fs" % [_demo_timer])
		_demo_step = 5

	elif _demo_step == 5 and _demo_timer >= _demo_duration:
		# End the run cleanly. Pass the cumulative run time (including pre-reset
		# simulation time) so run.json's simulation_time_s matches run_ended's
		# timestamp_s, which the completed-duration validation requires.
		var total_run_time = _cumulative_run_time + _sim_time.simulation_time
		_append_domain_event("run_ended", "", {
			"description": "Simulation ended",
			"final_objects": _metadata_array(objects),
		})
		var ok = _event_recorder.end_run(total_run_time)
		print("  RUN ENDED at t=%.1fs (end_run ok=%s)" % [_demo_timer, str(ok)])
		_demo_step = 6
		# Quit after a brief pause so the final state flushes to disk.
		set_process(false)
		set_physics_process(false)
		get_tree().create_timer(1.0).timeout.connect(func(): _finish_demo())

	return

func _finish_demo() -> void:
	var status = _event_recorder.get_run_status()
	print("=== Demo complete ===")
	print("Run directory: %s" % [_run_path])
	print("Status: %s" % [status["validity"]])
	print("Event count: %d" % [status["event_count"]])
	print("Files: run.json, events.jsonl, validity.jsonl")
	print("Inspect with: python3 -m agent_world_contracts.run_record <run-dir>")
	print("===================")
	get_tree().quit()

# --- Event recording --------------------------------------------------------

func _append_domain_event(event_type_id: String, target_id: String, metadata: Dictionary) -> void:
	if _event_recorder == null:
		return
	var event = {
		"id": "evt_%s_%04d" % [event_type_id, _event_recorder.get_run_status().event_count + 1],
		"run_id": _event_recorder.get_run_status().run_id,
		"timestamp_s": _cumulative_run_time + _sim_time.simulation_time,
		"version": "1.0.0",
		"event_type_id": event_type_id,
		"target_instance_id": target_id,
		"description": metadata.get("description", ""),
		"severity": "info",
		"metadata": metadata,
	}
	var success = _event_recorder.append_event(event)
	if not success:
		print("ERROR: Failed to append domain event: %s" % [event_type_id])

func _on_event_appended(event: Dictionary) -> void:
	_event_log_lines.append("[%.3fs] %s" % [event.get("timestamp_s", 0.0), event.get("event_type_id", "?")])
	if _event_log_lines.size() > 14:
		_event_log_lines.pop_front()
	if _hud_event_log:
		_hud_event_log.text = "\n".join(_event_log_lines)
	var count = _event_recorder.get_run_status().event_count
	if _hud_event_count:
		_hud_event_count.text = "Events recorded: %d" % [count]

func _on_run_ended(run_id: String, status: String) -> void:
	if _hud_status:
		_hud_status.text = "Status: %s" % [status]
		_hud_status.add_theme_color_override("font_color", Color(0.5, 1, 0.5) if status == "completed" else Color(1, 0.5, 0.5))

func _on_run_failed(run_id: String, reason: String) -> void:
	print("RUN FAILED: %s - %s" % [run_id, reason])
	if _hud_status:
		_hud_status.text = "Status: aborted"
		_hud_status.add_theme_color_override("font_color", Color(1, 0.3, 0.3))
	get_tree().quit()

# --- Agent / collision handlers ---------------------------------------------

func _on_object_body_entered(obj, other_body: Node) -> void:
	var other_id: String = ""
	if other_body.has_meta("instance_id"):
		other_id = other_body.get_meta("instance_id")
	elif other_body.name:
		other_id = other_body.name
	_append_domain_event("object_collided", obj.instance_id, {"other_id": other_id, "description": "Collision"})

func _on_object_landed(instance_id: String) -> void:
	_append_domain_event("object_landed", instance_id, {"description": "Object landed"})

func _on_agent_action_started(action_type_id: String, target_instance_id: String, command_id: String) -> void:
	_append_domain_event("agent_action_started", target_instance_id, {
		"action_type": action_type_id,
		"command_id": command_id,
		"description": "Agent started %s action" % [action_type_id],
	})

func _on_agent_action_completed(action_type_id: String, result: String, command_id: String) -> void:
	_append_domain_event("agent_action_completed", "", {
		"action_type": action_type_id,
		"result": result,
		"command_id": command_id,
		"description": "Agent completed %s with %s" % [action_type_id, result],
	})

func _on_agent_action_failed(action_type_id: String, reason: String, command_id: String) -> void:
	_append_domain_event("agent_action_failed", "", {
		"action_type": action_type_id,
		"reason": reason,
		"command_id": command_id,
		"description": "Agent %s failed: %s" % [action_type_id, reason],
	})

func _on_agent_action_interrupted(action_type_id: String, command_id: String) -> void:
	_append_domain_event("agent_action_interrupted", "", {
		"action_type": action_type_id,
		"command_id": command_id,
		"description": "Agent %s interrupted" % [action_type_id],
	})

func _find_object(instance_id: String):
	for obj in objects:
		if obj.instance_id == instance_id:
			return obj
	return null

func _animate_day_night(hour: float) -> void:
	if _light == null:
		return
	var angle = (hour - 6.0) / 24.0 * TAU
	var elevation = sin(angle)
	var azimuth = cos(angle)
	_light.rotation_degrees = Vector3(-90.0 + elevation * 45.0, azimuth * 30.0, 0)
	var energy = clamp(0.2 + 0.8 * max(0.0, sin(angle)), 0.1, 1.0)
	_light.light_energy = energy

func _update_hud() -> void:
	if not _hud_clock:
		return
	_hud_clock.text = "Sim time: %.3fs  |  paused: %s  |  scale: %.2fx" % [
		_sim_time.simulation_time,
		str(_sim_time.is_paused),
		_sim_time.time_scale,
	]
