"""Tests for mock-agent request correlation and stale-error handling."""
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from src.mock_agent import MockAgent
from src.schemas import CorrelationContext, Error


class MockAgentRequestTests(unittest.IsolatedAsyncioTestCase):
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


if __name__ == "__main__":
    unittest.main()
