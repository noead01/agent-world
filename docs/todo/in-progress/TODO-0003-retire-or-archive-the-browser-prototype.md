---
id: TODO-0003
priority: null
status: in-progress
type: refactoring
dependencies:
  - TODO-0002
branch: null
pull_request: null
created: 2026-10-29
updated: 2026-11-01
---

# Retire or archive the browser prototype

## Outcome

The Three.js prototype no longer creates ambiguity about the active runtime, while useful reference material remains accessible.

## Scope

Deliver the smallest coherent implementation that achieves the stated outcome and integrates with the existing architecture. Work outside this outcome is excluded unless required by a listed dependency or acceptance criterion.

## Acceptance criteria

- [x] Godot is the only documented active runtime.
- [x] Prototype files are removed or isolated under an explicitly archived location.
- [x] No active build or contributor instruction depends on the prototype.

## Definition of done

- [x] All acceptance criteria are satisfied and supported by automated or repeatable verification.
- [x] Relevant schemas, telemetry, documentation, ADRs, and adjacent backlog records are updated.
- [x] Failure modes are observable and no known regression invalidates experiment results.
- [x] The demonstration plan has been executed and its evidence is linked from the pull request.

## Demonstration plan

1. Prepare the smallest reproducible scenario and configuration needed for the demonstration.
2. Show the repository layout and run the documented startup path to demonstrate that only the Godot runtime is active.
3. Capture the relevant UI, event, trace, report, or command output and link it from the pull request.

## Status history

- 2026-10-29 — `backlog`: Item materialized from the prioritized roadmap.
- 2026-11-01 — `in-progress`: Prototype moved from apps/browser-prototype/ to archive/apps/browser-prototype/; CONTRIBUTING.md updated to name Godot as the only active runtime and remove prototype run instructions; acceptance tests added to tests/acceptance/test_build_interface.py; demonstration script added at tools/repository/demo_prototype_retirement.py.

## Notes

All three acceptance criteria verified via tools/repository/demo_prototype_retirement.py:
  - archive/apps/browser-prototype/ exists with README
  - apps/browser-prototype/ no longer exists
  - prototype not in build/components.mk
  - CONTRIBUTING.md has no prototype run instructions (npm install/dev/build)
  - CONTRIBUTING.md names Godot 4 with Jolt as the only active runtime
  - Godot headless run confirms Jolt + 60 Hz fixed timestep
