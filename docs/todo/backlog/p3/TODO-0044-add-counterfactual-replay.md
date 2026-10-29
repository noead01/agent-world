---
id: TODO-0044
priority: P3
status: backlog
type: research/experimentation
title: "Add counterfactual replay"
dependencies:
  - TODO-0023
  - TODO-0026
  - TODO-0037
branch: null
pull_request: null
created: 2026-10-29
updated: 2026-10-29
---

# Add counterfactual replay

## Outcome

Maintainers can branch a recorded run at a decision point and evaluate alternate valid agent decisions.

## Scope

Deliver the smallest coherent implementation that achieves the stated outcome and integrates with the existing architecture. Work outside this outcome is excluded unless required by a listed dependency or acceptance criterion.

## Acceptance criteria

- [ ] The counterfactual preserves the original state and configuration through the branch tick.
- [ ] Alternate actions are validated against the historical world state.
- [ ] Reports separate observed history from simulated counterfactual outcomes.

## Definition of done

- [ ] All acceptance criteria are satisfied and supported by automated or repeatable verification.
- [ ] Relevant schemas, telemetry, documentation, ADRs, and adjacent backlog records are updated.
- [ ] Failure modes are observable and no known regression invalidates experiment results.
- [ ] The demonstration plan has been executed and its evidence is linked from the pull request.

## Demonstration plan

1. Prepare the smallest reproducible scenario and configuration needed for the demonstration.
2. Select one recorded intention, substitute an alternate action, replay from the checkpoint, and compare downstream discoveries.
3. Capture the relevant UI, event, trace, report, or command output and link it from the pull request.

## Status history

- 2026-10-29 — `backlog`: Item materialized from the prioritized roadmap.

## Notes

Record blockers, scope changes, implementation decisions, and review context here.

