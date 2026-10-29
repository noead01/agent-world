---
id: TODO-0042
priority: P3
status: backlog
type: research/experimentation
title: "Explore grounded language development"
dependencies:
  - TODO-0041
branch: null
pull_request: null
created: 2026-10-29
updated: 2026-10-29
---

# Explore grounded language development

## Outcome

Agents can develop or adapt language grounded in shared world experiences and observable referents.

## Scope

Deliver the smallest coherent implementation that achieves the stated outcome and integrates with the existing architecture. Work outside this outcome is excluded unless required by a listed dependency or acceptance criterion.

## Acceptance criteria

- [ ] Utterances link to speaker context, perceived referents, and subsequent evidence.
- [ ] Evaluation distinguishes coordination success from surface-language similarity.
- [ ] Experiments prevent direct leakage of hidden fact identifiers.

## Definition of done

- [ ] All acceptance criteria are satisfied and supported by automated or repeatable verification.
- [ ] Relevant schemas, telemetry, documentation, ADRs, and adjacent backlog records are updated.
- [ ] Failure modes are observable and no known regression invalidates experiment results.
- [ ] The demonstration plan has been executed and its evidence is linked from the pull request.

## Demonstration plan

1. Prepare the smallest reproducible scenario and configuration needed for the demonstration.
2. Have two agents coordinate around initially unnamed objects and review how stable terms emerge and support a task.
3. Capture the relevant UI, event, trace, report, or command output and link it from the pull request.

## Status history

- 2026-10-29 — `backlog`: Item materialized from the prioritized roadmap.

## Notes

Record blockers, scope changes, implementation decisions, and review context here.

