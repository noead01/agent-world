---
id: TODO-0008
priority: P0
status: backlog
type: feature
title: "Implement a basic embodied agent"
dependencies:
  - TODO-0006
  - TODO-0007
branch: null
pull_request: null
created: 2026-10-29
updated: 2026-10-29
---

# Implement a basic embodied agent

## Outcome

A visible agent can orient, move, respect collisions and reach limits, and execute deterministic physical actions.

## Scope

Deliver the smallest coherent implementation that achieves the stated outcome and integrates with the existing architecture. Work outside this outcome is excluded unless required by a listed dependency or acceptance criterion.

## Acceptance criteria

- [ ] Locomotion and orientation use deterministic controllers rather than LLM frame control.
- [ ] Collision avoidance and reach constraints prevent invalid actions.
- [ ] Action start, completion, interruption, and failure are observable.

## Definition of done

- [ ] All acceptance criteria are satisfied and supported by automated or repeatable verification.
- [ ] Relevant schemas, telemetry, documentation, ADRs, and adjacent backlog records are updated.
- [ ] Failure modes are observable and no known regression invalidates experiment results.
- [ ] The demonstration plan has been executed and its evidence is linked from the pull request.

## Demonstration plan

1. Prepare the smallest reproducible scenario and configuration needed for the demonstration.
2. Direct the mock controller to navigate around an obstacle and attempt both reachable and unreachable object interactions.
3. Capture the relevant UI, event, trace, report, or command output and link it from the pull request.

## Status history

- 2026-10-29 — `backlog`: Item materialized from the prioritized roadmap.

## Notes

Record blockers, scope changes, implementation decisions, and review context here.

