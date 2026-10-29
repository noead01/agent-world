---
id: TODO-0009
priority: P0
status: backlog
type: feature
title: "Create the agent-service boundary"
dependencies:
  - TODO-0004
  - TODO-0005
branch: null
pull_request: null
created: 2026-10-29
updated: 2026-10-29
---

# Create the agent-service boundary

## Outcome

Godot and the external agent service exchange versioned asynchronous observations and intentions with lifecycle and stale-response handling.

## Scope

Deliver the smallest coherent implementation that achieves the stated outcome and integrates with the existing architecture. Work outside this outcome is excluded unless required by a listed dependency or acceptance criterion.

## Acceptance criteria

- [ ] Connection, reconnection, timeout, cancellation, and protocol mismatch states are defined.
- [ ] Messages carry run, agent, tick, world revision, and trace correlation.
- [ ] A response based on an obsolete world revision is rejected without blocking physics.

## Definition of done

- [ ] All acceptance criteria are satisfied and supported by automated or repeatable verification.
- [ ] Relevant schemas, telemetry, documentation, ADRs, and adjacent backlog records are updated.
- [ ] Failure modes are observable and no known regression invalidates experiment results.
- [ ] The demonstration plan has been executed and its evidence is linked from the pull request.

## Demonstration plan

1. Prepare the smallest reproducible scenario and configuration needed for the demonstration.
2. Delay a mock service response while the world changes and show that the stale intention is rejected while simulation continues.
3. Capture the relevant UI, event, trace, report, or command output and link it from the pull request.

## Status history

- 2026-10-29 — `backlog`: Item materialized from the prioritized roadmap.

## Notes

Record blockers, scope changes, implementation decisions, and review context here.

