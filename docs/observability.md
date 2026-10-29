# Telemetry, Observability, and Behavioral Review

This document defines how maintainers observe Agent World as a running software system and as an experimental environment. It covers the Godot/Jolt world runtime, deterministic agent layers, the external agent service, LLM interactions, memory and beliefs, discovery evaluation, and cross-process behavior.

The approach has four goals:

1. Explain what happened during a run.
2. Locate failures in physics, deterministic behavior, cognition, communication, or evaluation.
3. Compare behavior and performance across configurations without changing experimental semantics.
4. Detect software regressions and invalid experiment results early.

## Three records with different purposes

Do not treat telemetry, experiment events, and review artifacts as interchangeable.

### Experiment event record

The append-only event record is the authoritative semantic history of a run. It contains versioned domain events such as observations delivered, intentions proposed, actions accepted, collisions relevant to behavior, belief changes, and discovery stages awarded.

It supports behavioral reconstruction, metric reevaluation, and semantic replay. Events that affect the meaning or outcome of an experiment belong here even when telemetry is disabled.

### Operational telemetry

Telemetry consists of traces, metrics, and structured logs. It explains software execution and resource use: latency, queueing, errors, physics-step overruns, model requests, retries, connection health, and similar concerns.

Telemetry may be sampled, aggregated, or expired. It must not be the only record of an experiment outcome.

### Review artifacts

Review artifacts are larger, selectively captured materials such as world snapshots, screenshots, short video segments, perception frames, prompt/response envelopes, profiler captures, and crash dumps.

Artifacts provide detail that is too large or sensitive for ordinary telemetry. They are linked by identifiers and timestamps and retained according to an explicit capture policy.

## Common correlation model

Every signal must carry enough context to join it to the relevant run. Use these fields consistently:

| Field | Meaning |
|---|---|
| `experiment.id` | Logical experiment definition |
| `scenario.id` and `scenario.version` | World and hidden-fact definition |
| `run.id` | One execution of an experiment |
| `agent.id` | Agent whose state or action is involved |
| `world.revision` | Monotonic revision of authoritative world state |
| `simulation.tick` | Fixed physics-step number |
| `simulation.time` | Monotonic simulated time |
| `event.id` | Domain event identifier, when applicable |
| `trace_id` and `span_id` | Distributed-trace correlation |
| `component` | Emitting subsystem and version |

Object, fact, belief, intention, action, memory, and model-call identifiers should be included when relevant. Do not use these high-cardinality identifiers as metric labels unless a diagnostic mode explicitly requires it.

### Time domains

Record time explicitly in the domain where it has meaning:

- **Simulation time** orders world behavior and pauses with the world.
- **Physics tick** identifies the exact fixed update.
- **Monotonic process time** measures durations without wall-clock adjustments.
- **Wall-clock UTC** correlates processes and external services.

Never calculate model latency or process performance from simulation time. Never infer behavioral ordering from wall-clock timestamps when simulation ticks or event sequence numbers are available.

## OpenTelemetry as the instrumentation boundary

Use OpenTelemetry APIs and protocols for traces, operational metrics, and structured log correlation. Instrument application code against the vendor-neutral API rather than a specific storage or dashboard product.

The initial development configuration should work locally with console/file exporters. A collector and visualization backend can be added without changing instrumentation. Domain event schemas remain project-owned and are not replaced by OpenTelemetry semantic conventions.

Telemetry initialization must fail open during ordinary experiments: exporter failure may produce a health warning but must not stop physics, block agent behavior, or alter simulation timing.

## Distributed traces

A trace follows a causally related operation across Godot, the agent service, an LLM provider, memory, and evaluation. It is not expected to remain open for an entire experiment.

### Trace roots

Create bounded traces for operations such as:

- Perception cycle and observation assembly
- Deliberation request through intention acceptance or rejection
- Action execution from controller start to outcome
- Memory retrieval, consolidation, or belief revision
- Discovery-stage evaluation
- Scenario load, run start, pause, reset, checkpoint, and shutdown

Propagate trace context across the Godot/agent-service protocol. Link asynchronous work to the initiating span when parent-child timing would be misleading. Link resulting domain events through `event.id`.

### Suggested spans

Use stable names and place variable data in attributes:

