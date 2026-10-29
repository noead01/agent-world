# 0002: Layer agent control by response time and responsibility

- Status: Accepted
- Date: 2026-10-29

## Context

Realtime physical control cannot depend on the latency or availability of an LLM. At the same time, deterministic rules alone do not provide the open-ended goal formation and reflection the project intends to study.

## Decision

Model an embodied agent as cooperating control layers:

1. Body and reflexes provide deterministic realtime control.
2. Drives create deterministic internal pressures and opportunities.
3. Attention selects a bounded conscious context.
4. LLM deliberation proposes goals, hypotheses, and structured plans asynchronously.
5. Arbitration chooses executable behavior and gives physical integrity priority.
6. Memory and beliefs retain experiences, claims, evidence, and procedures.

The LLM produces high-level intentions. It does not control physics frames, body transforms, or joint forces directly.

## Alternatives considered

- Ask an LLM to choose every action at fixed intervals.
- Encode all behavior as deterministic rules.
- Use a single monolithic agent loop combining reflex, planning, and memory.

## Consequences

- The world remains responsive during model calls and model failures.
- Individual layers can be varied and evaluated independently.
- Arbitration, interruption, and context assembly become explicit design responsibilities.
- Some apparently intelligent behavior will originate from deterministic mechanisms; experiment records must identify the responsible layer.
