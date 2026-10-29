# GitHub Copilot project instructions

Use [`CONTRIBUTING.md`](../CONTRIBUTING.md) as the authoritative development and review guide.

## Repository workflow

- `main` is protected, releasable trunk. Do not commit or push directly to it.
- Work on one coherent change in a short-lived branch.
- Create and use a dedicated worktree under `.worktrees/` for the branch.
- Move the individual entry from `docs/todo/backlog/pN/` to `docs/todo/in-progress/`, set it to `in-progress`, clear its active priority, and record the selected priority as the branch's first meaningful change.
- Target `main` with a pull request and keep the diff small enough for meaningful review.
- Move the entry to `docs/todo/done/` and set it to `done` only after implementation and verification are complete, then link it from the pull request.
- Passing checks, one human approval, and resolved conversations are required before merge.
- Squash-merge approved pull requests, then delete the branch and remove its worktree.
- Urgent changes still require a branch and pull request.

Consult applicable files in `docs/adr/` before changing architecture and `docs/todo/README.md` before expanding scope. Keep `README.md` strictly user-facing. Put contributor and implementation guidance in `CONTRIBUTING.md`.

Review changes that require additional work move the entry from `done/` back to `in-progress/`; return it to `done/` when the branch is ready for review again. Reprioritization applies only inside `backlog/`. Path and metadata must agree.

Preserve the separation between the Godot world runtime, deterministic control layers, the external agent service, authoritative experiment events, operational telemetry, and review artifacts. Never allow model output to mutate physical state without current-world validation.
