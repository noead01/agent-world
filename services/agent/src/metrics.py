"""OpenTelemetry metrics for the agent service (TODO-0012).

Initializes a meter provider with a console exporter for local development.
Exporter failure fails open: it never blocks simulation or agent behavior.

Metrics use stable names from docs/observability.md and bounded attributes.
High-cardinality identifiers (run_id, object_id, request_id) are carried in
the correlation context, not as metric attributes.
"""
from __future__ import annotations

import os
from typing import Optional

from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import ConsoleMetricExporter, PeriodicExportingMetricReader

_METER: Optional[metrics.Meter] = None
_METER_PROVIDER: Optional[MeterProvider] = None

# Metric attribute keys (bounded cardinality)
EXPERIMENT_ID_ATTR = "experiment.id"
SCENARIO_ID_ATTR = "scenario.id"
SCENARIO_VERSION_ATTR = "scenario.version"
AGENT_ID_ATTR = "agent.id"
WORLD_REVISION_ATTR = "world.revision"
SIMULATION_TICK_ATTR = "simulation.tick"
SIMULATION_TIME_ATTR = "simulation.time"
COMPONENT_ATTR = "component"
COMPONENT_VERSION_ATTR = "component.version"
ACTION_TYPE_ATTR = "action.type"
RESULT_ATTR = "result"
MESSAGE_TYPE_ATTR = "message.type"
DIRECTION_ATTR = "direction"
OUTCOME_ATTR = "outcome"
DRIVE_TYPE_ATTR = "drive.type"
REFLEX_TYPE_ATTR = "reflex.type"
SELECTION_REASON_ATTR = "selection.reason"
WINNER_LAYER_ATTR = "winner.layer"
REASON_CATEGORY_ATTR = "reason.category"
CONTROLLER_ATTR = "controller"
ERROR_CATEGORY_ATTR = "error.category"
PROVIDER_ATTR = "provider"
MODEL_FAMILY_ATTR = "model.family"
PURPOSE_ATTR = "purpose"
MEMORY_TYPE_ATTR = "memory.type"
BELIEF_STATUS_ATTR = "belief.status"
REVISION_CATEGORY_ATTR = "revision.category"
DISCOVERY_STAGE_ATTR = "discovery.stage"
EVENT_FAMILY_ATTR = "event.family"
ARTIFACT_TYPE_ATTR = "artifact.type"
OBSERVABILITY_PROFILE_ATTR = "observability.profile"
TRACE_ID_ATTR = "trace_id"
SPAN_ID_ATTR = "span_id"
INTENTION_TYPE_ATTR = "intention.type"


def init_metrics(
    service_name: str = "agent-world-agent",
    service_version: str = "1.0.0",
    export_interval_millis: int = 30000,
) -> None:
    """Initialize the OpenTelemetry meter provider.
    
    Fails open: if the exporter cannot be created, telemetry is silently
    disabled rather than blocking the agent service.
    """
    global _METER, _METER_PROVIDER

    if _METER is not None:
        return

    try:
        readers = []
        if os.environ.get("AGENT_WORLD_VERBOSE_LOGS") == "1":
            readers.append(
                PeriodicExportingMetricReader(
                    ConsoleMetricExporter(),
                    export_interval_millis=export_interval_millis,
                )
            )
        provider = MeterProvider(metric_readers=readers)
        metrics.set_meter_provider(provider)
        _METER_PROVIDER = provider
    except Exception:  # noqa: BLE001 - telemetry must never block the service
        _METER_PROVIDER = None

    _METER = metrics.get_meter(service_name, service_version)


def get_meter() -> metrics.Meter:
    """Return the meter, initializing if needed."""
    if _METER is None:
        init_metrics()
    return _METER or metrics.get_meter("agent-world-agent", "1.0.0")


def shutdown_metrics() -> None:
    """Shutdown the meter provider (called on service stop)."""
    global _METER, _METER_PROVIDER
    if _METER_PROVIDER is not None:
        try:
            _METER_PROVIDER.shutdown()
        except Exception:  # noqa: BLE001
            pass
    _METER = None
    _METER_PROVIDER = None


