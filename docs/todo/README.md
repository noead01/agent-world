# Prioritized Backlog

This is the prioritized index for Agent World's repository-managed backlog. Priority reflects dependency and experimental value rather than estimated effort.

Each roadmap item has an individual Markdown record created from [`template.md`](template.md). Waiting work is prioritized by its `backlog/p0`–`p3` path. Once selected, it moves into a flat lifecycle folder and no longer carries an active priority. Front matter provides machine-readable metadata and optional task type and dependencies.

```text
docs/todo/
├── backlog/
│   ├── p0/
│   ├── p1/
│   ├── p2/
│   └── p3/
├── in-progress/   # Active work; no priority
├── blocked/       # Paused work; no priority
└── done/          # Review-ready work; no priority
```

## Status and priority workflow

| Status folder | Metadata | Meaning |
|---|---|---|
| `backlog/p0`–`p3` | `status: backlog`, `priority: P0`–`P3` | Prioritized, with no active implementation branch |
| `in-progress/` | `status: in-progress`, `priority: null` | Active work exists on the recorded short-lived branch |
| `blocked/` | `status: blocked`, `priority: null` | Work cannot proceed; the entry explains why |
| `done/` | `status: done`, `priority: null` | Implementation and verification are complete; the branch is ready for pull-request review |

The first meaningful change on a feature branch moves its entry from `backlog/pN/` to `in-progress/`, sets `priority: null`, and records the selected priority in status history. The final change before review moves it to `done/`. Review feedback that requires more work moves it back to `in-progress/`. Reprioritization applies only to waiting work and moves the entry between `backlog/p0`–`p3`. Update front matter with every move. `done` means ready for review; it does not mean deployed or released.

## Items in review

