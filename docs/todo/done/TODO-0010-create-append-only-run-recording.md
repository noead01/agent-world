---
id: TODO-0010
priority: null
status: done
type: feature
title: "Create append-only run recording"
dependencies:
  - TODO-0004
  - TODO-0005
branch: feature/todo-0010-append-only-run-recording
pull_request: "10"
created: 2026-10-29
updated: 2026-11-15
---

# Create append-only run recording

## Outcome

Each run persists initial conditions, configurations, seeds, versions, typed events, validity transitions, and final state in sequence.

## Scope

Deliver the smallest coherent implementation that achieves the stated outcome and integrates with the existing architecture. Work outside this outcome is excluded unless required by a listed dependency or acceptance criterion.

## Acceptance criteria

- [x] Required events are append-only, ordered, and schema validated.
- [x] A recorder failure marks the run invalid and is visible to the operator.
- [x] A completed run can be read back without relying on application logs.

## Definition of done

- [x] All acceptance criteria are satisfied and supported by automated or repeatable verification.
- [x] Relevant schemas, telemetry, documentation, ADRs, and adjacent backlog records are updated.
- [x] Failure modes are observable and no known regression invalidates experiment results.
- [x] The demonstration plan has been executed and its evidence is linked from the pull request.

## Demonstration plan

1. Prepare the smallest reproducible scenario and configuration needed for the demonstration.
2. Execute a short run, inspect its ordered record, replay the semantic timeline, and simulate a recorder failure.
3. Capture the relevant UI, event, trace, report, or command output and link it from the pull request.

**Evidence:** [Link to PR with test output showing valid run record and invalid run on recorder failure]

## Status history

- 2026-10-29 — `backlog`: Item materialized from the prioritized roadmap.
- 2026-11-10 — `done`: Implementation complete, all acceptance criteria verified.
- 2026-11-12 — `in-progress`: Reopened to address PR #10 review findings.
- 2026-11-12 — `done`: Review findings fixed and unit verification passed.
- 2026-11-12 — `in-progress`: Reopened to address follow-up PR #10 review findings.
- 2026-11-13 — `done`: Follow-up review findings fixed and unit and acceptance verification passed.
- 2026-11-14 — `in-progress`: Reopened to address new PR #10 review findings.
- 2026-11-14 — `done`: Impulse recording, handshake validation, and configuration fingerprint fixes verified.
- 2026-11-14 — `in-progress`: Reopened to address three further PR #10 review findings about simulation-driven agent timers and reconnect cancellation.
- 2026-11-14 — `in-progress`: Reopened for seven further PR #10 review findings; resynchronized the file location, status metadata, and backlog index link.
- 2026-11-15 — `in-progress`: All twelve PR #10 review findings implemented with regression tests; unit, acceptance, and repository validation pass.
- 2026-11-15 — `done`: PR #10 merged to main; item complete.

## Notes

Record blockers, scope changes, implementation decisions, and review context here.

- Review lesson: world revisions can advance while simulation is paused, so deterministic behavior timers must use simulation ticks and ignore repeated ticks. Keep cooldowns and seeded delays in ticks instead of converting service-loop deltas or assuming a wall-clock rate.
- Review lesson: transport shutdown is terminal even when reconnect backoff is already waiting. Check the shutdown state again after every asynchronous wait, before accessing a peer or reconnecting.
- Review lesson: pause, resume, time-scale, and reset change physics and agent timing. Append a domain event for each transition that actually executes; the planned demo schedule and console logs are not an authoritative record.
- Review lesson: an entry's directory, `status` front matter, and `docs/todo/README.md` link must move together. A reopened item belongs in `in-progress/` with `status: in-progress`.
- Review lesson: protocol session filtering must compare every identity field the message carries, including the top-level `run_id`, not just the correlation `run_id` and top-level `agent_id`.
- Review lesson: a schema is the contract for its loader too. Do not index a field in `load()` that the schema marks optional; require it in the schema or return a diagnostic instead of raising `KeyError` or a type error.
- Review lesson: dependency lower bounds must match the API actually imported. This service imports `websockets.asyncio.server`, which requires websockets 13 or newer, so `>=12.0` is not a supported floor.
- Review lesson: a recorder must enforce the same invariants as readback validation before writing. Reject duplicate event IDs at append and invalidate the run rather than persisting a stream that `RunRecord` will reject.
- Review lesson: a configuration fingerprint must include every behavior-affecting input across processes, including the agent service's target order, action cooldown, and seeded-delay policy; world-side settings alone cannot distinguish runs that differ in agent behavior.
- Review lesson: a scheduled control transition must be gated on one-shot state, not only elapsed time. Returning to the same phase after a transition re-fires the first matching branch forever, so the later transitions never execute.
- Review lesson: event-stream lifecycle boundaries (first event must be run_started, exactly one run_started, no events after run_ended, completed runs require run_ended) must be enforced at append time so the persisted stream is never structurally invalid.
- Review lesson: terminal action results (success/failure/partial) mutate session state and must be validated against the full session identity envelope — top-level run_id/agent_id and every correlation identity field — before they are allowed to clear pending requests.
- Review lesson: JSONL loaders must type-check each parsed line before semantic validation. Non-object entries (arrays, null, primitives) must be diagnosed during load so validation returns a diagnostic instead of raising AttributeError.
- Review lesson: protocol session isolation requires comparing every correlation identity field (experiment_id, scenario_id, scenario_version, agent_id, run_id) against the registered session, not just the correlation run_id. A foreign correlation with a matching run_id must still be rejected.
