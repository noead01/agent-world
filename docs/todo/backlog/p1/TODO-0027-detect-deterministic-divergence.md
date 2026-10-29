---
id: TODO-0027
priority: P1
status: backlog
type: feature
title: "Detect deterministic divergence"
dependencies:
  - TODO-0007
  - TODO-0010
  - TODO-0016
branch: null
pull_request: null
created: 2026-10-29
updated: 2026-10-29
---

# Detect deterministic divergence

## Outcome

Periodic canonical-state checksums locate the first deterministic divergence and trigger bounded diagnostic capture.

## Scope

Deliver the smallest coherent implementation that achieves the stated outcome and integrates with the existing architecture. Work outside this outcome is excluded unless required by a listed dependency or acceptance criterion.

## Acceptance criteria

- [ ] Canonical state encoding is documented and stable for the pinned runtime version.
- [ ] Repeated mock-brain runs compare checksums at identical ticks.
- [ ] A mismatch records the first divergent tick and a bounded surrounding diagnostic window.

## Definition of done

- [ ] All acceptance criteria are satisfied and supported by automated or repeatable verification.
- [ ] Relevant schemas, telemetry, documentation, ADRs, and adjacent backlog records are updated.
- [ ] Failure modes are observable and no known regression invalidates experiment results.
- [ ] The demonstration plan has been executed and its evidence is linked from the pull request.

## Demonstration plan

1. Prepare the smallest reproducible scenario and configuration needed for the demonstration.
2. Run identical seeded experiments to show matching checksums, then inject a controlled difference and locate its first divergence.
3. Capture the relevant UI, event, trace, report, or command output and link it from the pull request.

## Status history

- 2026-10-29 — `backlog`: Item materialized from the prioritized roadmap.

## Notes

Record blockers, scope changes, implementation decisions, and review context here.

