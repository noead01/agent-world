---
id: TODO-0010
priority: P0
status: backlog
type: feature
title: "Create append-only run recording"
dependencies:
  - TODO-0004
  - TODO-0005
branch: null
pull_request: null
created: 2026-10-29
updated: 2026-10-29
---

# Create append-only run recording

## Outcome

Each run persists initial conditions, configurations, seeds, versions, typed events, validity transitions, and final state in sequence.

## Scope

Deliver the smallest coherent implementation that achieves the stated outcome and integrates with the existing architecture. Work outside this outcome is excluded unless required by a listed dependency or acceptance criterion.

## Acceptance criteria

- [ ] Required events are append-only, ordered, and schema validated.
- [ ] A recorder failure marks the run invalid and is visible to the operator.
- [ ] A completed run can be read back without relying on application logs.

## Definition of done

- [ ] All acceptance criteria are satisfied and supported by automated or repeatable verification.
- [ ] Relevant schemas, telemetry, documentation, ADRs, and adjacent backlog records are updated.
- [ ] Failure modes are observable and no known regression invalidates experiment results.
- [ ] The demonstration plan has been executed and its evidence is linked from the pull request.

## Demonstration plan

1. Prepare the smallest reproducible scenario and configuration needed for the demonstration.
2. Execute a short run, inspect its ordered record, replay the semantic timeline, and simulate a recorder failure.
3. Capture the relevant UI, event, trace, report, or command output and link it from the pull request.

## Status history

- 2026-10-29 — `backlog`: Item materialized from the prioritized roadmap.

## Notes

Record blockers, scope changes, implementation decisions, and review context here.

