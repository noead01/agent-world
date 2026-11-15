---
id: TODO-0048
priority: P2
status: backlog
type: feature
title: "Add health endpoints and instrumentation overhead budget"
dependencies:
  - TODO-0011
branch: null
pull_request: null
created: 2026-11-15
updated: 2026-11-15
---

# Add health endpoints and instrumentation overhead budget

## Outcome

Maintainers can observe component health (Godot runtime, agent service, recorder, LLM provider, telemetry exporter) separately from experiment validity, and measure instrumentation overhead to enforce a performance budget.

## Scope

Deliver the smallest coherent implementation that achieves the stated outcome and integrates with the existing architecture. Work outside this outcome is excluded unless required by a listed dependency or acceptance criterion.

This item adds:
- Health check endpoints/status messages for each component
- Overhead measurement comparing telemetry-enabled vs disabled runs
- Configuration for minimal/standard/diagnostic observability profiles

It does not include alerting, dashboarding, or run-validity state machine changes (those are in TODO-0012).

## Acceptance criteria

- [ ] Agent service exposes `/health` HTTP endpoint returning JSON with component health:
  - `agent_service`: connected, protocol version, active sessions
  - `telemetry_exporter`: status (healthy/degraded/failed), last export timestamp
  - `llm_provider`: reachable, last request latency
- [ ] Godot world runtime publishes health status via protocol (e.g., `WorldState` extension or dedicated message) with:
  - `physics`: advancing, tick overrun count, active body count
  - `recorder`: writable, pending event count
  - `telemetry_exporter`: status
- [ ] Overhead benchmark script measures:
  - Simulation tick duration with telemetry disabled vs enabled (minimal profile)
  - Memory overhead of trace/metric collection
  - Target: <5% CPU overhead in minimal profile, <15% in standard profile
- [ ] Observability profile configuration (minimal/standard/diagnostic) controls:
  - Trace sampling rate (minimal: errors only; standard: 10%; diagnostic: 100%)
  - Metric export interval
  - Content capture mode (off/redacted/full)

## Definition of done

- [ ] All acceptance criteria are satisfied and supported by automated or repeatable verification.
- [ ] Relevant schemas, telemetry, documentation, ADRs, and adjacent backlog records are updated.
- [ ] Failure modes are observable and no known regression invalidates experiment results.
- [ ] The demonstration plan has been executed and its evidence is linked from the pull request.

## Demonstration plan

1. Start agent service and world runtime with telemetry enabled.
2. Query `/health` endpoint and verify all components report healthy.
3. Run overhead benchmark script; capture timing comparison output.
4. Switch observability profile via config; verify sampling behavior changes.

## Status history

- 2026-11-15 — `backlog`: Item materialized from TODO-0011 review findings; implements health/overhead requirements from docs/observability.md.

## Notes

- Per docs/observability.md: "Telemetry initialization must fail open during ordinary experiments: exporter failure may produce a health warning but must not stop physics, block agent behavior, or alter simulation timing."
- Health distinguishes component availability from experiment validity (valid/degraded/invalid/aborted).
- Overhead budget must be set before performance comparisons; measure with telemetry enabled/disabled.
- Three observability profiles defined in docs/observability.md: minimal, standard, diagnostic.
- See ADR 0006 for exporter failure semantics.