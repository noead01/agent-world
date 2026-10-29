# Claude project instructions

Follow [`CONTRIBUTING.md`](../CONTRIBUTING.md) as the authoritative development guide.

## Mandatory workflow

- Treat `main` as protected and releasable. Never commit or push directly to it.
- For new work, update `main`, create a short-lived branch, and create its worktree under `.worktrees/`.
- As the first meaningful branch change, move its individual entry from `docs/todo/backlog/pN/` to `docs/todo/in-progress/`, set `status: in-progress`, clear its active priority, and record the selected priority in status history.
- Make all edits and commits from that feature worktree.
- Keep each branch and pull request focused on one coherent change.
- Push the branch and open a pull request against `main`.
- Move the item to `docs/todo/done/` and set `status: done` only when implementation and verification are complete and the branch is ready for review. Link it in the pull request.
- Do not merge without passing checks, resolved review conversations, and human approval.
- Use squash merge and remove the branch and worktree after merge.
- Never discard uncommitted work or remove a worktree without inspecting it first.

Before coding, read the relevant ADRs and prioritized backlog. Update documentation, ADRs, telemetry, and backlog entries when the change makes them inaccurate. The world runtime remains authoritative for physical state; LLM output is a validated high-level intention and never direct per-frame control.

If review feedback requires more work, move the item from `done/` back to `in-progress/`; return it to `done/` when the branch is review-ready again. Reprioritization applies only to items still in `backlog/`. Keep metadata synchronized with the path.

When reporting completed work, identify the branch, worktree, verification performed, and pull-request state.
