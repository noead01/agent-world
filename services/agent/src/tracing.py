"""OpenTelemetry tracing and metrics for the agent service (TODO-0011, TODO-0012).

Initializes a tracer/meter provider with console exporters for local development.
Exporter failure fails open: it never blocks simulation or agent behavior.

Spans/metrics use stable names from docs/observability.md and bounded attributes.
High-cardinality identifiers (run_id, object_id, request_id) are carried in
the correlation context, not as span/metric attributes.
"""
from __future__ import annotations

import os
from typing import Optional

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased

from src.schemas import CorrelationContext
from src.metrics import init_metrics, shutdown_metrics

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
    profile: str = "standard",  # minimal, standard, diagnostic
) -> None:
    """Initialize the OpenTelemetry tracer and meter providers.

    Fails open: if the exporter cannot be created, telemetry is silently
    disabled rather than blocking the agent service.

    Args:
        service_name: Service name for telemetry.
        service_version: Service version for telemetry.
        profile: Observability profile (minimal, standard, diagnostic).
                 minimal: errors only, coarse metrics, 1min export interval
                 standard: 10% trace sampling, 30s metric export
                 diagnostic: 100% trace sampling, 5s metric export
    """
    global _TRACER, _TRACER_PROVIDER

    if _TRACER is not None:
        return

    # Profile-based sampler
    if profile == "minimal":
        sampler = ParentBased(TraceIdRatioBased(0.0))  # Errors only via parent
    elif profile == "standard":
        sampler = ParentBased(TraceIdRatioBased(0.1))  # 10%
    elif profile == "diagnostic":
        sampler = ParentBased(TraceIdRatioBased(1.0))  # 100%
    else:
        sampler = ParentBased(TraceIdRatioBased(0.1))

    try:
        provider = TracerProvider(sampler=sampler)
        # Console exporter for local development. A collector/OTLP exporter
        # can be added without changing instrumentation.
        exporter = ConsoleSpanExporter()
        provider.add_span_processor(SimpleSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        _TRACER_PROVIDER = provider
    except Exception:  # noqa: BLE001 - telemetry must never block the service
        _TRACER_PROVIDER = None

    _TRACER = trace.get_tracer(service_name, service_version)

    # Initialize metrics with same fail-open semantics
    try:
        # Profile-based export interval
        if profile == "minimal":
            export_interval_millis = 60000  # 1 minute
        elif profile == "diagnostic":
            export_interval_millis = 5000   # 5 seconds
        else:
            export_interval_millis = 30000  # 30 seconds
        init_metrics(service_name, service_version, export_interval_millis)
    except Exception:  # noqa: BLE001
        pass


def get_tracer() -> trace.Tracer:
    """Return the tracer, initializing if needed."""
    if _TRACER is None:
        init_tracing()
    return _TRACER or trace.get_tracer("agent-world-agent", "1.0.0")


def shutdown_tracing() -> None:
    """Shutdown the tracer and meter providers (called on service stop)."""
    global _TRACER, _TRACER_PROVIDER
    if _TRACER_PROVIDER is not None:
        try:
            _TRACER_PROVIDER.shutdown()
        except Exception:  # noqa: BLE001
            pass
    _TRACER = None
    _TRACER_PROVIDER = None

    # Shutdown metrics
    try:
        shutdown_metrics()
    except Exception:  # noqa: BLE001
        pass


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


def span_context_from_correlation(correlation: CorrelationContext) -> trace.SpanContext:
    """Reconstruct a remote SpanContext from correlation for proper trace propagation.

    Returns an invalid SpanContext when trace_id or span_id are missing, so callers can
    detect when trace context cannot be established.
    """
    trace_id_str = correlation.trace_id or ""
    span_id_str = correlation.span_id or ""
    if not trace_id_str or not span_id_str:
        return trace.INVALID_SPAN.get_span_context()
    try:
        return trace.SpanContext(
            trace_id=int(trace_id_str, 16),
            span_id=int(span_id_str, 16),
            is_remote=True,
            trace_flags=trace.TraceFlags(trace.TraceFlags.SAMPLED),
        )
    except ValueError:
        return trace.INVALID_SPAN.get_span_context()


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
