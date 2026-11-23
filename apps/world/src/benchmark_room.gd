extends Room
class_name BenchmarkRoom

## Benchmark room setup - configures the world, objects, and demo scenario
## before injecting the agent. This is the "demo" layer separate from the
## core Room system.

@export_group("Benchmark Room Objects")
var object_definitions: Array = [
	{
		"instance_id": "obj_wood_cube",
		"type_id": "wood_cube",
		"name": "Wood Cube",
		"kind": "artifact",
		"shape_type": "box",
		"mass_kg": 2.0,
		"brittleness": 0.1,
		"throwable": true,
		"stackable": false,
		"friction": 0.8,
		"bounciness": 0.3,
		"density_kg_per_m3": 650,
		"dimensions_m": {"x": 0.6, "y": 0.6, "z": 0.6},
		"position": {"x": -2.0, "y": -13.105, "z": 3.0}
	},
	{
		"instance_id": "obj_metal_sphere",
		"type_id": "metal_sphere",
		"name": "Metal Sphere",
		"kind": "mineral",
		"shape_type": "sphere",
		"mass_kg": 5.0,
		"brittleness": 0.05,
		"throwable": true,
		"stackable": false,
		"friction": 0.4,
		"bounciness": 0.8,
		"density_kg_per_m3": 7800,
		"dimensions_m": {"x": 0.4, "y": 0.4, "z": 0.4},
		"position": {"x": 0.0, "y": -13.205, "z": 3.0}
	},
	{
		"instance_id": "obj_glass_box",
		"type_id": "glass_box",
		"name": "Glass Box",
		"kind": "artifact",
		"shape_type": "box",
		"mass_kg": 1.0,
		"brittleness": 0.9,
		"throwable": true,
		"stackable": false,
		"friction": 0.9,
		"bounciness": 0.5,
		"density_kg_per_m3": 2500,
		"dimensions_m": {"x": 0.5, "y": 0.5, "z": 0.5},
		"position": {"x": 2.0, "y": -13.155, "z": 3.0}
	},
	{
		"instance_id": "obj_rubber_cylinder",
		"type_id": "rubber_cylinder",
		"name": "Rubber Cylinder",
		"kind": "organic",
		"shape_type": "cylinder",
		"mass_kg": 3.0,
		"brittleness": 0.2,
		"throwable": true,
		"stackable": false,
		"friction": 0.7,
		"bounciness": 0.7,
		"density_kg_per_m3": 1100,
		"dimensions_m": {"x": 0.4, "y": 0.8, "z": 0.4},
		"position": {"x": 0.0, "y": -13.005, "z": 5.0}
	}
]

# Demo scenario timing (overrides config defaults)
@export_group("Demo Scenario")
@export var demo_duration_s: float = 15.0
# Phase 1: Curiosity exploration (start)
@export var demo_phase1_time_s: float = 0.0
# Phase 2: Uncertainty investigation (impulse on metal_sphere)
@export var demo_phase2_time_s: float = 3.0
# Phase 3: Integrity safety (impulse toward agent)
@export var demo_phase3_time_s: float = 8.0
# Phase 4: Reset
@export var demo_phase4_time_s: float = 12.0
@export var demo_scale_factor: float = 2.0

# Automatic impulses for demonstration
@export_group("Automatic Impulses")
@export var impulse1_time_s: float = 3.0
@export var impulse1_target_id: String = "obj_metal_sphere"
@export var impulse1_vector: Vector3 = Vector3(3.0, 0.0, 0.0)
@export var impulse2_time_s: float = 8.0
@export var impulse2_target_id: String = "obj_rubber_cylinder"
@export var impulse2_vector: Vector3 = Vector3(0.0, 0.0, -5.0)

