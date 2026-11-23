---
id: TODO-0012
priority: null
status: done
type: feature
title: "Expose foundational health and metrics"
dependencies:
  - TODO-0005
  - TODO-0010
  - TODO-0011
branch: feature/todo-0012-foundational-health-metrics
pull_request: "12"
created: 2026-10-29
updated: 2026-11-15
---

# Expose foundational health and metrics

## Outcome

Maintainers can observe physics timing, overruns, recorder and protocol health, LLM failures, resource use, and run validity through OpenTelemetry-compatible signals.

## Scope

Deliver the smallest coherent implementation that achieves the stated outcome and integrates with the existing architecture. Work outside this outcome is excluded unless required by a listed dependency or acceptance criterion.

## Acceptance criteria

- [x] Health distinguishes component availability from experiment validity.
- [x] Metric labels follow bounded-cardinality conventions.
- [x] Telemetry exporter failure does not block or invalidate an otherwise valid run.

## Definition of done

- [x] All acceptance criteria are satisfied and supported by automated or repeatable verification.
- [x] Relevant schemas, telemetry, documentation, ADRs, and adjacent backlog records are updated.
- [x] Failure modes are observable and no known regression invalidates experiment results.
- [x] The demonstration plan has been executed and its evidence is linked from the pull request.

## Demonstration plan

1. Prepare the smallest reproducible scenario and configuration needed for the demonstration.
2. Display a normal run, inject protocol and exporter failures, and show the resulting health, metrics, and validity behavior.
3. Capture the relevant UI, event, trace, report, or command output and link it from the pull request.

## Status history

- 2026-10-29 — `backlog`: Item materialized from the prioritized roadmap.
- 2026-11-15 — `in-progress`: Starting implementation of foundational health and metrics; branch `feature/todo-0012-foundational-health-metrics`.
- 2026-11-15 — `done`: All acceptance criteria verified; health endpoints, validity state machine, metrics emission, and observability profiles implemented; 187 unit tests + 9 acceptance tests pass.

## Notes

Record blockers, scope changes, implementation decisions, and review context here.

