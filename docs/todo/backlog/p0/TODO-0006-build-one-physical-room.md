---
id: TODO-0006
priority: P0
status: backlog
type: feature
title: "Build one physical room"
dependencies:
  - TODO-0002
  - TODO-0004
branch: null
pull_request: null
created: 2026-10-29
updated: 2026-10-29
---

# Build one physical room

## Outcome

A bounded room contains gravity, collisions, four identifiable rigid objects, and configurable physical materials.

## Scope

Deliver the smallest coherent implementation that achieves the stated outcome and integrates with the existing architecture. Work outside this outcome is excluded unless required by a listed dependency or acceptance criterion.

## Acceptance criteria

- [ ] The agent and objects cannot pass through static room boundaries under normal operation.
- [ ] Four objects expose stable IDs, mass, friction, restitution, and shape metadata.
- [ ] Objects fall, collide, settle, and respond to impulses through Jolt.

## Definition of done

- [ ] All acceptance criteria are satisfied and supported by automated or repeatable verification.
- [ ] Relevant schemas, telemetry, documentation, ADRs, and adjacent backlog records are updated.
- [ ] Failure modes are observable and no known regression invalidates experiment results.
- [ ] The demonstration plan has been executed and its evidence is linked from the pull request.

## Demonstration plan

1. Prepare the smallest reproducible scenario and configuration needed for the demonstration.
2. Run the room, drop and push each object, and inspect identifiers and material-dependent physical responses.
3. Capture the relevant UI, event, trace, report, or command output and link it from the pull request.

## Status history

- 2026-10-29 — `backlog`: Item materialized from the prioritized roadmap.

## Notes

Record blockers, scope changes, implementation decisions, and review context here.

