---
id: TODO-0041
priority: P3
status: backlog
type: research/experimentation
title: "Introduce multiple embodied agents"
dependencies:
  - TODO-0008
  - TODO-0018
  - TODO-0022
branch: null
pull_request: null
created: 2026-10-29
updated: 2026-10-29
---

# Introduce multiple embodied agents

## Outcome

The world supports multiple independent embodied agents and measures social discovery without shared hidden truth.

## Scope

Deliver the smallest coherent implementation that achieves the stated outcome and integrates with the existing architecture. Work outside this outcome is excluded unless required by a listed dependency or acceptance criterion.

## Acceptance criteria

- [ ] Each agent has isolated perception, memory, beliefs, drives, and deliberation context.
- [ ] Physical and communication interactions are authoritative events.
- [ ] Metrics attribute discoveries and information transfer to specific agents.

## Definition of done

- [ ] All acceptance criteria are satisfied and supported by automated or repeatable verification.
- [ ] Relevant schemas, telemetry, documentation, ADRs, and adjacent backlog records are updated.
- [ ] Failure modes are observable and no known regression invalidates experiment results.
- [ ] The demonstration plan has been executed and its evidence is linked from the pull request.

## Demonstration plan

1. Prepare the smallest reproducible scenario and configuration needed for the demonstration.
2. Release two differently configured agents, observe one communicate a discovery, and trace what the other independently verifies.
3. Capture the relevant UI, event, trace, report, or command output and link it from the pull request.

## Status history

- 2026-10-29 — `backlog`: Item materialized from the prioritized roadmap.

## Notes

Record blockers, scope changes, implementation decisions, and review context here.

