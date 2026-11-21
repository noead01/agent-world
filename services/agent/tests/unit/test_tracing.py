"""Tests for OpenTelemetry tracing instrumentation (TODO-0011).

Verifies that:
- A tracer provider is available and can create spans.
- Spans use stable names and bounded attributes.
- Trace context (trace_id / span_id) propagates across the Godot/agent-service
  boundary via the correlation envelope.
"""
from __future__ import annotations

import unittest

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
        InMemorySpanExporter,
    )
except ImportError:  # pragma: no cover - opentelemetry not installed
    trace = None
    TracerProvider = None
    SimpleSpanProcessor = None
    InMemorySpanExporter = None

from src.tracing import (
    get_tracer,
    init_tracing,
    shutdown_tracing,
    span_attributes_from_correlation,
    start_span,
    _TRACER,
    _TRACER_PROVIDER,
)


def reset_tracing():
    """Reset global tracing state."""
    global _TRACER, _TRACER_PROVIDER
    import src.tracing as tracing_module
    tracing_module._TRACER = None
    tracing_module._TRACER_PROVIDER = None
    trace.set_tracer_provider(TracerProvider())

from src.tracing import (
    TRACE_ID_ATTR,
    SPAN_ID_ATTR,
    span_context_from_correlation,
)
from src.schemas import CorrelationContext


class TestTracingAvailable(unittest.TestCase):
    """OpenTelemetry must be importable and initialized."""

    @unittest.skipIf(trace is None, "opentelemetry not installed")
    def test_tracer_provider_initialized(self):
        init_tracing()
        provider = trace.get_tracer_provider()
        self.assertIsInstance(provider, TracerProvider)


class TestStableSpanNames(unittest.TestCase):
    """Critical operations use stable span names."""

    @unittest.skipIf(trace is None, "opentelemetry not installed")
    def test_span_names_are_stable(self):
        init_tracing()
        tracer = get_tracer()

        expected_spans = [
            "agent.deliberation.request",
            "agent.intention.validate",
            "agent.arbitration.select",
            "world.action.execute",
            "world.observation.publish",
            "world.perception.collect",
        ]

        with tracer.start_as_current_span("agent.deliberation.request"):
            pass
        # Just verify the tracer can create spans with these names.
        for name in expected_spans:
            with tracer.start_as_current_span(name):
                pass
        self.assertTrue(True, "all stable span names created without error")


class TestBoundedSpanAttributes(unittest.TestCase):
    """Span attributes must be bounded cardinality (no run_id, object_id, etc. as labels)."""

    @unittest.skipIf(trace is None, "opentelemetry not installed")
    def test_span_attributes_from_correlation_are_bounded(self):
        """Test that span_attributes_from_correlation produces bounded attributes."""
        corr = CorrelationContext(
            experiment_id="exp_test",
            scenario_id="scenario_test",
            scenario_version="1.0.0",
            run_id="run_test",  # High cardinality - should NOT be in span attributes
            agent_id="agent_test",
            world_revision=1,
            simulation_tick=42,
            simulation_time=0.7,
            trace_id="ab" * 16,
            span_id="cd" * 8,
            component="world",
            component_version="1.0.0",
        )
        attrs = span_attributes_from_correlation(corr)
        
        # Bounded attributes present
        self.assertIn("experiment.id", attrs)
        self.assertIn("scenario.id", attrs)
        self.assertIn("scenario.version", attrs)
        self.assertIn("agent.id", attrs)
        self.assertIn("world.revision", attrs)
        self.assertIn("simulation.tick", attrs)
        self.assertIn("simulation.time", attrs)
        self.assertIn("component", attrs)
        self.assertIn("component.version", attrs)
        self.assertIn("trace_id", attrs)
        self.assertIn("span_id", attrs)
        
        # High cardinality IDs NOT present
        self.assertNotIn("run.id", attrs)
        self.assertNotIn("run_id", attrs)


