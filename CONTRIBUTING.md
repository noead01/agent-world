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

## Prerequisites

### Godot 4 (world runtime)

Godot 4.x (official stable build, with Jolt physics integrated) must be installed and on `PATH`. The world runtime uses Godot's built-in Jolt physics engine, which is only available in Godot 4.

**Important:** `apt install godot3` installs Godot 3.6.x, which lacks Jolt physics and will not work for the world runtime.

**Ubuntu/Debian — install Godot 4:**

Godot 4 is not yet in the Ubuntu package repositories. Download the official Linux x86_64 editor binary from the Godot releases page:

```sh
# Pick the latest stable release (e.g. 4.7.2-stable)
GODOT_VERSION="4.7.2-stable"
curl -sL -o /tmp/godot-linux.zip \
  "https://github.com/godotengine/godot/releases/download/${GODOT_VERSION}/Godot_v${GODOT_VERSION}_linux.x86_64.zip"
python3 -c "import zipfile; zipfile.ZipFile('/tmp/godot-linux.zip').extractall('$HOME/.local/bin')"
chmod +x "$HOME/.local/bin/Godot_v${GODOT_VERSION}_linux.x86_64"
ln -sf "Godot_v${GODOT_VERSION}_linux.x86_64" "$HOME/.local/bin/godot"
rm /tmp/godot-linux.zip
```

Add `~/.local/bin` to your `PATH` if it is not already:

