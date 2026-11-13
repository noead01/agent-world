"""Pydantic models generated from JSON schemas."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class CorrelationContext(BaseModel):
    """Subset of correlation-context.schema.json for inline message correlation."""
    experiment_id: str = Field(pattern=r"^[a-z][a-z0-9_-]*$")
    scenario_id: str = Field(pattern=r"^[a-z][a-z0-9_-]*$")
    scenario_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    run_id: str = Field(pattern=r"^[a-z][a-z0-9_-]*$")
    agent_id: Optional[str] = Field(default=None, pattern=r"^[a-z][a-z0-9_-]*$")
    world_revision: int = Field(ge=0)
    simulation_tick: int = Field(ge=0)
    simulation_time: float = Field(ge=0)
    event_id: Optional[str] = Field(default=None, pattern=r"^[a-z][a-z0-9_-]*$")
    trace_id: Optional[str] = Field(default=None, pattern=r"^[0-9a-f]{32}$")
    span_id: Optional[str] = Field(default=None, pattern=r"^[0-9a-f]{16}$")
    component: str = Field(pattern=r"^[a-z][a-z0-9_-]*(:[a-z0-9][a-z0-9._-]*)?$")
    component_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")


class Observation(BaseModel):
    """observation.schema.json"""
    id: str = Field(pattern=r"^[a-z][a-z0-9_-]*$")
    run_id: str
    agent_id: str
    timestamp_s: float = Field(ge=0)
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    observation_type_id: str
    target_instance_id: Optional[str] = None
    target_type_id: Optional[str] = None
    properties: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=1.0, ge=0, le=1)
    correlation: CorrelationContext


class Intention(BaseModel):
    """intention.schema.json"""
    type: str = "Intention"
    id: str = Field(pattern=r"^[a-z][a-z0-9_-]*$")
    run_id: str
    agent_id: str
    timestamp_s: float = Field(ge=0)
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    intention_type_id: str
    target_instance_id: Optional[str] = None
    target_type_id: Optional[str] = None
    thought: Optional[str] = None
    goal: Optional[str] = None
    status: str = Field(pattern=r"^(formed|pursuing|completed|abandoned|failed)$")
    correlation: CorrelationContext
    request_world_revision: int = Field(ge=0, description="World revision this intention was based on")


class Action(BaseModel):
    """action.schema.json"""
    type: str = "Action"
    id: str = Field(pattern=r"^[a-z][a-z0-9_-]*$")
    run_id: str
    agent_id: str
    timestamp_s: float = Field(ge=0)
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    action_type_id: str
    target_instance_id: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    intention_id: Optional[str] = None
    result: Optional[str] = Field(default=None, pattern=r"^(success|failure|partial|pending)$")
    result_description: Optional[str] = None
    correlation: CorrelationContext
    request_world_revision: int = Field(ge=0, description="World revision this action was based on")


class WorldState(BaseModel):
    """Lightweight world snapshot sent periodically from world to agent."""
    type: str = "WorldState"
    world_revision: int
    simulation_tick: int
    simulation_time: float
    agent_id: str
    agent_position: Dict[str, float]  # {"x": 0.0, "y": 0.0, "z": 0.0}
    agent_heading_radians: float
    nearby_objects: List[Dict[str, Any]]  # [{"instance_id": "...", "position": {...}, "type_id": "..."}]
    correlation: CorrelationContext


class Hello(BaseModel):
    """Handshake from client to server."""
    type: str = "Hello"
    protocol_version: str = "1.0.0"
    agent_id: str
    run_id: str
    capabilities: List[str] = Field(default_factory=lambda: ["observation", "intention", "action"])
    correlation: CorrelationContext
    reconnect: bool = False
    last_known_world_revision: Optional[int] = None


class HelloAck(BaseModel):
    """Handshake acknowledgment from server to client."""
    type: str = "HelloAck"
    protocol_version: str = "1.0.0"
    server_id: str
    accepted_capabilities: List[str]
    initial_world_revision: int
    correlation: CorrelationContext


class Heartbeat(BaseModel):
    """Heartbeat message."""
    type: str = "Heartbeat"
    timestamp_s: float


class Error(BaseModel):
    """Protocol error."""
    type: str = "Error"
    code: str
    message: str
    request_id: Optional[str] = None
    current_revision: Optional[int] = None
    correlation: Optional[CorrelationContext] = None


class Goodbye(BaseModel):
    """Clean disconnect."""
    type: str = "Goodbye"
    reason: str
    correlation: Optional[CorrelationContext] = None


# Union type for message parsing
Message = Observation | Intention | Action | WorldState | Hello | HelloAck | Heartbeat | Error | Goodbye