```text
world.perception.collect
world.observation.publish
agent.attention.select
agent.drive.update
agent.deliberation.request
llm.inference
agent.intention.validate
agent.arbitration.select
world.action.execute
world.physics.contact
agent.memory.retrieve
agent.memory.write
agent.belief.revise
evaluation.discovery.assess
run.checkpoint.write
```

Do not create a span for every physics body on every tick. Trace physics details only for anomalous ticks, sampled diagnostic windows, or behaviorally significant interactions.

### LLM spans

Record:

- Provider and model identifier
- Model and adapter version
- Request purpose, such as deliberation or reflection
- Prompt-template and schema versions
- Input and output token counts when available
- Queue, network, and total latency
- Attempt number, retry reason, timeout, and cancellation
- Structured-output validation result
- World revision at request and response
- Whether the result was accepted, rejected, or stale
- Estimated or reported cost where available

Prompt and response bodies are artifacts, not default span attributes. Capture them only under the content policy below.

## Operational metrics

Metric names use the `agent_world` namespace. Counters end in `_total`; durations and sizes include their unit. Histograms are preferred for latency and step-time distributions.

### Runtime and physics

- `agent_world_simulation_tick_total`
- `agent_world_simulation_tick_duration_seconds`
- `agent_world_simulation_tick_overrun_total`
- `agent_world_simulation_time_scale`
- `agent_world_simulation_paused`
- `agent_world_physics_active_body_count`
- `agent_world_physics_contact_count`
- `agent_world_physics_sleeping_body_count`
- `agent_world_physics_constraint_error`
- `agent_world_physics_tunneling_suspect_total`
- `agent_world_world_revision`
- `agent_world_render_frame_duration_seconds`
- `agent_world_process_cpu_ratio`
- `agent_world_process_memory_bytes`

Record physics configuration, Godot version, Jolt version, fixed timestep, solver settings, and platform in run metadata rather than repeating them as high-cardinality labels.

### Deterministic agent layers

- `agent_world_drive_value` labeled by bounded `drive.type`
- `agent_world_reflex_activation_total` labeled by `reflex.type`
- `agent_world_attention_candidate_count`
- `agent_world_attention_selection_total` labeled by bounded selection reason
- `agent_world_intention_total` labeled by status and bounded action type
- `agent_world_intention_duration_seconds`
- `agent_world_action_total` labeled by action type and outcome
- `agent_world_action_duration_seconds`
- `agent_world_arbitration_total` labeled by winner layer and reason category
- `agent_world_plan_interruption_total` labeled by interruption category
- `agent_world_controller_error_total` labeled by controller and error category

Drive values and attention scores should also be captured as domain events when they materially explain a decision. Metrics alone cannot reconstruct causality.

### Agent service and protocol

- `agent_world_protocol_message_total` labeled by message type, direction, and outcome
- `agent_world_protocol_message_size_bytes`
- `agent_world_protocol_round_trip_seconds`
- `agent_world_protocol_decode_error_total`
- `agent_world_protocol_version_mismatch_total`
- `agent_world_agent_service_connected`
- `agent_world_agent_service_reconnect_total`
- `agent_world_deliberation_inflight`
- `agent_world_deliberation_queue_depth`
- `agent_world_stale_response_total`

### LLM interactions

- `agent_world_llm_request_total` labeled by provider, model family, purpose, and outcome
- `agent_world_llm_latency_seconds`
- `agent_world_llm_time_to_first_token_seconds` when available
- `agent_world_llm_input_tokens_total`
- `agent_world_llm_output_tokens_total`
- `agent_world_llm_cost_total` with currency kept in run metadata
- `agent_world_llm_retry_total` labeled by bounded reason
- `agent_world_llm_timeout_total`
- `agent_world_llm_schema_validation_failure_total`
- `agent_world_llm_intention_rejection_total` labeled by rejection category

Do not label metrics with full prompt hashes, run IDs, request IDs, object IDs, or arbitrary error messages. Those belong in traces or logs.

### Memory, beliefs, and discovery

