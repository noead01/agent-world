# Agent Service

External agent service for Agent World. Communicates with the Godot world runtime via WebSocket.

## Purpose

The agent service hosts the agent's cognitive layer (drives, attention, deliberation, memory, LLM integration) while the Godot world owns physics, simulation time, and action execution. The service receives WorldState and Observations, and sends Intentions and Actions.

## Running

```bash
# From repository root
make run-agent-service

# Or directly
cd services/agent
python -m src.agent_service
```

## Requirements

- Python 3.11+ as declared in `pyproject.toml`.
- `websockets` 13 or newer: `src/agent_service.py` imports
  `websockets.asyncio.server` and `ServerConnection`, introduced with the new
  asyncio implementation in websockets 13. A lower bound of 12.x permits an
  installation that cannot import the service.

## Configuration

Environment variables:
- `AGENT_SERVICE_HOST` (default: `127.0.0.1`; loopback-only unless explicitly exposed)
- `AGENT_SERVICE_PORT` (default: `8765`)
- `AGENT_EXPERIMENT_ID` (default: `exp_autonomous_discovery_01`)
- `AGENT_SCENARIO_ID` (default: `first_benchmark_room`)
- `AGENT_SCENARIO_VERSION` (default: `1.0.0`)
- `AGENT_RUN_ID` (default: `run_001`)

## Protocol

WebSocket JSON messages with `type` discriminator. Message schemas are defined in `src/schemas.py` and `src/protocol.py`. See [Agent Service Boundary Design](../../docs/superpowers/specs/2026-11-08-todo-0009-agent-service-boundary-design.md) for the protocol specification.

Session isolation is part of the protocol contract. Match an incoming message against the registered session using every identity field it carries: correlation `run_id`, top-level `run_id`, and top-level `agent_id`. A message with a foreign top-level run must not mutate the agent's request or target state.
