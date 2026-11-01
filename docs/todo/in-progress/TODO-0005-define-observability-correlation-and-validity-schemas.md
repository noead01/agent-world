---
id: TODO-0005
priority: null
status: in-progress
type: feature
dependencies:
  - TODO-0004
branch: feature/todo-0005-observability-schemas
pull_request: "7"
created: 2026-10-29
updated: 2026-11-01
---

# Define observability correlation and validity schemas

## Outcome

Run validity, simulation ticks, world revisions, trace context, component versions, content-capture mode, and configuration fingerprints share one validated schema.

## Scope

Deliver the smallest coherent implementation that achieves the stated outcome and integrates with the existing architecture. Work outside this outcome is excluded unless required by a listed dependency or acceptance criterion.

## Acceptance criteria

- [x] Correlation fields are consistent across world, agent, event, and telemetry messages.
- [x] Run-validity transitions are represented and validated.
- [x] Configuration fingerprints are stable for identical effective configurations.

## Definition of done

- [x] All acceptance criteria are satisfied and supported by automated or repeatable verification.
- [x] Relevant schemas, telemetry, documentation, ADRs, and adjacent backlog records are updated.
- [x] Failure modes are observable and no known regression invalidates experiment results.
- [x] The demonstration plan has been executed and its evidence is linked from the pull request.

## Demonstration plan

1. Prepare the smallest reproducible scenario and configuration needed for the demonstration.
2. Run a schema example across two simulated components and show joined correlation plus a deliberate invalid-run transition.
3. Capture the relevant UI, event, trace, report, or command output and link it from the pull request.

## Status history

- 2026-10-29 — `backlog`: Item materialized from the prioritized roadmap.
- 2026-11-01 — `in-progress`: Four schemas defined in packages/contracts/schemas/ (correlation-context, run-validity, configuration-fingerprint, observability-envelope); 9 unit tests added in packages/contracts/tests/unit/test_observability_schemas.py; demonstration script added at tools/repository/demo_observability_schemas.py.
- 2026-11-01 — `in-progress`: Addressed Codex review findings on PR #7: bound envelope run_id to correlation/validity run_ids; added terminal-state transition constraints (invalid/aborted cannot return to valid); specified canonical SHA-256 fingerprint computation with actual verification test; added content_capture_mode (off/redacted/full) to envelope; fixed component pattern to accept documented subsystem:version syntax (e.g. 'world:1.0.0').

## Notes

All three acceptance criteria verified via tools/repository/demo_observability_schemas.py:
  - Correlation fields consistent across world/agent/telemetry components
  - Run-validity transitions (valid → degraded → invalid) validated; invalid values rejected
  - Configuration fingerprints stable for identical configs, different for different configs
  - Observability envelope combines all three subschemas