```sh
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

Verify the installation:

```sh
godot --version
```

Expected output includes `Godot Engine v4.x`.

**Headless CI runs:** The world component can be run headless without a display:

```sh
godot --headless --path apps/world --quit-after 1
```

### Node.js (browser prototype)

The disposable Three.js browser prototype requires Node.js 20.19 or newer.

```sh
cd apps/browser-prototype
npm install
npm run dev
```

Use `npm run build` to produce a static build. Do not place LLM credentials or other secrets in browser code.

## Monorepo and build interface

The repository is organized by deployment and ownership boundary rather than by implementation language:

- `apps/` contains interactive executables such as the Godot world.
- `services/` contains independently running processes such as the agent service.
- `packages/` contains shared, versioned contracts and reusable assets.
- `scenarios/` contains experiment definitions and discovery criteria.
- `tools/` contains engineering, validation, and offline evaluation tools.
- `tests/` contains repository-level tests that verify build and cross-component behavior.

Registered components are listed explicitly in `build/components.mk`. Each has `component.mk`, a local Makefile, a README, and unit, integration, and acceptance test locations. Do not infer components by scanning directories: adding a component is an architectural change that should be visible in review.

The root Makefile is the stable contributor and CI interface. Run `make help` to discover it. Common commands are:

```sh
make bootstrap
make validate
make test-unit
make test-integration
make test-acceptance
make test
make ci
```

Components may use different native tooling, but their local Makefile must preserve the shared target names. `make ci` is non-mutating and combines formatting checks, linting, structural validation, tests, and builds. `make bootstrap` is intentionally separate so dependency installation is explicit.

### Test layers

- **Unit tests** exercise isolated deterministic logic and should be fast, seed-controlled, and network-free.
- **Integration tests** exercise technical boundaries such as physics scenes, persistence, schemas, provider adapters, or world-agent protocol exchanges.
- **Acceptance tests** exercise a component through its public boundary and demonstrate backlog acceptance criteria with machine-readable evidence where practical.

Every implementation backlog item must identify the acceptance tests that demonstrate its criteria. Default tests must not call a live LLM. Use deterministic fakes or recorded provider responses; keep opt-in live-provider experiments separate and report model, parameters, latency, cost, and run validity. Do not assert private chain-of-thought. Assert structured intentions, authoritative events, state changes, and evaluation results.

Runtime-specific test libraries are selected when the corresponding component is implemented. Record a choice in an ADR when it establishes a durable project constraint. Empty or not-yet-implemented components must say that no testable implementation exists rather than report a misleading behavioral pass.

## Development workflow

Agent World uses trunk-based development. `main` is the trunk and must remain releasable. All changes, including documentation and maintenance work, use short-lived branches and are reviewed through pull requests before being merged.

### Rules

- Do not commit or push directly to `main`.
- Start each change from an up-to-date `main`.
- Use one short-lived branch for one coherent change.
- Keep branches measured in hours or a few days, not weeks.
- Prefer small pull requests that can be reviewed as a single idea.
- Move the branch's backlog entry from its priority folder into the flat status folders: `in-progress/` while work is underway and `done/` immediately before opening or refreshing its pull request.
- Rebase the branch onto the latest `main` before final review when it has fallen behind.
- Require passing automated checks, at least one approving review, and resolution of review conversations before merge.
- Use squash merge so each pull request becomes one coherent commit on `main`.
- Delete the remote branch and remove its worktree after merge.
- Keep incomplete work behind an inactive code path or feature flag when a vertical slice cannot be completed in one small pull request.

Recommended branch prefixes are `feature/`, `fix/`, `docs/`, `refactor/`, `test/`, and `chore/`. Use a short descriptive suffix, for example `feature/scenario-schema` or `fix/stale-intention-validation`.

### Worktrees

Develop each branch in its own Git worktree under the repository-local `.worktrees/` directory. The directory is ignored by Git. Keep the primary checkout on `main` so it remains a clean integration and review point.

From the primary checkout:

```sh
git fetch origin
git switch main
git pull --ff-only
git worktree add .worktrees/feature-scenario-schema -b feature/scenario-schema main
```

Perform all edits, local checks, and commits from the new worktree:

```sh
cd .worktrees/feature-scenario-schema
# Move the selected item from docs/todo/backlog/pN/ to docs/todo/in-progress/ first.
git status
git add <paths>
git commit
git push -u origin feature/scenario-schema
```

When implementation and verification are complete, move the backlog item from `docs/todo/in-progress/` to `docs/todo/done/`, set its metadata to `status: done`, and commit the move with the branch. Then open a pull request targeting `main`. If the branch needs to catch up before final review:

```sh
git fetch origin
git rebase origin/main
git push --force-with-lease
```

After the pull request is approved and squash-merged, return to the primary checkout and clean up:

```sh
git switch main
git pull --ff-only
git worktree remove .worktrees/feature-scenario-schema
git branch -d feature/scenario-schema
git worktree prune
```

Never place one worktree inside another. Never reuse a worktree for an unrelated branch. Use `git worktree list` before removing or repairing worktrees, and do not remove a worktree containing uncommitted changes.

### Pull requests

A pull request should explain:

- The problem or experiment need being addressed
- The chosen approach and material tradeoffs
- How the change was verified
- Effects on schemas, experiment reproducibility, telemetry, or stored data
- Risks, limitations, and intentionally deferred work
- Documentation, ADR, or backlog changes included

Draft pull requests are encouraged for early feedback, but they are not mergeable. Keep commits understandable during review even though they will be squash-merged.

The author responds to review feedback on the feature branch. Material new scope should normally become a separate branch and pull request. Do not merge a pull request merely because checks pass; human approval remains required.

If review feedback requires code or documentation changes, move the backlog item from `done/` back to `in-progress/` before making them. Return it to `done/` only after the branch is ready for review again. Keep the metadata status synchronized with its directory path. A pull request must link its backlog entry.

### Urgent fixes

Urgent fixes still use a branch and pull request. Review may be expedited, but the change must remain traceable and must pass the checks relevant to the failure. Follow-up work created by an emergency compromise belongs in the prioritized backlog.

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

The canonical backlog is under `docs/todo/`. `docs/todo/README.md` is its prioritized index; actionable work is recorded in individual Markdown files created from `docs/todo/template.md`. Status is represented by location:

- `docs/todo/backlog/`
- `docs/todo/in-progress/`
- `docs/todo/blocked/`
- `docs/todo/done/`

Only `backlog/` contains `p0/`, `p1/`, `p2/`, and `p3/` subfolders. Priority determines which waiting item should be selected next; it no longer applies after work starts. `in-progress/`, `blocked/`, and `done/` are flat. Priorities are:

- **P0 — Foundation:** required to establish a coherent end-to-end experiment.
- **P1 — First experiment:** required for the initial autonomous-discovery study.
- **P2 — Expansion:** valuable after the first experiment is reproducible.
- **P3 — Exploration:** possible research directions without near-term commitment.

Each item must include its identifier, status, optional task type and dependencies, title, outcome, scope, acceptance criteria, definition of done, demonstration plan, and related branch or pull request. While in `backlog/`, its priority metadata must match its priority folder. On leaving the backlog, set `priority: null`; the status history retains its former priority. Use these statuses:

- `backlog`: prioritized but not being implemented
- `in-progress`: active work exists on a short-lived branch
- `blocked`: work started but cannot currently proceed; record the blocker
- `done`: implementation and verification are complete and the branch is ready for pull-request review

`done` describes branch readiness, not deployment or release. Moving the entry from `backlog/pN/` to `in-progress/`, clearing its active priority, and recording the selected priority belongs on the feature branch as its first meaningful change. Moving it to `done/` belongs on that same branch before its pull request is created or marked ready for another review. Reprioritization applies only in `backlog/` and moves the file between priority subfolders. Git must recognize these transitions as renames so the item's history remains continuous. Do not silently delete completed entries; retain them as the historical link between intent, implementation, and review.

If a branch is abandoned, move its item back to an explicitly chosen `backlog/pN/` priority or into `blocked/` in a separate reviewed change and update its metadata. If implementation changes the priority or scope of adjacent backlog work, update those entries in the same pull request when appropriate.

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

A change is complete when its behavior is observable, failure modes are represented, relevant documentation is current, and any affected experiment data remains interpretable. New architectural constraints require an ADR; new deferred work requires a prioritized backlog entry. The branch must also satisfy the pull-request requirements above before merge.
