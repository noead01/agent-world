---
id: TODO-0032
priority: P2
status: backlog
type: research/experimentation
title: "Add contradictory and deceptive evidence scenarios"
dependencies:
  - TODO-0019
  - TODO-0020
  - TODO-0022
branch: null
pull_request: null
created: 2026-10-29
updated: 2026-10-29
---

# Add contradictory and deceptive evidence scenarios

## Outcome

Controlled scenarios measure belief revision under noisy, contradictory, or misleading evidence.

## Scope

Deliver the smallest coherent implementation that achieves the stated outcome and integrates with the existing architecture. Work outside this outcome is excluded unless required by a listed dependency or acceptance criterion.

## Acceptance criteria

- [ ] Each evidence source and reliability profile is authored explicitly.
- [ ] Ground truth and deception mechanisms remain hidden from the agent.
- [ ] Reports distinguish justified revision, resistance, and false belief formation.

## Definition of done

- [ ] All acceptance criteria are satisfied and supported by automated or repeatable verification.
- [ ] Relevant schemas, telemetry, documentation, ADRs, and adjacent backlog records are updated.
- [ ] Failure modes are observable and no known regression invalidates experiment results.
- [ ] The demonstration plan has been executed and its evidence is linked from the pull request.

## Demonstration plan

1. Prepare the smallest reproducible scenario and configuration needed for the demonstration.
2. Run the same agent through consistent and deceptive variants and compare belief confidence and revision histories.
3. Capture the relevant UI, event, trace, report, or command output and link it from the pull request.

## Status history

- 2026-10-29 — `backlog`: Item materialized from the prioritized roadmap.

## Notes

Record blockers, scope changes, implementation decisions, and review context here.

