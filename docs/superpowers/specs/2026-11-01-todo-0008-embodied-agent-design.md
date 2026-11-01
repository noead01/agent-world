# TODO-0008 Design: Implement a Basic Embodied Agent

## Overview

Implement a visible embodied agent that can orient, move, respect collisions and reach limits, and execute deterministic physical actions. Builds on TODO-0006 (physical room) and TODO-0007 (simulation time).

## Acceptance Criteria

1. Locomotion and orientation use deterministic controllers rather than LLM frame control.
2. Collision avoidance and reach constraints prevent invalid actions.
3. Action start, completion, interruption, and failure are observable.

## Architecture

### Component: `Agent` (`apps/world/src/agent.gd`)

A `CharacterBody3D` subclass (`class_name Agent`) that owns agent state and locomotion logic. Spawned by `Room` as a child node.

**Responsibilities:**
- Track `position`, `heading_radians`, `status`, `current_goal`, `world_time_s` matching `agent.schema.json`
- Deterministic movement via `move_and_slide()` (no LLM frame control)
- Orient toward targets using fixed turn speed
- Enforce reach constraints before permitting touch/inspect actions
- Emit action lifecycle signals for observability

**Properties** (all `@export`):
| Property | Type | Default | Description |
|---|---|---|---|
| `agent_id` | String | `"wanderer_01"` | Stable agent identifier |
| `agent_type_id` | String | `"exploration_agent"` | Agent type/template ID |
| `name` | String | `"Wanderer"` | Human-readable name |
| `move_speed` | float | `2.0` | Movement speed in m/s |
| `turn_speed` | float | `1.5` | Turn speed in rad/s |
| `reach_distance` | float | `0.5` | Max distance for touch/inspect |
| `position` | Vector3 | `Vector3(0, 0.56, 1.5)` | Spawn position |
| `heading_radians` | float | `0.0` | Current facing heading |

**Signals:**
- `action_started(action_type_id: String, target_instance_id: String)`
- `action_completed(action_type_id: String, result: String)`
- `action_failed(action_type_id: String, reason: String)`
- `action_interrupted(action_type_id: String)`

**Methods:**
- `move_toward(target: Vector3, delta: float)` — moves agent using `move_and_slide()`
- `turn_toward(target: Vector3, delta: float)` — orients agent toward target
- `can_reach(target_instance_id: String) -> bool` — checks reach constraint against object
- `execute_action(action_type_id: String, target_instance_id: String)` — attempts action, emits lifecycle signals
- `get_agent_dict() -> Dictionary` — returns state matching `agent.schema.json`

### Component: `MockController` (`apps/world/src/mock_controller.gd`)

A `Node` subclass that issues deterministic actions to the Agent each physics tick.

**Responsibilities:**
- Directs agent to move toward objects in sequence
- Attempts touch/inspect on reachable objects
- Reports action lifecycle through Agent signals

**Methods:**
- `_physics_process(delta)` — issues next deterministic action each tick
- `issue_move_action(target_instance_id)` — tells agent to move toward object
- `issue_touch_action(target_instance_id)` — tells agent to touch object if reachable

### Integration: `Room` (`apps/world/src/room.gd`)

**Changes:**
- Spawns `Agent` child at `(0, 0.56, 1.5)` in `_spawn_objects()` (or new `_spawn_agent()`)
- Agent reads `world_time_s` from `_sim_time.simulation_time` (single source of truth)
- Prints agent state (position, heading, status, world_time_s) each second alongside object states

## Data Flow

```
_physics_process(delta)
    ├─> MockController._physics_process(delta)
    │     ├─> agent.move_toward(target, delta)  [CharacterBody3D.move_and_slide]
    │     ├─> agent.turn_toward(target, delta)
    │     └─> agent.execute_action(action_type, target_id)
    │           ├─> check can_reach(target_id) -> emit action_failed if unreachable
    │           ├─> emit action_started
    │           ├─> perform action -> emit action_completed / action_failed
    ├─> _sim_time.tick(delta)  [from TODO-0007]
    ├─> if !paused: apply gravity to objects
    └─> print agent + object state each second
```

## Testing

### Unit Tests (`apps/world/tests/unit/test_agent.py`)

Pure Python tests validating source text:
- `agent.gd` exists
- `class_name Agent` declared, extends `CharacterBody3D`
- Required properties: `agent_id`, `agent_type_id`, `name`, `move_speed`, `turn_speed`, `reach_distance`, `position`, `heading_radians`
- Required methods: `move_toward`, `turn_toward`, `can_reach`, `execute_action`, `get_agent_dict`
- Required signals: `action_started`, `action_completed`, `action_failed`, `action_interrupted`
- `mock_controller.gd` exists with `_physics_process`
- `room.gd` spawns Agent and reads `simulation_time`

### Demo (`tools/repository/demo_agent.py`)

Runs Godot headless, parses stdout, validates:
- **AC1**: Deterministic locomotion — agent position changes over time, heading updates
- **AC2**: Collision avoidance — agent doesn't pass through room boundaries; reach constraints prevent touching unreachable objects
- **AC3**: Observable action lifecycle — `action_started`/`action_completed`/`action_failed` signals appear in output

Follows existing `demo_room_physics.py` / `demo_simulation_time.py` patterns.

## Definition of Done

- [ ] All 3 acceptance criteria satisfied with automated verification
- [ ] Unit tests pass (source-text validation)
- [ ] Demo passes all acceptance criteria
- [ ] `make validate` passes
- [ ] No regressions in existing 70 tests
- [ ] TODO-0007 marked done (status file → done/)
- [ ] TODO-0008 status file updated (backlog → in-progress → done via PR)

## Scope Boundaries (Out of Scope)

- LLM-based frame control — explicitly excluded by AC1
- Persistent run recording — TODO-0010
- Agent service boundary — TODO-0009
- Health/metrics — TODO-0012

## Failure Modes

- Godot timeout → demo treats as failure
- `can_reach()` returns false → `action_failed` emitted, no invalid action attempted
- Agent reaches room boundary → `move_and_slide()` slides along boundary, no pass-through