- `agent_world_memory_entry_count` labeled by memory type
- `agent_world_memory_write_total` labeled by type and outcome
- `agent_world_memory_retrieval_seconds`
- `agent_world_memory_retrieval_result_count`
- `agent_world_belief_count` labeled by status
- `agent_world_belief_revision_total` labeled by revision category
- `agent_world_discovery_stage_total` labeled by stage
- `agent_world_discovery_evaluation_seconds`
- `agent_world_discovery_false_positive_total`
- `agent_world_discovery_false_negative_total` when independently established

Discovery scores, coverage, retention, transfer, and evidence quality are experiment-result metrics. Store their full values and derivations in the run report. Operational aggregation may expose summaries, but it is not their source of truth.

### Event recording and storage

- `agent_world_event_append_total` labeled by event family and outcome
- `agent_world_event_append_latency_seconds`
- `agent_world_event_buffer_depth`
- `agent_world_event_sequence_gap_total`
- `agent_world_artifact_write_total` labeled by artifact type and outcome
- `agent_world_artifact_size_bytes`
- `agent_world_checkpoint_duration_seconds`
- `agent_world_checkpoint_size_bytes`

Failure to persist a required domain event invalidates the run and must be visible in run status. Failure to export optional telemetry does not invalidate the run.

## Structured logs

Logs are for discrete software diagnostics that do not warrant their own domain event. Emit JSON records with severity, component, message template, relevant correlation fields, and a stable `error.type` or `reason.code`.

Good log messages state what failed, where, and the immediate consequence. Avoid prose-only errors that cannot be grouped. Include exception type and stack trace for unexpected failures, but keep stack traces out of metric labels and ordinary info messages.

Recommended severity semantics:

- `DEBUG`: diagnostic detail disabled in normal runs
- `INFO`: lifecycle transitions and concise operator-relevant state
- `WARN`: degraded behavior with a defined fallback
- `ERROR`: operation failed or run validity may be affected
- `FATAL`: process or experiment cannot continue coherently

Rate-limit repetitive logs such as recurring collisions, rejected paths, or provider retry messages. A suppressed-message counter should show how much was omitted.

## Behavioral events

The following belong in the authoritative event stream when they occur:

- Observation delivered to attention or deliberation
- Drive threshold crossing that can affect behavior
- Attention selection used to construct conscious context
- Goal, hypothesis, intention, or plan created or abandoned
- Arbitration decision and interruption
- Action requested, accepted, started, completed, failed, or cancelled
- Behaviorally meaningful contact or object-state change
- LLM structured response and its acceptance outcome
- Memory addition, consolidation, deletion, or retrieval used in a decision
- Belief creation, revision, contradiction, or retirement
- Discovery stage awarded or revoked, including evidence references
- Operator intervention, pause, reset, or configuration change
- Recording degradation or run invalidation

High-frequency raw physics contacts that have no behavioral significance remain telemetry unless diagnostic capture is active.

## Determinism and physics diagnostics

Each reproducible run should record periodic checksums over a canonical subset of authoritative state. The subset includes stable body identifiers, transforms, velocities, relevant object state, simulation tick, and deterministic agent-layer state. Quantize or encode floating-point values consistently before hashing.

Use these checksums to:

- Detect divergence between repeated mock-brain runs
- Identify the first tick where replay diverges
- Separate physics nondeterminism from cognition differences
- Confirm that telemetry instrumentation does not alter behavior

On divergence, capture a bounded diagnostic window around the first mismatched tick: preceding checkpoint, relevant domain events, body states, contacts, actions, and deterministic-layer state. Do not enable full per-tick state capture by default.

Monitor physical invariants appropriate to the scenario, including non-finite values, excessive velocities, unexpected penetration, out-of-bounds bodies, impossible energy growth, stuck controllers, and bodies that never settle. An invariant violation must emit a domain event when it can affect experiment validity.

## Health and run validity

Expose component health separately from experiment validity.

### Component health

At minimum, report:

- Godot runtime ready and physics advancing
- Agent service connected and protocol-compatible
- Event recorder writable
- Artifact store writable when capture is required
- LLM provider reachable when the run requires it
- Evaluator loaded with the expected scenario and schema version
- Telemetry exporter status

### Run validity

A run is one of:

- `valid`: required records and invariants are intact
- `degraded`: experiment continued with a documented fallback that does not invalidate its stated analysis
- `invalid`: missing required evidence, recorder failure, incompatible configuration, invariant violation, or other condition prevents trustworthy interpretation
- `aborted`: intentionally or fatally stopped before completion