def metric_attributes_from_correlation(correlation) -> dict:
    """Convert a correlation context to bounded metric attributes.
    
    run_id is intentionally excluded (high cardinality); it remains in the
    correlation context for trace correlation.
    trace_id and span_id are intentionally excluded (high cardinality per-message);
    they remain in trace correlation/exemplars.
    Per-tick identifiers (world_revision, simulation_tick, simulation_time) are
    intentionally excluded to prevent unbounded cardinality as they change on
    every WorldState update. These values remain available in trace correlation.
    """
    attrs = {
        EXPERIMENT_ID_ATTR: correlation.experiment_id,
        SCENARIO_ID_ATTR: correlation.scenario_id,
        SCENARIO_VERSION_ATTR: correlation.scenario_version,
        AGENT_ID_ATTR: correlation.agent_id or "",
        COMPONENT_ATTR: correlation.component,
        COMPONENT_VERSION_ATTR: correlation.component_version,
    }
    # trace_id and span_id intentionally excluded from metric labels
    return attrs


def create_counters(meter: metrics.Meter) -> dict:
    """Create all counter instruments with bounded attributes."""
    return {
        # Protocol
        "agent_world_protocol_message_total": meter.create_counter(
            "agent_world_protocol_message_total",
            description="Total protocol messages by type, direction, and outcome",
            unit="1",
        ),
        "agent_world_agent_service_reconnect_total": meter.create_counter(
            "agent_world_agent_service_reconnect_total",
            description="Total agent service reconnection attempts",
            unit="1",
        ),
        "agent_world_stale_response_total": meter.create_counter(
            "agent_world_stale_response_total",
            description="Total stale responses rejected",
            unit="1",
        ),
        # LLM
        "agent_world_llm_request_total": meter.create_counter(
            "agent_world_llm_request_total",
            description="Total LLM requests by provider, model family, purpose, outcome",
            unit="1",
        ),
        "agent_world_llm_retry_total": meter.create_counter(
            "agent_world_llm_retry_total",
            description="Total LLM retries by bounded reason",
            unit="1",
        ),
        "agent_world_llm_timeout_total": meter.create_counter(
            "agent_world_llm_timeout_total",
            description="Total LLM request timeouts",
            unit="1",
        ),
        "agent_world_llm_schema_validation_failure_total": meter.create_counter(
            "agent_world_llm_schema_validation_failure_total",
            description="Total LLM schema validation failures",
            unit="1",
        ),
        "agent_world_llm_intention_rejection_total": meter.create_counter(
            "agent_world_llm_intention_rejection_total",
            description="Total LLM intention rejections by category",
            unit="1",
        ),
        # Deterministic layers
        "agent_world_controller_error_total": meter.create_counter(
            "agent_world_controller_error_total",
            description="Total controller errors by controller and error category",
            unit="1",
        ),
        "agent_world_plan_interruption_total": meter.create_counter(
            "agent_world_plan_interruption_total",
            description="Total plan interruptions by category",
            unit="1",
        ),
        # Event recording
        "agent_world_event_append_total": meter.create_counter(
            "agent_world_event_append_total",
            description="Total domain events appended by family and outcome",
            unit="1",
        ),
        "agent_world_artifact_write_total": meter.create_counter(
            "agent_world_artifact_write_total",
            description="Total artifacts written by type and outcome",
            unit="1",
        ),
        "agent_world_checkpoint_total": meter.create_counter(
            "agent_world_checkpoint_total",
            description="Total checkpoints written",
            unit="1",
        ),
        # Physics
        "agent_world_physics_tunneling_suspect_total": meter.create_counter(
            "agent_world_physics_tunneling_suspect_total",
            description="Total suspected physics tunneling events",
            unit="1",
        ),
        # Drives/reflexes
        "agent_world_reflex_activation_total": meter.create_counter(
            "agent_world_reflex_activation_total",
            description="Total reflex activations by type",
            unit="1",
        ),
        # Attention
        "agent_world_attention_selection_total": meter.create_counter(
            "agent_world_attention_selection_total",
            description="Total attention selections by bounded reason",
            unit="1",
        ),
        # Intentions/actions
        "agent_world_intention_total": meter.create_counter(
            "agent_world_intention_total",
            description="Total intentions by status and bounded action type",
            unit="1",
        ),
        "agent_world_action_total": meter.create_counter(
            "agent_world_action_total",
            description="Total actions by type and outcome",
            unit="1",
        ),
        "agent_world_arbitration_total": meter.create_counter(
            "agent_world_arbitration_total",
            description="Total arbitration decisions by winner layer and reason category",
            unit="1",
        ),
        # Beliefs
        "agent_world_belief_revision_total": meter.create_counter(
            "agent_world_belief_revision_total",
            description="Total belief revisions by category",
            unit="1",
        ),
        # Discovery
        "agent_world_discovery_stage_total": meter.create_counter(
            "agent_world_discovery_stage_total",
            description="Total discovery stages awarded by stage",
            unit="1",
        ),
        "agent_world_discovery_false_positive_total": meter.create_counter(
            "agent_world_discovery_false_positive_total",
            description="Total false positive discoveries",
            unit="1",
        ),
        "agent_world_discovery_false_negative_total": meter.create_counter(
            "agent_world_discovery_false_negative_total",
            description="Total false negative discoveries",
            unit="1",
        ),
        # Memory
        "agent_world_memory_write_total": meter.create_counter(
            "agent_world_memory_write_total",
            description="Total memory writes by type and outcome",
            unit="1",
        ),
        # Protocol errors
        "agent_world_protocol_version_mismatch_total": meter.create_counter(
            "agent_world_protocol_version_mismatch_total",
            description="Total protocol version mismatches",
            unit="1",
        ),
        "agent_world_protocol_decode_error_total": meter.create_counter(
            "agent_world_protocol_decode_error_total",
            description="Total protocol decode errors",
            unit="1",
        ),
    }


