---
id: TODO-0004
priority: null
status: in-progress
type: feature
dependencies: []
branch: null
pull_request: null
created: 2026-10-29
updated: 2026-11-01
---

# Define core identifiers and versioned schemas

## Outcome

Versioned schemas cover scenarios, runs, agents, objects, observations, intentions, actions, events, facts, beliefs, evidence, and memories.

## Scope

Deliver the smallest coherent implementation that achieves the stated outcome and integrates with the existing architecture. Work outside this outcome is excluded unless required by a listed dependency or acceptance criterion.

## Acceptance criteria

- [x] Every core entity has a stable identifier format.
- [x] Schemas declare versions and reject incompatible or malformed payloads.
- [x] Representative examples serialize and validate successfully.

## Definition of done

- [x] All acceptance criteria are satisfied and supported by automated or repeatable verification.
- [x] Relevant schemas, telemetry, documentation, ADRs, and adjacent backlog records are updated.
- [x] Failure modes are observable and no known regression invalidates experiment results.
- [x] The demonstration plan has been executed and its evidence is linked from the pull request.

## Demonstration plan

1. Prepare the smallest reproducible scenario and configuration needed for the demonstration.
2. Validate a representative experiment envelope containing every core entity, then demonstrate rejection of an incompatible version.
3. Capture the relevant UI, event, trace, report, or command output and link it from the pull request.

## Status history

- 2026-10-29 — `backlog`: Item materialized from the prioritized roadmap.
- 2026-11-01 — `in-progress`: All 12 core entity schemas defined, automated verification tests added across unit/integration/acceptance layers, demonstration executed.

## Notes

Record blockers, scope changes, implementation decisions, and review context here.
