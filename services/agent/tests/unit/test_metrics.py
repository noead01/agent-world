"""Unit tests for metrics module."""
from __future__ import annotations

import pytest
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import ConsoleMetricExporter, PeriodicExportingMetricReader

from src.metrics import (
    init_metrics,
    shutdown_metrics,
    get_meter,
    create_counters,
    create_histograms,
    create_gauges,
    metric_attributes_from_correlation,
    _METER,
    _METER_PROVIDER,
)
from src.schemas import CorrelationContext


@pytest.fixture(autouse=True)
def reset_metrics():
    """Reset global metrics state before and after each test."""
    # Store original state
    import src.metrics as metrics_module
    orig_meter = metrics_module._METER
    orig_provider = metrics_module._METER_PROVIDER
    
    # Reset to clean state
    metrics_module._METER = None
    metrics_module._METER_PROVIDER = None
    
    # Also reset the global meter provider
    # Note: Can't override once set, so we just let it be and the fixture
    # will restore the original state after the test
    metrics.set_meter_provider(MeterProvider())
    
    yield
    
    # Cleanup
    shutdown_metrics()
    metrics_module._METER = orig_meter
    metrics_module._METER_PROVIDER = orig_provider


def test_init_metrics_creates_meter():
    """init_metrics should create and register a meter provider."""
    init_metrics(service_name="test-service", service_version="1.0.0")
    meter = get_meter()
    assert meter is not None
    assert isinstance(meter, metrics.Meter)


def test_init_metrics_fails_open_on_exporter_error(monkeypatch):
    """init_metrics should fail open if exporter creation fails."""
    import opentelemetry.sdk.metrics.export as export_mod
    
    def failing_exporter(*args, **kwargs):
        raise RuntimeError("exporter failed")
    
    monkeypatch.setattr(export_mod, "ConsoleMetricExporter", failing_exporter)
    
    # Should not raise
    init_metrics(service_name="test-service", service_version="1.0.0")
    meter = get_meter()
    assert meter is not None


def test_get_meter_initializes_if_needed():
    """get_meter should initialize if not already done."""
    meter = get_meter()
    assert meter is not None
    assert isinstance(meter, metrics.Meter)


def test_metric_attributes_from_correlation_excludes_run_id():
    """metric_attributes_from_correlation should exclude run_id (high cardinality)."""
    correlation = CorrelationContext(
        experiment_id="exp_01",
        scenario_id="scenario_01",
        scenario_version="1.0.0",
        run_id="run_01",  # Should be excluded
        agent_id="agent_01",
        world_revision=10,
        simulation_tick=100,
        simulation_time=1.5,
        component="agent",
        component_version="1.0.0",
    )
    
    attrs = metric_attributes_from_correlation(correlation)
    
    assert "experiment.id" in attrs
    assert "scenario.id" in attrs
    assert "scenario.version" in attrs
    assert "agent.id" in attrs
    assert "world.revision" in attrs
    assert "simulation.tick" in attrs
    assert "simulation.time" in attrs
    assert "component" in attrs
    assert "component.version" in attrs
    # run_id should NOT be present
    assert "run.id" not in attrs
    assert "run_id" not in attrs


def test_create_counters_returns_all_instruments():
    """create_counters should return all counter instruments from observability.md."""
    init_metrics()
    counters = create_counters(get_meter())
    
    expected = [
        "agent_world_protocol_message_total",
        "agent_world_agent_service_reconnect_total",
        "agent_world_stale_response_total",
        "agent_world_llm_request_total",
        "agent_world_llm_retry_total",
        "agent_world_llm_timeout_total",
        "agent_world_llm_schema_validation_failure_total",
        "agent_world_llm_intention_rejection_total",
        "agent_world_controller_error_total",
        "agent_world_plan_interruption_total",
        "agent_world_event_append_total",
        "agent_world_artifact_write_total",
        "agent_world_checkpoint_total",
        "agent_world_physics_tunneling_suspect_total",
        "agent_world_reflex_activation_total",
        "agent_world_attention_selection_total",
        "agent_world_intention_total",
        "agent_world_action_total",
        "agent_world_arbitration_total",
        "agent_world_belief_revision_total",
        "agent_world_discovery_stage_total",
        "agent_world_discovery_false_positive_total",
        "agent_world_discovery_false_negative_total",
        "agent_world_memory_write_total",
        "agent_world_protocol_version_mismatch_total",
        "agent_world_protocol_decode_error_total",
    ]
    for name in expected:
        assert name in counters, f"Missing counter: {name}"
        assert hasattr(counters[name], "add")


