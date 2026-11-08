"""WebSocket server for agent service."""
import asyncio
import uuid
import json
import os
from typing import Dict, Optional
import websockets
from websockets.server import WebSocketServerProtocol
from .schemas import (
    Hello, HelloAck, CorrelationContext, WorldState, Intention, Action, Error
)
from .protocol import (
    parse_message, serialize_message, PROTOCOL_VERSION
)
from .mock_agent import MockAgent


class AgentService:
    """Asyncio WebSocket server for agent communication."""
    
    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8765,
        experiment_id: str = "exp_autonomous_discovery_01",
        scenario_id: str = "first_benchmark_room",
        scenario_version: str = "1.0.0",
        run_id: str = "run_001",
    ):
        self.host = host
        self.port = port
        self.experiment_id = experiment_id
        self.scenario_id = scenario_id
        self.scenario_version = scenario_version
        self.run_id = run_id
        
        self.server: Optional[websockets.Server] = None
        self.clients: Dict[str, Dict] = {}  # agent_id -> {websocket, mock_agent, correlation}
        self.world_revision = 0
        self.simulation_tick = 0
        self.simulation_time = 0.0
        self._running = False
        self._tick_task: Optional[asyncio.Task] = None
        
    async def start(self) -> None:
        """Start the WebSocket server."""
        self.server = await websockets.serve(
            self._handle_connection,
            self.host,
            self.port,
            ping_interval=5,
            ping_timeout=10,
        )
        self._running = True
        # Start world simulation tick (simulates world sending WorldState)
        self._tick_task = asyncio.create_task(self._world_tick_loop())
        print(f"Agent service started on ws://{self.host}:{self.port}")
        
    async def stop(self) -> None:
        """Stop the server."""
        self._running = False
        if self._tick_task:
            self._tick_task.cancel()
            try:
                await self._tick_task
            except asyncio.CancelledError:
                pass
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        # Close all client connections
        for client_info in self.clients.values():
            await client_info["websocket"].close()
        print("Agent service stopped")
        
    async def _handle_connection(self, websocket: WebSocketServerProtocol) -> None:
        """Handle a new WebSocket connection."""
        agent_id = None
        try:
            async for message in websocket:
                msg = parse_message(message)
                
                if isinstance(msg, Hello):
                    agent_id = msg.agent_id
                    await self._handle_hello(websocket, msg)
                elif agent_id and agent_id in self.clients:
                    client = self.clients[agent_id]
                    await self._route_message(client, msg)
                else:
                    # No handshake yet
                    err = make_error("PROTOCOL_ERROR", "Expected Hello message first")
                    await websocket.send(serialize_message(err))
                    
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            print(f"Connection error: {e}")
        finally:
            if agent_id and agent_id in self.clients:
                del self.clients[agent_id]
                
    async def _handle_hello(self, websocket: WebSocketServerProtocol, hello: Hello) -> None:
        """Process Hello handshake."""
        if hello.protocol_version != PROTOCOL_VERSION:
            err = make_error("PROTOCOL_MISMATCH", f"Expected {PROTOCOL_VERSION}, got {hello.protocol_version}")
            await websocket.send(serialize_message(err))
            await websocket.close()
            return
            
        agent_id = hello.agent_id
        
        # Create correlation context
        correlation = CorrelationContext(
            experiment_id=self.experiment_id,
            scenario_id=self.scenario_id,
            scenario_version=self.scenario_version,
            run_id=self.run_id,
            agent_id=agent_id,
            world_revision=self.world_revision,
            simulation_tick=self.simulation_tick,
            simulation_time=self.simulation_time,
            component="agent",
            component_version=PROTOCOL_VERSION,
        )
        
        # Create mock agent for this connection
        mock_agent = MockAgent(
            agent_id=agent_id,
            run_id=self.run_id,
            experiment_id=self.experiment_id,
            scenario_id=self.scenario_id,
            scenario_version=self.scenario_version,
            send_callback=lambda msg: websocket.send(msg),
            correlation_base=correlation
        )
        
        # Set deterministic target sequence (matching room.gd)
        target_ids = [
            "obj_wood_cube", "obj_metal_sphere", "obj_glass_box", "obj_rubber_cylinder"
        ]
        targets = [
            {"target_id": "obj_nonexistent", "action_type": "touch"},
            {"target_id": "", "action_type": "wait"},
        ]
        for tid in target_ids:
            targets.append({"target_id": tid, "action_type": "move"})
            is_first = (tid == "obj_wood_cube")
            targets.append({"target_id": tid, "action_type": "touch", "interrupt_after": is_first})
        mock_agent.set_targets(targets)
        
        self.clients[agent_id] = {
            "websocket": websocket,
            "mock_agent": mock_agent,
            "correlation": correlation
        }
        
        # Send HelloAck
        ack = HelloAck(
            protocol_version=PROTOCOL_VERSION,
            server_id="agent-service-01",
            accepted_capabilities=hello.capabilities,
            initial_world_revision=self.world_revision,
            correlation=correlation
        )
        await websocket.send(serialize_message(ack))
        
        # Notify mock agent of handshake completion
        await mock_agent.on_hello_ack(ack)
        
    async def _route_message(self, client: Dict, msg) -> None:
        """Route incoming message to mock agent."""
        mock_agent = client["mock_agent"]
        
        # Update world revision from WorldState first
        if isinstance(msg, WorldState):
            self.world_revision = msg.world_revision
            self.simulation_tick = msg.simulation_tick
            self.simulation_time = msg.simulation_time
        
        # Route to mock agent
        if isinstance(msg, WorldState):
            await mock_agent.on_world_state(msg)
        elif isinstance(msg, Observation):
            await mock_agent.on_observation(msg)
        elif isinstance(msg, Action):
            # World sends ActionResult back as Action with result field
            await mock_agent.on_action_result(msg)
        elif isinstance(msg, Intention):
            # World sends Intention (touch/inspect) - treat as action request
            await mock_agent.on_action_result(msg)  # Reuse same handler for now
        elif isinstance(msg, Error):
            await mock_agent.on_error(msg)
            
    async def _world_tick_loop(self) -> None:
        """Process world state and issue actions for all connected agents."""
        while self._running:
            # Tick all connected mock agents to issue actions based on latest world state
            for agent_id, client_info in self.clients.items():
                mock_agent = client_info["mock_agent"]
                if mock_agent.last_world_state:
                    # Use a small delta (1/60 = ~0.016s) to match physics tick rate
                    await mock_agent.run_tick(1.0 / 60.0)
            await asyncio.sleep(1.0 / 60.0)  # Run at 60Hz to match physics
            
    # Godot is authoritative for WorldState. Agent service receives WorldState
    # via _route_message and forwards to MockAgent. No simulation here.


async def main() -> None:
    """Entry point for running the agent service."""
    host = os.getenv("AGENT_SERVICE_HOST", "0.0.0.0")
    port = int(os.getenv("AGENT_SERVICE_PORT", "8765"))
    experiment_id = os.getenv("AGENT_EXPERIMENT_ID", "exp_autonomous_discovery_01")
    scenario_id = os.getenv("AGENT_SCENARIO_ID", "first_benchmark_room")
    scenario_version = os.getenv("AGENT_SCENARIO_VERSION", "1.0.0")
    run_id = os.getenv("AGENT_RUN_ID", "run_001")
    
    service = AgentService(
        host=host,
        port=port,
        experiment_id=experiment_id,
        scenario_id=scenario_id,
        scenario_version=scenario_version,
        run_id=run_id,
    )
    
    try:
        await service.start()
        # Keep running until interrupted
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        await service.stop()


if __name__ == "__main__":
    asyncio.run(main())