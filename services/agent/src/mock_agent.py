"""Deterministic mock agent - replaces MockController logic."""
import json
import asyncio
import random
import time
import uuid
from typing import Callable, Awaitable, Dict, Any, List, Optional
from .schemas import (
    Intention, Action, WorldState, Observation, CorrelationContext, Hello, HelloAck, Error
)
from .protocol import serialize_message, PROTOCOL_VERSION


class MockAgent:
    """Deterministic agent that produces intentions/actions on a fixed schedule."""
    
    def __init__(
        self, 
        agent_id: str, 
        run_id: str,
        experiment_id: str,
        scenario_id: str,
        scenario_version: str,
        send_callback: Callable[[str], Awaitable[None]],
        correlation_base: CorrelationContext
    ):
        self.agent_id = agent_id
        self.run_id = run_id
        self.experiment_id = experiment_id
        self.scenario_id = scenario_id
        self.scenario_version = scenario_version
        self.send = send_callback
        self.correlation_base = correlation_base
        
        # Local RNG seeded from run_id for reproducible delays
        self._rng = random.Random()
        self._rng.seed(run_id)
        
        # Deterministic action sequence (same as room.gd MockController)
        self.targets: List[Dict[str, Any]] = []
        self.current_target_index = 0
        self.action_cooldown = 0.0
        self.cooldown_timer = 0.0
        self.last_world_state: Optional[WorldState] = None
        self.pending_requests: Dict[str, Dict] = {}  # request_id -> {type, timestamp, target_index, payload}
        self._action_in_progress: bool = False  # Track if action is awaiting result
        self._active_request_id: Optional[str] = None  # Command whose terminal result is awaited
        self._resume_pending: bool = False
        self._awaiting_world_state: bool = False
        
    def set_targets(self, targets: List[Dict[str, Any]]) -> None:
        """Set the action target sequence."""
        self.targets = targets
        self.current_target_index = 0
        self.cooldown_timer = 0.0
        self._action_in_progress = False
        self._active_request_id = None
        
    def _make_correlation(self, world_revision: int, simulation_tick: int, simulation_time: float) -> CorrelationContext:
        """Create correlation context for outgoing messages."""
        return CorrelationContext(
            experiment_id=self.experiment_id,
            scenario_id=self.scenario_id,
            scenario_version=self.scenario_version,
            run_id=self.run_id,
            agent_id=self.agent_id,
            world_revision=world_revision,
            simulation_tick=simulation_tick,
            simulation_time=simulation_time,
            trace_id=self.correlation_base.trace_id or uuid.uuid4().hex,
            span_id=uuid.uuid4().hex[:16],
            component="agent",
            component_version=PROTOCOL_VERSION,
        )
    
    async def on_hello_ack(self, ack: HelloAck, resume: bool = False) -> None:
        """Handle handshake acknowledgment."""
        self.correlation_base = ack.correlation
        self._resume_pending = resume
        self._awaiting_world_state = True

    async def _retransmit_active_request(self) -> None:
        """Re-send the command whose terminal result we are still waiting on."""
        if not self._action_in_progress or not self._active_request_id:
            return
        request = self.pending_requests.get(self._active_request_id)
        if request and request.get("payload"):
            # Refresh revision and correlation from this session's first state.
            # Keep the command ID so the world can deduplicate a request that
            # was accepted before the connection dropped.
            payload = json.loads(request["payload"])
            state = self.last_world_state
            payload["request_world_revision"] = state.world_revision
            payload["timestamp_s"] = state.simulation_time
            payload["correlation"] = self._make_correlation(
                state.world_revision,
                state.simulation_tick,
                state.simulation_time,
            ).model_dump(exclude_none=True)
            request["payload"] = json.dumps(payload, separators=(",", ":"))
            await self.send(request["payload"])
            return
        # Fallback when no serialized payload was retained: reissue the same
        # target without advancing the cursor.
        target_index = request.get("target_index") if request else None
        if target_index is None:
            target_index = max(0, self.current_target_index - 1)
        base = self.correlation_base
        await self._issue_next_action(
            base.world_revision,
            base.simulation_tick,
            base.simulation_time,
            target_index=target_index,
            advance=False,
            apply_delay=False,
        )
    
    async def on_world_state(self, state: WorldState) -> None:
        """Handle periodic world state update."""
        self.last_world_state = state
        # Update correlation base with latest world revision
        self.correlation_base = state.correlation
        if self._awaiting_world_state:
            self._awaiting_world_state = False
            if self._resume_pending:
                self._resume_pending = False
                await self._retransmit_active_request()
        
    async def on_observation(self, observation: Observation) -> None:
        """Handle observation (currently no-op for mock)."""
        pass
    
    async def on_action_result(self, action: Action) -> None:
        """Handle a terminal action result from the world."""
        # A result only terminates the action we are currently awaiting. Older
        # results (e.g. a move interrupted by a touch) must not clear the state
        # of the command that superseded them.
        is_active = action.id == self._active_request_id
        self.pending_requests.pop(action.id, None)
        if not is_active:
            return
        self._active_request_id = None
        # The target index is advanced when an action is issued, so a terminal
        # result must not advance it again (that would skip the next target).
        self._action_in_progress = False
        # Issue next action after cooldown
        self.cooldown_timer = 0.5  # 500ms cooldown
    
    async def on_error(self, error: Error) -> None:
        """Handle protocol error (e.g., STALE_REVISION)."""
        if (
            error.code != "STALE_REVISION"
            or not self.last_world_state
            or not self._active_request_id
            or error.request_id != self._active_request_id
        ):
            return

        # The rejected target was already advanced past when it was issued, so
        # recover its index from the pending request and resend it instead of
        # silently skipping ahead to the following target.
        request = self.pending_requests.pop(error.request_id, None) if error.request_id else None
        target_index = request.get("target_index") if request else None
        if target_index is None:
            # Fallback: the request map may have been cleared; retry the last
            # issued target (the one immediately before the read cursor).
            target_index = max(0, self.current_target_index - 1)

        await self._issue_next_action(
            error.current_revision or self.last_world_state.world_revision,
            self.last_world_state.simulation_tick,
            self.last_world_state.simulation_time,
            target_index=target_index,
            advance=False,
            apply_delay=False,
        )
    
    async def run_tick(self, delta: float) -> None:
        """Main tick - called periodically to issue actions."""
        if self._awaiting_world_state:
            return
        if self.cooldown_timer > 0:
            self.cooldown_timer -= delta
            return

        # While an action is in progress, only issue the next target when it is
        # explicitly marked to interrupt the current (possibly stuck) action.
        if self._action_in_progress:
            if (
                self.current_target_index < len(self.targets)
                and self.targets[self.current_target_index].get("interrupt_after", False)
                and self.last_world_state
            ):
                await self._issue_next_action(
                    self.last_world_state.world_revision,
                    self.last_world_state.simulation_tick,
                    self.last_world_state.simulation_time,
                )
            return

        if self.current_target_index < len(self.targets) and self.last_world_state:
            await self._issue_next_action(
                self.last_world_state.world_revision,
                self.last_world_state.simulation_tick,
                self.last_world_state.simulation_time
            )
    
    async def _issue_next_action(
        self,
        world_revision: int,
        simulation_tick: int,
        simulation_time: float,
        target_index: Optional[int] = None,
        advance: bool = True,
        apply_delay: bool = True,
    ) -> None:
        """Issue a target, optionally resending a specific index (for retries)."""
        if target_index is None:
            target_index = self.current_target_index
        if target_index >= len(self.targets):
            return

        target = self.targets[target_index]
        action_type = target.get("action_type", "move")
        target_id = target.get("target_id", "")

        correlation = self._make_correlation(world_revision, simulation_tick, simulation_time)

        # Artificial delay to simulate slow response (50% chance, 200ms = ~12 ticks at 60Hz).
        # This causes the request_world_revision to become stale by the time the
        # response is processed. Retries skip it so they can land in time.
        if apply_delay and self._rng.random() < 0.5:
            await asyncio.sleep(0.2)

        message_id = None
        if action_type in ["touch", "inspect"]:
            intention = Intention(
                id=f"int_{uuid.uuid4().hex[:12]}",
                run_id=self.run_id,
                agent_id=self.agent_id,
                timestamp_s=simulation_time,
                version=PROTOCOL_VERSION,
                intention_type_id=action_type,
                target_instance_id=target_id,
                target_type_id=None,
                thought=f"Mock agent {action_type}ing {target_id}",
                goal=f"Test {action_type}",
                status="formed",
                correlation=correlation,
                request_world_revision=world_revision
            )
            message_id = intention.id
            payload = serialize_message(intention)
            self.pending_requests[message_id] = {
                "type": "intention", "timestamp": time.time(),
                "target_index": target_index, "payload": payload,
            }
            await self.send(payload)

        elif action_type == "move":
            action = Action(
                id=f"act_{uuid.uuid4().hex[:12]}",
                run_id=self.run_id,
                agent_id=self.agent_id,
                timestamp_s=simulation_time,
                version=PROTOCOL_VERSION,
                action_type_id=action_type,
                target_instance_id=target_id,
                parameters={"approach_distance_m": 0.5},
                intention_id=None,
                result="pending",
                correlation=correlation,
                request_world_revision=world_revision
            )
            message_id = action.id
            payload = serialize_message(action)
            self.pending_requests[message_id] = {
                "type": "action", "timestamp": time.time(),
                "target_index": target_index, "payload": payload,
            }
            await self.send(payload)

        elif action_type == "wait":
            # Wait completes as soon as the world processes it; the terminal
            # result will clear _action_in_progress like any other action.
            action = Action(
                id=f"act_{uuid.uuid4().hex[:12]}",
                run_id=self.run_id,
                agent_id=self.agent_id,
                timestamp_s=simulation_time,
                version=PROTOCOL_VERSION,
                action_type_id=action_type,
                target_instance_id=target_id,
                parameters={},
                intention_id=None,
                result="pending",
                correlation=correlation,
                request_world_revision=world_revision
            )
            message_id = action.id
            payload = serialize_message(action)
            self.pending_requests[message_id] = {
                "type": "action", "timestamp": time.time(),
                "target_index": target_index, "payload": payload,
            }
            await self.send(payload)
        else:
            # Unknown action type: leave the index untouched.
            return

        if advance:
            self.current_target_index = max(self.current_target_index, target_index + 1)
        self._action_in_progress = True
        self._active_request_id = message_id
        self.cooldown_timer = 0.5
