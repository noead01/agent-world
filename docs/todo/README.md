# Prioritized Backlog

This is the canonical backlog for Agent World. Priority reflects dependency and experimental value rather than estimated effort.

## P0 — Foundation

- [ ] **Create the Godot 4 project.** A project opens in the supported Godot version with Jolt selected, a main scene, fixed physics timing, and documented runtime configuration.
- [ ] **Retire or archive the browser prototype.** Preserve anything useful as a reference and remove ambiguity about the active runtime.
- [ ] **Define core identifiers and versioned schemas.** Cover scenarios, runs, agents, objects, observations, intentions, actions, events, facts, beliefs, evidence, and memories.
- [ ] **Define observability correlation and validity schemas.** Cover run validity, simulation ticks, world revisions, trace context, component versions, content-capture mode, and configuration fingerprints.
- [ ] **Build one physical room.** Include gravity, collisions, static boundaries, four rigid objects, stable object identifiers, and configurable material properties.
- [ ] **Implement simulation time.** Support pause, resume, reset, time scaling, fixed physics steps, and an accelerated day/night lighting cycle.
- [ ] **Implement a basic embodied agent.** Provide a visible body, locomotion, orientation, reach constraints, collision avoidance, and deterministic action execution.
- [ ] **Create the agent-service boundary.** Establish asynchronous connection lifecycle, observation and intention messages, world revisions, timeouts, cancellation, and stale-response handling.
- [ ] **Create append-only run recording.** Save initial conditions, configurations, seeds, version information, typed events, and final state.
- [ ] **Instrument the critical path.** Trace observation, attention, deliberation, validation, arbitration, action, physical outcome, memory, and discovery evaluation across Godot and the agent service.
- [ ] **Expose foundational health and metrics.** Report physics timing and overruns, recorder health, protocol health, LLM latency and failures, resource use, and run validity through OpenTelemetry-compatible signals.

## P1 — First autonomous-discovery experiment

- [ ] **Implement three initial drives.** Curiosity, uncertainty, and physical integrity must have explicit update rules and observable values.
- [ ] **Implement deterministic attention.** Rank candidate observations using novelty, proximity, change, drive relevance, and current-goal relevance.
- [ ] **Implement action arbitration.** Reflexes and integrity constraints can interrupt plans; accepted, rejected, interrupted, and resumed intentions are recorded.
- [ ] **Add a mock brain.** Generate structured intentions without an external model so the full experiment can run locally and repeatably.
- [ ] **Add an LLM provider adapter.** Support one provider through server-side credentials, structured output, timeouts, retries, and recorded model configuration.
- [ ] **Implement layered memory.** Separate working, episodic, semantic, and procedural memory from the objective event log.
- [ ] **Implement beliefs and evidence.** Store claims, confidence, status, supporting and contradicting evidence, and revision history.
- [ ] **Define the scenario manifest.** Allow an operator to author objects, hidden facts, prerequisites, evidence conditions, difficulty metadata, and verification criteria.
- [ ] **Create the first benchmark room.** Include four objects and at least six facts spanning direct observation, physical experimentation, temporal behavior, and multi-step inference.
- [ ] **Implement discovery-stage evaluation.** Award and explain encountered, noticed, investigated, hypothesized, verified, retained, applied, and generalized stages.
- [ ] **Build the observer interface.** Show world time, agent status, drives, attention, current goal, plan, notes, beliefs, recent events, and pending deliberation.
- [ ] **Build a maintainer timeline.** Correlate domain events, traces, logs, snapshots, internal agent state, and discovery stages by simulation tick.
- [ ] **Build the run report.** Report coverage, depth, accuracy, autonomy, efficiency, evidence quality, retention, and reasons for missed facts.
- [ ] **Support reproducible run comparison.** Compare at least two agent configurations on the same scenario and seeds.
- [ ] **Detect deterministic divergence.** Emit periodic canonical-state checksums and capture a bounded diagnostic window around the first mismatch.

## P2 — Expansion

- [ ] Add a visual world-authoring interface for objects and discoverable facts.
- [ ] Add semantic retrieval and memory consolidation policies.
- [ ] Add explicit hypothesis generation and experiment planning.
- [ ] Add delayed retention tests and changed-world transfer tests.
- [ ] Add contradictory and deceptive evidence scenarios.
- [ ] Add manipulators, articulated bodies, and richer affordances.
- [ ] Add scenario packaging, import, export, and validation.
- [ ] Add batch and headless experiment execution.
- [ ] Add model-cost and latency analysis to run comparison.
- [ ] Add saved-run playback synchronized with agent state and metrics.
- [ ] Add configurable minimal, standard, and diagnostic observability profiles with retention and redaction policies.

## P3 — Research directions

- [ ] Evaluate learned low-level policies alongside deterministic controllers.
- [ ] Study emergent specialization from different drive configurations.
- [ ] Introduce multiple embodied agents and social discovery.
- [ ] Explore language development grounded in shared world experience.
- [ ] Add procedural world generation with controlled fact difficulty.
- [ ] Investigate counterfactual replay using alternate agent decisions.
- [ ] Compare symbolic, vector, graph, and hybrid memory systems.

## Completion log

Move completed items here with the completion date and a link to the implementing change or relevant ADR.

- 2026-10-29 — Selected Godot 4 with Jolt as the target world runtime ([ADR 0001](../adr/0001-use-godot-with-jolt.md)).
- 2026-10-29 — Established layered agent control, an external cognition service, ground-truth discovery evaluation, and append-only experiment records ([ADRs](../adr/README.md)).
- 2026-10-29 — Defined the telemetry, observability, behavioral-review, and run-validity approach ([observability design](../observability.md), [ADR 0006](../adr/0006-use-opentelemetry-and-separate-telemetry-from-experiment-events.md)).