def create_histograms(meter: metrics.Meter) -> dict:
    """Create all histogram instruments with bounded attributes."""
    return {
        # Protocol
        "agent_world_protocol_message_size_bytes": meter.create_histogram(
            "agent_world_protocol_message_size_bytes",
            description="Protocol message size in bytes",
            unit="By",
        ),
        "agent_world_protocol_round_trip_seconds": meter.create_histogram(
            "agent_world_protocol_round_trip_seconds",
            description="Protocol round-trip latency in seconds",
            unit="s",
        ),
        # LLM
        "agent_world_llm_latency_seconds": meter.create_histogram(
            "agent_world_llm_latency_seconds",
            description="LLM request latency in seconds",
            unit="s",
        ),
        "agent_world_llm_time_to_first_token_seconds": meter.create_histogram(
            "agent_world_llm_time_to_first_token_seconds",
            description="LLM time to first token in seconds",
            unit="s",
        ),
        "agent_world_llm_input_tokens_total": meter.create_histogram(
            "agent_world_llm_input_tokens_total",
            description="LLM input tokens",
            unit="1",
        ),
        "agent_world_llm_output_tokens_total": meter.create_histogram(
            "agent_world_llm_output_tokens_total",
            description="LLM output tokens",
            unit="1",
        ),
        "agent_world_llm_cost_total": meter.create_histogram(
            "agent_world_llm_cost_total",
            description="LLM estimated cost",
            unit="1",
        ),
        # Deterministic layers
        "agent_world_deliberation_duration_seconds": meter.create_histogram(
            "agent_world_deliberation_duration_seconds",
            description="Deliberation request duration in seconds",
            unit="s",
        ),
        "agent_world_intention_duration_seconds": meter.create_histogram(
            "agent_world_intention_duration_seconds",
            description="Intention validation duration in seconds",
            unit="s",
        ),
        "agent_world_action_duration_seconds": meter.create_histogram(
            "agent_world_action_duration_seconds",
            description="Action execution duration in seconds",
            unit="s",
        ),
        # Memory
        "agent_world_memory_retrieval_seconds": meter.create_histogram(
            "agent_world_memory_retrieval_seconds",
            description="Memory retrieval duration in seconds",
            unit="s",
        ),
        "agent_world_memory_retrieval_result_count": meter.create_histogram(
            "agent_world_memory_retrieval_result_count",
            description="Memory retrieval result count",
            unit="1",
        ),
        # Discovery
        "agent_world_discovery_evaluation_seconds": meter.create_histogram(
            "agent_world_discovery_evaluation_seconds",
            description="Discovery evaluation duration in seconds",
            unit="s",
        ),
        # Event recording
        "agent_world_event_append_latency_seconds": meter.create_histogram(
            "agent_world_event_append_latency_seconds",
            description="Event append latency in seconds",
            unit="s",
        ),
        "agent_world_artifact_size_bytes": meter.create_histogram(
            "agent_world_artifact_size_bytes",
            description="Artifact size in bytes",
            unit="By",
        ),
        "agent_world_checkpoint_duration_seconds": meter.create_histogram(
            "agent_world_checkpoint_duration_seconds",
            description="Checkpoint write duration in seconds",
            unit="s",
        ),
        "agent_world_checkpoint_size_bytes": meter.create_histogram(
            "agent_world_checkpoint_size_bytes",
            description="Checkpoint size in bytes",
            unit="By",
        ),
        # Runtime/physics
        "agent_world_simulation_tick_duration_seconds": meter.create_histogram(
            "agent_world_simulation_tick_duration_seconds",
            description="Simulation tick duration in seconds",
            unit="s",
        ),
        "agent_world_render_frame_duration_seconds": meter.create_histogram(
            "agent_world_render_frame_duration_seconds",
            description="Render frame duration in seconds",
            unit="s",
        ),
        "agent_world_process_cpu_ratio": meter.create_histogram(
            "agent_world_process_cpu_ratio",
            description="Process CPU utilization ratio",
            unit="1",
        ),
        "agent_world_process_memory_bytes": meter.create_histogram(
            "agent_world_process_memory_bytes",
            description="Process memory usage in bytes",
            unit="By",
        ),
    }


