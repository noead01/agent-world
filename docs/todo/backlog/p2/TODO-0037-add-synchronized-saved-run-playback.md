---
id: TODO-0037
priority: P2
status: backlog
type: feature
title: "Add synchronized saved-run playback"
dependencies:
  - TODO-0010
  - TODO-0023
branch: null
pull_request: null
created: 2026-10-29
updated: 2026-10-29
---

# Add synchronized saved-run playback

## Outcome

Maintainers can replay recorded world state alongside agent state, telemetry, events, and discovery awards.

## Scope

Deliver the smallest coherent implementation that achieves the stated outcome and integrates with the existing architecture. Work outside this outcome is excluded unless required by a listed dependency or acceptance criterion.

## Acceptance criteria

- [ ] Playback clearly identifies reconstructed versus authoritative recorded data.
- [ ] Seeking by simulation tick keeps all displayed signals aligned.
- [ ] Missing artifacts or sampled traces degrade gracefully and visibly.

## Definition of done

- [ ] All acceptance criteria are satisfied and supported by automated or repeatable verification.
- [ ] Relevant schemas, telemetry, documentation, ADRs, and adjacent backlog records are updated.
- [ ] Failure modes are observable and no known regression invalidates experiment results.
- [ ] The demonstration plan has been executed and its evidence is linked from the pull request.

## Demonstration plan

1. Prepare the smallest reproducible scenario and configuration needed for the demonstration.
2. Open a saved benchmark run, seek to a discovery event, and inspect synchronized world, decision, and evidence state.
3. Capture the relevant UI, event, trace, report, or command output and link it from the pull request.

## Status history

- 2026-10-29 — `backlog`: Item materialized from the prioritized roadmap.

## Notes

Record blockers, scope changes, implementation decisions, and review context here.

