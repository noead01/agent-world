# Codex project instructions

Read and follow [`CONTRIBUTING.md`](../CONTRIBUTING.md) before modifying the project. It is the authoritative source for development, architecture, documentation, and review conventions.

## Git and worktree requirements

- Never implement a change directly on `main` and never push to `main`.
- Update the primary `main` checkout, then create a short-lived branch and a dedicated worktree under `.worktrees/`.
- As the first meaningful branch change, move the individual entry from `docs/todo/backlog/pN/` to `docs/todo/in-progress/`, set `status: in-progress`, clear its active priority, and record the selected priority in status history.
- Perform all edits, checks, and commits from that worktree.
- Keep a branch limited to one reviewable change and avoid long-lived divergence from `main`.
- Push the feature branch and create a pull request targeting `main`.
- Move the item to `docs/todo/done/` and set `status: done` only after implementation and verification are complete. Link it in the pull request.
- Do not merge without explicit human approval, passing checks, and resolved review conversations.
- Use squash merge. After merge, update `main`, remove the worktree, delete the branch, and prune worktree metadata.
- Inspect status and `git worktree list` before cleanup. Preserve all user changes.

Read relevant ADRs and the backlog before implementation. Add an ADR for a durable architectural constraint and update the backlog for intentionally deferred work. Keep the user-facing README free of development instructions.

If review feedback reopens implementation work, move the entry from `done/` back to `in-progress/`; return it to `done/` only when the branch is ready for another review. Reprioritization applies only inside `backlog/`. Keep path and metadata synchronized.

Maintain clear boundaries between world simulation, deterministic agent behavior, asynchronous LLM deliberation, memory, evaluation, and observability. Record behaviorally meaningful outcomes in the authoritative event stream; use OpenTelemetry for operational diagnostics.

In the final handoff, report the branch, worktree, commit, verification, and pull-request status. Stop before merge unless the user has explicitly authorized it.
