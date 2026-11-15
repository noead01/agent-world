"""OpenTelemetry tracing for the agent service (TODO-0011).

Initializes a tracer provider with a console exporter for local development.
Exporter failure fails open: it never blocks simulation or agent behavior.

Spans use stable names from docs/observability.md and bounded attributes.
High-cardinality identifiers (run_id, object_id, request_id) are carried in
the correlation context, not as span attributes.
"""
from __future__ import annotations

import os
from typing import Optional

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

from src.schemas import CorrelationContext

_TRACER: Optional[trace.Tracer] = None
_TRACER_PROVIDER: Optional[TracerProvider] = None

# Span attribute keys (OpenTelemetry semantic conventions where applicable).
TRACE_ID_ATTR = "trace_id"
SPAN_ID_ATTR = "span_id"
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
INTENTION_TYPE_ATTR = "intention.type"
RESULT_ATTR = "result"
REQUEST_WORLD_REVISION_ATTR = "request.world_revision"

# Stable span names (docs/observability.md).
SPAN_DELIBERATION_REQUEST = "agent.deliberation.request"
SPAN_INTENTION_VALIDATE = "agent.intention.validate"
SPAN_ARBITRATION_SELECT = "agent.arbitration.select"
SPAN_ACTION_EXECUTE = "world.action.execute"
SPAN_OBSERVATION_PUBLISH = "world.observation.publish"
SPAN_PERCEPTION_COLLECT = "world.perception.collect"


def init_tracing(
    service_name: str = "agent-world-agent",
    service_version: str = "1.0.0",
) -> None:
    """Initialize the OpenTelemetry tracer provider.

    Fails open: if the exporter cannot be created, telemetry is silently
    disabled rather than blocking the agent service.
    """
    global _TRACER, _TRACER_PROVIDER

    if _TRACER is not None:
        return

    try:
        provider = TracerProvider()
        # Console exporter for local development. A collector/OTLP exporter
        # can be added without changing instrumentation.
        exporter = ConsoleSpanExporter()
        provider.add_span_processor(SimpleSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        _TRACER_PROVIDER = provider
    except Exception:  # noqa: BLE001 - telemetry must never block the service
        _TRACER_PROVIDER = None

    _TRACER = trace.get_tracer(service_name, service_version)


def get_tracer() -> trace.Tracer:
    """Return the tracer, initializing if needed."""
    if _TRACER is None:
        init_tracing()
    return _TRACER or trace.get_tracer("agent-world-agent", "1.0.0")


def shutdown_tracing() -> None:
    """Shutdown the tracer provider (called on service stop)."""
    global _TRACER, _TRACER_PROVIDER
    if _TRACER_PROVIDER is not None:
        try:
            _TRACER_PROVIDER.shutdown()
        except Exception:  # noqa: BLE001
            pass
    _TRACER = None
    _TRACER_PROVIDER = None


def span_attributes_from_correlation(correlation: CorrelationContext) -> dict:
    """Convert a correlation context to bounded span attributes.

    run_id is intentionally excluded (high cardinality); it remains in the
    correlation context for trace correlation.
    """
    return {
        EXPERIMENT_ID_ATTR: correlation.experiment_id,
        SCENARIO_ID_ATTR: correlation.scenario_id,
        SCENARIO_VERSION_ATTR: correlation.scenario_version,
        AGENT_ID_ATTR: correlation.agent_id,
        WORLD_REVISION_ATTR: correlation.world_revision,
        SIMULATION_TICK_ATTR: correlation.simulation_tick,
        SIMULATION_TIME_ATTR: correlation.simulation_time,
        COMPONENT_ATTR: correlation.component,
        COMPONENT_VERSION_ATTR: correlation.component_version,
        TRACE_ID_ATTR: correlation.trace_id or "",
        SPAN_ID_ATTR: correlation.span_id or "",
    }


def start_span(
    name: str,
    correlation: Optional[CorrelationContext] = None,
    attributes: Optional[dict] = None,
) -> trace.Span:
    """Start a span with stable name and bounded attributes.

    When ``correlation`` is provided, its trace_id/span_id are used as the
    parent context so spans form a causal chain across the Godot/agent-service
    boundary.
    """
    tracer = get_tracer()
    start_attributes = dict(attributes or {})
    if correlation is not None:
        start_attributes.update(span_attributes_from_correlation(correlation))
    return tracer.start_span(name, attributes=start_attributes)
