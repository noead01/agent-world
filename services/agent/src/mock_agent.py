"""Deterministic mock agent - replaces MockController logic."""
import json
import random
import time
import uuid
from typing import Callable, Awaitable, Dict, Any, List, Optional, Tuple

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
from .metrics import (
    get_meter,
    create_counters,
    create_histograms,
    create_gauges,
    metric_attributes_from_correlation,
    ACTION_TYPE_ATTR as METRIC_ACTION_TYPE_ATTR,
    RESULT_ATTR as METRIC_RESULT_ATTR,
    INTENTION_TYPE_ATTR as METRIC_INTENTION_TYPE_ATTR,
    WINNER_LAYER_ATTR,
    REASON_CATEGORY_ATTR,
    DRIVE_TYPE_ATTR,
)


# Load drive policy from config file for fingerprinting
def _load_drive_policy() -> Dict[str, Any]:
    """Load drive policy from JSON config file."""
    import os
    config_path = os.path.join(os.path.dirname(__file__), "..", "drive_policy.json")
    with open(config_path, "r") as f:
        return json.load(f)


_DRIVE_POLICY = _load_drive_policy()


class MockAgent:
    """Deterministic agent that produces intentions/actions on a fixed schedule."""

    # Artificial latency is measured in simulation ticks rather than wall time
    # so a recorded seed replays identically at any simulation speed. 12 ticks
    # is ~0.2s at 60Hz, and the delay freezes while the world is paused.
    ACTION_DELAY_TICKS = 12
    ACTION_COOLDOWN_TICKS = 30
    
    # Drive thresholds for arbitration influence (from drive_policy.json)
    CURIOSITY_EXPLORE_THRESHOLD = _DRIVE_POLICY["thresholds"]["curiosity_explore"]
    UNCERTAINTY_INVESTIGATE_THRESHOLD = _DRIVE_POLICY["thresholds"]["uncertainty_investigate"]
    INTEGRITY_SAFETY_THRESHOLD = _DRIVE_POLICY["thresholds"]["integrity_safety"]
    
    # Drive initial values (from drive_policy.json)
    INITIAL_CURIOSITY = _DRIVE_POLICY["initial_values"]["curiosity"]
    INITIAL_UNCERTAINTY = _DRIVE_POLICY["initial_values"]["uncertainty"]
    INITIAL_PHYSICAL_INTEGRITY = _DRIVE_POLICY["initial_values"]["physical_integrity"]
    
    # Drive update rates (from drive_policy.json)
    CURIOSITY_NOVEL_BOOST = _DRIVE_POLICY["update_rates"]["curiosity"]["novel_object_boost"]
    CURIOSITY_MOVED_BOOST = _DRIVE_POLICY["update_rates"]["curiosity"]["moved_object_boost"]
    CURIOSITY_DECAY_RATE = _DRIVE_POLICY["update_rates"]["curiosity"]["decay_rate"]
    
    UNCERTAINTY_HIGH_ERROR_BOOST = _DRIVE_POLICY["update_rates"]["uncertainty"]["high_prediction_error_boost"]
    UNCERTAINTY_MEDIUM_ERROR_BOOST = _DRIVE_POLICY["update_rates"]["uncertainty"]["medium_prediction_error_boost"]
    UNCERTAINTY_GOOD_PREDICTION_DECAY = _DRIVE_POLICY["update_rates"]["uncertainty"]["good_prediction_decay"]
    UNCERTAINTY_UNEXPECTED_MOVEMENT_BOOST = _DRIVE_POLICY["update_rates"]["uncertainty"]["unexpected_movement_boost"]
    UNCERTAINTY_DECAY_RATE = _DRIVE_POLICY["update_rates"]["uncertainty"]["decay_rate"]
    
    INTEGRITY_COLLISION_PENALTY = _DRIVE_POLICY["update_rates"]["physical_integrity"]["collision_risk_penalty"]
    INTEGRITY_RECOVERY_RATE = _DRIVE_POLICY["update_rates"]["physical_integrity"]["recovery_rate"]
    INTEGRITY_COLLISION_DISTANCE = _DRIVE_POLICY["update_rates"]["physical_integrity"]["collision_distance_threshold"]
    
    # Prediction error thresholds (from drive_policy.json)
    PREDICTION_ERROR_HIGH = _DRIVE_POLICY["prediction_error_thresholds"]["high"]
    PREDICTION_ERROR_MEDIUM = _DRIVE_POLICY["prediction_error_thresholds"]["medium"]
    UNEXPECTED_MOVEMENT_THRESHOLD = _DRIVE_POLICY["prediction_error_thresholds"]["unexpected_movement"]
    
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
        
        # --- Drive system ---
        # Each drive in range [0.0, 1.0], updated deterministically per tick
        # Curiosity: increases with novel observations, decays with familiarity
        self.curiosity: float = self.INITIAL_CURIOSITY
        # Uncertainty: increases with prediction error, decays with confirmation
        self.uncertainty: float = self.INITIAL_UNCERTAINTY
        # Physical Integrity: decreases with impacts, recovers in safety
        self.physical_integrity: float = self.INITIAL_PHYSICAL_INTEGRITY
        
        # Drive history for deterministic replay and observability
        self._drive_history: List[Dict[str, Any]] = []
        self._seen_objects: Dict[str, int] = {}  # object_id -> tick last seen
        self._exploration_count: Dict[str, int] = {}  # object_id -> times selected for curiosity exploration
        self._last_agent_position: Optional[Tuple[float, float, float]] = None
        self._predicted_positions: Dict[str, Tuple[float, float, float]] = {}  # object_id -> predicted position
        
        # Metrics instruments (initialized lazily on first use)
        self._counters: Optional[Dict] = None
        self._histograms: Optional[Dict] = None
        self._gauges: Optional[Dict] = None
        self._metrics_initialized: bool = False
        
    def _init_metrics(self) -> None:
        """Lazy initialization of metrics instruments."""
        if self._metrics_initialized:
            return
        meter = get_meter()
        self._counters = create_counters(meter)
        self._histograms = create_histograms(meter)
        self._gauges = create_gauges(meter)
        self._metrics_initialized = True
        
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
        delta_ticks = self._advance_simulation_progress(state.simulation_tick)
        
        # Update drives based on world state (deterministic, scaled by elapsed ticks)
        self._update_drives(state, delta_ticks)
        
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
        request = self.pending_requests.pop(action.id, None)
        if not is_active:
            return
        self._active_request_id = None
        # The target index is advanced when an action is issued, so a terminal
        # result must not advance it again (that would skip the next target).
        self._action_in_progress = False
        # Issue next action after cooldown
        self.cooldown_remaining_ticks = self.ACTION_COOLDOWN_TICKS
        
        # Record terminal action result metric + action duration
        if self._metrics_initialized and request:
            correlation = request.get("correlation")
            if correlation:
                base_attrs = metric_attributes_from_correlation(correlation)
                action_attrs = dict(base_attrs)
                action_attrs[METRIC_ACTION_TYPE_ATTR] = action.action_type_id
                action_attrs[METRIC_RESULT_ATTR] = action.result or "unknown"
                self._counters["agent_world_action_total"].add(1, action_attrs)
                
                # Record action execution duration (from send to terminal result)
                action_start = request.get("action_start")
                if action_start is not None:
                    duration = time.perf_counter() - action_start
                    self._histograms["agent_world_action_duration_seconds"].record(duration, action_attrs)

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
    
    def _advance_simulation_progress(self, simulation_tick: int) -> int:
        """Advance every agent timer from simulated progress only.

        The world keeps sending WorldState while paused, but simulation_tick is
        frozen, so a paused world advances nothing. A reset moves the tick
        backwards; treat that as a zero-progress boundary instead of rewinding
        active timers.

        Returns:
            delta_ticks: Number of simulation ticks elapsed since last call (>= 0)
        """
        previous_tick = self._last_simulation_tick
        self._last_simulation_tick = simulation_tick
        if previous_tick is None or simulation_tick <= previous_tick:
            return 0

        delta_ticks = simulation_tick - previous_tick
        if self._pending_delay is not None:
            self._pending_delay["remaining_ticks"] -= delta_ticks
        if self.cooldown_remaining_ticks > 0:
            self.cooldown_remaining_ticks = max(0, self.cooldown_remaining_ticks - delta_ticks)
        return delta_ticks

    def _update_drives(self, state: WorldState, delta_ticks: int = 1) -> None:
        """Update all three drives deterministically based on world state.
        
        Each drive in range [0.0, 1.0]:
        - Curiosity: increases with novel observations, decays with familiarity
        - Uncertainty: increases with prediction error, decays with confirmation  
        - Physical Integrity: decreases with impacts, recovers in safety
        
        Updates are deterministic: identical inputs + seed = identical drive histories.
        Drive deltas are scaled by delta_ticks (elapsed simulation ticks since last WorldState).
        """
        tick = state.simulation_tick
        agent_pos_dict = state.agent_position
        agent_pos = (agent_pos_dict.get("x", 0.0), agent_pos_dict.get("y", 0.0), agent_pos_dict.get("z", 0.0))
        nearby_objects = state.nearby_objects
        
        # --- Curiosity: novelty-seeking ---
        # Increase for each newly seen or changed object (one-time events, NOT scaled by delta_ticks),
        # decay is continuous (scaled by delta_ticks)
        curiosity_delta = 0.0
        for obj in nearby_objects:
            obj_id = obj.get("instance_id", "")
            pos_dict = obj.get("position", {})
            obj_pos = (pos_dict.get("x", 0.0), pos_dict.get("y", 0.0), pos_dict.get("z", 0.0))
            
            if obj_id not in self._seen_objects:
                # Never seen before - strong curiosity boost (one-time)
                curiosity_delta += self.CURIOSITY_NOVEL_BOOST
                self._seen_objects[obj_id] = tick
            else:
                # Check if object moved (novel state) - compare against PREVIOUS prediction
                predicted = self._predicted_positions.get(obj_id)
                if predicted:
                    dx = obj_pos[0] - predicted[0]
                    dy = obj_pos[1] - predicted[1]
                    dz = obj_pos[2] - predicted[2]
                    dist_sq = dx*dx + dy*dy + dz*dz
                    if dist_sq > self.PREDICTION_ERROR_MEDIUM:  # Moved > 10cm
                        curiosity_delta += self.CURIOSITY_MOVED_BOOST  # One-time boost
                        self._seen_objects[obj_id] = tick  # Only update when object actually moved
                # Update prediction AFTER computing curiosity delta
                self._predicted_positions[obj_id] = obj_pos
        
        # Curiosity decay when nothing novel (continuous rate, scaled by delta_ticks)
        if curiosity_delta == 0.0:
            curiosity_delta = -self.CURIOSITY_DECAY_RATE * delta_ticks
        
        self.curiosity = max(0.0, min(1.0, self.curiosity + curiosity_delta))
        
        # --- Uncertainty: prediction error ---
        # Increase when predictions don't match observations
        # IMPORTANT: Uses predictions that were set in PREVIOUS tick (not overwritten this tick)
        uncertainty_delta = 0.0
        for obj in nearby_objects:
            obj_id = obj.get("instance_id", "")
            pos_dict = obj.get("position", {})
            obj_pos = (pos_dict.get("x", 0.0), pos_dict.get("y", 0.0), pos_dict.get("z", 0.0))
            predicted = self._predicted_positions.get(obj_id)
            if predicted:
                dx = obj_pos[0] - predicted[0]
                dy = obj_pos[1] - predicted[1]
                dz = obj_pos[2] - predicted[2]
                dist_sq = dx*dx + dy*dy + dz*dz
                if dist_sq > self.PREDICTION_ERROR_HIGH:  # Prediction error > 20cm
                    uncertainty_delta += self.UNCERTAINTY_HIGH_ERROR_BOOST * delta_ticks
                elif dist_sq > self.PREDICTION_ERROR_MEDIUM:  # Prediction error > 10cm
                    uncertainty_delta += self.UNCERTAINTY_MEDIUM_ERROR_BOOST * delta_ticks
                else:
                    # Good prediction - uncertainty decreases
                    uncertainty_delta -= self.UNCERTAINTY_GOOD_PREDICTION_DECAY * delta_ticks
        
        # Agent self-prediction error (did we move as expected?)
        if self._last_agent_position is not None:
            dx = agent_pos[0] - self._last_agent_position[0]
            dy = agent_pos[1] - self._last_agent_position[1]
            dz = agent_pos[2] - self._last_agent_position[2]
            dist_sq = dx*dx + dy*dy + dz*dz
            if dist_sq > self.UNEXPECTED_MOVEMENT_THRESHOLD:  # Unexpected movement > 50cm
                uncertainty_delta += self.UNCERTAINTY_UNEXPECTED_MOVEMENT_BOOST * delta_ticks
        self._last_agent_position = agent_pos
        
        # Uncertainty decay
        if uncertainty_delta == 0.0:
            uncertainty_delta = -self.UNCERTAINTY_DECAY_RATE * delta_ticks
            
        self.uncertainty = max(0.0, min(1.0, self.uncertainty + uncertainty_delta))
        
        # --- Physical Integrity: safety/damage ---
        # Decrease with high-speed impacts, recover when stationary and safe
        integrity_delta = 0.0
        
        # Check nearby objects for collision risk
        for obj in nearby_objects:
            pos_dict = obj.get("position", {})
            obj_pos = (pos_dict.get("x", 0.0), pos_dict.get("y", 0.0), pos_dict.get("z", 0.0))
            dx = agent_pos[0] - obj_pos[0]
            dy = agent_pos[1] - obj_pos[1]
            dz = agent_pos[2] - obj_pos[2]
            dist_sq = dx*dx + dy*dy + dz*dz
            if dist_sq < self.INTEGRITY_COLLISION_DISTANCE:  # Very close to object (< ~70cm)
                integrity_delta -= self.INTEGRITY_COLLISION_PENALTY * delta_ticks
        
        # Recovery when stationary and not near hazards
        if integrity_delta == 0.0:
            integrity_delta = self.INTEGRITY_RECOVERY_RATE * delta_ticks  # Slow recovery
        
        self.physical_integrity = max(0.0, min(1.0, self.physical_integrity + integrity_delta))
        
        # Emit drive values to telemetry for observability
        self._init_metrics()
        base_attrs = metric_attributes_from_correlation(self.correlation_base)
        if self._metrics_initialized:
            drive_attrs = dict(base_attrs)
            drive_attrs[DRIVE_TYPE_ATTR] = "curiosity"
            self._gauges["agent_world_drive_value"].set(self.curiosity, drive_attrs)
            drive_attrs[DRIVE_TYPE_ATTR] = "uncertainty"
            self._gauges["agent_world_drive_value"].set(self.uncertainty, drive_attrs)
            drive_attrs[DRIVE_TYPE_ATTR] = "physical_integrity"
            self._gauges["agent_world_drive_value"].set(self.physical_integrity, drive_attrs)
        
        # Record drive state for observability and deterministic replay verification
        self._drive_history.append({
            "tick": tick,
            "curiosity": round(self.curiosity, 4),
            "uncertainty": round(self.uncertainty, 4),
            "physical_integrity": round(self.physical_integrity, 4),
        })
        # Keep history bounded (last 1000 ticks)
        if len(self._drive_history) > 1000:
            self._drive_history = self._drive_history[-1000:]

    def _select_action_by_drives(self) -> Tuple[Optional[str], str, str]:
        """Select next action based on drive states.
        
        Returns:
            (action_type, target_id, reason_category) or (None, "", "") if no drive threshold crossed
            
        Drive influences:
        - Curiosity > 0.7: explore (move to nearest unseen/least-seen object)
        - Uncertainty > 0.6: investigate (touch/inspect most uncertain object)
        - Physical Integrity < 0.3: safety (move away from nearest hazard, or wait)
        
        Priority order: Integrity (safety) > Uncertainty > Curiosity
        """
        if not self.last_world_state:
            return None, "", ""
        
        agent_pos_dict = self.last_world_state.agent_position
        agent_pos = (agent_pos_dict.get("x", 0.0), agent_pos_dict.get("y", 0.0), agent_pos_dict.get("z", 0.0))
        nearby_objects = self.last_world_state.nearby_objects
        
        if not nearby_objects:
            return None, "", ""
        
        # Priority 1: Physical Integrity - Safety takes precedence
        if self.physical_integrity < self.INTEGRITY_SAFETY_THRESHOLD:
            # For safety, wait rather than approach hazards. The protocol only supports
            # "move toward target", so moving toward the nearest object would worsen safety.
            # Use wait when integrity is in safety range (0.15-0.3) and critical wait (<0.15).
            if self.physical_integrity < 0.15:
                return "wait", "", "integrity_critical"
            return "wait", "", "integrity_safety"
        
        # Priority 2: Uncertainty - Investigate uncertain objects
        if self.uncertainty > self.UNCERTAINTY_INVESTIGATE_THRESHOLD:
            # Find object with highest prediction error
            max_error_obj = None
            max_error = 0.0
            for obj in nearby_objects:
                obj_id = obj.get("instance_id", "")
                pos = obj.get("position", {})
                obj_pos = (pos.get("x", 0.0), pos.get("y", 0.0), pos.get("z", 0.0))
                predicted = self._predicted_positions.get(obj_id)
                if predicted:
                    dx = obj_pos[0] - predicted[0]
                    dy = obj_pos[1] - predicted[1]
                    dz = obj_pos[2] - predicted[2]
                    error = dx*dx + dy*dy + dz*dz
                    if error > max_error:
                        max_error = error
                        max_error_obj = obj
            
            if max_error_obj:
                return "touch", max_error_obj.get("instance_id", ""), "uncertainty_investigation"
            return "inspect", nearby_objects[0].get("instance_id", ""), "uncertainty_investigation"
        
        # Priority 3: Curiosity - Explore novel objects
        if self.curiosity > self.CURIOSITY_EXPLORE_THRESHOLD:
            # Find least-seen object; break ties by exploration count (least explored first)
            least_seen_obj = None
            min_seen_tick = float('inf')
            min_explore_count = float('inf')
            for obj in nearby_objects:
                obj_id = obj.get("instance_id", "")
                seen_tick = self._seen_objects.get(obj_id, -1)
                explore_count = self._exploration_count.get(obj_id, 0)
                # Primary: least seen; secondary: least explored
                if seen_tick < min_seen_tick or (seen_tick == min_seen_tick and explore_count < min_explore_count):
                    min_seen_tick = seen_tick
                    min_explore_count = explore_count
                    least_seen_obj = obj
            
            if least_seen_obj:
                obj_id = least_seen_obj.get("instance_id", "")
                self._exploration_count[obj_id] = self._exploration_count.get(obj_id, 0) + 1
                return "move", obj_id, "curiosity_exploration"
            return "move", nearby_objects[0].get("instance_id", ""), "curiosity_exploration"
        
        # No drive threshold crossed - return None to use target sequence
        return None, "", ""

    async def run_tick(self) -> None:
        """Main tick - called periodically to issue actions.

        No wall-clock delta enters behavior: cooldowns and artificial delays
        advance with the world's simulation tick, so a recorded seed replays
        identically at any frame rate.
        """
        if self._awaiting_world_state:
            return

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
                    await self._issue_next_action(
                        self.last_world_state.world_revision,
                        self.last_world_state.simulation_tick,
                        self.last_world_state.simulation_time,
                    )
            return

        # Drive-based arbitration: select action based on drive states
        action_type = None
        target_id = ""
        reason = ""
        synthetic_target = None
        
        if self.last_world_state:
            action_type, target_id, reason = self._select_action_by_drives()
            if action_type:
                # Create a synthetic target for _issue_next_action
                synthetic_target = {
                    "action_type": action_type,
                    "target_id": target_id,
                    "interrupt_after": False,
                }
        
        # If drive arbitration selected an action, use it; otherwise fall back to target sequence
        if synthetic_target is not None:
            # Use drive-selected action without mutating self.targets
            # Pass target_index=None so _issue_next_action uses current_target_index
            # but we'll pass the synthetic action via a special mechanism
            target_index = self.current_target_index
            
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
                # Record arbitration metric with drive-influenced reason
                self._init_metrics()
                base_attrs = metric_attributes_from_correlation(self.correlation_base)
                arb_attrs = dict(base_attrs)
                arb_attrs[WINNER_LAYER_ATTR] = "drive_arbitration"
                arb_attrs[REASON_CATEGORY_ATTR] = reason
                if self._metrics_initialized:
                    self._counters["agent_world_arbitration_total"].add(1, arb_attrs)
                
                # Temporarily swap the target for this action
                original_target = None
                if target_index < len(self.targets):
                    original_target = self.targets[target_index]
                    self.targets[target_index] = synthetic_target
                else:
                    self.targets.append(synthetic_target)
                
                try:
                    await self._issue_next_action(
                        self.last_world_state.world_revision,
                        self.last_world_state.simulation_tick,
                        self.last_world_state.simulation_time,
                        target_index=target_index,
                    )
                finally:
                    # Restore the original target at the SAME index
                    if original_target is not None:
                        self.targets[target_index] = original_target
                    elif len(self.targets) > target_index:
                        self.targets.pop(target_index)
        elif self.current_target_index < len(self.targets):
            # Fallback to original target sequence
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

        # Initialize metrics
        self._init_metrics()
        
        # Base metric attributes from correlation
        base_attrs = metric_attributes_from_correlation(correlation)

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
        deliberation_start = time.perf_counter()

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
            # Record arbitration metric
            if self._metrics_initialized:
                arb_attrs = dict(base_attrs)
                arb_attrs[WINNER_LAYER_ATTR] = "mock"
                arb_attrs[REASON_CATEGORY_ATTR] = "target_sequence"
                self._counters["agent_world_arbitration_total"].add(1, arb_attrs)
            
            # Intention validation: touch/inspect become intentions.
            if action_type in ["touch", "inspect"]:
                intention_start = time.perf_counter()
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
                
                # Record intention metrics
                if self._metrics_initialized:
                    intention_attrs = dict(base_attrs)
                    intention_attrs[METRIC_INTENTION_TYPE_ATTR] = action_type
                    intention_attrs[METRIC_RESULT_ATTR] = "formed"
                    self._counters["agent_world_intention_total"].add(1, intention_attrs)
                    self._histograms["agent_world_intention_duration_seconds"].record(
                        time.perf_counter() - intention_start, intention_attrs
                    )

            # Action execution: move/wait become actions sent to the world.
            elif action_type == "move":
                action_start = time.perf_counter()
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
                        "action_start": action_start,
                        "correlation": correlation,
                    }
                    await self.send(payload)
                
                # Record action initiation metrics (not duration - that's at terminal result)
                if self._metrics_initialized:
                    action_attrs = dict(base_attrs)
                    action_attrs[METRIC_ACTION_TYPE_ATTR] = action_type
                    action_attrs[METRIC_RESULT_ATTR] = "pending"
                    self._counters["agent_world_action_total"].add(1, action_attrs)

            elif action_type == "wait":
                action_start = time.perf_counter()
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
                        "action_start": action_start,
                        "correlation": correlation,
                    }
                    await self.send(payload)
                
                # Record action initiation metrics (not duration - that's at terminal result)
                if self._metrics_initialized:
                    action_attrs = dict(base_attrs)
                    action_attrs[METRIC_ACTION_TYPE_ATTR] = action_type
                    action_attrs[METRIC_RESULT_ATTR] = "pending"
                    self._counters["agent_world_action_total"].add(1, action_attrs)
            else:
                # Unknown action type: leave the index untouched.
                return

        # Record deliberation duration
        if self._metrics_initialized:
            self._histograms["agent_world_deliberation_duration_seconds"].record(
                time.perf_counter() - deliberation_start, base_attrs
            )

        if advance:
            self.current_target_index = max(self.current_target_index, target_index + 1)
        self._action_in_progress = True
        self._active_request_id = message_id
        self.cooldown_remaining_ticks = self.ACTION_COOLDOWN_TICKS