def create_gauges(meter: metrics.Meter) -> dict:
    """Create all gauge instruments with bounded attributes."""
    return {
        # Runtime/physics
        "agent_world_simulation_tick_overrun_total": meter.create_up_down_counter(
            "agent_world_simulation_tick_overrun_total",
            description="Total simulation tick overruns",
            unit="1",
        ),
        "agent_world_simulation_time_scale": meter.create_gauge(
            "agent_world_simulation_time_scale",
            description="Current simulation time scale factor",
            unit="1",
        ),
        "agent_world_simulation_paused": meter.create_gauge(
            "agent_world_simulation_paused",
            description="Whether simulation is paused (1) or running (0)",
            unit="1",
        ),
        "agent_world_physics_active_body_count": meter.create_gauge(
            "agent_world_physics_active_body_count",
            description="Number of active physics bodies",
            unit="1",
        ),
        "agent_world_physics_contact_count": meter.create_gauge(
            "agent_world_physics_contact_count",
            description="Number of physics contacts in current tick",
            unit="1",
        ),
        "agent_world_physics_sleeping_body_count": meter.create_gauge(
            "agent_world_physics_sleeping_body_count",
            description="Number of sleeping physics bodies",
            unit="1",
        ),
        "agent_world_physics_constraint_error": meter.create_gauge(
            "agent_world_physics_constraint_error",
            description="Physics constraint error metric",
            unit="1",
        ),
        "agent_world_world_revision": meter.create_gauge(
            "agent_world_world_revision",
            description="Current world revision",
            unit="1",
        ),
        # Drives
        "agent_world_drive_value": meter.create_gauge(
            "agent_world_drive_value",
            description="Current drive value by bounded drive type",
            unit="1",
        ),
        # Attention
        "agent_world_attention_candidate_count": meter.create_gauge(
            "agent_world_attention_candidate_count",
            description="Number of attention candidates in current cycle",
            unit="1",
        ),
        # Agent service
        "agent_world_agent_service_connected": meter.create_gauge(
            "agent_world_agent_service_connected",
            description="Agent service connection status (1=connected, 0=disconnected)",
            unit="1",
        ),
        "agent_world_deliberation_inflight": meter.create_gauge(
            "agent_world_deliberation_inflight",
            description="Number of in-flight deliberation requests",
            unit="1",
        ),
        "agent_world_deliberation_queue_depth": meter.create_gauge(
            "agent_world_deliberation_queue_depth",
            description="Deliberation request queue depth",
            unit="1",
        ),
        # Memory/beliefs
        "agent_world_memory_entry_count": meter.create_gauge(
            "agent_world_memory_entry_count",
            description="Number of memory entries by type",
            unit="1",
        ),
        "agent_world_belief_count": meter.create_gauge(
            "agent_world_belief_count",
            description="Number of beliefs by status",
            unit="1",
        ),
        # Event recording
        "agent_world_event_buffer_depth": meter.create_gauge(
            "agent_world_event_buffer_depth",
            description="Event buffer depth",
            unit="1",
        ),
        "agent_world_event_sequence_gap_total": meter.create_up_down_counter(
            "agent_world_event_sequence_gap_total",
            description="Total event sequence gaps detected",
            unit="1",
        ),
        "agent_world_simulation_tick_total": meter.create_gauge(
            "agent_world_simulation_tick_total",
            description="Total simulation ticks elapsed",
            unit="1",
        ),
    }
