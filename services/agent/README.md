# Agent Service

External agent service for Agent World. Communicates with Godot world runtime via WebSocket.

## Running

```bash
cd services/agent
python -m src.agent_service
```

Or from repo root:

```bash
make run-agent-service
```

## Configuration

Environment variables:
- `AGENT_SERVICE_HOST` (default: 0.0.0.0)
- `AGENT_SERVICE_PORT` (default: 8765)
- `AGENT_EXPERIMENT_ID` (default: exp_autonomous_discovery_01)
- `AGENT_SCENARIO_ID` (default: first_benchmark_room)
- `AGENT_SCENARIO_VERSION` (default: 1.0.0)
- `AGENT_RUN_ID` (default: run_001)

## Protocol

WebSocket JSON messages with `type` discriminator. See `src/protocol.py` and `docs/superpowers/specs/2026-11-08-todo-0009-agent-service-boundary-design.md`.

## Testing

```bash
cd services/agent
pytest tests/unit/ -v
pytest tests/integration/ -v
```

## Architecture

- `agent_service.py`: WebSocket server, connection lifecycle, message routing
- `mock_agent.py`: Deterministic agent logic (replaces Godot MockController)
- `protocol.py`: Message parsing, serialization, validation
- `schemas.py`: Pydantic models from JSON schemas