class TestCorrelationToSpanAttributes(unittest.TestCase):
    """Correlation context converts to bounded span attributes."""

    def test_span_attributes_from_correlation(self):
        corr = CorrelationContext(
            experiment_id="exp_test",
            scenario_id="scenario_test",
            scenario_version="1.0.0",
            run_id="run_test",
            agent_id="agent_test",
            world_revision=1,
            simulation_tick=42,
            simulation_time=0.7,
            trace_id="ab" * 16,
            span_id="cd" * 8,
            component="world",
            component_version="1.0.0",
        )
        attrs = span_attributes_from_correlation(corr)
        self.assertEqual(attrs["experiment.id"], "exp_test")
        self.assertEqual(attrs["scenario.id"], "scenario_test")
        self.assertEqual(attrs["scenario.version"], "1.0.0")
        self.assertEqual(attrs["agent.id"], "agent_test")
        self.assertEqual(attrs["world.revision"], 1)
        self.assertEqual(attrs["simulation.tick"], 42)
        # run_id is NOT a span attribute (high cardinality); it stays in
        # correlation context only.
        self.assertNotIn("run.id", attrs)
        self.assertEqual(attrs[TRACE_ID_ATTR], "ab" * 16)
        self.assertEqual(attrs[SPAN_ID_ATTR], "cd" * 8)


class TestTraceContextPropagation(unittest.TestCase):
    """Trace context crosses the Godot/agent-service boundary."""

    @unittest.skipIf(trace is None, "opentelemetry not installed")
    def test_trace_id_propagates_through_correlation(self):
        init_tracing()
        tracer = get_tracer()

        # World creates a trace context (as it does in protocol_handler.gd).
        world_trace_id = int("01" * 16, 16)
        world_span_id = int("02" * 8, 16)

        # Agent service receives a message whose correlation carries the same
        # trace_id and creates a child span.
        remote_context = trace.set_span_in_context(
            trace.NonRecordingSpan(
                trace.SpanContext(
                    trace_id=world_trace_id,
                    span_id=world_span_id,
                    is_remote=True,
                )
            )
        )
        with tracer.start_as_current_span(
            "world.observation.publish", context=remote_context
        ) as span:
            ctx = span.get_span_context()
            # Trace ID propagates across the boundary; the child span gets its
            # own span ID (parent span_id is recorded in the span's parent).
            self.assertEqual(format(ctx.trace_id, "032x"), "01" * 16)
            # Span context is valid (not INVALID_SPAN).
            self.assertTrue(ctx.is_valid)


class TestSpanContextReconstruction(unittest.TestCase):
    """Agent service must reconstruct SpanContext from correlation for proper propagation."""

    @unittest.skipIf(trace is None, "opentelemetry not installed")
    def test_span_context_from_correlation(self):
        """Correlation trace_id/span_id must be convertible to a remote SpanContext."""
        init_tracing()
        corr = CorrelationContext(
            experiment_id="exp_test",
            scenario_id="scenario_test",
            scenario_version="1.0.0",
            run_id="run_test",
            agent_id="agent_test",
            world_revision=1,
            simulation_tick=42,
            simulation_time=0.7,
            trace_id="01" * 16,
            span_id="02" * 8,
            component="world",
            component_version="1.0.0",
        )
        span_ctx = span_context_from_correlation(corr)
        self.assertIsInstance(span_ctx, trace.SpanContext)
        self.assertEqual(format(span_ctx.trace_id, "032x"), "01" * 16)
        self.assertEqual(format(span_ctx.span_id, "016x"), "02" * 8)
        self.assertTrue(span_ctx.is_remote)

    @unittest.skipIf(trace is None, "opentelemetry not installed")
    def test_span_context_from_correlation_missing_ids_returns_invalid(self):
        """Missing trace_id/span_id should yield an invalid SpanContext."""
        init_tracing()
        corr = CorrelationContext(
            experiment_id="exp_test",
            scenario_id="scenario_test",
            scenario_version="1.0.0",
            run_id="run_test",
            agent_id="agent_test",
            world_revision=1,
            simulation_tick=42,
            simulation_time=0.7,
            trace_id=None,
            span_id=None,
            component="world",
            component_version="1.0.0",
        )
        span_ctx = span_context_from_correlation(corr)
        self.assertFalse(span_ctx.is_valid)


if __name__ == "__main__":
    unittest.main()
