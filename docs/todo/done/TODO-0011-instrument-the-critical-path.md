---
id: TODO-0011
priority: null
status: done
type: feature
title: "Instrument the critical path"
dependencies:
  - TODO-0005
  - TODO-0009
  - TODO-0010
branch: feature/todo-0011-instrument-the-critical-path
pull_request: "11"
created: 2026-10-29
updated: 2026-11-15
---

# Instrument the critical path

## Outcome

Traces connect observation, attention, deliberation, validation, arbitration, action, physical outcome, memory, and discovery evaluation.

## Scope

Deliver the smallest coherent implementation that achieves the stated outcome and integrates with the existing architecture. Work outside this outcome is excluded unless required by a listed dependency or acceptance criterion.

## Acceptance criteria

- [x] Trace context crosses the Godot and agent-service boundary.
- [x] Each critical operation uses stable span names and bounded attributes.
- [x] An unexpected action can be followed from observation through physical outcome.

## Definition of done

- [ ] All acceptance criteria are satisfied and supported by automated or repeatable verification.
- [ ] Relevant schemas, telemetry, documentation, ADRs, and adjacent backlog records are updated.
- [ ] Failure modes are observable and no known regression invalidates experiment results.
- [ ] The demonstration plan has been executed and its evidence is linked from the pull request.

## Demonstration plan

1. Prepare the smallest reproducible scenario and configuration needed for the demonstration.
2. Run one autonomous intention and navigate its trace from perception to action result across both processes.
3. Capture the relevant UI, event, trace, report, or command output and link it from the pull request.

## Status history

- 2026-10-29 — `backlog`: Item materialized from the prioritized roadmap.
- 2026-11-15 — `in-progress`: Selected for implementation; branch `feature/todo-0011-instrument-the-critical-path`.
- 2026-11-15 — `done`: All 8 review findings addressed; trace context propagates with sampling; 158 unit + 9 acceptance tests pass; PR #11 ready for merge.

## Notes

Record blockers, scope changes, implementation decisions, and review context here.

