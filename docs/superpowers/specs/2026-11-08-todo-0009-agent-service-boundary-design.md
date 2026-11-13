# TODO-0009 Design: Create the Agent-Service Boundary

## Overview

Establish the versioned asynchronous protocol between the Godot world runtime and the external agent service. The boundary carries observations (world → agent) and intentions/actions (agent → world) with full correlation context, connection lifecycle management, and stale-response rejection based on world revision.

**Dependencies**: TODO-0004 (core identifiers/schemas), TODO-0005 (observability schemas) — both complete.
**Transport**: WebSocket (Godot `WebSocketPeer` ↔ Python `websockets`).
**Agent service runtime**: Python (mock implementation for MVP).
**Scope**: Connection lifecycle, message schemas, correlation, stale-response rejection. No LLM integration (TODO-0017).

---

## Architecture

### Components

```
┌─────────────────────────────────────┐     WebSocket      ┌─────────────────────────────────────┐
│         Godot World Runtime         │ ◄─────────────────► │         Agent Service (Python)      │
│  apps/world/                        │                     │  services/agent/                    │
│  - Room (Node3D)                    │   Observations      │  - AgentService (asyncio server)    │
│  - SimulationTime                   │   Intentions        │  - MockAgent (deterministic logic)  │
│  - Agent (CharacterBody3D)          │   Actions           │  - Protocol handler                 │
│  - WebSocketClient (WebSocketPeer)  │   ActionResults     │  - Schema validation (pydantic)     │
│  - ProtocolHandler                  │   Heartbeats        │                                     │
└─────────────────────────────────────┘                     └─────────────────────────────────────┘
```

### Godot Side: `WebSocketClient` + `ProtocolHandler`

- **`WebSocketClient`** (Node, `class_name WebSocketClient`): wraps `WebSocketPeer`, handles connection, reconnection, heartbeats, message framing.
- **`ProtocolHandler`** (Node, `class_name ProtocolHandler`): builds/sends observations, parses intentions/actions, manages request/response correlation, enforces world-revision staleness check.

### Agent Service Side: `AgentService` + `MockAgent`

- **`AgentService`** (asyncio WebSocket server): accepts connections, routes messages, manages session state per agent.
- **`MockAgent`** (deterministic): replaces `MockController` logic; receives observations, produces intentions/actions on a fixed schedule.

---

## Message Protocol

All messages are JSON objects with a `type` discriminator and inline `correlation` (per `correlation-context.schema.json` subset).

### Message Types

| Type | Direction | Schema | Purpose |
|------|-----------|--------|---------|
| `Hello` | Both → Both | Custom | Connection handshake: protocol version, agent_id, run_id, capabilities |
| `Observation` | World → Agent | `observation.schema.json` | Perception data (visual, tactile, etc.) |
| `WorldState` | World → Agent | Custom (lightweight) | Periodic snapshot: world_revision, simulation_tick, simulation_time, agent pose, nearby objects |
| `Intention` | Agent → World | `intention.schema.json` | Agent proposes a goal (e.g., "approach obj_wood_cube") |
| `Action` | Agent → World | `action.schema.json` | Agent requests concrete action execution |
| `ActionResult` | World → Agent | `action.schema.json` (result field) | World confirms outcome (success/failure/partial) |
| `Heartbeat` | Both → Both | Custom | `{"type": "Heartbeat", "timestamp_s": 123.45}` |
| `Error` | Both → Both | Custom | Protocol errors: `{"type": "Error", "code": "STALE_REVISION", "message": "...", "request_id": "..."}` |
| `Goodbye` | Both → Both | Custom | Clean disconnect |

### Correlation Fields (inline on every message)

From `correlation-context.schema.json` — required subset:

```json
"correlation": {
  "experiment_id": "exp_autonomous_discovery_01",
  "scenario_id": "first_benchmark_room",
  "scenario_version": "1.0.0",
  "run_id": "run_20261108_demo",
  "agent_id": "wanderer_01",
  "world_revision": 42,
  "simulation_tick": 1200,
  "simulation_time": 20.0,
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7",
  "component": "world",
  "component_version": "1.0.0"
}
```

- `world_revision`: monotonic counter incremented each physics tick (or each state change)
- `simulation_tick`: fixed physics step number
- `simulation_time`: monotonic simulated seconds
- `trace_id` / `span_id`: W3C trace context for distributed tracing

