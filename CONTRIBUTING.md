# Contributing to Agent World

Agent World is currently an early architecture and exploration project. Contributions should preserve its experimental character: behavior must be inspectable, physical effects must remain under the simulator's authority, and experiment results must be reproducible enough to compare configurations.

## Documentation responsibilities

Keep the documentation types separate:

- `README.md` is strictly user-facing. It explains the project's purpose, user concepts, current availability, and how to use released functionality. Do not put build instructions, internal architecture, contributor workflow, or implementation plans there.
- `CONTRIBUTING.md` contains development setup, implementation guidance, conventions, and contributor workflow.
- `docs/adr/` records durable architecture decisions and their consequences.
- `docs/todo/` contains the prioritized engineering and research backlog.
- `docs/observability.md` defines telemetry, experiment-recording, and behavioral-review conventions.

Update documentation in the same change that makes it inaccurate. Do not use TODO comments or ADRs as substitutes for an issue description when a task needs implementation detail.

## Current repository state

The repository contains an early Three.js browser prototype. It demonstrates continuous simulation, autonomous curiosity, object interaction, a day/night cycle, field notes, and an observer panel. It is a disposable behavioral prototype; Godot 4 with Jolt is the selected runtime for the project foundation.

The browser prototype may remain temporarily as a behavioral reference. New world-runtime development should target Godot rather than extending its hand-written physics.

## Running the browser prototype

The prototype requires Node.js 20.19 or newer.

```sh
npm install
npm run dev
```

Use `npm run build` to produce a static build. Do not place LLM credentials or other secrets in browser code.

## Target architecture

The system is divided into two processes with an explicit protocol between them:

1. **Godot world runtime** owns simulation time, Jolt physics, object state, perception queries, action execution, animation, and the operator-facing visualization.
2. **Agent service** owns internal drives, attention, memories, beliefs, goal formation, deliberation, reflection, and LLM-provider integration.

The world is authoritative. The agent service can request an action but cannot directly set transforms, bypass collisions, or mutate hidden world state.

### Control layers

Implement agent behavior through layers with different responsibilities and update rates:

1. **Body and reflexes:** deterministic, realtime control inside the world runtime.
2. **Drives:** deterministic internal variables such as curiosity, uncertainty, integrity, and energy.
3. **Attention:** selection and compression of observations into a bounded conscious context.
4. **Deliberation:** asynchronous LLM calls that return structured goals or intentions.
5. **Arbitration:** deterministic selection between reflexes, bodily constraints, and deliberative intentions.
6. **Memory and belief:** explicit records of experiences, learned claims, confidence, and evidence.

An LLM response must never be interpreted as per-frame motor input. Validate every proposed intention against current world state before execution. Reflexes and physical integrity may interrupt a deliberative plan.

### Time and concurrency

Use fixed physics steps. Simulation time must be independent of wall-clock time and pausable by the operator. LLM requests run asynchronously while physics and existing behaviors continue. Attach a world-state revision to each request and revalidate its response if the world has changed.

Avoid coupling deterministic simulation progress to network latency. Record decision request and response times separately from simulated time.

### World truth and agent belief

Never expose hidden fact definitions directly to the agent. Maintain separate representations for:

- Authoritative world state and fact definitions
- Agent observations
- Agent beliefs, confidence, and supporting evidence
- Objective experiment events
- Agent-authored notes and memories

Metrics must be calculated from the authoritative event record and fact criteria, not from an LLM's self-assessment.

### Telemetry and observability

Follow [`docs/observability.md`](docs/observability.md) when adding instrumentation. Preserve the separation between authoritative domain events, operational telemetry, and review artifacts.

Use OpenTelemetry APIs for traces and operational metrics. Propagate run, agent, world-revision, simulation-tick, and trace correlation across process boundaries. Keep metric labels bounded; stable object, event, request, and run identifiers belong in traces, logs, or domain events rather than metric dimensions.

Instrumentation must not block the simulation, change decision ordering, or become required for experiment meaning. A required event-recording failure invalidates the run; an optional telemetry-export failure only degrades observability.

## Architecture decisions

Before making a change that establishes or reverses a durable architectural constraint, add or update an ADR in `docs/adr/`. Use the next four-digit sequence number and the template in that directory.

ADR statuses are `Proposed`, `Accepted`, `Superseded`, or `Rejected`. Do not rewrite the reasoning of an accepted ADR to make a later decision appear inevitable. Add a new ADR and mark the previous decision as superseded.

## Backlog management

The canonical backlog is `docs/todo/README.md`. Priorities are:

- **P0 — Foundation:** required to establish a coherent end-to-end experiment.
- **P1 — First experiment:** required for the initial autonomous-discovery study.
- **P2 — Expansion:** valuable after the first experiment is reproducible.
- **P3 — Exploration:** possible research directions without near-term commitment.

Each backlog item should state an observable outcome. Move completed items to the completion log rather than silently deleting them. If implementation changes the priority or scope of adjacent work, update the backlog in the same change.

## Change guidelines

- Prefer small vertical slices that can be observed through the operator interface and event log.
- Keep simulation, agent cognition, and evaluation boundaries explicit.
- Represent commands, observations, intentions, facts, and events with versioned schemas.
- Assign stable identifiers to agents, objects, facts, experiments, and runs.
- Make random seeds and configuration values explicit in experiment records.
- Use monotonic simulation timestamps for ordering world events.
- Preserve raw evidence used to award discovery stages.
- Add telemetry for new failure modes and performance-sensitive paths without duplicating authoritative domain events.
- Keep provider-specific LLM code behind an adapter.
- Never treat private model reasoning as required experiment data; store structured decisions and concise justifications instead.

## Definition of done

A change is complete when its behavior is observable, failure modes are represented, relevant documentation is current, and any affected experiment data remains interpretable. New architectural constraints require an ADR; new deferred work requires a prioritized backlog entry.