Validity transitions are domain events and appear prominently in run reports. Telemetry-export failure alone results in degraded observability, not an invalid experiment, provided the authoritative record remains intact.

## Content, privacy, and sensitive data

Default telemetry must not include secrets, provider credentials, complete prompts, complete model responses, private reasoning traces, or arbitrary memory contents.

Content capture is an explicit run-level mode with these controls:

- `off`: metadata and structured decisions only
- `redacted`: prompt/response artifacts after configured redaction
- `full`: complete permitted content for a controlled local experiment

Record the selected mode in run metadata. Artifacts should have content type, checksum, size, creation time, redaction status, and retention class. Access to content artifacts should be narrower than access to aggregate metrics.

Store structured intentions, concise model-provided justifications, tool requests, and validation errors. Do not design the system to request or retain hidden chain-of-thought.

## Sampling, retention, and overhead

Authoritative domain events are never probabilistically sampled. Operational traces may be sampled based on operation type, latency, error, or diagnostic mode. Always retain traces associated with errors, run invalidation, schema failures, stale decisions, and physics divergence when possible.

Use three observability profiles:

| Profile | Intended use | Behavior |
|---|---|---|
| `minimal` | Batch experiments | Required events, health, coarse metrics, errors |
| `standard` | Normal development | Metrics, sampled traces, structured logs, periodic checksums |
| `diagnostic` | Focused troubleshooting | Unsampled relevant traces, bounded state windows, optional content artifacts |

Set an overhead budget before performance comparisons. Measure instrumentation cost with telemetry enabled and disabled. Telemetry configuration and sampling policy are part of run metadata.

## Maintainer views

The initial observability experience should provide these views:

### Run overview

Run validity, configuration fingerprint, simulation progress, real-time factor, physics overruns, agent state, pending deliberations, model cost, discovered facts, and active warnings.

### Physics and runtime

Tick-duration percentiles, overruns, body and contact counts, constraint errors, invariant violations, rendering performance, and resource usage.

### Agent behavior

Drive timelines, attention selections, goals and intentions, arbitration outcomes, action durations, interruptions, failures, and responsible control layer.

### LLM and service

Request rate, latency distribution, tokens, cost, retries, timeouts, validation failures, stale responses, and intention acceptance rate.

### Discovery and belief

Fact-stage progression, belief confidence over time, evidence graph, contradictions, revisions, missed-fact reasons, and discovery efficiency.

### Timeline review

A synchronized timeline joining domain events, traces, logs, world snapshots, agent internal state, and discovery awards by simulation tick. Maintainers should be able to select an unexpected action and navigate backward to the observation, drive state, memory retrieval, LLM decision, arbitration result, and physical outcome that produced it.

## Troubleshooting workflow

When reviewing surprising behavior:

1. Confirm run validity, versions, configuration fingerprint, and random seed.
2. Locate the first unexpected domain event rather than the final visible symptom.
3. Determine which layer owned the decision: reflex, controller, drive, attention, arbitration, LLM, memory, or evaluator.
4. Follow the correlated trace across process boundaries.
5. Compare the agent's observation and beliefs with authoritative world state without exposing hidden truth to the running agent.
6. Inspect action validation and the physical outcome.
7. Compare against a repeated run or checkpoint replay and locate checksum divergence.
8. Enter diagnostic mode only for a bounded reproduction if existing evidence is insufficient.
9. Record whether the cause is implementation, configuration, nondeterminism, model variability, scenario ambiguity, or metric/evaluator error.

## Initial implementation sequence

1. Define the correlation fields and run-validity state machine in the core schemas.
2. Implement the append-only event recorder before optional telemetry exporters.
3. Add OpenTelemetry initialization to Godot and the agent service with local exporters.
4. Trace the observation-to-intention-to-action path end to end.
5. Add runtime, physics, protocol, and LLM metrics with bounded labels.
6. Add structured logs and health endpoints or status messages.
7. Add deterministic-state checksums and bounded divergence capture.
8. Build the run overview and synchronized behavioral timeline.
9. Add retention, redaction, artifact capture, and diagnostic profiles.
10. Establish overhead budgets and regression checks.
