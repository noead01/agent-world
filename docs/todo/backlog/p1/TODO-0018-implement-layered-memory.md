---
id: TODO-0018
priority: P1
status: backlog
type: feature
title: "Implement layered memory"
dependencies:
  - TODO-0004
  - TODO-0010
  - TODO-0016
branch: null
pull_request: null
created: 2026-10-29
updated: 2026-10-29
---

# Implement layered memory

## Outcome

Working, episodic, semantic, and procedural memory are distinct from one another and from the objective event record.

## Scope

Deliver the smallest coherent implementation that achieves the stated outcome and integrates with the existing architecture. Work outside this outcome is excluded unless required by a listed dependency or acceptance criterion.

## Acceptance criteria

- [ ] Each memory type has explicit write, retrieval, update, and retention semantics.
- [ ] Retrieved memories include provenance and relevance information.
- [ ] Memory failure or absence cannot rewrite the authoritative event history.

## Definition of done

- [ ] All acceptance criteria are satisfied and supported by automated or repeatable verification.
- [ ] Relevant schemas, telemetry, documentation, ADRs, and adjacent backlog records are updated.
- [ ] Failure modes are observable and no known regression invalidates experiment results.
- [ ] The demonstration plan has been executed and its evidence is linked from the pull request.

## Demonstration plan

1. Prepare the smallest reproducible scenario and configuration needed for the demonstration.
2. Create one memory of each type, retrieve it in a later decision, and compare memory content with the immutable event record.
3. Capture the relevant UI, event, trace, report, or command output and link it from the pull request.

## Status history

- 2026-10-29 — `backlog`: Item materialized from the prioritized roadmap.

## Notes

Record blockers, scope changes, implementation decisions, and review context here.

