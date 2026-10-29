---
id: TODO-0022
priority: P1
status: backlog
type: feature
title: "Implement discovery-stage evaluation"
dependencies:
  - TODO-0010
  - TODO-0019
  - TODO-0020
branch: null
pull_request: null
created: 2026-10-29
updated: 2026-10-29
---

# Implement discovery-stage evaluation

## Outcome

Evaluation awards and explains encountered, noticed, investigated, hypothesized, verified, retained, applied, and generalized stages.

## Scope

Deliver the smallest coherent implementation that achieves the stated outcome and integrates with the existing architecture. Work outside this outcome is excluded unless required by a listed dependency or acceptance criterion.

## Acceptance criteria

- [ ] Awards derive from authoritative criteria and recorded evidence rather than agent self-assessment.
- [ ] Each award or revocation links to its evidence and evaluator version.
- [ ] The evaluator explains where progress stopped for each undiscovered fact.

## Definition of done

- [ ] All acceptance criteria are satisfied and supported by automated or repeatable verification.
- [ ] Relevant schemas, telemetry, documentation, ADRs, and adjacent backlog records are updated.
- [ ] Failure modes are observable and no known regression invalidates experiment results.
- [ ] The demonstration plan has been executed and its evidence is linked from the pull request.

## Demonstration plan

1. Prepare the smallest reproducible scenario and configuration needed for the demonstration.
2. Feed known event sequences for full, partial, and false discovery and inspect stage awards and explanations.
3. Capture the relevant UI, event, trace, report, or command output and link it from the pull request.

## Status history

- 2026-10-29 — `backlog`: Item materialized from the prioritized roadmap.

## Notes

Record blockers, scope changes, implementation decisions, and review context here.

