---
id: TODO-0033
priority: P2
status: backlog
type: feature
title: "Add manipulators and articulated bodies"
dependencies:
  - TODO-0007
  - TODO-0008
branch: null
pull_request: null
created: 2026-10-29
updated: 2026-10-29
---

# Add manipulators and articulated bodies

## Outcome

Agents can use articulated effectors and richer affordances while physics remains authoritative.

## Scope

Deliver the smallest coherent implementation that achieves the stated outcome and integrates with the existing architecture. Work outside this outcome is excluded unless required by a listed dependency or acceptance criterion.

## Acceptance criteria

- [ ] Joint limits, forces, reach, and grasp constraints are physically enforced.
- [ ] High-level intentions compile into bounded deterministic controllers.
- [ ] Failed grasps and unsafe motions produce observable outcomes.

## Definition of done

- [ ] All acceptance criteria are satisfied and supported by automated or repeatable verification.
- [ ] Relevant schemas, telemetry, documentation, ADRs, and adjacent backlog records are updated.
- [ ] Failure modes are observable and no known regression invalidates experiment results.
- [ ] The demonstration plan has been executed and its evidence is linked from the pull request.

## Demonstration plan

1. Prepare the smallest reproducible scenario and configuration needed for the demonstration.
2. Reach for, grasp, move, and release several objects, including an unreachable and an unsafe case.
3. Capture the relevant UI, event, trace, report, or command output and link it from the pull request.

## Status history

- 2026-10-29 — `backlog`: Item materialized from the prioritized roadmap.

## Notes

Record blockers, scope changes, implementation decisions, and review context here.

