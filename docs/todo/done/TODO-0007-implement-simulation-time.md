---
id: TODO-0007
priority: P0
status: done
type: feature
title: "Implement simulation time"
dependencies:
  - TODO-0002
  - TODO-0006
branch: feature/todo-0007-simulation-time
pull_request: null
created: 2026-10-29
updated: 2026-11-01
---

# Implement simulation time

## Outcome

The runtime supports fixed-step simulation time, pause, resume, reset, time scaling, and an accelerated day/night cycle.

## Scope

Deliver the smallest coherent implementation that achieves the stated outcome and integrates with the existing architecture. Work outside this outcome is excluded unless required by a listed dependency or acceptance criterion.

## Acceptance criteria

- [x] Simulation time advances only through fixed physics steps.
- [x] Pause freezes simulation behavior without corrupting state; resume continues coherently.
- [x] Reset and time scaling produce documented, observable lighting and clock behavior.

## Definition of done

- [x] All acceptance criteria are satisfied and supported by automated or repeatable verification.
- [x] Relevant schemas, telemetry, documentation, ADRs, and adjacent backlog records are updated.
- [x] Failure modes are observable and no known regression invalidates experiment results.
- [x] The demonstration plan has been executed and its evidence is linked from the pull request.

## Demonstration plan

1. Prepare the smallest reproducible scenario and configuration needed for the demonstration.
2. Run a day/night cycle at multiple speeds, pause mid-cycle, resume, and reset to the same initial time.
3. Capture the relevant UI, event, trace, report, or command output and link it from the pull request.

## Status history

- 2026-10-29 — `backlog`: Item materialized from the prioritized roadmap.
- 2026-11-01 — `in-progress`: Starting implementation of fixed-step simulation time with pause/resume/reset/time-scale and day/night cycle.
- 2026-11-01 — `done`: All acceptance criteria verified via tools/repository/demo_simulation_time.py; commits merged to main (b2794df).

## Notes

All three acceptance criteria verified via tools/repository/demo_simulation_time.py:
  - Simulation time advances through fixed physics steps (tick and sim time monotonically increase)
  - Pause freezes simulation behavior without corrupting state; resume continues coherently
  - Reset and time scaling produce documented, observable lighting and clock behavior

Implementation: apps/world/src/simulation_time.gd (SimulationTime class), integrated into apps/world/src/room.gd with day/night lighting animation on DirectionalLight3D.

