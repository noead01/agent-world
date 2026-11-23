---
id: TODO-0013
priority: null
status: in-progress
type: feature
title: "Implement three initial drives"
dependencies:
  - TODO-0008
  - TODO-0012
branch: feature/todo-0013-implement-three-initial-drives
pull_request: null
created: 2026-10-29
updated: 2026-11-21
---

# Implement three initial drives

## Outcome

Curiosity, uncertainty, and physical integrity have explicit deterministic update rules and observable state.

## Scope

Deliver the smallest coherent implementation that achieves the stated outcome and integrates with the existing architecture. Work outside this outcome is excluded unless required by a listed dependency or acceptance criterion.

## Acceptance criteria

- [x] Each drive has documented range, inputs, update frequency, and thresholds.
- [x] Identical inputs and seeds produce identical drive histories.
- [x] Threshold crossings can influence arbitration and are recorded when behaviorally relevant.

## Definition of done

- [ ] All acceptance criteria are satisfied and supported by automated or repeatable verification.
- [ ] Relevant schemas, telemetry, documentation, ADRs, and adjacent backlog records are updated.
- [ ] Failure modes are observable and no known regression invalidates experiment results.
- [ ] The demonstration plan has been executed and its evidence is linked from the pull request.

## Demonstration plan

1. Prepare the smallest reproducible scenario and configuration needed for the demonstration.
2. Use controlled stimuli to raise and lower each drive and display the resulting timeline and threshold effects.
3. Capture the relevant UI, event, trace, report, or command output and link it from the pull request.

## Status history

- 2026-10-29 — `backlog`: Item materialized from the prioritized roadmap.
- 2026-11-21 — `in-progress`: Started implementation on branch `feature/todo-0013-implement-three-initial-drives`.
- 2026-11-21 — Core drive system implemented in `services/agent/src/mock_agent.py`:
  - Curiosity (0.0-1.0): novelty-seeking, +0.15 for new objects, -0.01/tick decay
  - Uncertainty (0.0-1.0): prediction error, +0.1 for >20cm error, -0.005/tick decay
  - Physical Integrity (0.0-1.0): safety, -0.005/tick near hazards, +0.002/tick recovery
  - Update frequency: per simulation tick (60Hz)
  - Thresholds: Curiosity > 0.7 (explore), Uncertainty > 0.6 (investigate), Integrity < 0.3 (safety)
  - Arbitration priority: Integrity > Uncertainty > Curiosity
  - Drive history recorded for deterministic replay verification

## Notes

Record blockers, scope changes, implementation decisions, and review context here.

### Implementation decisions:
- Drives implemented in MockAgent (agent service) rather than Godot world - keeps cognition separate from physics
- WorldState provides agent_position (dict) and nearby_objects (list of dicts) for drive computation
- Deterministic updates using simulation tick, not wall time - ensures replay reproducibility
- Drive history bounded to last 1000 ticks to prevent memory growth
- Thresholds as class constants for easy tuning

### Codex Review Findings (2026-11-21) - All Addressed:
- **P1**: Drive fallback logic - agent now falls back to target sequence when no drive threshold crossed
- **P1**: Target slot restoration - fixed try/finally to restore at correct index after _issue_next_action advances cursor  
- **P1**: Prediction overwrite - compute uncertainty BEFORE updating _predicted_positions in curiosity loop
- **P1**: Drive delta scaling - scale by elapsed simulation ticks (delta_ticks) for correct threshold timing
- **P2**: HealthStatus protocol parser - added to schemas.py and protocol.py
- **P2**: Mock action double-execution - _on_mock_action_issued now observational only
- **P1**: Per-tick metrics spam - gated to emit once per second wall time instead of 60Hz
- **P1**: Demo duration - made configurable via AGENT_WORLD_DEMO_DURATION (default 10s for tests)

