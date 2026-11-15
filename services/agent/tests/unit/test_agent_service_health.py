"""Unit tests for agent service health endpoint."""
from __future__ import annotations

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer
from src.agent_service import AgentService


@pytest.fixture
async def health_service():
    """Create agent service with health endpoint for testing."""
    service = AgentService(
        host="127.0.0.1",
        port=0,  # Let OS assign
        experiment_id="test_exp",
        scenario_id="test_scenario",
        scenario_version="1.0.0",
        run_id="test_run",
    )
    await service.start()
    
    yield service
    
    await service.stop()


@pytest.fixture
async def health_client(health_service):
    """Create test client for the health app."""
    async with TestClient(TestServer(health_service.health_app)) as client:
        yield client


async def test_health_endpoint_returns_json(health_client):
    """GET /health should return JSON with component health."""
    resp = await health_client.get("/health")
    assert resp.status == 200
    data = await resp.json()
    
    # Required top-level fields
    assert "status" in data
    assert "components" in data
    assert "timestamp" in data
    
    # Component health
    components = data["components"]
    assert "agent_service" in components
    assert "telemetry_exporter" in components
    assert "llm_provider" in components
    
    for comp_name, comp_data in components.items():
        assert "status" in comp_data
        # Validity uses different states; others use healthy/degraded/failed
        if comp_name == "validity":
            assert comp_data["status"] in ["valid", "degraded", "invalid", "aborted"]
        else:
            assert comp_data["status"] in ["healthy", "degraded", "failed"]


async def test_health_endpoint_agent_service_connected(health_client):
    """Health should report agent_service as healthy when running."""
    resp = await health_client.get("/health")
    data = await resp.json()
    assert data["components"]["agent_service"]["status"] == "healthy"
    assert "active_sessions" in data["components"]["agent_service"]


async def test_health_endpoint_telemetry_exporter(health_client):
    """Health should report telemetry exporter status."""
    resp = await health_client.get("/health")
    data = await resp.json()
    comp = data["components"]["telemetry_exporter"]
    assert comp["status"] in ["healthy", "degraded", "failed"]
    assert "last_export_timestamp" in comp


async def test_health_endpoint_llm_provider(health_client):
    """Health should report LLM provider status."""
    resp = await health_client.get("/health")
    data = await resp.json()
    comp = data["components"]["llm_provider"]
    assert comp["status"] in ["healthy", "degraded", "failed"]
    assert "reachable" in comp


async def test_ready_endpoint(health_client):
    """GET /ready should return readiness status."""
    resp = await health_client.get("/ready")
    assert resp.status == 200
    data = await resp.json()
    assert "ready" in data
    assert data["ready"] is True


async def test_live_endpoint(health_client):
    """GET /live should return liveness status."""
    resp = await health_client.get("/live")
    assert resp.status == 200
    data = await resp.json()
    assert "alive" in data
    assert data["alive"] is True