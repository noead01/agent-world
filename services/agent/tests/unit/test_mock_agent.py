"""Tests for mock-agent request correlation and stale-error handling."""
import json
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from src.mock_agent import MockAgent
from src.schemas import CorrelationContext, Error


class MockAgentRequestTests(unittest.IsolatedAsyncioTestCase):
    def _make_agent(self, random_seed=None):
        correlation = CorrelationContext(
            experiment_id="exp_test",
            scenario_id="scenario_test",
            scenario_version="1.0.0",
            run_id="run_test",
            agent_id="agent_test",
            world_revision=9,
            simulation_tick=9,
            simulation_time=0.15,
            component="agent",
            component_version="1.0.0",
        )
        return MockAgent(
            "agent_test", "run_test", "exp_test", "scenario_test", "1.0.0",
            AsyncMock(), correlation, random_seed=random_seed,
        )

    async def test_stale_error_for_superseded_request_does_not_replace_active_action(self):
        correlation = CorrelationContext(
            experiment_id="exp_test",
            scenario_id="scenario_test",
            scenario_version="1.0.0",
            run_id="run_test",
            agent_id="agent_test",
            world_revision=9,
            simulation_tick=9,
            simulation_time=0.15,
            component="agent",
            component_version="1.0.0",
        )
        agent = MockAgent(
            "agent_test", "run_test", "exp_test", "scenario_test", "1.0.0",
            AsyncMock(), correlation,
        )
        agent.set_targets([
            {"target_id": "obj_old", "action_type": "move"},
            {"target_id": "obj_next", "action_type": "touch"},
        ])
        agent.targets[0]["id"] = "req_old"
        agent.pending_requests["req_old"] = {"target_index": 0}
        agent.pending_requests["req_next"] = {"target_index": 1}
        agent.last_world_state = SimpleNamespace(
            world_revision=9, simulation_tick=9, simulation_time=0.15
        )
        agent.current_target_index = 2
        agent._action_in_progress = True
        agent._active_request_id = "req_next"

        await agent.on_error(Error(
            code="STALE_REVISION",
            message="old request is stale",
            request_id="req_old",
            current_revision=9,
        ))

        self.assertEqual(agent._active_request_id, "req_next")
        self.assertIn("req_next", agent.pending_requests)
        agent.send.assert_not_awaited()


    async def test_invalid_command_error_releases_the_active_request(self):
        agent = self._make_agent()
        agent._action_in_progress = True
        agent._active_request_id = "req_bad"
        agent.pending_requests["req_bad"] = {"target_index": 0}

        await agent.on_error(Error(
            code="INVALID_COMMAND",
            message="command run_id does not match this session",
            request_id="req_bad",
        ))

        self.assertIsNone(agent._active_request_id)
        self.assertFalse(agent._action_in_progress)
        self.assertNotIn("req_bad", agent.pending_requests)

    async def test_invalid_command_error_for_another_request_is_ignored(self):
        agent = self._make_agent()
        agent._action_in_progress = True
        agent._active_request_id = "req_active"

        await agent.on_error(Error(
            code="INVALID_COMMAND",
            message="bad command",
            request_id="req_other",
        ))

        self.assertEqual(agent._active_request_id, "req_active")
        self.assertTrue(agent._action_in_progress)

    def test_recorded_random_seed_reproduces_the_delay_schedule(self):
        first = self._make_agent(random_seed=1234)
        second = self._make_agent(random_seed=1234)

        self.assertEqual(
            [first._rng.random() for _ in range(5)],
            [second._rng.random() for _ in range(5)],
        )

    async def test_artificial_delay_waits_for_simulation_ticks_and_stays_stale(self):
        agent = self._make_agent()
        agent.set_targets([{"target_id": "obj_a", "action_type": "move"}])
        await agent.on_world_state(self._world_state(agent, 100, 100, 1.0))

        with patch.object(agent._rng, "random", return_value=0.0):
            await agent.run_tick()

        # The delay neither blocks nor sends: it waits for simulation progress.
        agent.send.assert_not_awaited()
        self.assertIsNotNone(agent._pending_delay)
        self.assertEqual(agent.current_target_index, 0)

        await agent.on_world_state(
            self._world_state(agent, 111, 100 + agent.ACTION_DELAY_TICKS - 1, 1.18)
        )
        await agent.run_tick()
        agent.send.assert_not_awaited()
        self.assertEqual(agent._pending_delay["remaining_ticks"], 1)

        await agent.on_world_state(
            self._world_state(agent, 112, 100 + agent.ACTION_DELAY_TICKS, 1.2)
        )
        await agent.run_tick()

        agent.send.assert_awaited_once()
        payload = json.loads(agent.send.await_args.args[0])
        # The command keeps the revision and timestamp captured before the
        # delay, so it arrives stale exactly like a slow response.
        self.assertEqual(payload["correlation"]["world_revision"], 100)
        self.assertEqual(payload["timestamp_s"], 1.0)
        self.assertEqual(agent.current_target_index, 1)
        self.assertTrue(agent._action_in_progress)

    async def test_artificial_delay_freezes_while_world_is_paused(self):
        agent = self._make_agent()
        agent.set_targets([{"target_id": "obj_a", "action_type": "move"}])
        await agent.on_world_state(self._world_state(agent, 200, 200, 2.0))

        with patch.object(agent._rng, "random", return_value=0.0):
            await agent.run_tick()
        self.assertEqual(agent._pending_delay["remaining_ticks"], agent.ACTION_DELAY_TICKS)

        # A paused world keeps sending states with an unchanged simulation tick.
        for _ in range(50):
            await agent.on_world_state(self._world_state(agent, 201, 200, 2.0))
            await agent.run_tick()

        agent.send.assert_not_awaited()
        self.assertEqual(agent._pending_delay["remaining_ticks"], agent.ACTION_DELAY_TICKS)

        # Resuming advances the tick and lets the delay complete.
        await agent.on_world_state(
            self._world_state(agent, 202, 200 + agent.ACTION_DELAY_TICKS, 2.2)
        )
        await agent.run_tick()
        agent.send.assert_awaited_once()

    async def test_cooldown_advances_with_simulation_ticks_not_service_calls(self):
        agent = self._make_agent()
        agent.set_targets([{"target_id": "obj_a", "action_type": "move"}])
        await agent.on_world_state(self._world_state(agent, 300, 300, 3.0))
        agent.cooldown_remaining_ticks = agent.ACTION_COOLDOWN_TICKS

        # Service-loop calls alone must not expire a world-time cooldown.
        with patch.object(agent._rng, "random", return_value=1.0):
            for _ in range(120):
                await agent.run_tick()
        agent.send.assert_not_awaited()
        self.assertEqual(agent.cooldown_remaining_ticks, agent.ACTION_COOLDOWN_TICKS)

        await agent.on_world_state(self._world_state(agent, 305, 305, 3.08))
        self.assertEqual(agent.cooldown_remaining_ticks, agent.ACTION_COOLDOWN_TICKS - 5)

        with patch.object(agent._rng, "random", return_value=1.0):
            for _ in range(120):
                await agent.run_tick()
        agent.send.assert_not_awaited()

        await agent.on_world_state(self._world_state(agent, 330, 330, 3.5))
        with patch.object(agent._rng, "random", return_value=1.0):
            await agent.run_tick()
        agent.send.assert_awaited_once()

    def _world_state(self, agent, world_revision, simulation_tick, simulation_time):
        return SimpleNamespace(
            world_revision=world_revision,
            simulation_tick=simulation_tick,
            simulation_time=simulation_time,
            correlation=agent.correlation_base,
        )


if __name__ == "__main__":
    unittest.main()
