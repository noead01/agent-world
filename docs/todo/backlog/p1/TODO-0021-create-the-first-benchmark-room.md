---
id: TODO-0021
priority: P1
status: backlog
type: research/experimentation
title: "Create the first benchmark room"
dependencies:
  - TODO-0006
  - TODO-0007
  - TODO-0019
  - TODO-0020
branch: null
pull_request: null
created: 2026-10-29
updated: 2026-10-29
---

# Create the first benchmark room

## Outcome

A four-object benchmark contains at least six facts spanning direct observation, physical experimentation, temporal behavior, and multi-step inference.

## Scope

Deliver the smallest coherent implementation that achieves the stated outcome and integrates with the existing architecture. Work outside this outcome is excluded unless required by a listed dependency or acceptance criterion.

## Acceptance criteria

- [ ] Every fact has explicit evidence and verification criteria.
- [ ] The room can be reset to identical initial conditions using its seed.
- [ ] Fact difficulty and required interaction depth are documented.

## Definition of done

- [ ] All acceptance criteria are satisfied and supported by automated or repeatable verification.
- [ ] Relevant schemas, telemetry, documentation, ADRs, and adjacent backlog records are updated.
- [ ] Failure modes are observable and no known regression invalidates experiment results.
- [ ] The demonstration plan has been executed and its evidence is linked from the pull request.

## Demonstration plan

1. Prepare the smallest reproducible scenario and configuration needed for the demonstration.
2. Release the mock-brain agent into the room, then review which fact stages were reached without exposing hidden truth during the run.
3. Capture the relevant UI, event, trace, report, or command output and link it from the pull request.

## Status history

- 2026-10-29 — `backlog`: Item materialized from the prioritized roadmap.

## Notes

Record blockers, scope changes, implementation decisions, and review context here.