def test_create_histograms_returns_all_instruments():
    """create_histograms should return all histogram instruments from observability.md."""
    init_metrics()
    histograms = create_histograms(get_meter())
    
    expected = [
        "agent_world_protocol_message_size_bytes",
        "agent_world_protocol_round_trip_seconds",
        "agent_world_llm_latency_seconds",
        "agent_world_llm_time_to_first_token_seconds",
        "agent_world_llm_input_tokens_total",
        "agent_world_llm_output_tokens_total",
        "agent_world_llm_cost_total",
        "agent_world_deliberation_duration_seconds",
        "agent_world_intention_duration_seconds",
        "agent_world_action_duration_seconds",
        "agent_world_memory_retrieval_seconds",
        "agent_world_memory_retrieval_result_count",
        "agent_world_discovery_evaluation_seconds",
        "agent_world_event_append_latency_seconds",
        "agent_world_artifact_size_bytes",
        "agent_world_checkpoint_duration_seconds",
        "agent_world_checkpoint_size_bytes",
        "agent_world_simulation_tick_duration_seconds",
        "agent_world_render_frame_duration_seconds",
        "agent_world_process_cpu_ratio",
        "agent_world_process_memory_bytes",
    ]
    for name in expected:
        assert name in histograms, f"Missing histogram: {name}"
        assert hasattr(histograms[name], "record")


def test_create_gauges_returns_all_instruments():
    """create_gauges should return all gauge instruments from observability.md."""
    init_metrics()
    gauges = create_gauges(get_meter())
    
    expected = [
        "agent_world_simulation_tick_overrun_total",
        "agent_world_simulation_time_scale",
        "agent_world_simulation_paused",
        "agent_world_physics_active_body_count",
        "agent_world_physics_contact_count",
        "agent_world_physics_sleeping_body_count",
        "agent_world_physics_constraint_error",
        "agent_world_world_revision",
        "agent_world_drive_value",
        "agent_world_attention_candidate_count",
        "agent_world_agent_service_connected",
        "agent_world_deliberation_inflight",
        "agent_world_deliberation_queue_depth",
        "agent_world_memory_entry_count",
        "agent_world_belief_count",
        "agent_world_event_buffer_depth",
        "agent_world_event_sequence_gap_total",
        "agent_world_simulation_tick_total",
    ]
    for name in expected:
        assert name in gauges, f"Missing gauge: {name}"
        # Gauges have set/observe methods (Gauge) or add (UpDownCounter)
        assert hasattr(gauges[name], "set") or hasattr(gauges[name], "observe") or hasattr(gauges[name], "add")


def test_instrument_creation_is_idempotent():
    """Calling create_counters/histograms/gauges multiple times should work."""
    init_metrics()
    meter = get_meter()
    
    counters1 = create_counters(meter)
    counters2 = create_counters(meter)
    # Should return the same instruments (or new ones with same name)
    assert counters1.keys() == counters2.keys()
    
    histograms1 = create_histograms(meter)
    histograms2 = create_histograms(meter)
    assert histograms1.keys() == histograms2.keys()
    
    gauges1 = create_gauges(meter)
    gauges2 = create_gauges(meter)
    assert gauges1.keys() == gauges2.keys()