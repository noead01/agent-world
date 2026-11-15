---
id: TODO-0047
priority: P2
status: backlog
type: feature
title: "Add operational metrics for critical path operations"
dependencies:
  - TODO-0011
branch: null
pull_request: null
created: 2026-11-15
updated: 2026-11-15
---

# Add operational metrics for critical path operations

## Outcome

Maintainers can observe latency distributions, error rates, and throughput for the instrumented critical path (perception, deliberation, arbitration, action execution) through OpenTelemetry metrics with bounded cardinality.

## Scope

Deliver the smallest coherent implementation that achieves the stated outcome and integrates with the existing architecture. Work outside this outcome is excluded unless required by a listed dependency or acceptance criterion.

This item adds OpenTelemetry metrics (counters, histograms) for the span operations already introduced in TODO-0011. It does not include dashboard/visualization work or alerting configuration.

## Acceptance criteria

- [ ] `agent.deliberation.request` latency histogram recorded with bounded attributes (experiment.id, scenario.id, agent.id, component)
- [ ] `agent.intention.validate` duration histogram with result attribute (formed/rejected)
- [ ] `agent.arbitration.select` duration histogram with winner layer and reason category
- [ ] `world.action.execute` latency histogram with action type and result (success/failure/partial/pending)
- [ ] `world.observation.publish` / `world.perception.collect` latency histograms
- [ ] Error counters for each operation with bounded error category attributes
- [ ] Metrics exported via console exporter (fails open) with same OTel initialization as traces

## Definition of done

- [ ] All acceptance criteria are satisfied and supported by automated or repeatable verification.
- [ ] Relevant schemas, telemetry, documentation, ADRs, and adjacent backlog records are updated.
- [ ] Failure modes are observable and no known regression invalidates experiment results.
- [ ] The demonstration plan has been executed and its evidence is linked from the pull request.

## Demonstration plan

1. Run a short autonomous episode with the agent service and world runtime.
2. Observe console exporter output showing metric points for each critical path operation.
3. Verify metric attributes are bounded (no run_id, object_id, request_id as labels).
4. Inject a simulated error (e.g., stale revision rejection) and confirm error counter increments.

## Status history

- 2026-11-15 — `backlog`: Item materialized from TODO-0011 review findings; follows up on span instrumentation.

## Notes

- Metric names follow `agent_world_` namespace per docs/observability.md.
- Counters end in `_total`; durations in `_seconds` with unit suffix.
- Histograms preferred for latency/step-time distributions.
- Must use the same `init_tracing()` / `shutdown_tracing()` lifecycle as traces.
- Exporter failure must not block simulation or agent behavior (fail open).
- See docs/observability.md § Operational metrics for full metric catalog.