---
id: TODO-0036
priority: P2
status: backlog
type: feature
title: "Add model cost and latency comparison"
dependencies:
  - TODO-0017
  - TODO-0025
  - TODO-0035
branch: null
pull_request: null
created: 2026-10-29
updated: 2026-10-29
---

# Add model cost and latency comparison

## Outcome

Run comparison includes model tokens, estimated cost, latency, retries, and their relationship to behavioral outcomes.

## Scope

Deliver the smallest coherent implementation that achieves the stated outcome and integrates with the existing architecture. Work outside this outcome is excluded unless required by a listed dependency or acceptance criterion.

## Acceptance criteria

- [ ] Cost currency and pricing assumptions are recorded with their version or date.
- [ ] Latency separates queue, provider, and total elapsed time when available.
- [ ] Reports can normalize discovery results by tokens, cost, and wall-clock time.

## Definition of done

- [ ] All acceptance criteria are satisfied and supported by automated or repeatable verification.
- [ ] Relevant schemas, telemetry, documentation, ADRs, and adjacent backlog records are updated.
- [ ] Failure modes are observable and no known regression invalidates experiment results.
- [ ] The demonstration plan has been executed and its evidence is linked from the pull request.

## Demonstration plan

1. Prepare the smallest reproducible scenario and configuration needed for the demonstration.
2. Compare two model configurations and display discovery quality alongside tokens, cost, and latency distributions.
3. Capture the relevant UI, event, trace, report, or command output and link it from the pull request.

## Status history

- 2026-10-29 — `backlog`: Item materialized from the prioritized roadmap.

## Notes

Record blockers, scope changes, implementation decisions, and review context here.

