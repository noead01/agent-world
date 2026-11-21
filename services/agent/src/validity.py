"""Run validity state machine (TODO-0012).

Distinguishes component availability from experiment validity.
A run is one of: valid, degraded, invalid, aborted.

Telemetry exporter failure alone results in degraded observability,
not an invalid experiment, provided the authoritative record remains intact.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
import time


class RunValidity(str, Enum):
    """Experiment run validity states."""
    VALID = "valid"       # Required records and invariants intact
    DEGRADED = "degraded" # Experiment continued with documented fallback
    INVALID = "invalid"   # Missing required evidence, recorder failure, etc.
    ABORTED = "aborted"   # Intentionally or fatally stopped before completion


@dataclass
class ValidityTransition:
    """A validity state transition (domain event)."""
    type: str = "RunValidityTransition"
    run_id: str = ""
    experiment_id: str = ""
    timestamp_s: float = field(default_factory=time.time)
    from_state: str = ""
    to_state: str = ""
    reason: str = ""
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "run_id": self.run_id,
            "experiment_id": self.experiment_id,
            "timestamp_s": self.timestamp_s,
            "from": self.from_state,
            "to": self.to_state,
            "reason": self.reason,
            "description": self.description,
        }


class ValidityTracker:
    """Tracks run validity state and emits transitions as domain events."""
    
    # Valid transitions: from -> set of allowed to states
    ALLOWED_TRANSITIONS = {
        RunValidity.VALID: {RunValidity.DEGRADED, RunValidity.INVALID, RunValidity.ABORTED},
        RunValidity.DEGRADED: {RunValidity.INVALID, RunValidity.ABORTED},
        RunValidity.INVALID: {RunValidity.ABORTED},
        RunValidity.ABORTED: set(),  # Terminal
    }
    
    # Reasons that only cause degraded (not invalid)
    DEGRADED_ONLY_REASONS = {
        "telemetry_exporter_failed",
        "telemetry_export_timeout",
        "llm_provider_unreachable",
        "artifact_store_degraded",
    }
    
    def __init__(self, run_id: str, experiment_id: str):
        self.run_id = run_id
        self.experiment_id = experiment_id
        self._current = RunValidity.VALID
        self._history: list[ValidityTransition] = []
    
    @property
    def current(self) -> RunValidity:
        return self._current
    
    @property
    def history(self) -> list[ValidityTransition]:
        return list(self._history)
    
    def transition(self, new_state: RunValidity, reason: str) -> Optional[ValidityTransition]:
        """Attempt to transition to a new validity state.
        
        Returns the transition event if successful, None if rejected.
        """
        if new_state == self._current:
            return None  # No-op
        
        # Check if transition is allowed
        allowed = self.ALLOWED_TRANSITIONS.get(self._current, set())
        if new_state not in allowed:
            return None  # Rejected
        
        # Special handling: telemetry failure only degrades
        if self._current == RunValidity.VALID and new_state == RunValidity.INVALID:
            if reason in self.DEGRADED_ONLY_REASONS:
                new_state = RunValidity.DEGRADED
        
        old_state = self._current
        self._current = new_state
        
        transition = ValidityTransition(
            run_id=self.run_id,
            experiment_id=self.experiment_id,
            from_state=old_state.value,
            to_state=new_state.value,
            reason=reason,
            description=f"Run validity changed from {old_state.value} to {new_state.value}: {reason}",
        )
        self._history.append(transition)
        return transition
    
    def is_valid(self) -> bool:
        return self._current == RunValidity.VALID
    
    def is_degraded(self) -> bool:
        return self._current == RunValidity.DEGRADED
    
    def is_invalid(self) -> bool:
        return self._current == RunValidity.INVALID
    
    def is_aborted(self) -> bool:
        return self._current == RunValidity.ABORTED
    
    def can_trust_results(self) -> bool:
        """Return True if experiment results can be trusted."""
        return self._current in (RunValidity.VALID, RunValidity.DEGRADED)