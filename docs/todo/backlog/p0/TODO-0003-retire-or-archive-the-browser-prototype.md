---
id: TODO-0003
priority: P0
status: backlog
type: refactoring
title: "Retire or archive the browser prototype"
dependencies:
  - TODO-0002
branch: null
pull_request: null
created: 2026-10-29
updated: 2026-10-29
---

# Retire or archive the browser prototype

## Outcome

The Three.js prototype no longer creates ambiguity about the active runtime, while useful reference material remains accessible.

## Scope

Deliver the smallest coherent implementation that achieves the stated outcome and integrates with the existing architecture. Work outside this outcome is excluded unless required by a listed dependency or acceptance criterion.

## Acceptance criteria

- [ ] Godot is the only documented active runtime.
- [ ] Prototype files are removed or isolated under an explicitly archived location.
- [ ] No active build or contributor instruction depends on the prototype.

## Definition of done

- [ ] All acceptance criteria are satisfied and supported by automated or repeatable verification.
- [ ] Relevant schemas, telemetry, documentation, ADRs, and adjacent backlog records are updated.
- [ ] Failure modes are observable and no known regression invalidates experiment results.
- [ ] The demonstration plan has been executed and its evidence is linked from the pull request.

## Demonstration plan

1. Prepare the smallest reproducible scenario and configuration needed for the demonstration.
2. Show the repository layout and run the documented startup path to demonstrate that only the Godot runtime is active.
3. Capture the relevant UI, event, trace, report, or command output and link it from the pull request.

## Status history

- 2026-10-29 — `backlog`: Item materialized from the prioritized roadmap.

## Notes

Record blockers, scope changes, implementation decisions, and review context here.

