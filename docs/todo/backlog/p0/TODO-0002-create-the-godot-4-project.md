---
id: TODO-0002
priority: P0
status: backlog
type: setup
title: "Create the Godot 4 project"
dependencies: []
branch: null
pull_request: null
created: 2026-10-29
updated: 2026-10-29
---

# Create the Godot 4 project

## Outcome

A supported Godot project opens with Jolt enabled, a main scene, fixed physics timing, and documented runtime settings.

## Scope

Deliver the smallest coherent implementation that achieves the stated outcome and integrates with the existing architecture. Work outside this outcome is excluded unless required by a listed dependency or acceptance criterion.

## Acceptance criteria

- [ ] The project opens without import or configuration errors in the supported Godot version.
- [ ] Jolt is selected for 3D physics and the fixed timestep is explicit.
- [ ] The main scene runs and reports its runtime and physics versions.

## Definition of done

- [ ] All acceptance criteria are satisfied and supported by automated or repeatable verification.
- [ ] Relevant schemas, telemetry, documentation, ADRs, and adjacent backlog records are updated.
- [ ] Failure modes are observable and no known regression invalidates experiment results.
- [ ] The demonstration plan has been executed and its evidence is linked from the pull request.

## Demonstration plan

1. Prepare the smallest reproducible scenario and configuration needed for the demonstration.
2. Open the project in a clean checkout, run the main scene, and show the configured physics engine and fixed timestep.
3. Capture the relevant UI, event, trace, report, or command output and link it from the pull request.

## Status history

- 2026-10-29 — `backlog`: Item materialized from the prioritized roadmap.

## Notes

Record blockers, scope changes, implementation decisions, and review context here.

