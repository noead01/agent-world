"""Message serialization, parsing, and validation."""
import json
from typing import Any, Dict, Optional, Union
from .schemas import (
    Message, Hello, HelloAck, Heartbeat, Error, Goodbye,
    Observation, Intention, Action, WorldState, CorrelationContext
)

PROTOCOL_VERSION = "1.0.0"
STALE_THRESHOLD = 5

def parse_message(data: str) -> Message:
    """Parse JSON string to validated message model."""
    obj = json.loads(data)
    msg_type = obj.get("type")
    
    if msg_type == "Hello":
        return Hello(**obj)
    elif msg_type == "HelloAck":
        return HelloAck(**obj)
    elif msg_type == "Heartbeat":
        return Heartbeat(**obj)
    elif msg_type == "Error":
        return Error(**obj)
    elif msg_type == "Goodbye":
        return Goodbye(**obj)
    elif msg_type == "Observation":
        return Observation(**obj)
    elif msg_type == "Intention":
        return Intention(**obj)
    elif msg_type == "Action":
        return Action(**obj)
    elif msg_type == "WorldState":
        return WorldState(**obj)
    else:
        raise ValueError(f"Unknown message type: {msg_type}")

def serialize_message(msg: Message) -> str:
    """Serialize message model to JSON string."""
    return msg.model_dump_json(exclude_none=True)

def make_error(code: str, message: str, request_id: Optional[str] = None, 
               current_revision: Optional[int] = None, 
               correlation: Optional[CorrelationContext] = None) -> Error:
    """Create an Error message."""
    return Error(
        code=code,
        message=message,
        request_id=request_id,
        current_revision=current_revision,
        correlation=correlation
    )

def is_stale(request_revision: int, current_revision: int, threshold: int = STALE_THRESHOLD) -> bool:
    """Check if a request is stale based on world revision."""
    return request_revision < current_revision - threshold