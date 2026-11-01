# TODO-0007 Design: Implement Simulation Time

## Overview

Implement fixed-step simulation time with pause, resume, reset, time scaling, and an accelerated day/night cycle. Builds on TODO-0002 (Godot project) and TODO-0006 (physical room with Jolt physics).

## Acceptance Criteria

1. Simulation time advances only through fixed physics steps.
2. Pause freezes simulation behavior without corrupting state; resume continues coherently.
3. Reset and time scaling produce documented, observable lighting and clock behavior.

## Architecture

### Component: `SimulationTime` (`apps/world/src/simulation_time.gd`)

A `Node` subclass (`class_name SimulationTime`) that owns all simulation-time state and logic. Created programmatically by `Room` in `_ready()` and added as a child node.

**Responsibilities:**
- Track monotonic `simulation_time` (seconds) and `simulation_tick` (fixed step count)
- Apply `time_scale` multiplier to physics `delta` on each tick
- Honor `is_paused` — when true, `tick()` is a no-op (state preserved, no time advancement)
- Compute `time_of_day` (0–24 hours) from `simulation_time` relative to `time_of_day_start_hour` and `day_cycle_duration_s`
- Emit signals for time progression, pause/resume/reset, and time-of-day changes

**Properties** (all `@export`):
| Property | Type | Default | Description |
|---|---|---|---|
| `simulation_time` | float | 0.0 | Monotonic simulated seconds |
| `simulation_tick` | int | 0 | Fixed physics-step counter |
| `time_scale` | float | 1.0 | Multiplier applied to `delta` |
| `is_paused` | bool | false | Freeze simulation when true |
| `time_of_day_start_hour` | float | 6.0 | Sim hour at t=0 |
| `day_cycle_duration_s` | float | 300.0 | Real seconds per 24h sim cycle |

**Signals:**
- `simulation_ticked(tick: int, time: float)` — emitted each fixed step
- `simulation_paused()` — emitted on pause
- `simulation_resumed()` — emitted on resume
- `simulation_reset()` — emitted on reset
- `time_of_day_changed(hour: float)` — emitted when time_of_day changes

**Methods:**
- `tick(delta: float)` — advances time (no-op if paused)
- `pause()` — sets `is_paused = true`, emits `simulation_paused()`
- `resume()` — sets `is_paused = false`, emits `simulation_resumed()`
- `reset()` — zeroes time and tick, emits `simulation_reset()`
- `set_time_scale(scale: float)` — updates `time_scale`
- `get_time_of_day() -> float` — returns current sim hour (0–24)

### Integration: `Room` (`apps/world/src/room.gd`)

**Changes:**
- Creates `SimulationTime` child in `_ready()` via `load("res://src/simulation_time.gd").new()` + `add_child()`
- `_physics_process(delta)`:
  - Calls `simulation_time.tick(delta)` first
  - Applies gravity/impulses only when `!simulation_time.is_paused`
  - Prints sim state (time, tick, paused, scale, time_of_day) each second
  - Runs auto-demo sequence: pause@2s → resume@4s → time_scale=2.0@6s → reset@8s → quit@10s
- Connects `simulation_time.time_of_day_changed` to lighting animation
- Animates `DirectionalLight3D` (found via `get_node("../DirectionalLight3D")`) rotation and energy based on `time_of_day`

### Day/Night Lighting

Maps `time_of_day` (0–24) to `DirectionalLight3D`:
| Time | Rotation | Energy | Color |
|---|---|---|---|
| 6h (sunrise) | Low angle east | 0.6 | Warm |
| 12h (noon) | Overhead | 1.0 | Neutral |
| 18h (sunset) | Low angle west | 0.6 | Warm |
| 0h (midnight) | Below horizon | 0.1 | Dark blue |

Interpolated between keyframes for smooth transitions.

## Data Flow

```
_physics_process(delta)
    └─> simulation_time.tick(delta)
          ├─> if paused: return (state preserved)
          ├─> simulation_time += delta * time_scale
          ├─> simulation_tick += 1
          ├─> emit simulation_ticked(tick, time)
          └─> emit time_of_day_changed(hour) [when hour changes]
    ├─> if !paused: apply gravity forces to objects
    ├─> print sim state (periodic)
    └─> run demo sequence (pause/resume/scale/reset/quit)
```

## Testing

### Unit Tests (`apps/world/tests/unit/test_simulation_time.py`)

Pure Python tests validating source text (no Godot required):
- `simulation_time.gd` exists
- `class_name SimulationTime` declared
- Required properties present: `simulation_time`, `simulation_tick`, `time_scale`, `is_paused`, `time_of_day_start_hour`, `day_cycle_duration_s`
- Required methods present: `tick`, `pause`, `resume`, `reset`, `set_time_scale`, `get_time_of_day`
- Required signals present: `simulation_ticked`, `simulation_paused`, `simulation_resumed`, `simulation_reset`, `time_of_day_changed`
- `room.gd` creates and uses `SimulationTime`

### Demo (`tools/repository/demo_simulation_time.py`)

Runs Godot headless, parses stdout, validates:
- **AC1**: Simulation time advances through fixed physics steps (tick increments monotonically, time increases between prints)
- **AC2**: Pause freezes simulation (time constant across prints while paused; objects don't move); resume continues coherently (time resumes advancing; object positions continue from pause point)
- **AC3**: Reset returns time to ~0; time scale 2.0 advances time ~2x faster; day/night cycle produces observable lighting changes (energy/rotation differ across time_of_day)

Follows existing `demo_room_physics.py` patterns: `subprocess.Popen([godot, "--headless", "--path", WORLD_DIR])`, `check()` helper, `all_pass` accumulation, `raise SystemExit(main())`.

## Definition of Done

- [ ] All 3 acceptance criteria satisfied with automated verification
- [ ] Unit tests pass (source-text validation)
- [ ] Demo passes all acceptance criteria
- [ ] `make validate` passes
- [ ] No regressions in existing 59 tests
- [ ] TODO-0007 status file updated (backlog → in-progress → done via PR)

## Scope Boundaries (Out of Scope)

- Agent time perception (`world_time_s` in agent.schema.json) — TODO-0008/agent work
- Event timestamping integration — TODO-0011/instrumentation
- Run recording/persistence — TODO-0010
- Health/metrics endpoints — TODO-0012
- Service boundary — TODO-0009

## Failure Modes

- Godot timeout → demo treats as failure (`all_pass = False`, non-zero exit)
- `DirectionalLight3D` not found → Room prints warning, continues without lighting animation
- `time_scale <= 0` → clamped to minimum 0.001 to prevent division by zero in time_of_day
- Pause during object settlement → objects retain positions/velocities; no state corruption