"""Deterministic mock agent - replaces MockController logic."""
import json
import random
import time
import uuid
from typing import Callable, Awaitable, Dict, Any, List, Optional

from opentelemetry import trace

from .schemas import (
    Intention, Action, WorldState, Observation, CorrelationContext, Hello, HelloAck, Error
)
from .protocol import serialize_message, PROTOCOL_VERSION
from .tracing import (
    start_span,
    span_attributes_from_correlation,
    span_context_from_correlation,
    SPAN_DELIBERATION_REQUEST,
    SPAN_INTENTION_VALIDATE,
    SPAN_ARBITRATION_SELECT,
    SPAN_ACTION_EXECUTE,
    ACTION_TYPE_ATTR,
    RESULT_ATTR,
    INTENTION_TYPE_ATTR,
)


class MockAgent:
    """Deterministic agent that produces intentions/actions on a fixed schedule."""

    # Artificial latency is measured in simulation ticks rather than wall time
    # so a recorded seed replays identically at any simulation speed. 12 ticks
    # is ~0.2s at 60Hz, and the delay freezes while the world is paused.
    ACTION_DELAY_TICKS = 12
    ACTION_COOLDOWN_TICKS = 30
    
    def __init__(
        self, 
        agent_id: str, 
        run_id: str,
        experiment_id: str,
        scenario_id: str,
        scenario_version: str,
        send_callback: Callable[[str], Awaitable[None]],
        correlation_base: CorrelationContext,
        random_seed: Optional[int] = None,
    ):
        self.agent_id = agent_id
        self.run_id = run_id
        self.experiment_id = experiment_id
        self.scenario_id = scenario_id
        self.scenario_version = scenario_version
        self.send = send_callback
        self.correlation_base = correlation_base
        
        # Seed from the run's recorded random_seed when provided so reruns can
        # reproduce the delay schedule; fall back to run_id for older clients.
        self._rng = random.Random()
        self._rng.seed(random_seed if random_seed is not None else run_id)
        
        # Deterministic action sequence (same as room.gd MockController)
        self.targets: List[Dict[str, Any]] = []
        self.current_target_index = 0
        self.action_cooldown = 0.0
        self.cooldown_remaining_ticks = 0
        self.last_world_state: Optional[WorldState] = None
        self.pending_requests: Dict[str, Dict] = {}  # request_id -> {type, timestamp, target_index, payload}
        self._action_in_progress: bool = False  # Track if action is awaiting result
        self._active_request_id: Optional[str] = None  # Command whose terminal result is awaited
        self._resume_pending: bool = False
        self._awaiting_world_state: bool = False
        # A seeded artificial delay that is waiting for simulation progress
        # instead of blocking the tick loop on wall time.
        self._pending_delay: Optional[Dict[str, Any]] = None
        # Baseline for converting successive WorldState updates into simulated
        # progress. A pause leaves it unchanged; a reset moves it backwards.
        self._last_simulation_tick: Optional[int] = None
        
    def set_targets(self, targets: List[Dict[str, Any]]) -> None:
        """Set the action target sequence."""
        self.targets = targets
        self.current_target_index = 0
        self.cooldown_remaining_ticks = 0
        self._action_in_progress = False
        self._active_request_id = None
        self._pending_delay = None
        self._last_simulation_tick = None
        
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
        self._advance_simulation_progress(state.simulation_tick)
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
        self.cooldown_remaining_ticks = self.ACTION_COOLDOWN_TICKS

    def _abandon_request(self, request_id: Optional[str]) -> None:
        """Stop awaiting a command the world rejected as invalid.

        The world will never execute it, so keeping it active would stall the
        deterministic sequence indefinitely. Only the active request is cleared.
        """
        if not request_id or request_id != self._active_request_id:
            return
        self.pending_requests.pop(request_id, None)
        self._active_request_id = None
        self._action_in_progress = False
        self.cooldown_remaining_ticks = self.ACTION_COOLDOWN_TICKS

    async def on_error(self, error: Error) -> None:
        """Handle protocol error (e.g., STALE_REVISION)."""
        if error.code == "INVALID_COMMAND":
            self._abandon_request(error.request_id)
            return
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
    
    def _advance_simulation_progress(self, simulation_tick: int) -> None:
        """Advance every agent timer from simulated progress only.

        The world keeps sending WorldState while paused, but simulation_tick is
        frozen, so a paused world advances nothing. A reset moves the tick
        backwards; treat that as a zero-progress boundary instead of rewinding
        active timers.
        """
        previous_tick = self._last_simulation_tick
        self._last_simulation_tick = simulation_tick
        if previous_tick is None or simulation_tick <= previous_tick:
            return

        delta_ticks = simulation_tick - previous_tick
        if self._pending_delay is not None:
            self._pending_delay["remaining_ticks"] -= delta_ticks
        if self.cooldown_remaining_ticks > 0:
            self.cooldown_remaining_ticks = max(0, self.cooldown_remaining_ticks - delta_ticks)

    async def run_tick(self) -> None:
        """Main tick - called periodically to issue actions.

        No wall-clock delta enters behavior: cooldowns and artificial delays
        advance with the world's simulation tick, so a recorded seed replays
        identically at any frame rate.
        """
        if self._awaiting_world_state:
            return

        # Reconstruct the parent span context from the correlation base so
        # deliberation traces are children of the world trace that sent the
        # WorldState. If correlation lacks trace_id/span_id, a new trace is
        # started (fails open for telemetry).
        parent_span_ctx = span_context_from_correlation(self.correlation_base)
        if parent_span_ctx.is_valid:
            parent_context = trace.set_span_in_context(
                trace.NonRecordingSpan(parent_span_ctx)
            )
        else:
            parent_context = None

        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span(
            SPAN_DELIBERATION_REQUEST,
            context=parent_context,
            attributes=span_attributes_from_correlation(self.correlation_base),
        ):
            # Serve an artificial delay once simulated time has advanced far enough.
            # The command keeps the revision/timestamp captured when it was
            # scheduled so it arrives stale, reproducing the seeded behavior.
            pending = self._pending_delay
            if pending is not None:
                if pending["remaining_ticks"] > 0:
                    return
                self._pending_delay = None
                await self._issue_next_action(
                    pending["world_revision"],
                    pending["simulation_tick"],
                    pending["simulation_time"],
                    target_index=pending["target_index"],
                    advance=pending["advance"],
                    apply_delay=False,
                )
                return

            if self.cooldown_remaining_ticks > 0:
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

        # Artificial delay to simulate slow response (50% chance, 12 simulation
        # ticks). Scheduling against simulated progress keeps replay
        # deterministic regardless of wall-clock speed and freezes the delay
        # while the world is paused; the captured revision makes the request
        # stale by the time it is sent. Retries skip it so they land in time.
        if apply_delay and self._rng.random() < 0.5:
            self._pending_delay = {
                "world_revision": world_revision,
                "simulation_tick": simulation_tick,
                "simulation_time": simulation_time,
                "target_index": target_index,
                "advance": advance,
                "remaining_ticks": self.ACTION_DELAY_TICKS,
            }
            return

        tracer = trace.get_tracer(__name__)

        # Arbitration: the mock agent selects a single action from the target
        # sequence. The winner layer is always "mock" for this implementation.
        with tracer.start_as_current_span(
            SPAN_ARBITRATION_SELECT,
            attributes={
                **span_attributes_from_correlation(correlation),
                "winner.layer": "mock",
                "reason.category": "target_sequence",
            },
        ):
            # Intention validation: touch/inspect become intentions.
            if action_type in ["touch", "inspect"]:
                with tracer.start_as_current_span(
                    SPAN_INTENTION_VALIDATE,
                    attributes={
                        **span_attributes_from_correlation(correlation),
                        INTENTION_TYPE_ATTR: action_type,
                        RESULT_ATTR: "formed",
                    },
                ):
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

            # Action execution: move/wait become actions sent to the world.
            elif action_type == "move":
                with tracer.start_as_current_span(
                    SPAN_ACTION_EXECUTE,
                    attributes={
                        **span_attributes_from_correlation(correlation),
                        ACTION_TYPE_ATTR: action_type,
                        RESULT_ATTR: "pending",
                    },
                ):
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
                with tracer.start_as_current_span(
                    SPAN_ACTION_EXECUTE,
                    attributes={
                        **span_attributes_from_correlation(correlation),
                        ACTION_TYPE_ATTR: action_type,
                        RESULT_ATTR: "pending",
                    },
                ):
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
        self.cooldown_remaining_ticks = self.ACTION_COOLDOWN_TICKS