func _ready() -> void:
	# Apply benchmark-specific object definitions before parent _ready spawns them
	# (parent's _ready calls _spawn_objects which we override)
	
	# Override demo timing from exports (these take precedence over config file)
	_demo_duration = demo_duration_s
	_demo_phase1_time = demo_phase1_time_s
	_demo_phase2_time = demo_phase2_time_s
	_demo_phase3_time = demo_phase3_time_s
	_demo_phase4_time = demo_phase4_time_s
	_demo_scale_factor = demo_scale_factor
	_demo_impulse1_time = impulse1_time_s
	_demo_impulse1_target_id = impulse1_target_id
	_demo_impulse1_vector = impulse1_vector
	_demo_impulse2_time = impulse2_time_s
	_demo_impulse2_target_id = impulse2_target_id
	_demo_impulse2_vector = impulse2_vector
	
	# Allow env var to override demo duration for acceptance tests
	var env_duration = OS.get_environment("AGENT_WORLD_DEMO_DURATION")
	if env_duration != "":
		_demo_duration = float(env_duration)
	
	# Call parent _ready which loads config, spawns agent, starts recorder
	super._ready()
	
	# Reset demo state after super._ready()
	_demo_timer = 0.0
	_demo_step = 0
	_impulse_applied = false
	_last_print_time = 0.0
	_landed_count = 0

func _spawn_objects() -> void:
	# Override parent's _spawn_objects to use our definitions
	# Create all objects first (initially sleeping) so they start falling simultaneously
	var created_objects: Array = []
	for def in object_definitions:
		var obj = load("res://src/rigid_object.gd").new()
		obj.configure(def)
		obj.position = Vector3(def["position"]["x"], def["position"]["y"], def["position"]["z"])
		_add_object_visual(obj, def)
		# Enable contact monitoring so body_entered signals fire on collisions
		obj.contact_monitor = true
		obj.max_contacts_reported = 1
		# Start sleeping so physics doesn't simulate until all objects are added
		obj.sleeping = true
		created_objects.append(obj)
	
	# Now add all objects to scene tree at once
	for obj in created_objects:
		add_child(obj)
		objects.append(obj)
		obj.body_entered.connect(_on_object_landed.bind(obj.instance_id))
	
	# Wake all objects simultaneously so they fall together
	for obj in created_objects:
		obj.set_sleeping(false)

func _add_object_visual(obj: RigidBody3D, def: Dictionary) -> void:
	var mesh_instance = MeshInstance3D.new()
	var shape_type = def["shape_type"]
	var dims = def["dimensions_m"]
	
	if shape_type == "box":
		var box_mesh = BoxMesh.new()
		box_mesh.size = Vector3(dims["x"], dims["y"], dims["z"])
		mesh_instance.mesh = box_mesh
	elif shape_type == "sphere":
		var sphere_mesh = SphereMesh.new()
		sphere_mesh.radius = dims["x"] / 2.0
		sphere_mesh.height = dims["x"]
		mesh_instance.mesh = sphere_mesh
	elif shape_type == "cylinder":
		var cylinder_mesh = CylinderMesh.new()
		cylinder_mesh.top_radius = dims["x"] / 2.0
		cylinder_mesh.bottom_radius = dims["x"] / 2.0
		cylinder_mesh.height = dims["y"]
		mesh_instance.mesh = cylinder_mesh
	
	# Material based on type_id
	var material = StandardMaterial3D.new()
	var type_id = def["type_id"]
	if type_id == "wood_cube":
		material.albedo_color = Color(0.6, 0.4, 0.2)
		material.roughness = 0.8
	elif type_id == "metal_sphere":
		material.albedo_color = Color(0.7, 0.7, 0.8)
		material.roughness = 0.2
		material.metallic = 0.9
	elif type_id == "glass_box":
		material.albedo_color = Color(0.8, 0.9, 1.0)
		material.roughness = 0.05
		material.transparency = 0.3
		material.render_priority = 1
	elif type_id == "rubber_cylinder":
		material.albedo_color = Color(0.2, 0.2, 0.3)
		material.roughness = 0.9
	material.cull_mode = StandardMaterial3D.CULL_BACK
	mesh_instance.material_override = material
	
	obj.add_child(mesh_instance)

