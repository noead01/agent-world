"""Deterministic mock agent - replaces MockController logic."""
import asyncio
import uuid
import time
import random
from typing import Callable, Awaitable, Dict, Any, List, Optional
from .schemas import (
    Intention, Action, WorldState, Observation, CorrelationContext, Hello, HelloAck
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
        
        # Deterministic action sequence (same as room.gd MockController)
        self.targets: List[Dict[str, Any]] = []
        self.current_target_index = 0
        self.action_cooldown = 0.0
        self.cooldown_timer = 0.0
        self.last_world_state: Optional[WorldState] = None
        self.pending_requests: Dict[str, Dict] = {}  # request_id -> {type, timestamp}
        self._action_in_progress: bool = False  # Track if action is awaiting result
        
    def set_targets(self, targets: List[Dict[str, Any]]) -> None:
        """Set the action target sequence."""
        self.targets = targets
        self.current_target_index = 0
        self.cooldown_timer = 0.0
        self._action_in_progress = False
        
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
            component="agent",
            component_version=PROTOCOL_VERSION,
        )
    
    async def on_hello_ack(self, ack: HelloAck) -> None:
        """Handle handshake acknowledgment."""
        self.correlation_base = ack.correlation
        # Send initial intention after handshake
        if self.targets:
            await self._issue_next_action(ack.correlation.world_revision, ack.correlation.simulation_tick, ack.correlation.simulation_time)
    
    async def on_world_state(self, state: WorldState) -> None:
        """Handle periodic world state update."""
        self.last_world_state = state
        # Update correlation base with latest world revision
        self.correlation_base = state.correlation
        
    async def on_observation(self, observation: Observation) -> None:
        """Handle observation (currently no-op for mock)."""
        pass
    
    async def on_action_result(self, action: Action) -> None:
        """Handle action result from world."""
        # Clear pending request
        if action.id in self.pending_requests:
            del self.pending_requests[action.id]
        # Mark action as complete and advance to next target
        self._action_in_progress = False
        self.current_target_index += 1
        # Issue next action after cooldown
        self.cooldown_timer = 0.5  # 500ms cooldown
    
    async def on_error(self, error: Error) -> None:
        """Handle protocol error (e.g., STALE_REVISION)."""
        if error.code == "STALE_REVISION" and self.last_world_state:
            # Re-plan with fresh world state
            await self._issue_next_action(
                error.current_revision or self.last_world_state.world_revision,
                self.last_world_state.simulation_tick,
                self.last_world_state.simulation_time
            )
    
    async def run_tick(self, delta: float) -> None:
        """Main tick - called periodically to issue actions."""
        if self.cooldown_timer > 0:
            self.cooldown_timer -= delta
            return
            
        # Don't issue next action if one is already in progress
        if self._action_in_progress:
            return
            
        if self.current_target_index < len(self.targets) and self.last_world_state:
            await self._issue_next_action(
                self.last_world_state.world_revision,
                self.last_world_state.simulation_tick,
                self.last_world_state.simulation_time
            )
    
    async def _issue_next_action(self, world_revision: int, simulation_tick: int, simulation_time: float) -> None:
        """Issue the next action in the sequence."""
        if self.current_target_index >= len(self.targets):
            return
            
        target = self.targets[self.current_target_index]
        action_type = target.get("action_type", "move")
        target_id = target.get("target_id", "")
        
        correlation = self._make_correlation(world_revision, simulation_tick, simulation_time)
        request_id = f"req_{uuid.uuid4().hex[:12]}"
        
        # Artificial delay to simulate slow response (50% chance, 200ms = ~12 ticks at 60Hz)
        # This causes the request_world_revision to become stale by the time the response is processed
        if random.random() < 0.5:
            await asyncio.sleep(0.2)
        
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
            self.pending_requests[intention.id] = {"type": "intention", "timestamp": time.time()}
            await self.send(serialize_message(intention))
            
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
            self.pending_requests[action.id] = {"type": "action", "timestamp": time.time()}
            await self.send(serialize_message(action))
            
        elif action_type == "wait":
            # Wait completes immediately - send action that completes immediately
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
            self.pending_requests[action.id] = {"type": "action", "timestamp": time.time()}
            await self.send(serialize_message(action))
            # For wait, advance immediately since it completes instantly
            self.current_target_index += 1
            return
            
        # Mark action as in progress (except wait which completes immediately)
        self._action_in_progress = True
        self.cooldown_timer = 0.5