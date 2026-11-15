# 0006: Use OpenTelemetry and separate telemetry from experiment events

- Status: Accepted
- Date: 2026-10-29

## Context

Maintainers need to troubleshoot a distributed realtime system spanning Godot/Jolt physics, deterministic agent layers, an external cognition service, LLM providers, memory, and discovery evaluation. They also need to reconstruct and compare experimental behavior.

Application logs alone cannot express causality across processes or support reliable aggregation. Conversely, sampled operational telemetry cannot serve as the authoritative record of an experiment.

## Decision

Use OpenTelemetry APIs and protocols for operational traces, metrics, and structured log correlation. Keep the project independent of a specific telemetry storage or visualization product.

Maintain three distinct records:

1. An unsampled, append-only domain event stream is the authoritative semantic history of an experiment.
2. Operational telemetry diagnoses software execution, performance, reliability, and resource usage and may be sampled or aggregated.
3. Review artifacts contain selectively captured heavyweight material such as snapshots, perception frames, and redacted model envelopes.

Correlate all three using stable experiment, scenario, run, agent, event, world-revision, simulation-tick, and trace identifiers. Exporter failure must not block simulation or alter experimental behavior. Failure to persist a required domain event invalidates the run.

## Alternatives considered

- Use application logs as the only diagnostic record.
- Encode all diagnostics as experiment events.
- Use OpenTelemetry traces as the experiment history.
- Couple instrumentation directly to one observability backend.
- Capture every physics update and LLM payload by default.

## Consequences

- Maintainers can follow causality across world, agent, model, memory, and evaluation components.
- Experiment meaning is preserved independently from telemetry retention and sampling.
- Instrumentation can begin with local exporters and adopt another backend later.
- Domain events and telemetry require separate schemas, storage policies, and failure semantics.
- Correlation fields, cardinality controls, content redaction, and overhead budgets become part of the platform design.
- Behavioral review requires tooling that joins signals by simulation time and stable identifiers.

The detailed signal catalog and operating approach are defined in [`docs/observability.md`](../observability.md).

## Lessons Learned (TODO-0011 Implementation)

### 1. Reconstruct parent SpanContext from correlation for trace propagation
When a service receives a message with `trace_id`/`span_id` in its correlation envelope, those must be reconstructed into a proper OpenTelemetry `SpanContext` and passed via the `context` argument when starting spans. Merely recording them as span attributes creates disconnected traces—the tracer generates new trace IDs instead of continuing the parent trace.

**Fix:** `tracing.span_context_from_correlation()` builds a remote `SpanContext` from correlation; `mock_agent.run_tick()` passes it to `start_as_current_span(context=...)`.

### 2. Start publish span before sending; use its trace context in the outgoing message
If the correlation is created *before* starting the span, the message carries a random span ID that doesn't match the logged span. The receiver cannot link its child span to the logged publish span.

**Fix:** In `protocol_handler.gd`, `send_observation`, `send_action`, `send_intention` now start the span first, then copy `span.trace_id`/`span.span_id` into the outbound correlation.

### 3. Keep execution spans open through async action completion
World-side action execution spans must span the full action lifecycle (start → physical outcome). The world schedules an action via `execute_action()` but completion arrives on a later physics tick via `_on_agent_action_completed/failed/interrupted`. Ending the span immediately after scheduling loses result, duration, and the link to the physical outcome.

**Fix:** `room.gd` stores spans by `command_id` in `_active_action_spans` and ends them in the three lifecycle handlers.

### 4. Instrument the actual message path used by the running demo
A repo-wide search showed no caller of `send_observation`; the demo delivers perception through `tick_world_state` → `_send_world_state`. The new `world.observation.publish` span was therefore dead code in the demo, and `world.perception.collect` was only declared.

**Fix:** Added `world.perception.collect` and `world.observation.publish` spans directly in `_send_world_state`, which is the actual path the demo uses.

### 5. Validate session identity before adopting incoming trace context
Any incoming message with a `correlation.trace_id` was immediately adopted into the session's trace state, even before message type or session identity was checked. A foreign-run action/result (or unknown message type) that `_validate_session_identity` subsequently rejects could poison the trace ID used by all later outbound messages.

**Fix:** `_adopt_trace_context()` is now called *only after* `_validate_session_identity` succeeds for each message type. It also validates the trace_id format (32 hex chars) before storing.
