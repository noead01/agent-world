---
id: TODO-0023
priority: P1
status: backlog
type: feature
title: "Build the observer interface"
dependencies:
  - TODO-0007
  - TODO-0011
  - TODO-0013
  - TODO-0015
  - TODO-0019
branch: null
pull_request: null
created: 2026-10-29
updated: 2026-10-29
---

# Build the observer interface

## Outcome

Operators can inspect world time, agent status, drives, attention, goal, plan, notes, beliefs, events, and pending deliberation without controlling moment-to-moment behavior.

## Scope

Deliver the smallest coherent implementation that achieves the stated outcome and integrates with the existing architecture. Work outside this outcome is excluded unless required by a listed dependency or acceptance criterion.

## Acceptance criteria

- [ ] Displayed state is correlated to simulation tick and clearly distinguishes truth from belief.
- [ ] Pause, resume, reset, and inspection do not mutate hidden agent knowledge.
- [ ] Pending, stale, rejected, and failed deliberations are visually distinct.

## Definition of done

- [ ] All acceptance criteria are satisfied and supported by automated or repeatable verification.
- [ ] Relevant schemas, telemetry, documentation, ADRs, and adjacent backlog records are updated.
- [ ] Failure modes are observable and no known regression invalidates experiment results.
- [ ] The demonstration plan has been executed and its evidence is linked from the pull request.

## Demonstration plan

1. Prepare the smallest reproducible scenario and configuration needed for the demonstration.
2. Run the benchmark and use the interface to follow one complete curiosity-to-outcome cycle, including a delayed decision.
3. Capture the relevant UI, event, trace, report, or command output and link it from the pull request.

## Status history

- 2026-10-29 — `backlog`: Item materialized from the prioritized roadmap.

## Notes

Record blockers, scope changes, implementation decisions, and review context here.

