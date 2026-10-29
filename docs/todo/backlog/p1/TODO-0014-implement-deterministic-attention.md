---
id: TODO-0014
priority: P1
status: backlog
type: feature
title: "Implement deterministic attention"
dependencies:
  - TODO-0013
branch: null
pull_request: null
created: 2026-10-29
updated: 2026-10-29
---

# Implement deterministic attention

## Outcome

Attention ranks candidate observations using novelty, proximity, change, drive relevance, and current-goal relevance.

## Scope

Deliver the smallest coherent implementation that achieves the stated outcome and integrates with the existing architecture. Work outside this outcome is excluded unless required by a listed dependency or acceptance criterion.

## Acceptance criteria

- [ ] The scoring factors and tie-breaking behavior are documented and deterministic.
- [ ] Selected and rejected candidates can be inspected with their scores.
- [ ] Attention produces a bounded context within configured limits.

## Definition of done

- [ ] All acceptance criteria are satisfied and supported by automated or repeatable verification.
- [ ] Relevant schemas, telemetry, documentation, ADRs, and adjacent backlog records are updated.
- [ ] Failure modes are observable and no known regression invalidates experiment results.
- [ ] The demonstration plan has been executed and its evidence is linked from the pull request.

## Demonstration plan

1. Prepare the smallest reproducible scenario and configuration needed for the demonstration.
2. Present competing objects and events, vary one scoring factor at a time, and show predictable selection changes.
3. Capture the relevant UI, event, trace, report, or command output and link it from the pull request.

## Status history

- 2026-10-29 — `backlog`: Item materialized from the prioritized roadmap.

## Notes

Record blockers, scope changes, implementation decisions, and review context here.

