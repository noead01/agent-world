# Prioritized Backlog

This is the prioritized index for Agent World's repository-managed backlog. Priority reflects dependency and experimental value rather than estimated effort.

Each item selected for implementation has an individual Markdown record created from [`template.md`](template.md). The priority lists below remain concise roadmap candidates until an individual record is created in `backlog/`. The record's directory is its visible workflow status, while its front matter provides machine-readable metadata. It moves with its feature branch and provides the durable link between the planned outcome, implementation status, and pull request.

```text
docs/todo/
├── backlog/       # Prioritized, not started
├── in-progress/   # Active feature branch
├── blocked/       # Cannot currently proceed
└── done/          # Branch is ready for review
```

## Status workflow

| Status | Meaning |
|---|---|
| Folder | Metadata | Meaning |
|---|---|---|
| `backlog/` | `status: backlog` | Prioritized, with no active implementation branch |
| `in-progress/` | `status: in-progress` | Active work exists on the recorded short-lived branch |
| `blocked/` | `status: blocked` | Work cannot proceed; the entry explains why |
| `done/` | `status: done` | Implementation and verification are complete; the branch is ready for pull-request review |

The first meaningful change on a feature branch moves its entry from `backlog/` to `in-progress/`. The final change before opening a pull request moves it to `done/`. Review feedback that requires more work moves it back to `in-progress/` until the branch is ready again. Update the front matter with every move. `done` means ready for review; it does not mean deployed or released.

## Items in review

| Priority | Item | Status | Branch | Pull request |
|---|---|---|---|---|
| P0 | [Trunk-based development workflow](done/TODO-0001-trunk-development-workflow.md) | `done` | `docs/trunk-development-workflow` | [#1](https://github.com/noead01/agent-world/pull/1) |

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

Retain completed entries and link them here after merge with the completion date and pull request. Do not use this log as a substitute for the individual item record.

- 2026-10-29 — Selected Godot 4 with Jolt as the target world runtime ([ADR 0001](../adr/0001-use-godot-with-jolt.md)).
- 2026-10-29 — Established layered agent control, an external cognition service, ground-truth discovery evaluation, and append-only experiment records ([ADRs](../adr/README.md)).
- 2026-10-29 — Defined the telemetry, observability, behavioral-review, and run-validity approach ([observability design](../observability.md), [ADR 0006](../adr/0006-use-opentelemetry-and-separate-telemetry-from-experiment-events.md)).