func _process_demo(delta: float) -> void:
	# Update demo timer using simulation time (not wall time)
	if not _sim_time:
		return
	_demo_timer += delta
	
	# Demo sequence showing three drive behaviors:
	# Phase 1 (t=0): Curiosity - agent explores novel objects
	# Phase 2 (t=3): Uncertainty - impulse on metal_sphere -> agent investigates
	# Phase 3 (t=8): Physical Integrity - fast impulse on cylinder toward agent -> agent waits (safety)
	# Phase 4 (t=12): Reset
	
	if _demo_step == 0 and _demo_timer >= _demo_phase2_time:
		# Phase 2: Apply impulse to metal_sphere to create prediction error (uncertainty)
		var target = _find_object(_demo_impulse1_target_id)
		if target:
			apply_impulse(target.instance_id, _demo_impulse1_vector)
			_impulse_applied = true
			print("  PHASE 2: IMPULSE applied to %s at t=%.1fs (triggers Uncertainty > 0.6 -> investigate)" % [_demo_impulse1_target_id, _demo_timer])
		_demo_step = 1
	elif _demo_step == 1 and _demo_timer >= _demo_phase3_time:
		# Phase 3: Apply impulse to rubber_cylinder toward agent (integrity risk)
		var target = _find_object(_demo_impulse2_target_id)
		if target:
			apply_impulse(target.instance_id, _demo_impulse2_vector)
			print("  PHASE 3: IMPULSE applied to %s at t=%.1fs (triggers Integrity < 0.3 -> safety wait)" % [_demo_impulse2_target_id, _demo_timer])
		_demo_step = 2
	elif _demo_step == 2 and _demo_timer >= _demo_phase4_time:
		# Phase 4: Reset
		_cumulative_run_time += _sim_time.simulation_time
		_sim_time.reset()
		_sim_time.set_time_scale(1.0)
		_demo_step = 3
		_append_domain_event("simulation_reset", "", {
			"description": "Simulation reset by demo control",
			"reason": "demo_schedule",
			"cumulative_run_time_s": _cumulative_run_time,
		})
		print("  PHASE 4: SIM RESET at t=%.1fs (sim_time=%.3f, tick=%d, cumulative=%.3f)" % [_demo_timer, _sim_time.simulation_time, _sim_time.simulation_tick, _cumulative_run_time])
	
	# Print status once per second with simulation time
	if _verbose_logging and _demo_timer - _last_print_time >= 1.0:
		_last_print_time = _demo_timer
		var settled: Array[String] = get_settled_objects()
		print("T+: wall=%.1fs sim=%.3f tick=%d paused=%s scale=%.1f tod=%.1f settled=%d/%d landed=%d" % [
			_demo_timer, _sim_time.simulation_time, _sim_time.simulation_tick,
			str(_sim_time.is_paused), _sim_time.time_scale, _sim_time.get_time_of_day(),
			settled.size(), objects.size(), _landed_count
		])
		for obj in objects:
			var p: Vector3 = obj.position
			var meta: Dictionary = obj.get_metadata()
			print("  %s: (%.2f, %.2f, %.2f) sleeping=%s mass=%.1f friction=%.1f bounciness=%.1f shape=%s dims=(%.2f,%.2f,%.2f)" % [
				meta["instance_id"], p.x, p.y, p.z, str(obj.is_sleeping()), meta["mass_kg"], meta["friction"], meta["bounciness"],
				meta.get("shape_type", "unknown"), meta["dimensions_m"]["x"], meta["dimensions_m"]["y"], meta["dimensions_m"]["z"]
			])

func _on_object_landed(body: Node3D, instance_id: String) -> void:
	if body.is_in_group("room_boundary"):
		_landed_count += 1
		_append_domain_event("object_landed", instance_id, {
			"surface": body.name,
		})
		object_landed.emit(instance_id)

# Note: _process is defined in parent Room. We override _process_demo instead.
# The parent's _process calls _process_demo(delta) after updating demo_timer.
