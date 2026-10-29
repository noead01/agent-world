---
id: TODO-0031
priority: P2
status: backlog
type: research/experimentation
title: "Add retention and transfer tests"
dependencies:
  - TODO-0018
  - TODO-0022
  - TODO-0024
branch: null
pull_request: null
created: 2026-10-29
updated: 2026-10-29
---

# Add retention and transfer tests

## Outcome

Scenarios can test delayed recall and application of learned facts in changed environments.

## Scope

Deliver the smallest coherent implementation that achieves the stated outcome and integrates with the existing architecture. Work outside this outcome is excluded unless required by a listed dependency or acceptance criterion.

## Acceptance criteria

- [ ] Retention intervals and distractions are explicit in scenario metadata.
- [ ] Transfer tests vary relevant context while preserving the learned principle.
- [ ] Results distinguish recall failure, execution failure, and invalid transfer assumptions.

## Definition of done

- [ ] All acceptance criteria are satisfied and supported by automated or repeatable verification.
- [ ] Relevant schemas, telemetry, documentation, ADRs, and adjacent backlog records are updated.
- [ ] Failure modes are observable and no known regression invalidates experiment results.
- [ ] The demonstration plan has been executed and its evidence is linked from the pull request.

## Demonstration plan

1. Prepare the smallest reproducible scenario and configuration needed for the demonstration.
2. Teach one fact, advance through a distraction period, then test recall and application in a changed room.
3. Capture the relevant UI, event, trace, report, or command output and link it from the pull request.

## Status history

- 2026-10-29 — `backlog`: Item materialized from the prioritized roadmap.

## Notes

Record blockers, scope changes, implementation decisions, and review context here.