---

## Connection Lifecycle

### States

```
DISCONNECTED
    │
    ▼ (connect)
CONNECTING ──timeout──► DISCONNECTED
    │
    ▼ (Hello/HelloAck)
CONNECTED ──protocol mismatch──► DISCONNECTED
    │
    ├──► RECONNECTING (on disconnect) ──success──► CONNECTED
    │                                      └──max retries──► DISCONNECTED
    │
    ▼ (Goodbye / close frame)
DISCONNECTED
```

### Handshake

1. **Client (Godot) → Server**: `Hello` with `protocol_version`, `agent_id`, `run_id`, `capabilities: ["observation", "intention", "action"]`
2. **Server → Client**: `HelloAck` with `protocol_version`, `server_id`, `accepted_capabilities`, `initial_world_revision`
3. If versions mismatch → `Error(code="PROTOCOL_MISMATCH")` + close

### Reconnection

- Exponential backoff: 1s, 2s, 4s, 8s, max 30s
- On reconnect, send `Hello` with `reconnect: true`, `last_known_world_revision`
- Server resends missed observations/state if revision gap < threshold (configurable, default 100)

### Heartbeat

- Interval: 5s (configurable)
- Missed 3 consecutive → treat as disconnected, enter RECONNECTING

---

## Stale-Response Rejection

**Requirement**: "A response based on an obsolete world revision is rejected without blocking physics."

### Mechanism

1. World includes `world_revision` in every `WorldState` and `Observation`.
2. Agent includes `request_world_revision` in every `Intention`/`Action`.
3. World, when receiving `Intention`/`Action`:
   - If `request_world_revision < current_world_revision - STALE_THRESHOLD` (default 5):
     - Reply `Error(code="STALE_REVISION", request_id=..., current_revision=...)`
     - **Do not** execute action, **do not** block physics tick
   - Else: process normally, reply `ActionResult`

### Why this works

- Physics continues at fixed 60Hz regardless of agent round-trip latency
- Agent can detect staleness, request fresh `WorldState`, re-plan
- No head-of-line blocking: multiple in-flight requests each carry their own revision

---

## Godot Implementation Details

### Files

| File | Responsibility |
|------|----------------|
| `apps/world/src/websocket_client.gd` | WebSocketPeer wrapper, connection management, reconnection, heartbeats |
| `apps/world/src/protocol_handler.gd` | Message serialization, correlation injection, request/response mapping, staleness check |
| `apps/world/src/room.gd` (modifications) | Spawn `WebSocketClient` + `ProtocolHandler`, feed observations/state, handle `ActionResult` |

### `WebSocketClient` API

```gdscript
class_name WebSocketClient extends Node

signal connected(server_id: String)
signal disconnected(reason: String)
signal message_received(message: Dictionary)
signal error(code: String, message: String)

# Configuration
@export var url: String = "ws://localhost:8765"
@export var reconnect_max_attempts: int = 10
@export var heartbeat_interval_s: float = 5.0

# Methods
func connect_to_server() -> void
func send_message(message: Dictionary) -> void
func close() -> void
```

### `ProtocolHandler` API

```gdscript
class_name ProtocolHandler extends Node

signal observation_ready(observation: Dictionary)
signal intention_sent(intention: Dictionary)
signal action_result_received(result: Dictionary)
signal stale_request_rejected(request_id: String, current_revision: int)

# Called by Room each physics tick
func tick_world_state(world_revision: int, simulation_tick: int, simulation_time: float, agent_dict: Dictionary, nearby_objects: Array) -> void

# Called when agent perceives something
func send_observation(observation: Dictionary) -> void

# Called when agent forms intention (from MockController or future LLM)
func send_intention(intention: Dictionary) -> void

# Called when agent requests action execution
func send_action(action: Dictionary) -> void
```

### Room Integration

- In `_ready()`: create `WebSocketClient` + `ProtocolHandler`, connect signals
- In `_physics_process()`:
  - `protocol_handler.tick_world_state(...)` — sends `WorldState` periodically (e.g., every 5 ticks)
  - Handle `action_result_received` → forward to `Agent` for lifecycle completion
  - Handle `stale_request_rejected` → log, let agent re-plan

---

## Agent Service Implementation Details (Python)

### Files

