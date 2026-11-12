"""Run record loading and validation."""
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from jsonschema import validate, ValidationError, FormatChecker

# Load schemas bundled inside the installed package so a wheel install works
# without relying on the repository checkout.
SCHEMA_DIR = Path(__file__).parent / "schemas"

# JSON Schema treats `format` as an annotation unless a checker is supplied.
# Enforce RFC 3339 date-times without pulling in an optional validator package.
_DATETIME_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)
FORMAT_CHECKER = FormatChecker()


@FORMAT_CHECKER.checks("date-time", raises=(ValueError, TypeError))
def _check_datetime(value: object) -> bool:
    if not isinstance(value, str):
        return True  # Non-string values are rejected by the schema's type check.
    if not _DATETIME_PATTERN.match(value):
        return False
    datetime.fromisoformat(value.replace("Z", "+00:00"))
    return True

def _load_schema(name: str) -> Dict[str, Any]:
    with open(SCHEMA_DIR / name) as f:
        return json.load(f)

EVENT_SCHEMA = _load_schema("event.schema.json")
RUN_SCHEMA = _load_schema("run.schema.json")
VALIDITY_SCHEMA = _load_schema("run-validity.schema.json")

@dataclass
class RunRecord:
    run_id: str
    scenario_id: str
    version: str
    agent_id: str
    started_at: str
    ended_at: Optional[str]
    simulation_time_s: float
    status: str
    random_seed: int
    config_fingerprint: str = ""
    events: List[Dict[str, Any]] = field(default_factory=list)
    validity_history: List[Dict[str, Any]] = field(default_factory=list)
    run_dir: str = ""
    _raw_run_metadata: Optional[Dict[str, Any]] = field(default=None, repr=False)
    
    @classmethod
    def load(cls, run_dir: str) -> "RunRecord":
        run_path = Path(run_dir)
        
        # Load run metadata
        run_json_path = run_path / "run.json"
        if not run_json_path.exists():
            raise FileNotFoundError(f"run.json not found in {run_dir}")
        with open(run_json_path) as f:
            run_meta = json.load(f)
        
        # Load events
        events = []
        events_path = run_path / "events.jsonl"
        if not events_path.is_file():
            raise FileNotFoundError(f"events.jsonl not found in {run_dir}")
        with open(events_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    events.append(json.loads(line))
        
        # Load validity history
        validity_history = []
        validity_path = run_path / "validity.jsonl"
        if not validity_path.is_file():
            raise FileNotFoundError(f"validity.jsonl not found in {run_dir}")
        with open(validity_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    validity_history.append(json.loads(line))
        
        return cls(
            run_id=run_meta["id"],
            scenario_id=run_meta["scenario_id"],
            version=run_meta["version"],
            agent_id=run_meta["agent_id"],
            started_at=run_meta["started_at"],
            ended_at=run_meta.get("ended_at"),
            simulation_time_s=run_meta["simulation_time_s"],
            status=run_meta["status"],
            random_seed=run_meta["random_seed"],
            config_fingerprint=run_meta.get("config_fingerprint", ""),
            events=events,
            validity_history=validity_history,
            run_dir=str(run_path),
            _raw_run_metadata=run_meta,
        )
    
    def validate(self) -> List[str]:
        errors = []

        if not self.events:
            errors.append("Event stream is empty; run_started event is missing")
        if not self.validity_history:
            errors.append("Validity history is empty; initial validity record is missing")

        errors.extend(self._validate_event_boundaries())
        
        # Validate run metadata
        try:
            run_metadata = self._raw_run_metadata if self._raw_run_metadata is not None else self._as_run_dict()
            validate(instance=run_metadata, schema=RUN_SCHEMA, format_checker=FORMAT_CHECKER)
        except ValidationError as e:
            errors.append(f"Run metadata: {e.message}")
        
        # Validate each event
        for i, event in enumerate(self.events):
            try:
                validate(instance=event, schema=EVENT_SCHEMA, format_checker=FORMAT_CHECKER)
            except ValidationError as e:
                errors.append(f"Event {i} ({event.get('id', 'unknown')}): {e.message}")
        
        # Validate validity history
        for i, validity in enumerate(self.validity_history):
            try:
                validate(instance=validity, schema=VALIDITY_SCHEMA, format_checker=FORMAT_CHECKER)
            except ValidationError as e:
                errors.append(f"Validity {i}: {e.message}")

        errors.extend(self._validate_validity_history())
        errors.extend(self._validate_terminal_validity())
        
        # Check run_id consistency
        for event in self.events:
            if event.get("run_id") != self.run_id:
                errors.append(f"Event {event.get('id')} has mismatched run_id: {event.get('run_id')} != {self.run_id}")
        
        for validity in self.validity_history:
            if validity.get("run_id") != self.run_id:
                errors.append(f"Validity record has mismatched run_id: {validity.get('run_id')} != {self.run_id}")
        
        return errors

    def _validate_event_boundaries(self) -> List[str]:
        if not self.events:
            return []

        event_types = [event.get("event_type_id") for event in self.events]
        errors = []
        if event_types[0] != "run_started" or event_types.count("run_started") != 1:
            errors.append("Event stream must begin with exactly one run_started event")

        has_run_ended = event_types.count("run_ended") > 0
        if self.status == "completed":
            if event_types[-1] != "run_ended" or event_types.count("run_ended") != 1:
                errors.append("Completed event stream must end with exactly one run_ended event")
        elif has_run_ended:
            errors.append("Only completed runs may contain a run_ended event")
        return errors

    def _validate_validity_history(self) -> List[str]:
        errors = []
        previous_validity = None
        terminal_states = {"invalid", "aborted"}

        for index, record in enumerate(self.validity_history):
            declared_previous = record.get("previous_validity")
            current_validity = record.get("validity")
            if declared_previous != previous_validity:
                errors.append(
                    f"Validity {index} declares previous_validity {declared_previous!r}; "
                    f"expected {previous_validity!r}"
                )
            if previous_validity in terminal_states and current_validity != previous_validity:
                errors.append(
                    f"Validity {index} recovers from terminal state {previous_validity!r}"
                )
            previous_validity = current_validity

        return errors

    def _validate_terminal_validity(self) -> List[str]:
        expected = {"completed": "valid", "aborted": "invalid"}.get(self.status)
        if expected is None:
            return []
        if (
            len(self.validity_history) < 2
            or self.get_final_validity() != expected
            or self.validity_history[-1].get("previous_validity")
            != self.validity_history[-2].get("validity")
        ):
            return [
                f"Terminal validity for {self.status} run must be {expected!r}"
            ]
        return []
    
    def _as_run_dict(self) -> Dict[str, Any]:
        run_metadata = {
            "id": self.run_id,
            "scenario_id": self.scenario_id,
            "version": self.version,
            "agent_id": self.agent_id,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "simulation_time_s": self.simulation_time_s,
            "status": self.status,
            "random_seed": self.random_seed,
        }
        if self.config_fingerprint:
            run_metadata["config_fingerprint"] = self.config_fingerprint
        return run_metadata
    
    def get_events(self, event_type_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if event_type_id is None:
            return self.events
        return [e for e in self.events if e.get("event_type_id") == event_type_id]
    
    def get_final_validity(self) -> Optional[str]:
        if not self.validity_history:
            return None
        return self.validity_history[-1].get("validity")
    
    def is_valid(self) -> bool:
        return self.get_final_validity() == "valid" and not self.validate()
    
    def get_event_count(self) -> int:
        return len(self.events)

    def get_validity_history(self) -> List[Dict[str, Any]]:
        return self.validity_history
