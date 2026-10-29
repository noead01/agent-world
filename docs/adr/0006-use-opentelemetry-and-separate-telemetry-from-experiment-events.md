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
