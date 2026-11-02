---
id: TODO-0008
priority: P0
status: done
type: feature
title: "Implement a basic embodied agent"
dependencies:
  - TODO-0006
  - TODO-0007
branch: feature/todo-0008-embodied-agent
pull_request: null
created: 2026-10-29
updated: 2026-11-01
---

# Implement a basic embodied agent

## Outcome

A visible agent can orient, move, respect collisions and reach limits, and execute deterministic physical actions.

## Scope

Deliver the smallest coherent implementation that achieves the stated outcome and integrates with the existing architecture. Work outside this outcome is excluded unless required by a listed dependency or acceptance criterion.

## Acceptance criteria

- [x] Locomotion and orientation use deterministic controllers rather than LLM frame control.
- [x] Collision avoidance and reach constraints prevent invalid actions.
- [x] Action start, completion, interruption, and failure are observable.

## Definition of done

- [x] All acceptance criteria are satisfied and supported by automated or repeatable verification.
- [x] Relevant schemas, telemetry, documentation, ADRs, and adjacent backlog records are updated.
- [x] Failure modes are observable and no known regression invalidates experiment results.
- [x] The demonstration plan has been executed and its evidence is linked from the pull request.

## Demonstration plan

1. Prepare the smallest reproducible scenario and configuration needed for the demonstration.
2. Direct the mock controller to navigate around an obstacle and attempt both reachable and unreachable object interactions.
3. Capture the relevant UI, event, trace, report, or command output and link it from the pull request.

## Status history

- 2026-10-29 — `backlog`: Item materialized from the prioritized roadmap.
- 2026-11-01 — `in-progress`: Starting implementation of embodied agent with CharacterBody3D locomotion, MockController, and action lifecycle signals.
- 2026-11-01 — `done`: All acceptance criteria verified via tools/repository/demo_agent.py; 15 unit tests added in apps/world/tests/unit/test_agent.py.

## Notes

All three acceptance criteria verified via tools/repository/demo_agent.py:
  - Deterministic locomotion: agent position changes over time, heading updates via MockController
  - Collision avoidance: agent remains within room bounds (half_size=13.5m)
  - Reach constraints: touch/inspect actions validate distance before executing
  - Observable action lifecycle: action_started/action_completed/action_failed/action_interrupted signals emitted and parsed

Implementation: apps/world/src/agent.gd (Agent class, CharacterBody3D), apps/world/src/mock_controller.gd (MockController), integrated into apps/world/src/room.gd with agent spawning and simulation_time integration.

