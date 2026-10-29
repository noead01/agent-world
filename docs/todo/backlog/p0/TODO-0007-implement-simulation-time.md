---
id: TODO-0007
priority: P0
status: backlog
type: feature
title: "Implement simulation time"
dependencies:
  - TODO-0002
  - TODO-0006
branch: null
pull_request: null
created: 2026-10-29
updated: 2026-10-29
---

# Implement simulation time

## Outcome

The runtime supports fixed-step simulation time, pause, resume, reset, time scaling, and an accelerated day/night cycle.

## Scope

Deliver the smallest coherent implementation that achieves the stated outcome and integrates with the existing architecture. Work outside this outcome is excluded unless required by a listed dependency or acceptance criterion.

## Acceptance criteria

- [ ] Simulation time advances only through fixed physics steps.
- [ ] Pause freezes simulation behavior without corrupting state; resume continues coherently.
- [ ] Reset and time scaling produce documented, observable lighting and clock behavior.

## Definition of done

- [ ] All acceptance criteria are satisfied and supported by automated or repeatable verification.
- [ ] Relevant schemas, telemetry, documentation, ADRs, and adjacent backlog records are updated.
- [ ] Failure modes are observable and no known regression invalidates experiment results.
- [ ] The demonstration plan has been executed and its evidence is linked from the pull request.

## Demonstration plan

1. Prepare the smallest reproducible scenario and configuration needed for the demonstration.
2. Run a day/night cycle at multiple speeds, pause mid-cycle, resume, and reset to the same initial time.
3. Capture the relevant UI, event, trace, report, or command output and link it from the pull request.

## Status history

- 2026-10-29 — `backlog`: Item materialized from the prioritized roadmap.

## Notes

Record blockers, scope changes, implementation decisions, and review context here.