| File | Responsibility |
|------|----------------|
| `services/agent/src/agent_service.py` | WebSocket server, session management, message routing |
| `services/agent/src/protocol.py` | Message types, serialization, validation (pydantic models) |
| `services/agent/src/mock_agent.py` | Deterministic agent logic (replaces `MockController`) |
| `services/agent/src/schemas.py` | Pydantic models generated from JSON schemas |

### `AgentService` API

```python
class AgentService:
    async def start(host: str = "0.0.0.0", port: int = 8765) -> None
    async def stop() -> None
    
    # Called for each connected agent
    async def handle_agent(websocket: WebSocketServerProtocol, agent_id: str) -> None
```

### `MockAgent` API

```python
class MockAgent:
    def __init__(self, agent_id: str, send_callback: Callable[[dict], Awaitable[None]]):
        ...
    
    async def on_observation(self, observation: dict) -> None
    async def on_world_state(self, world_state: dict) -> None
    async def on_action_result(self, result: dict) -> None
    
    # Deterministic loop (like MockController._physics_process)
    async def run_tick(self, delta: float) -> None
```

### Message Validation

- Use `pydantic` models generated from JSON schemas (`observation.schema.json`, `intention.schema.json`, `action.schema.json`, `correlation-context.schema.json`)
- Validate inbound messages; reject with `Error(code="VALIDATION_ERROR")` on failure

---

## Data Flow

```
Godot Physics Tick (60Hz)
        │
        ▼
Room._physics_process(delta)
        │
        ├──► SimulationTime.tick(delta)
        │
        ├──► ProtocolHandler.tick_world_state(world_revision, tick, time, agent, objects)
        │         │
        │         ▼
        │    WebSocketClient.send_message(WorldState)
        │         │
        │         ▼ (WebSocket)
        │    AgentService.handle_agent()
        │         │
        │         ├──► MockAgent.on_world_state() ──► MockAgent.run_tick()
        │         │         │
        │         │         ├──► send_intention(Intention)
        │         │         └──► send_action(Action)
        │         │                  │
        │         ▼                  ▼ (WebSocket)
        │    ProtocolHandler.parse_intention/action()
        │         │
        │         ▼ (validate revision)
        ├──► Agent.execute_action() ◄─── ActionResult (success/failure)
        │         │
        │         ▼ (stale check failed)
        └──► Error(STALE_REVISION) ──► Agent re-plans
```

---

## Acceptance Criteria Mapping

| Criterion | Implementation |
|-----------|----------------|
| Connection, reconnection, timeout, cancellation, protocol mismatch states defined | `WebSocketClient` state machine + handshake protocol |
| Messages carry run, agent, tick, world revision, trace correlation | Inline `correlation` object on every message (per schema) |
| Stale response rejected without blocking physics | World checks `request_world_revision` before executing action; returns `Error(STALE_REVISION)` immediately |

---

## Testing

### Unit Tests (Python)

- `services/agent/tests/unit/test_protocol.py`: message serialization, validation, correlation injection
- `services/agent/tests/unit/test_mock_agent.py`: deterministic behavior, intention/action generation

### Integration Tests

- `services/agent/tests/integration/test_websocket.py`: full handshake, message exchange, reconnection
- `apps/world/tests/integration/test_protocol_handler.py`: Godot-side protocol handling (requires Godot headless)

### Acceptance Demo

`tools/repository/demo_agent_service.py`:
1. Start agent service (mock)
2. Start Godot world headless
3. Verify handshake, `WorldState` flow
4. Delay mock agent response by >5 ticks
5. Verify `STALE_REVISION` error, physics continues
6. Verify reconnection after forced disconnect

---

## Definition of Done

- [ ] All 3 acceptance criteria verified via automated demo
- [ ] Unit tests pass (Python + Godot source validation)
- [ ] Integration test passes (WebSocket round-trip)
- [ ] `make validate` passes
- [ ] No regressions in existing tests
- [ ] Schemas updated if needed (version bump)
- [ ] ADR recorded for WebSocket transport choice
- [ ] TODO-0009 status: `backlog` → `in-progress` → `done` via PR

---

## Out of Scope

- LLM integration (TODO-0017)
- Real agent drives/memory/beliefs (TODO-0013, TODO-0018, TODO-0019)
- Run recording/persistence (TODO-0010)
- Observability instrumentation (TODO-0011, TODO-0012)
- Visual operator interface (TODO-0023)