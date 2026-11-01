---
id: TODO-0006
priority: null
status: done
type: feature
dependencies:
  - TODO-0002
  - TODO-0004
branch: feature/todo-0006-physical-room
pull_request: "8"
created: 2026-10-29
updated: 2026-11-01
---

# Build one physical room

## Outcome

A bounded room contains gravity, collisions, four identifiable rigid objects, and configurable physical materials.

## Scope

Deliver the smallest coherent implementation that achieves the stated outcome and integrates with the existing architecture. Work outside this outcome is excluded unless required by a listed dependency or acceptance criterion.

## Acceptance criteria

- [x] The agent and objects cannot pass through static room boundaries under normal operation.
- [x] Four objects expose stable IDs, mass, friction, restitution, and shape metadata.
- [x] Objects fall, collide, settle, and respond to impulses through Jolt.

## Definition of done

- [x] All acceptance criteria are satisfied and supported by automated or repeatable verification.
- [x] Relevant schemas, telemetry, documentation, ADRs, and adjacent backlog records are updated.
- [x] Failure modes are observable and no known regression invalidates experiment results.
- [x] The demonstration plan has been executed and its evidence is linked from the pull request.

## Demonstration plan

1. Prepare the smallest reproducible scenario and configuration needed for the demonstration.
2. Run the room, drop and push each object, and inspect identifiers and material-dependent physical responses.
3. Capture the relevant UI, event, trace, report, or command output and link it from the pull request.

## Status history

- 2026-10-29 — `backlog`: Item materialized from the prioritized roadmap.
- 2026-11-01 — `in-progress`: Starting implementation of bounded room with static boundaries and four rigid objects.
- 2026-11-01 — `done`: All acceptance criteria verified via tools/repository/demo_room_physics.py; PR #8 merged (feat/simulation-time merged afterward on main).

## Notes

All three acceptance criteria verified via tools/repository/demo_room_physics.py:
  - Objects cannot pass through static room boundaries (X/Z within half_size bounds)
  - Four objects expose stable IDs, mass, friction, bounciness, shape_type, dimensions_m
  - Objects fall, collide, settle, and respond to impulses (obj_metal_sphere moved after impulse at t=1s)

Per-object collision shapes (BoxShape3D/SphereShape3D/CylinderShape3D) constructed based on shape_type metadata.
PhysicsMaterial assigned per object via physics_material_override for configurable friction/restitution.
Pause/resume/reset/time-scale implemented in TODO-0007 builds on this room.
