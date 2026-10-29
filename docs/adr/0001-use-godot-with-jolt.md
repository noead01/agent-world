# 0001: Use Godot with Jolt for the world runtime

- Status: Accepted
- Date: 2026-10-29

## Context

Agent World needs continuous 3D simulation, rigid-body physics, lighting, animation, navigation, scene authoring, debugging, and an operator interface. The initial browser prototype uses Three.js and hand-written object motion, but extending it would require assembling or building many capabilities supplied by a complete game engine.

The project should rest on a fully open-source foundation and avoid an expensive runtime migration as experiments become richer.

## Decision

Use Godot 4 as the virtual-world runtime and its integrated Jolt implementation for 3D physics. Godot owns simulation time, physical world state, rendering, scene composition, perception queries, action execution, and the operator-facing runtime UI.

The current Three.js prototype is a temporary behavioral reference rather than the production runtime foundation.

## Alternatives considered

- Continue with Three.js and add Rapier for physics.
- Use Unity and its physics and authoring tools.
- Build directly on Bullet, MuJoCo, Jolt, or another physics library.
- Use AI2-THOR as a prebuilt embodied-AI environment.

## Consequences

- The project gains an editor, scene graph, renderer, asset pipeline, physics integration, animation, audio, and multiplatform export.
- Initial setup is larger than a browser-only prototype.
- World code will use Godot concepts and APIs.
- Cognition and experiment records must remain outside engine-specific internals where practical, preserving their portability.