| Item | Status | Branch | Pull request |
|---|---|---|---|
| [TODO-0004 — Define core identifiers and versioned schemas](done/TODO-0004-define-core-identifiers-and-versioned-schemas.md) | `done` | `feature/todo-0004-core-identifiers-versioned-schemas` | [#2](https://github.com/noead01/agent-world/pull/2) |
| [TODO-0001 — Trunk-based development workflow](done/TODO-0001-trunk-development-workflow.md) | `done` | `docs/trunk-development-workflow` | [#1](https://github.com/noead01/agent-world/pull/1) |
| [TODO-0046 — Establish the monorepo build and test framework](done/TODO-0046-establish-monorepo-build-and-test-framework.md) | `done` | `docs/trunk-development-workflow` | [#1](https://github.com/noead01/agent-world/pull/1) |

## P0 — Foundation

| ID | Item | Type |
|---|---|---|
| TODO-0002 | [Create the Godot 4 project](backlog/p0/TODO-0002-create-the-godot-4-project.md) | `setup` |
| TODO-0003 | [Retire or archive the browser prototype](backlog/p0/TODO-0003-retire-or-archive-the-browser-prototype.md) | `refactoring` |
| TODO-0005 | [Define observability correlation and validity schemas](backlog/p0/TODO-0005-define-observability-correlation-and-validity-schemas.md) | `feature` |
| TODO-0006 | [Build one physical room](backlog/p0/TODO-0006-build-one-physical-room.md) | `feature` |
| TODO-0007 | [Implement simulation time](backlog/p0/TODO-0007-implement-simulation-time.md) | `feature` |
| TODO-0008 | [Implement a basic embodied agent](backlog/p0/TODO-0008-implement-a-basic-embodied-agent.md) | `feature` |
| TODO-0009 | [Create the agent-service boundary](backlog/p0/TODO-0009-create-the-agent-service-boundary.md) | `feature` |
| TODO-0010 | [Create append-only run recording](backlog/p0/TODO-0010-create-append-only-run-recording.md) | `feature` |
| TODO-0011 | [Instrument the critical path](backlog/p0/TODO-0011-instrument-the-critical-path.md) | `feature` |
| TODO-0012 | [Expose foundational health and metrics](backlog/p0/TODO-0012-expose-foundational-health-and-metrics.md) | `feature` |

## P1 — First autonomous-discovery experiment

| ID | Item | Type |
|---|---|---|
| TODO-0013 | [Implement three initial drives](backlog/p1/TODO-0013-implement-three-initial-drives.md) | `feature` |
| TODO-0014 | [Implement deterministic attention](backlog/p1/TODO-0014-implement-deterministic-attention.md) | `feature` |
| TODO-0015 | [Implement action arbitration](backlog/p1/TODO-0015-implement-action-arbitration.md) | `feature` |
| TODO-0016 | [Add a mock brain](backlog/p1/TODO-0016-add-a-mock-brain.md) | `feature` |
| TODO-0017 | [Add an LLM provider adapter](backlog/p1/TODO-0017-add-an-llm-provider-adapter.md) | `feature` |
| TODO-0018 | [Implement layered memory](backlog/p1/TODO-0018-implement-layered-memory.md) | `feature` |
| TODO-0019 | [Implement beliefs and evidence](backlog/p1/TODO-0019-implement-beliefs-and-evidence.md) | `feature` |
| TODO-0020 | [Define the scenario manifest](backlog/p1/TODO-0020-define-the-scenario-manifest.md) | `feature` |
| TODO-0021 | [Create the first benchmark room](backlog/p1/TODO-0021-create-the-first-benchmark-room.md) | `research/experimentation` |
| TODO-0022 | [Implement discovery-stage evaluation](backlog/p1/TODO-0022-implement-discovery-stage-evaluation.md) | `feature` |
| TODO-0023 | [Build the observer interface](backlog/p1/TODO-0023-build-the-observer-interface.md) | `feature` |
| TODO-0024 | [Build a maintainer timeline](backlog/p1/TODO-0024-build-a-maintainer-timeline.md) | `feature` |
| TODO-0025 | [Build the run report](backlog/p1/TODO-0025-build-the-run-report.md) | `feature` |
| TODO-0026 | [Support reproducible run comparison](backlog/p1/TODO-0026-support-reproducible-run-comparison.md) | `feature` |
| TODO-0027 | [Detect deterministic divergence](backlog/p1/TODO-0027-detect-deterministic-divergence.md) | `feature` |

## P2 — Expansion

| ID | Item | Type |
|---|---|---|
| TODO-0028 | [Add visual world authoring](backlog/p2/TODO-0028-add-visual-world-authoring.md) | `feature` |
| TODO-0029 | [Add semantic retrieval and memory consolidation](backlog/p2/TODO-0029-add-semantic-retrieval-and-memory-consolidation.md) | `research/experimentation` |
| TODO-0030 | [Add hypothesis generation and experiment planning](backlog/p2/TODO-0030-add-hypothesis-generation-and-experiment-planning.md) | `feature` |
| TODO-0031 | [Add retention and transfer tests](backlog/p2/TODO-0031-add-retention-and-transfer-tests.md) | `research/experimentation` |
| TODO-0032 | [Add contradictory and deceptive evidence scenarios](backlog/p2/TODO-0032-add-contradictory-and-deceptive-evidence-scenarios.md) | `research/experimentation` |
| TODO-0033 | [Add manipulators and articulated bodies](backlog/p2/TODO-0033-add-manipulators-and-articulated-bodies.md) | `feature` |
| TODO-0034 | [Add scenario packaging and validation](backlog/p2/TODO-0034-add-scenario-packaging-and-validation.md) | `feature` |
| TODO-0035 | [Add batch and headless execution](backlog/p2/TODO-0035-add-batch-and-headless-execution.md) | `optimization` |
| TODO-0036 | [Add model cost and latency comparison](backlog/p2/TODO-0036-add-model-cost-and-latency-comparison.md) | `feature` |
| TODO-0037 | [Add synchronized saved-run playback](backlog/p2/TODO-0037-add-synchronized-saved-run-playback.md) | `feature` |
| TODO-0038 | [Add observability profiles and retention policies](backlog/p2/TODO-0038-add-observability-profiles-and-retention-policies.md) | `feature` |

## P3 — Research directions

| ID | Item | Type |
|---|---|---|
| TODO-0039 | [Evaluate learned low-level policies](backlog/p3/TODO-0039-evaluate-learned-low-level-policies.md) | `research/experimentation` |
| TODO-0040 | [Study drive-configuration specialization](backlog/p3/TODO-0040-study-drive-configuration-specialization.md) | `research/experimentation` |
| TODO-0041 | [Introduce multiple embodied agents](backlog/p3/TODO-0041-introduce-multiple-embodied-agents.md) | `research/experimentation` |
| TODO-0042 | [Explore grounded language development](backlog/p3/TODO-0042-explore-grounded-language-development.md) | `research/experimentation` |
| TODO-0043 | [Add procedural world generation](backlog/p3/TODO-0043-add-procedural-world-generation.md) | `research/experimentation` |
| TODO-0044 | [Add counterfactual replay](backlog/p3/TODO-0044-add-counterfactual-replay.md) | `research/experimentation` |
| TODO-0045 | [Compare memory-system architectures](backlog/p3/TODO-0045-compare-memory-system-architectures.md) | `research/experimentation` |

## Completion log

Retain completed entries and link them here after merge with the completion date and pull request. Do not use this log as a substitute for the individual item record.

- 2026-10-29 — Selected Godot 4 with Jolt as the target world runtime ([ADR 0001](../adr/0001-use-godot-with-jolt.md)).
- 2026-10-29 — Established layered agent control, an external cognition service, ground-truth discovery evaluation, and append-only experiment records ([ADRs](../adr/README.md)).
- 2026-10-29 — Defined the telemetry, observability, behavioral-review, and run-validity approach ([observability design](../observability.md), [ADR 0006](../adr/0006-use-opentelemetry-and-separate-telemetry-from-experiment-events.md)).
