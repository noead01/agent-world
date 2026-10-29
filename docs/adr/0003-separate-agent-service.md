# 0003: Separate the agent service from the world runtime

- Status: Accepted
- Date: 2026-10-29

## Context

Agent cognition will evolve independently from visualization and physics. It may use different LLM providers, memory systems, retrieval strategies, or experimental configurations. Network-bound model calls must not block Godot's realtime loop.

## Decision

Run cognition in an agent service connected to Godot through a versioned, asynchronous protocol. Godot sends bounded observations and action outcomes. The service returns structured intentions and memory-related outputs.

Godot remains authoritative for world state and validates all requested actions. Requests and responses include stable agent and run identifiers, simulation timestamps, and a world-state revision suitable for stale-response detection.

## Alternatives considered

- Implement LLM calls and memory directly in Godot scripts.
- Embed the agent service as a native Godot extension.
- Allow the agent service direct access to the scene tree or physics state.

## Consequences

- Model latency and provider SDKs remain outside the simulation loop.
- Agent services can be tested or replaced without rendering the world.
- The protocol and lifecycle of two processes must be designed and operated.
- Observation and intention schemas become explicit compatibility boundaries.
