# Claude project instructions

Follow [`CONTRIBUTING.md`](../CONTRIBUTING.md) as the authoritative development guide.

## Mandatory workflow

- Treat `main` as protected and releasable. Never commit or push directly to it.
- For new work, update `main`, create a short-lived branch, and create its worktree under `.worktrees/`.
- Make all edits and commits from that feature worktree.
- Keep each branch and pull request focused on one coherent change.
- Push the branch and open a pull request against `main`.
- Do not merge without passing checks, resolved review conversations, and human approval.
- Use squash merge and remove the branch and worktree after merge.
- Never discard uncommitted work or remove a worktree without inspecting it first.

Before coding, read the relevant ADRs and prioritized backlog. Update documentation, ADRs, telemetry, and backlog entries when the change makes them inaccurate. The world runtime remains authoritative for physical state; LLM output is a validated high-level intention and never direct per-frame control.

When reporting completed work, identify the branch, worktree, verification performed, and pull-request state.
