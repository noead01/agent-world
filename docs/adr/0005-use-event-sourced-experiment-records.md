# 0005: Use append-only event records for experiment runs

- Status: Accepted
- Date: 2026-10-29

## Context

Discovery results must be explainable and reproducible. Final world state and final agent notes do not reveal which observations, decisions, physical effects, or memory updates produced an outcome.

## Decision

Record each run as an append-only sequence of typed events accompanied by its initial world snapshot, random seed, scenario version, agent configuration, model configuration, and schema versions.

Events include observations delivered to the agent, drive changes relevant to decisions, deliberation requests and structured responses, accepted and rejected intentions, physical action outcomes, belief changes, memory changes, interventions, and awarded discovery stages.

Store concise structured decisions and justifications. Do not depend on private model reasoning traces as experiment data.

## Alternatives considered

- Persist only periodic world snapshots.
- Store application logs without a formal event schema.
- Save only the final metric report and agent memory.

## Consequences

- Runs can be inspected, replayed semantically, and reevaluated when metrics improve.
- Event schemas and ordering guarantees require deliberate versioning.
- Storage requirements increase, particularly if visual observations are retained.
- Physics replay may require engine-version pinning in addition to the semantic event record.
