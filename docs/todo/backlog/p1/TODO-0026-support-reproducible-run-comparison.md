---
id: TODO-0026
priority: P1
status: backlog
type: feature
title: "Support reproducible run comparison"
dependencies:
  - TODO-0021
  - TODO-0024
branch: null
pull_request: null
created: 2026-10-29
updated: 2026-10-29
---

# Support reproducible run comparison

## Outcome

Maintainers can compare at least two agent configurations on identical scenarios and seeds with configuration differences made explicit.

## Scope

Deliver the smallest coherent implementation that achieves the stated outcome and integrates with the existing architecture. Work outside this outcome is excluded unless required by a listed dependency or acceptance criterion.

## Acceptance criteria

- [ ] Comparison rejects or warns on incompatible scenario, schema, engine, or evaluator versions.
- [ ] Behavioral and discovery differences link back to the contributing runs.
- [ ] Model latency and nondeterminism are separated from deterministic configuration changes.

## Definition of done

- [ ] All acceptance criteria are satisfied and supported by automated or repeatable verification.
- [ ] Relevant schemas, telemetry, documentation, ADRs, and adjacent backlog records are updated.
- [ ] Failure modes are observable and no known regression invalidates experiment results.
- [ ] The demonstration plan has been executed and its evidence is linked from the pull request.

## Demonstration plan

1. Prepare the smallest reproducible scenario and configuration needed for the demonstration.
2. Run two drive configurations on the same benchmark seeds and inspect aligned behavior and discovery deltas.
3. Capture the relevant UI, event, trace, report, or command output and link it from the pull request.

## Status history

- 2026-10-29 — `backlog`: Item materialized from the prioritized roadmap.

## Notes

Record blockers, scope changes, implementation decisions, and review context here.

