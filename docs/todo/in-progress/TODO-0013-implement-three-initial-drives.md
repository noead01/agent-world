---
id: TODO-0013
priority: null
status: in-progress
type: feature
title: "Implement three initial drives"
dependencies:
  - TODO-0008
  - TODO-0012
branch: feature/todo-0013-implement-three-initial-drives
pull_request: null
created: 2026-10-29
updated: 2026-11-21
---

# Implement three initial drives

## Outcome

Curiosity, uncertainty, and physical integrity have explicit deterministic update rules and observable state.

## Scope

Deliver the smallest coherent implementation that achieves the stated outcome and integrates with the existing architecture. Work outside this outcome is excluded unless required by a listed dependency or acceptance criterion.

## Acceptance criteria

- [ ] Each drive has documented range, inputs, update frequency, and thresholds.
- [ ] Identical inputs and seeds produce identical drive histories.
- [ ] Threshold crossings can influence arbitration and are recorded when behaviorally relevant.

## Definition of done

- [ ] All acceptance criteria are satisfied and supported by automated or repeatable verification.
- [ ] Relevant schemas, telemetry, documentation, ADRs, and adjacent backlog records are updated.
- [ ] Failure modes are observable and no known regression invalidates experiment results.
- [ ] The demonstration plan has been executed and its evidence is linked from the pull request.

## Demonstration plan

1. Prepare the smallest reproducible scenario and configuration needed for the demonstration.
2. Use controlled stimuli to raise and lower each drive and display the resulting timeline and threshold effects.
3. Capture the relevant UI, event, trace, report, or command output and link it from the pull request.

## Status history

- 2026-10-29 — `backlog`: Item materialized from the prioritized roadmap.
- 2026-11-21 — `in-progress`: Started implementation on branch `feature/todo-0013-implement-three-initial-drives`.

## Notes

Record blockers, scope changes, implementation decisions, and review context here.

