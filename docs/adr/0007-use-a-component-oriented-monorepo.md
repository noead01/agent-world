# 0007: Use a component-oriented monorepo with a shared build contract

- Status: Accepted
- Date: 2026-10-29

## Context

Agent World will combine a Godot application, an independently running agent service, shared protocol schemas, scenario data, and experiment-evaluation tools. These parts use different runtimes but must change together when contracts, experiment semantics, or observability correlation change. Contributors and CI need one predictable way to validate the whole system without pretending that every component uses the same language or test library.

## Decision

Keep the project in one repository with these top-level roles:

- `apps/` contains executable interactive applications, beginning with the authoritative world runtime.
- `services/` contains independently running backend processes, beginning with the agent service.
- `packages/` contains versioned shared contracts and reusable implementation-neutral assets.
- `scenarios/` contains experiment inputs and expected discovery criteria.
- `tools/` contains engineering and offline evaluation tooling.
- `tests/` contains repository-level tests that cross or validate component boundaries.

Every registered component has a `component.mk`, a local Makefile, documentation, and `tests/unit`, `tests/integration`, and `tests/acceptance` conventions. The root Makefile is the stable developer and CI interface. It delegates common lifecycle targets to components; it does not dictate their implementation language or underlying test framework.

Unit tests isolate deterministic logic. Integration tests exercise adapters or multiple technical units. Acceptance tests use public component boundaries and map to backlog acceptance criteria. Live LLM calls are excluded from default test suites: deterministic fakes or recorded responses are used unless an explicitly configured experiment requires a provider.

## Alternatives considered

- **Separate repositories per process:** offers independent versioning but makes atomic protocol changes, reproducible experiment baselines, and initial project governance unnecessarily difficult.
- **One language-level workspace:** provides strong tooling for a homogeneous codebase but cannot naturally govern Godot, service code, schemas, and analysis tools together.
- **A root script with hard-coded commands:** is initially simple but becomes brittle as components and runtimes are added.
- **One universal test framework:** produces superficial consistency while coupling unrelated runtimes and reducing access to their native testing tools.

## Consequences

Cross-component changes can be reviewed and tested atomically, and contributors get one discoverable command surface. Each component can still select a runtime-appropriate test framework. Registration and shared-contract changes receive explicit review.

The repository can grow large, so CI will eventually need affected-component selection and caching. Shared contracts require compatibility discipline rather than implicit in-process coupling. Placeholder components must report that they have no implementation yet; they must not present empty suites as behavioral verification.
