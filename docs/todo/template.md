---
id: TODO-NNNN
priority: P0
status: backlog
type: feature
title: Short outcome-oriented title
dependencies: []
branch: null
pull_request: null
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# Short outcome-oriented title

## Outcome

Describe the observable result this work must produce.

## Scope

Describe what belongs in this item and any meaningful exclusions.

## Acceptance criteria

- [ ] State externally verifiable completion conditions.

## Definition of done

- [ ] All acceptance criteria are satisfied and supported by automated or repeatable verification.
- [ ] Relevant schemas, telemetry, documentation, ADRs, and adjacent backlog records are updated.
- [ ] Failure modes are observable and no known regression invalidates experiment results.
- [ ] The demonstration plan has been executed and its evidence is linked from the pull request.

## Demonstration plan

1. Describe how to prepare the smallest reproducible demonstration.
2. Describe the behavior and failure cases to exercise.
3. Identify the UI, event, trace, report, or command output to capture as evidence.

## Status history

- YYYY-MM-DD — `backlog`: Item created and prioritized.

## Notes

Record blockers, material changes in scope, review context, or links to related ADRs and items.

Place a new copy of this file in `backlog/pN/`, matching its `priority`. Choose a task type such as `feature`, `refactoring`, `optimization`, `setup`, or `research/experimentation`; add dependency IDs when ordering matters. Reprioritize waiting work by moving it between `p0/`–`p3/` and updating `priority`. When work starts, move that same file to flat `in-progress/`, set `priority: null`, and record its selected priority in status history. Later status moves use flat `blocked/` and `done/`. Update `status`, `branch`, `pull_request`, `updated`, and status history as work progresses. Do not create a replacement file for a transition.
