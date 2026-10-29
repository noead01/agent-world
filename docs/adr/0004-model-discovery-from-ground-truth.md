# 0004: Evaluate discovery against authored ground truth

- Status: Accepted
- Date: 2026-10-29

## Context

The project needs to measure autonomous discovery rather than merely produce plausible behavior. LLM self-reports are insufficient: an agent may claim knowledge without evidence, overlook a fact after encountering it, or retain an incorrect belief.

## Decision

Each experimental world may define hidden facts, prerequisites, qualifying evidence, and verification criteria. These authoritative definitions remain inaccessible to the agent.

Track discovery as staged progress: encountered, noticed, investigated, hypothesized, verified, retained, applied, and generalized. Store the agent's beliefs, confidence, and evidence separately from world truth and from the objective event log.

Metrics are computed from authored criteria and recorded evidence. They include coverage, depth, accuracy, autonomy, efficiency, evidence quality, retention, transfer, curiosity diversity, and belief revision.

## Alternatives considered

- Score only whether the agent completed predefined tasks.
- Ask an LLM evaluator to judge the agent's narrative at the end of a run.
- Treat a fact as discovered as soon as the relevant object is observed.

## Consequences

- Experiment authors must explicitly describe facts and evidence conditions.
- Results can explain where discovery stopped and compare different configurations.
- Some semantic verification may still require a model-assisted evaluator, but it must operate against explicit criteria and preserve its evidence.
- Fact schema design becomes part of the core experimental platform.
