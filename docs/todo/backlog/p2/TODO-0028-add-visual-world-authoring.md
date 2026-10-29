---
id: TODO-0028
priority: P2
status: backlog
type: feature
title: "Add visual world authoring"
dependencies:
  - TODO-0019
branch: null
pull_request: null
created: 2026-10-29
updated: 2026-10-29
---

# Add visual world authoring

## Outcome

An operator can visually compose objects and discoverable facts and export a valid scenario manifest.

## Scope

Deliver the smallest coherent implementation that achieves the stated outcome and integrates with the existing architecture. Work outside this outcome is excluded unless required by a listed dependency or acceptance criterion.

## Acceptance criteria

- [ ] Authored objects expose stable IDs and supported physical properties.
- [ ] Fact and evidence references are validated before export.
- [ ] Round-tripping a manifest preserves its semantic content.

## Definition of done

- [ ] All acceptance criteria are satisfied and supported by automated or repeatable verification.
- [ ] Relevant schemas, telemetry, documentation, ADRs, and adjacent backlog records are updated.
- [ ] Failure modes are observable and no known regression invalidates experiment results.
- [ ] The demonstration plan has been executed and its evidence is linked from the pull request.

## Demonstration plan

1. Prepare the smallest reproducible scenario and configuration needed for the demonstration.
2. Build a small room visually, define one hidden fact, export it, reload it, and run its validation.
3. Capture the relevant UI, event, trace, report, or command output and link it from the pull request.

## Status history

- 2026-10-29 — `backlog`: Item materialized from the prioritized roadmap.

## Notes

Record blockers, scope changes, implementation decisions, and review context here.

