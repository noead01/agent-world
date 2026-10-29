---
id: TODO-0001
priority: P0
status: in-progress
title: Establish trunk-based development workflow
branch: docs/trunk-development-workflow
pull_request: https://github.com/noead01/agent-world/pull/1
created: 2026-10-29
updated: 2026-10-29
---

# Establish trunk-based development workflow

## Outcome

Contributors and AI coding assistants consistently use short-lived feature branches, repository-local Git worktrees, pull-request review, and squash merging while keeping `main` releasable.

## Scope

- Document the workflow and pull-request expectations in `CONTRIBUTING.md`.
- Ignore `.worktrees/` while allowing committed project instructions under `.codex/`.
- Provide aligned instructions for Claude, GitHub Copilot, and Codex.
- Define repository-managed backlog status folders and transitions that accompany branch and review work.

Repository branch-protection settings and continuous-integration checks are separate follow-up work.

## Acceptance criteria

- [x] Direct commits and pushes to `main` are prohibited by contributor guidance.
- [x] Work uses short-lived branches with dedicated worktrees under `.worktrees/`.
- [x] Pull requests require checks, human review, and resolved conversations before squash merge.
- [x] Claude, GitHub Copilot, and Codex receive committed, consistent workflow instructions.
- [x] Backlog entries move from `backlog/` to `in-progress/` on the feature branch and to `done/` when ready for review.
- [x] Pull request #1 contains the complete documentation change and is ready for human review.

## Status history

- 2026-10-29 — `backlog`: Workflow requirement identified.
- 2026-10-29 — `in-progress`: Documentation and assistant instructions implemented on `docs/trunk-development-workflow`.
- 2026-10-29 — `done`: Verification completed and pull request #1 opened for review.
- 2026-10-29 — `in-progress`: Review expanded the workflow to require individual backlog records and folder-based status transitions.
- 2026-10-29 — `done`: Folder workflow, template, status index, and assistant guidance completed for renewed review.
- 2026-10-29 — `in-progress`: Review requested materializing every roadmap candidate as a complete individual backlog record.

## Notes

This item is back in `in-progress/` while the repository backlog is expanded into individual, reviewable records.
