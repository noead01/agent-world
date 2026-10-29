---
id: TODO-0019
priority: P1
status: backlog
type: feature
title: "Implement beliefs and evidence"
dependencies:
  - TODO-0004
  - TODO-0010
  - TODO-0018
branch: null
pull_request: null
created: 2026-10-29
updated: 2026-10-29
---

# Implement beliefs and evidence

## Outcome

Claims track confidence, status, supporting and contradicting evidence, provenance, and revision history.

## Scope

Deliver the smallest coherent implementation that achieves the stated outcome and integrates with the existing architecture. Work outside this outcome is excluded unless required by a listed dependency or acceptance criterion.

## Acceptance criteria

- [ ] Beliefs are distinct from authoritative facts and agent-authored notes.
- [ ] New evidence can increase, decrease, contradict, or retire a belief without erasing history.
- [ ] Every material belief revision links to recorded evidence.

## Definition of done

- [ ] All acceptance criteria are satisfied and supported by automated or repeatable verification.
- [ ] Relevant schemas, telemetry, documentation, ADRs, and adjacent backlog records are updated.
- [ ] Failure modes are observable and no known regression invalidates experiment results.
- [ ] The demonstration plan has been executed and its evidence is linked from the pull request.

## Demonstration plan

1. Prepare the smallest reproducible scenario and configuration needed for the demonstration.
2. Let the agent form a belief, introduce contradictory evidence, and inspect confidence and revision history.
3. Capture the relevant UI, event, trace, report, or command output and link it from the pull request.

## Status history

- 2026-10-29 — `backlog`: Item materialized from the prioritized roadmap.

## Notes

Record blockers, scope changes, implementation decisions, and review context here.

