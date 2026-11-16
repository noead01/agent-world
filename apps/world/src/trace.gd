extends RefCounted

class_name Trace

# Lightweight OpenTelemetry-compatible trace context for the Godot world runtime.
#
# Godot 4 has no official OpenTelemetry SDK for GDScript, so this implements a
# minimal trace context that:
# - Creates spans with stable names from docs/observability.md
# - Uses bounded attributes (no high-cardinality IDs as span attributes)
# - Propagates trace_id / span_id through the correlation envelope so traces
#   cross the Godot / agent-service boundary
# - Emits span events to the console for local development
#
# Span IDs follow OpenTelemetry format: trace_id is 32 hex chars, span_id is 16
# hex chars. These match the CorrelationContext.trace_id / span_id fields.

var _trace_id: String = ""
var _span_id: String = ""

# Stack of active spans for parent-child relationships.
var _span_stack: Array = []

# Stable span names (docs/observability.md).
const SPAN_PERCEPTION_COLLECT = "world.perception.collect"
const SPAN_OBSERVATION_PUBLISH = "world.observation.publish"
const SPAN_ACTION_EXECUTE = "world.action.execute"

func _init() -> void:
	_trace_id = Crypto.new().generate_random_bytes(16).hex_encode()
	_span_id = ""

# Start a span with a stable name and bounded attributes.
#
# ``parent_context`` is an optional dictionary with ``trace_id`` and ``span_id``
# keys representing a remote parent span (e.g., from an incoming agent-service
# message). When provided, the new span becomes a child of that remote span.
#
# Returns a span dictionary with ``name``, ``trace_id``, ``span_id``, and
# ``parent_span_id`` fields. The caller must call ``end_span(span)`` when the
# operation completes.
func start_span(name: String, parent_context: Dictionary = {}, attributes: Dictionary = {}) -> Dictionary:
	var parent_span_id: String = ""
	var child_trace_id: String = _trace_id

	if parent_context.has("trace_id") and parent_context["trace_id"] != "":
		child_trace_id = parent_context["trace_id"]
	if parent_context.has("span_id") and parent_context["span_id"] != "":
		parent_span_id = parent_context["span_id"]

	var new_span_id: String = Crypto.new().generate_random_bytes(8).hex_encode()

	var span: Dictionary = {
		"name": name,
		"trace_id": child_trace_id,
		"span_id": new_span_id,
		"parent_span_id": parent_span_id,
		"attributes": attributes,
		"started_at": Time.get_ticks_msec(),
	}

	_span_stack.append(span)

	# Emit span start for local observability.
	var attr_str: String = ""
	if attributes.size() > 0:
		attr_str = " attrs=%s" % [JSON.stringify(attributes)]
	print("TRACE_SPAN: start=%s trace_id=%s span_id=%s parent=%s%s" % [
		name, child_trace_id, new_span_id, parent_span_id if parent_span_id != "" else "-", attr_str,
	])

	return span

# End a span and pop it from the stack.
func end_span(span: Dictionary) -> void:
	var index: int = _span_stack.find(span, 0)
	if index >= 0:
		_span_stack.remove_at(index)
	var duration_ms: int = Time.get_ticks_msec() - int(span.get("started_at", 0))
	print("TRACE_SPAN: end=%s trace_id=%s span_id=%s duration_ms=%d" % [
		span.get("name", ""), span.get("trace_id", ""), span.get("span_id", ""), duration_ms,
	])

# Get the current trace ID (for propagation in correlation contexts).
func get_trace_id() -> String:
	if _trace_id == "":
		_trace_id = Crypto.new().generate_random_bytes(16).hex_encode()
	return _trace_id

# Convert a span's context to bounded correlation fields for propagation.
func span_to_correlation_fields(span: Dictionary) -> Dictionary:
	return {
		"trace_id": span.get("trace_id", ""),
		"span_id": span.get("span_id", ""),
	}

