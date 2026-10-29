---
id: TODO-0046
priority: null
status: done
type: setup
title: "Establish the monorepo build and test framework"
dependencies: []
branch: docs/trunk-development-workflow
pull_request: https://github.com/noead01/agent-world/pull/1
created: 2026-10-29
updated: 2026-10-29
---

# Establish the monorepo build and test framework

## Outcome

The repository has explicit component boundaries, one discoverable root build interface, and repeatable unit, integration, acceptance, and structural validation entry points.

## Scope

- Define the initial monorepo directory model for applications, services, shared packages, scenarios, and engineering tools.
- Add a root Makefile that delegates a consistent lifecycle to registered components.
- Add dependency-free repository validation and tests for the build contract.
- Document how each component supplies its own implementation-specific tests without weakening repository-wide checks.

Implementing the Godot world or agent service is outside this setup item.

## Acceptance criteria

- [x] A root `make help` documents all supported developer and CI commands.
- [x] Components are explicitly registered and expose the required build and test targets.
- [x] Unit, integration, and acceptance suites can be invoked independently or together.
- [x] Repository validation detects malformed component registrations and missing test conventions.
- [x] The monorepo and test architecture is recorded in an ADR and contributor guidance.

## Definition of done

- [x] All acceptance criteria pass in a clean checkout using documented prerequisites.
- [x] Root validation and test commands run successfully.
- [x] The structure does not claim unimplemented world or agent behavior is tested.
- [x] The pull request explains deferred runtime-specific framework choices.

## Demonstration plan

1. Run `make help` and `make components` to show the public build interface and registered components.
2. Run `make validate` to verify component metadata, directory conventions, and Makefile contracts.
3. Run `make test` and show the independently reported unit, integration, and acceptance suites.
4. Introduce a temporary invalid component declaration and demonstrate that validation rejects it.

## Status history

- 2026-10-29 — `backlog` (P0): Monorepo build and validation foundation identified during scaffold review.
- 2026-10-29 — `in-progress`: Work started on `docs/trunk-development-workflow`; active priority cleared.
- 2026-10-29 — `done`: Root build contract, component layout, validation, tests, documentation, and ADR verified with `make ci`.

## Notes

This setup extends the initial repository-scaffolding pull request. Runtime-specific test libraries will be selected with the implementation language of each component. Verification evidence: `make help`, `make components`, `make validate`, `make test`, `make ci`, `git diff --check`, and Python bytecode compilation all completed successfully.
