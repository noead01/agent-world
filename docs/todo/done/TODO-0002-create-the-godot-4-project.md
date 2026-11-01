---
id: TODO-0002
priority: null
status: done
type: setup
dependencies: []
branch: feature/todo-0002-godot-4-project
pull_request: "3"
created: 2026-10-29
updated: 2026-11-01
---

# Create the Godot 4 project

## Outcome

A supported Godot project opens with Jolt enabled, a main scene, fixed physics timing, and documented runtime settings.

## Scope

Deliver the smallest coherent implementation that achieves the stated outcome and integrates with the existing architecture. Work outside this outcome is excluded unless required by a listed dependency or acceptance criterion.

## Acceptance criteria

- [x] The project opens without import or configuration errors in the supported Godot version.
- [x] Jolt is selected for 3D physics and the fixed timestep is explicit.
- [x] The main scene runs and reports its runtime and physics versions.

## Definition of done

- [x] All acceptance criteria are satisfied and supported by automated or repeatable verification.
- [x] Relevant schemas, telemetry, documentation, ADRs, and adjacent backlog records are updated.
- [x] Failure modes are observable and no known regression invalidates experiment results.
- [x] The demonstration plan has been executed and its evidence is linked from the pull request.

## Demonstration plan

1. Prepare the smallest reproducible scenario and configuration needed for the demonstration.
2. Open the project in a clean checkout, run the main scene, and show the configured physics engine and fixed timestep.
3. Capture the relevant UI, event, trace, report, or command output and link it from the pull request.

## Status history

- 2026-10-29 — `backlog`: Item materialized from the prioritized roadmap.
- 2026-11-01 — `in-progress`: Godot 4 project created with `project.godot` (Jolt physics engine, fixed 60 Hz timestep), `main.tscn` main scene, `main.gd` reporting runtime/physics versions, and repeatable unit tests validating the project configuration.
- 2026-11-01 — `done`: All acceptance criteria verified via Godot 4.7.2 headless run. Output:
    `Runtime: Godot 4.7.2-stable (official)`
    `Physics engine: JoltPhysics`
    `Fixed timestep: 60 Hz`
  Unit tests in `apps/world/tests/unit/test_project_config.py` provide repeatable verification. PR #3 opened and merged.

## Notes

Godot 4.7.2-stable Linux x86_64 was downloaded and used to run the project headless (`godot --headless --path apps/world --quit-after 1`), confirming all three acceptance criteria.
