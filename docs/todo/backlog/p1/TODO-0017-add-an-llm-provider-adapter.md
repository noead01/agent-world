---
id: TODO-0017
priority: P1
status: backlog
type: feature
title: "Add an LLM provider adapter"
dependencies:
  - TODO-0009
  - TODO-0011
  - TODO-0016
branch: null
pull_request: null
created: 2026-10-29
updated: 2026-10-29
---

# Add an LLM provider adapter

## Outcome

One server-side LLM adapter supports structured output, protected credentials, timeouts, retries, validation, and recorded model configuration.

## Scope

Deliver the smallest coherent implementation that achieves the stated outcome and integrates with the existing architecture. Work outside this outcome is excluded unless required by a listed dependency or acceptance criterion.

## Acceptance criteria

- [ ] Credentials never enter Godot, browser code, logs, or experiment events.
- [ ] Responses are schema validated and categorized as accepted, rejected, stale, timed out, or failed.
- [ ] Provider, model, template, token, latency, and cost metadata are recorded when available.

## Definition of done

- [ ] All acceptance criteria are satisfied and supported by automated or repeatable verification.
- [ ] Relevant schemas, telemetry, documentation, ADRs, and adjacent backlog records are updated.
- [ ] Failure modes are observable and no known regression invalidates experiment results.
- [ ] The demonstration plan has been executed and its evidence is linked from the pull request.

## Demonstration plan

1. Prepare the smallest reproducible scenario and configuration needed for the demonstration.
2. Run one valid deliberation, one schema-invalid response, and one timeout while showing physics remains responsive.
3. Capture the relevant UI, event, trace, report, or command output and link it from the pull request.

## Status history

- 2026-10-29 — `backlog`: Item materialized from the prioritized roadmap.

## Notes

Record blockers, scope changes, implementation decisions, and review context here.

