---
id: 0007
title: Use WebSocket for agent-service boundary
status: Accepted
date: 2026-11-08
---

## Context

The Godot world runtime and the external agent service need a communication protocol for exchanging observations, intentions, and actions with correlation context and stale-response rejection.

## Decision

Use WebSocket (Godot `WebSocketPeer` ↔ Python `websockets`) as the transport protocol.

## Rationale

- Godot has built-in `WebSocketPeer` - no GDExtension needed
- Python has mature `websockets` library
- Bidirectional, asynchronous, works locally and over network
- Simple JSON framing, easy to debug
- Avoids complexity of ZeroMQ GDExtensions or bridge processes
- Framing overhead negligible for small message sizes

## Consequences

- HTTP framing overhead (~2 bytes/frame) accepted
- TLS/WSS available for future remote deployments
- Reconnection logic implemented in Godot client