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

## Configuration

Environment variables:
- `AGENT_SERVICE_HOST` (default: `0.0.0.0`)
- `AGENT_SERVICE_PORT` (default: `8765`)
- `AGENT_EXPERIMENT_ID` (default: `exp_autonomous_discovery_01`)
- `AGENT_SCENARIO_ID` (default: `first_benchmark_room`)
- `AGENT_SCENARIO_VERSION` (default: `1.0.0`)
- `AGENT_RUN_ID` (default: `run_001`)

## Protocol

WebSocket JSON messages with `type` discriminator. Message schemas are defined in `src/schemas.py` and `src/protocol.py`. See [Agent Service Boundary Design](docs/superpowers/specs/2026-11-08-todo-0009-agent-service-boundary-design.md) for the protocol specification.