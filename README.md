# Agent World

Agent World is an experimental virtual world for observing self-directed, embodied AI agents.

An operator constructs a world containing inanimate objects, physical properties, and facts that can be discovered. An agent is then released into that world without being given a task to complete. Its embodiment constrains what it can perceive and do; its internal drives, memory, and reasoning shape what it chooses to explore.

The aim is to study autonomous discovery: what an agent notices, which questions it forms, how it investigates them, what it learns, and whether it can retain and apply that knowledge.

## The world

The virtual world runs continuously and follows consistent physical and environmental rules. Its initial form is intentionally small: an enclosed 3D environment, inanimate objects, gravity, collisions, and a day/night cycle.

Worlds may contain properties and relationships that are not initially known to the agent. An object might roll when pushed, conceal another object, react to light, or participate in a relationship that can only be inferred through experimentation.

## The agent

An agent combines several kinds of behavior:

- Fast bodily functions and reflexes maintain movement and physical integrity.
- Internal drives such as curiosity and uncertainty create reasons to act.
- Attention selects a limited set of relevant observations.
- Memory retains experiences, learned facts, and reusable procedures.
- An LLM supports goal formation, deliberation, and reflection when deeper reasoning is useful.

The world continues to run while the agent deliberates. The LLM proposes intentions and plans; deterministic controllers execute physical actions within the rules of the world.

## The operator

The operator creates an experiment rather than driving the agent. They can:

- Construct and configure a world.
- Define discoverable facts and the evidence required to establish them.
- Configure the agent's embodiment, drives, memory, and reasoning model.
- Release, observe, pause, and reset the agent.
- Inspect the agent's goals, notes, beliefs, and actions.
- Review discovery metrics and compare experiment runs.

## Measuring discovery

The system distinguishes the world's authoritative truth from the agent's beliefs. A fact can progress through several stages: encountered, noticed, investigated, hypothesized, verified, retained, applied, and generalized.

Experiment results will describe more than total coverage. They will also show accuracy, evidence quality, autonomy, efficiency, retention, transfer, curiosity diversity, and recovery from mistaken beliefs. Runs retain enough information to explain why a fact was learned or missed and to compare different agent configurations reproducibly.

## Project status

Agent World is in its initial design and prototyping stage. The first milestone is a single autonomous agent exploring a small world of inanimate objects and independently discovering a set of measurable facts.

The project is not yet available as a usable release.

## License

No project license has been selected yet.
