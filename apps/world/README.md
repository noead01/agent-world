# World runtime

This component will contain the authoritative Godot 4 world runtime: simulation time, Jolt physics, object state, perception, action execution, animation, and operator visualization.

Its implementation and Godot-specific test framework belong to `TODO-0002`. Until then, its Makefile reports unimplemented lifecycle stages explicitly rather than claiming placeholder tests passed.

## Recording and reproducibility

The world owns the authoritative event stream. When run recording is enabled, it must:

- Record pause, resume, time-scale, and reset transitions as domain events, not only console output.
- Reject events that violate the event schema, ordering, run identity, or event-ID uniqueness, and mark the run invalid before persisting them.
- Include every behavior-affecting input in the configuration fingerprint, including the external agent service's target order, cooldown, and seeded-delay policy. World-only settings cannot distinguish runs whose agent behavior differs.
