---
id: TODO-0005
priority: P0
status: backlog
type: feature
title: "Define observability correlation and validity schemas"
dependencies:
  - TODO-0004
branch: null
pull_request: null
created: 2026-10-29
updated: 2026-10-29
---

# Define observability correlation and validity schemas

## Outcome

Run validity, simulation ticks, world revisions, trace context, component versions, content-capture mode, and configuration fingerprints share one validated schema.

## Scope

Deliver the smallest coherent implementation that achieves the stated outcome and integrates with the existing architecture. Work outside this outcome is excluded unless required by a listed dependency or acceptance criterion.

## Acceptance criteria

- [ ] Correlation fields are consistent across world, agent, event, and telemetry messages.
- [ ] Run-validity transitions are represented and validated.
- [ ] Configuration fingerprints are stable for identical effective configurations.

## Definition of done

- [ ] All acceptance criteria are satisfied and supported by automated or repeatable verification.
- [ ] Relevant schemas, telemetry, documentation, ADRs, and adjacent backlog records are updated.
- [ ] Failure modes are observable and no known regression invalidates experiment results.
- [ ] The demonstration plan has been executed and its evidence is linked from the pull request.

## Demonstration plan

1. Prepare the smallest reproducible scenario and configuration needed for the demonstration.
2. Run a schema example across two simulated components and show joined correlation plus a deliberate invalid-run transition.
3. Capture the relevant UI, event, trace, report, or command output and link it from the pull request.

## Status history

- 2026-10-29 — `backlog`: Item materialized from the prioritized roadmap.

## Notes

Record blockers, scope changes, implementation decisions, and review context here.

