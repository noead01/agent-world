"""Tests that a socket only routes messages for its registered client entry."""
import asyncio
import json
import unittest
from unittest.mock import AsyncMock

from src.agent_service import AgentService
from src.schemas import CorrelationContext, WorldState


def _correlation(run_id="run_test", agent_id="agent_test"):
    return CorrelationContext(
        experiment_id="exp_test",
        scenario_id="scenario_test",
        scenario_version="1.0.0",
        run_id=run_id,
        agent_id=agent_id,
        world_revision=1,
        simulation_tick=1,
        simulation_time=0.1,
        component="world",
        component_version="1.0.0",
    )


def _world_state(run_id="run_test", agent_id="agent_test"):
    return WorldState(
        world_revision=1,
        simulation_tick=1,
        simulation_time=0.1,
        agent_id=agent_id,
        agent_position={"x": 0.0, "y": 0.0, "z": 0.0},
        agent_heading_radians=0.0,
        nearby_objects=[],
        correlation=_correlation(run_id, agent_id),
    )


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
    async def test_default_listener_binds_loopback_only(self):
        self.assertEqual(AgentService().host, "127.0.0.1")

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

    async def test_world_state_from_registered_session_is_routed(self):
        service = AgentService()
        mock_agent = AsyncMock()
        client = {"mock_agent": mock_agent, "correlation": _correlation()}

        await service._route_message(client, _world_state())

        mock_agent.on_world_state.assert_awaited_once()

    async def test_world_state_from_foreign_session_is_ignored(self):
        service = AgentService()
        mock_agent = AsyncMock()
        client = {"mock_agent": mock_agent, "correlation": _correlation()}

        await service._route_message(
            client, _world_state(run_id="run_foreign", agent_id="agent_foreign")
        )

        mock_agent.on_world_state.assert_not_awaited()

    async def test_world_state_with_mismatched_agent_id_is_ignored(self):
        service = AgentService()
        mock_agent = AsyncMock()
        client = {"mock_agent": mock_agent, "correlation": _correlation()}

        await service._route_message(client, _world_state(agent_id="agent_foreign"))

        mock_agent.on_world_state.assert_not_awaited()

    async def test_replacement_run_marks_displaced_session_disconnected(self):
        service = AgentService(session_ttl_s=10)
        old_session_key = "agent_test:run_old"
        service.agent_sessions[old_session_key] = object()
        service.clients["agent_test"] = {
            "websocket": object(),
            "session_key": old_session_key,
        }

        service._displace_previous_session("agent_test", "agent_test:run_new")

        self.assertIn(old_session_key, service._disconnected_sessions)

    async def test_same_run_reconnect_is_not_marked_displaced(self):
        service = AgentService(session_ttl_s=10)
        session_key = "agent_test:run_test"
        service.agent_sessions[session_key] = object()
        service.clients["agent_test"] = {
            "websocket": object(),
            "session_key": session_key,
        }

        service._displace_previous_session("agent_test", session_key)

        self.assertNotIn(session_key, service._disconnected_sessions)

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


    async def test_failing_client_does_not_stop_other_ticks(self):
        service = AgentService()
        failing_agent = AsyncMock()
        failing_agent.last_world_state = object()
        failing_agent.run_tick.side_effect = ConnectionError("socket closed")
        healthy_agent = AsyncMock()
        healthy_agent.last_world_state = object()

        await service._tick_client("failing", {"mock_agent": failing_agent})
        await service._tick_client("healthy", {"mock_agent": healthy_agent})

        healthy_agent.run_tick.assert_awaited_once_with(1.0 / 60.0)

    async def test_client_without_world_state_is_not_ticked(self):
        service = AgentService()
        idle_agent = AsyncMock()
        idle_agent.last_world_state = None

        await service._tick_client("idle", {"mock_agent": idle_agent})

        idle_agent.run_tick.assert_not_awaited()

    async def test_slow_session_does_not_delay_other_sessions(self):
        service = AgentService()
        release_slow = asyncio.Event()
        slow_started = asyncio.Event()
        fast_completed = asyncio.Event()
        slow_starts = 0

        slow_agent = AsyncMock()
        slow_agent.last_world_state = object()

        async def slow_tick(_delta):
            nonlocal slow_starts
            slow_starts += 1
            slow_started.set()
            await release_slow.wait()

        slow_agent.run_tick.side_effect = slow_tick

        fast_agent = AsyncMock()
        fast_agent.last_world_state = object()

        async def fast_tick(_delta):
            fast_completed.set()

        fast_agent.run_tick.side_effect = fast_tick

        service.clients["slow"] = {"mock_agent": slow_agent}
        service.clients["fast"] = {"mock_agent": fast_agent}

        service._schedule_client_ticks()
        try:
            await slow_started.wait()
            await asyncio.wait_for(fast_completed.wait(), timeout=1)

            # A session whose tick is still in flight is not ticked twice.
            service._schedule_client_ticks()
            await asyncio.sleep(0)
            self.assertEqual(slow_starts, 1)
        finally:
            release_slow.set()
            await asyncio.gather(*service._tick_tasks.values())


if __name__ == "__main__":
    unittest.main()
