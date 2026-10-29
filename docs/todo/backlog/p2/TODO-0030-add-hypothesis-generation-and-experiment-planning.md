---
id: TODO-0030
priority: P2
status: backlog
type: feature
title: "Add hypothesis generation and experiment planning"
dependencies:
  - TODO-0017
  - TODO-0019
  - TODO-0022
branch: null
pull_request: null
created: 2026-10-29
updated: 2026-10-29
---

# Add hypothesis generation and experiment planning

## Outcome

The deliberative layer can express testable hypotheses and choose evidence-producing experiments.

## Scope

Deliver the smallest coherent implementation that achieves the stated outcome and integrates with the existing architecture. Work outside this outcome is excluded unless required by a listed dependency or acceptance criterion.

## Acceptance criteria

- [ ] Hypotheses identify claims, expected observations, and falsifying outcomes.
- [ ] Plans use available affordances and pass current-world validation.
- [ ] Outcomes update the associated hypothesis and belief evidence.

## Definition of done

- [ ] All acceptance criteria are satisfied and supported by automated or repeatable verification.
- [ ] Relevant schemas, telemetry, documentation, ADRs, and adjacent backlog records are updated.
- [ ] Failure modes are observable and no known regression invalidates experiment results.
- [ ] The demonstration plan has been executed and its evidence is linked from the pull request.

## Demonstration plan

1. Prepare the smallest reproducible scenario and configuration needed for the demonstration.
2. Present an unknown object, inspect the generated hypothesis and experiment, execute it, and show the resulting revision.
3. Capture the relevant UI, event, trace, report, or command output and link it from the pull request.

## Status history

- 2026-10-29 — `backlog`: Item materialized from the prioritized roadmap.

## Notes

Record blockers, scope changes, implementation decisions, and review context here.

