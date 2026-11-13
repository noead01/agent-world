"""Tests that a socket only routes messages for its registered client entry."""
import asyncio
import json
import unittest
from unittest.mock import AsyncMock

from src.agent_service import AgentService


class FakeWebSocket:
    def __init__(self, hello, world_state, continue_reading):
        self.messages = (hello, world_state)
        self.continue_reading = continue_reading
        self.closed = False

    def __aiter__(self):
        return self._messages()

    async def _messages(self):
        yield json.dumps(self.messages[0])
        await self.continue_reading.wait()
        yield json.dumps(self.messages[1])

    async def send(self, _message):
        pass

    async def close(self, **_kwargs):
        self.closed = True


class AgentServiceRoutingTests(unittest.IsolatedAsyncioTestCase):
    async def test_disconnect_starts_reconnect_expiry_window(self):
        service = AgentService(session_ttl_s=10)
        websocket = object()
        session_key = "agent_test:run_test"
        client = {"websocket": websocket, "session_key": session_key}
        service.clients["agent_test"] = client
        service.agent_sessions[session_key] = object()

        service._unregister_disconnected_client("agent_test", websocket, client)

        self.assertNotIn("agent_test", service.clients)
        self.assertIn(session_key, service._disconnected_sessions)

    async def test_disconnected_sessions_expire_after_reconnect_window(self):
        service = AgentService(session_ttl_s=10)
        service.agent_sessions = {
            "agent_old:run_old": object(),
            "agent_recent:run_recent": object(),
            "agent_active:run_active": object(),
        }
        service._disconnected_sessions = {
            "agent_old:run_old": 89.0,
            "agent_recent:run_recent": 95.0,
        }

        service._expire_disconnected_sessions(now=100.0)

        self.assertNotIn("agent_old:run_old", service.agent_sessions)
        self.assertIn("agent_recent:run_recent", service.agent_sessions)
        self.assertIn("agent_active:run_active", service.agent_sessions)

    async def test_superseded_socket_cannot_route_into_replacement_client(self):
        correlation = {
            "experiment_id": "exp_test",
            "scenario_id": "scenario_test",
            "scenario_version": "1.0.0",
            "run_id": "run_test",
            "agent_id": "agent_test",
            "world_revision": 1,
            "simulation_tick": 1,
            "simulation_time": 0.1,
            "component": "world",
            "component_version": "1.0.0",
        }
        hello = {
            "type": "Hello",
            "protocol_version": "1.0.0",
            "agent_id": "agent_test",
            "run_id": "run_test",
            "correlation": correlation,
        }
        world_state = {
            "type": "WorldState",
            "world_revision": 1,
            "simulation_tick": 1,
            "simulation_time": 0.1,
            "agent_id": "agent_test",
            "agent_position": {"x": 0, "y": 0, "z": 0},
            "agent_heading_radians": 0,
            "nearby_objects": [],
            "correlation": correlation,
        }

        continue_reading = asyncio.Event()
        registered = asyncio.Event()
        old_socket = FakeWebSocket(hello, world_state, continue_reading)
        replacement_socket = FakeWebSocket(hello, world_state, continue_reading)
        old_client = {"websocket": old_socket, "mock_agent": object()}
        replacement_client = {"websocket": replacement_socket, "mock_agent": object()}
        service = AgentService()

        async def register_old_client(_websocket, message):
            service.clients[message.agent_id] = old_client
            registered.set()
            return old_client

        service._handle_hello = AsyncMock(side_effect=register_old_client)
        service._route_message = AsyncMock()

        connection_task = asyncio.create_task(service._handle_connection(old_socket))
        await registered.wait()
        service.clients["agent_test"] = replacement_client
        continue_reading.set()
        await connection_task

        service._route_message.assert_not_awaited()
        self.assertTrue(old_socket.closed)
        self.assertIs(service.clients["agent_test"], replacement_client)


if __name__ == "__main__":
    unittest.main()
