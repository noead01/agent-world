---
id: TODO-0039
priority: P3
status: backlog
type: research/experimentation
title: "Evaluate learned low-level policies"
dependencies:
  - TODO-0008
  - TODO-0025
branch: null
pull_request: null
created: 2026-10-29
updated: 2026-10-29
---

# Evaluate learned low-level policies

## Outcome

Learned low-level policies can be compared with deterministic controllers without changing high-level intention semantics.

## Scope

Deliver the smallest coherent implementation that achieves the stated outcome and integrates with the existing architecture. Work outside this outcome is excluded unless required by a listed dependency or acceptance criterion.

## Acceptance criteria

- [ ] Controller interfaces and action bounds are identical across variants.
- [ ] Training data and policy versions are recorded.
- [ ] Safety, determinism, efficiency, and discovery effects are compared.

## Definition of done

- [ ] All acceptance criteria are satisfied and supported by automated or repeatable verification.
- [ ] Relevant schemas, telemetry, documentation, ADRs, and adjacent backlog records are updated.
- [ ] Failure modes are observable and no known regression invalidates experiment results.
- [ ] The demonstration plan has been executed and its evidence is linked from the pull request.

## Demonstration plan

1. Prepare the smallest reproducible scenario and configuration needed for the demonstration.
2. Execute identical intentions with deterministic and learned controllers and compare trajectories, failures, and experiment metrics.
3. Capture the relevant UI, event, trace, report, or command output and link it from the pull request.

## Status history

- 2026-10-29 — `backlog`: Item materialized from the prioritized roadmap.

## Notes

Record blockers, scope changes, implementation decisions, and review context here.