# Build a full correlation dictionary from a span, for outbound messages.
func span_to_correlation(span: Dictionary) -> Dictionary:
	return {
		"trace_id": span.get("trace_id", ""),
		"span_id": span.get("span_id", ""),
	}

# Build bounded span attributes from world correlation data. run_id is
# intentionally excluded (high cardinality); it stays in the correlation
# envelope.
func bounded_attributes(
	experiment_id: String = "",
	scenario_id: String = "",
	scenario_version: String = "",
	agent_id: String = "",
	world_revision: int = 0,
	simulation_tick: int = 0,
	simulation_time: float = 0.0,
	component: String = "world",
	component_version: String = "1.0.0",
) -> Dictionary:
	return {
		"experiment.id": experiment_id,
		"scenario.id": scenario_id,
		"scenario.version": scenario_version,
		"agent.id": agent_id,
		"world.revision": world_revision,
		"simulation.tick": simulation_tick,
		"simulation.time": simulation_time,
		"component": component,
		"component.version": component_version,
	}

# Metrics emission (console-based for local development)
# In GDScript, we emit metrics as structured log lines that can be parsed
# by the console exporter or collected by a metrics aggregator.

# Metrics storage
var _metrics_initialized: bool = false

func _init_metrics():
	if _metrics_initialized:
		return
	_metrics_initialized = true

func _build_metric_attributes(
	experiment_id: String,
	scenario_id: String,
	scenario_version: String,
	agent_id: String,
	world_revision: int,
	simulation_tick: int,
	simulation_time: float,
	attributes: Dictionary
) -> Dictionary:
	var base = bounded_attributes(
		experiment_id,
		scenario_id,
		scenario_version,
		agent_id,
		world_revision,
		simulation_tick,
		simulation_time,
	)
	for key in attributes:
		base[key] = attributes[key]
	return base

func record_counter(
	name: String,
	value: float = 1.0,
	attributes: Dictionary = {},
	experiment_id: String = "",
	scenario_id: String = "",
	scenario_version: String = "",
	agent_id: String = "",
	world_revision: int = 0,
	simulation_tick: int = 0,
	simulation_time: float = 0.0,
) -> void:
	if not _metrics_initialized:
		_init_metrics()
	var attrs = _build_metric_attributes(
		experiment_id,
		scenario_id,
		scenario_version,
		agent_id,
		world_revision,
		simulation_tick,
		simulation_time,
		attributes
	)
	print("METRIC_COUNTER: name=%s value=%f attrs=%s" % [name, value, JSON.stringify(attrs)])

func record_histogram(
	name: String,
	value: float,
	attributes: Dictionary = {},
	experiment_id: String = "",
	scenario_id: String = "",
	scenario_version: String = "",
	agent_id: String = "",
	world_revision: int = 0,
	simulation_tick: int = 0,
	simulation_time: float = 0.0,
) -> void:
	if not _metrics_initialized:
		_init_metrics()
	var attrs = _build_metric_attributes(
		experiment_id,
		scenario_id,
		scenario_version,
		agent_id,
		world_revision,
		simulation_tick,
		simulation_time,
		attributes
	)
	print("METRIC_HISTOGRAM: name=%s value=%f attrs=%s" % [name, value, JSON.stringify(attrs)])

func set_gauge(
	name: String,
	value: float,
	attributes: Dictionary = {},
	experiment_id: String = "",
	scenario_id: String = "",
	scenario_version: String = "",
	agent_id: String = "",
	world_revision: int = 0,
	simulation_tick: int = 0,
	simulation_time: float = 0.0,
) -> void:
	if not _metrics_initialized:
		_init_metrics()
	var attrs = _build_metric_attributes(
		experiment_id,
		scenario_id,
		scenario_version,
		agent_id,
		world_revision,
		simulation_tick,
		simulation_time,
		attributes
	)
	print("METRIC_GAUGE: name=%s value=%f attrs=%s" % [name, value, JSON.stringify(attrs)])
