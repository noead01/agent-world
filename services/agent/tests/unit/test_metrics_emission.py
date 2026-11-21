"""Tests for metric emission in agent service operations."""
from __future__ import annotations

import time
from unittest.mock import MagicMock, patch, AsyncMock
import pytest

from src.metrics import (
    init_metrics,
    shutdown_metrics,
    get_meter,
    create_counters,
    create_histograms,
    create_gauges,
    metric_attributes_from_correlation,
)
from src.schemas import CorrelationContext, WorldState, Action, Hello, HelloAck


@pytest.fixture(autouse=True)
def reset_metrics():
    """Reset global metrics state before and after each test."""
    import src.metrics as metrics_module
    orig_meter = metrics_module._METER
    orig_provider = metrics_module._METER_PROVIDER
    
    metrics_module._METER = None
    metrics_module._METER_PROVIDER = None
    
    from opentelemetry import metrics
    from opentelemetry.sdk.metrics import MeterProvider
    metrics.set_meter_provider(MeterProvider())
    
    yield
    
    shutdown_metrics()
    metrics_module._METER = orig_meter
    metrics_module._METER_PROVIDER = orig_provider


def test_protocol_message_counter_increments():
    """Protocol message counter should be incrementable."""
    init_metrics()
    counters = create_counters(get_meter())
    
    attrs = {
        "experiment.id": "exp_01",
        "scenario.id": "scenario_01",
        "scenario.version": "1.0.0",
        "agent.id": "agent_01",
        "world.revision": 10,
        "simulation.tick": 100,
        "simulation.time": 1.5,
        "component": "world",
        "component.version": "1.0.0",
        "message.type": "WorldState",
        "direction": "outbound",
        "outcome": "success",
    }
    
    counters["agent_world_protocol_message_total"].add(1, attrs)
    shutdown_metrics()


def test_protocol_message_histogram_records():
    """Protocol message size and round-trip histograms should be recordable."""
    init_metrics()
    histograms = create_histograms(get_meter())
    
    attrs = {
        "experiment.id": "exp_01",
        "scenario.id": "scenario_01",
        "scenario.version": "1.0.0",
        "agent.id": "agent_01",
        "world.revision": 10,
        "simulation.tick": 100,
        "simulation.time": 1.5,
        "component": "world",
        "component.version": "1.0.0",
        "message.type": "WorldState",
        "direction": "outbound",
        "outcome": "success",
    }
    
    histograms["agent_world_protocol_message_size_bytes"].record(512, attrs)
    histograms["agent_world_protocol_round_trip_seconds"].record(0.015, attrs)
    shutdown_metrics()


def test_llm_metrics_emit():
    """LLM request/latency/token metrics should be recordable."""
    init_metrics()
    counters = create_counters(get_meter())
    histograms = create_histograms(get_meter())
    
    attrs = {
        "experiment.id": "exp_01",
        "scenario.id": "scenario_01",
        "scenario.version": "1.0.0",
        "agent.id": "agent_01",
        "world.revision": 10,
        "simulation.tick": 100,
        "simulation.time": 1.5,
        "component": "agent",
        "component.version": "1.0.0",
        "provider": "openai",
        "model.family": "gpt-4",
        "purpose": "deliberation",
        "outcome": "success",
    }
    
    counters["agent_world_llm_request_total"].add(1, attrs)
    histograms["agent_world_llm_latency_seconds"].record(0.85, attrs)
    histograms["agent_world_llm_input_tokens_total"].record(1200, attrs)
    histograms["agent_world_llm_output_tokens_total"].record(300, attrs)
    histograms["agent_world_llm_cost_total"].record(0.002, attrs)
    shutdown_metrics()


def test_deliberation_metrics_emit():
    """Deliberation/arbitration/action metrics should be recordable."""
    init_metrics()
    counters = create_counters(get_meter())
    histograms = create_histograms(get_meter())
    
    attrs = {
        "experiment.id": "exp_01",
        "scenario.id": "scenario_01",
        "scenario.version": "1.0.0",
        "agent.id": "agent_01",
        "world.revision": 10,
        "simulation.tick": 100,
        "simulation.time": 1.5,
        "component": "agent",
        "component.version": "1.0.0",
    }
    
    # Deliberation
    histograms["agent_world_deliberation_duration_seconds"].record(0.12, attrs)
    
    # Intention
    intention_attrs = dict(attrs)
    intention_attrs["intention.type"] = "move"
    intention_attrs["outcome"] = "formed"
    counters["agent_world_intention_total"].add(1, intention_attrs)
    histograms["agent_world_intention_duration_seconds"].record(0.05, intention_attrs)
    
    # Arbitration
    arb_attrs = dict(attrs)
    arb_attrs["winner.layer"] = "deliberation"
    arb_attrs["reason.category"] = "goal_pursuit"
    counters["agent_world_arbitration_total"].add(1, arb_attrs)
    
    # Action
    action_attrs = dict(attrs)
    action_attrs["action.type"] = "move"
    action_attrs["result"] = "success"
    counters["agent_world_action_total"].add(1, action_attrs)
    histograms["agent_world_action_duration_seconds"].record(0.08, action_attrs)
    
    shutdown_metrics()


