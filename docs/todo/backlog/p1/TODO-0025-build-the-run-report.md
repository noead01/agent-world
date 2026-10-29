---
id: TODO-0025
priority: P1
status: backlog
type: feature
title: "Build the run report"
dependencies:
  - TODO-0010
  - TODO-0022
branch: null
pull_request: null
created: 2026-10-29
updated: 2026-10-29
---

# Build the run report

## Outcome

A run report presents coverage, depth, accuracy, autonomy, efficiency, evidence quality, retention, and reasons for missed facts.

## Scope

Deliver the smallest coherent implementation that achieves the stated outcome and integrates with the existing architecture. Work outside this outcome is excluded unless required by a listed dependency or acceptance criterion.

## Acceptance criteria

- [ ] Every reported value identifies its metric and evaluator version.
- [ ] The report distinguishes invalid, degraded, aborted, and valid runs.
- [ ] Fact-level drill-down exposes the evidence behind aggregate scores.

## Definition of done

- [ ] All acceptance criteria are satisfied and supported by automated or repeatable verification.
- [ ] Relevant schemas, telemetry, documentation, ADRs, and adjacent backlog records are updated.
- [ ] Failure modes are observable and no known regression invalidates experiment results.
- [ ] The demonstration plan has been executed and its evidence is linked from the pull request.

## Demonstration plan

1. Prepare the smallest reproducible scenario and configuration needed for the demonstration.
2. Generate reports for a successful, partially successful, and invalid run and compare their fact-level explanations.
3. Capture the relevant UI, event, trace, report, or command output and link it from the pull request.

## Status history

- 2026-10-29 — `backlog`: Item materialized from the prioritized roadmap.

## Notes

Record blockers, scope changes, implementation decisions, and review context here.

