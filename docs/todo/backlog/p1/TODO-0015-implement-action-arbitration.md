---
id: TODO-0015
priority: P1
status: backlog
type: feature
title: "Implement action arbitration"
dependencies:
  - TODO-0008
  - TODO-0013
  - TODO-0014
branch: null
pull_request: null
created: 2026-10-29
updated: 2026-10-29
---

# Implement action arbitration

## Outcome

A deterministic arbiter selects between reflexes, integrity constraints, current plans, new intentions, and idle exploration.

## Scope

Deliver the smallest coherent implementation that achieves the stated outcome and integrates with the existing architecture. Work outside this outcome is excluded unless required by a listed dependency or acceptance criterion.

## Acceptance criteria

- [ ] Priority and interruption rules are explicit and deterministic.
- [ ] Accepted, rejected, interrupted, resumed, and abandoned intentions are recorded.
- [ ] Physical integrity can preempt deliberative behavior without corrupting the plan state.

## Definition of done

- [ ] All acceptance criteria are satisfied and supported by automated or repeatable verification.
- [ ] Relevant schemas, telemetry, documentation, ADRs, and adjacent backlog records are updated.
- [ ] Failure modes are observable and no known regression invalidates experiment results.
- [ ] The demonstration plan has been executed and its evidence is linked from the pull request.

## Demonstration plan

1. Prepare the smallest reproducible scenario and configuration needed for the demonstration.
2. Start a multi-step intention, trigger an integrity reflex, and show interruption followed by safe resume or reconsideration.
3. Capture the relevant UI, event, trace, report, or command output and link it from the pull request.

## Status history

- 2026-10-29 — `backlog`: Item materialized from the prioritized roadmap.

## Notes

Record blockers, scope changes, implementation decisions, and review context here.