def test_gauges_update():
    """Gauge metrics should be updatable."""
    init_metrics()
    gauges = create_gauges(get_meter())
    
    attrs = {
        "experiment.id": "exp_01",
        "scenario.id": "scenario_01",
        "scenario.version": "1.0.0",
        "agent.id": "agent_01",
        "world.revision": 10,
        "simulation.tick": 100,
        "simulation.time": 1.5,
        "component": "world",
        "component.version": "1.0.0",
    }
    
    gauges["agent_world_simulation_time_scale"].set(1.0, attrs)
    gauges["agent_world_simulation_paused"].set(0, attrs)
    gauges["agent_world_physics_active_body_count"].set(5, attrs)
    gauges["agent_world_world_revision"].set(10, attrs)
    gauges["agent_world_agent_service_connected"].set(1, attrs)
    gauges["agent_world_deliberation_inflight"].set(2, attrs)
    gauges["agent_world_deliberation_queue_depth"].set(0, attrs)
    
    # UpDownCounter uses add
    gauges["agent_world_simulation_tick_overrun_total"].add(1, attrs)
    gauges["agent_world_event_sequence_gap_total"].add(1, attrs)
    
    shutdown_metrics()


def test_metric_attributes_from_correlation_includes_bounded_only():
    """metric_attributes_from_correlation should produce bounded attributes."""
    correlation = CorrelationContext(
        experiment_id="exp_01",
        scenario_id="scenario_01",
        scenario_version="1.0.0",
        run_id="run_01",
        agent_id="agent_01",
        world_revision=10,
        simulation_tick=100,
        simulation_time=1.5,
        component="agent",
        component_version="1.0.0",
        trace_id="ab" * 16,
        span_id="cd" * 8,
    )
    
    attrs = metric_attributes_from_correlation(correlation)
    
    # All bounded attributes present
    assert attrs["experiment.id"] == "exp_01"
    assert attrs["scenario.id"] == "scenario_01"
    assert attrs["scenario.version"] == "1.0.0"
    assert attrs["agent.id"] == "agent_01"
    assert attrs["world.revision"] == 10
    assert attrs["simulation.tick"] == 100
    assert attrs["simulation.time"] == 1.5
    assert attrs["component"] == "agent"
    assert attrs["component.version"] == "1.0.0"
    assert attrs["trace_id"] == "ab" * 16
    assert attrs["span_id"] == "cd" * 8
    
    # High cardinality excluded
    assert "run.id" not in attrs
    assert "run_id" not in attrs


@pytest.mark.asyncio
async def test_agent_service_records_protocol_metrics():
    """AgentService should record protocol metrics on message send."""
    from src.agent_service import AgentService
    
    service = AgentService(
        host="127.0.0.1",
        port=0,
        experiment_id="test_exp",
        scenario_id="test_scenario",
        scenario_version="1.0.0",
        run_id="test_run",
        health_port=18080,
    )
    
    # Initialize metrics instruments
    from src.metrics import get_meter, create_counters, create_histograms
    meter = get_meter()
    service._counters = create_counters(meter)
    service._histograms = create_histograms(meter)
    service._gauges = create_gauges(meter)
    service._metrics_initialized = True
    
    # Create a test correlation
    correlation = CorrelationContext(
        experiment_id="test_exp",
        scenario_id="test_scenario",
        scenario_version="1.0.0",
        run_id="test_run",
        agent_id="agent_01",
        world_revision=5,
        simulation_tick=50,
        simulation_time=0.833,
        component="world",
        component_version="1.0.0",
    )
    
    # Verify counters exist
    assert "agent_world_protocol_message_total" in service._counters
    assert "agent_world_protocol_message_size_bytes" in service._histograms
    assert "agent_world_protocol_round_trip_seconds" in service._histograms
    
    await service.stop()


@pytest.mark.asyncio
async def test_agent_service_records_llm_metrics_placeholder():
    """AgentService should have placeholder for LLM metrics."""
    from src.agent_service import AgentService
    
    service = AgentService(
        host="127.0.0.1",
        port=0,
        experiment_id="test_exp",
        scenario_id="test_scenario",
        scenario_version="1.0.0",
        run_id="test_run",
        health_port=18081,
    )
    
    # Initialize metrics
    from src.metrics import get_meter, create_counters, create_histograms
    meter = get_meter()
    service._counters = create_counters(meter)
    service._histograms = create_histograms(meter)
    service._gauges = create_gauges(meter)
    service._metrics_initialized = True
    
    # Verify LLM counters/histograms exist
    assert "agent_world_llm_request_total" in service._counters
    assert "agent_world_llm_latency_seconds" in service._histograms
    assert "agent_world_llm_input_tokens_total" in service._histograms
    assert "agent_world_llm_output_tokens_total" in service._histograms
    
    await service.stop()