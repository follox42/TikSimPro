# backend/api/websocket/handler.py
"""
WebSocket handler for real-time updates.
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
import json
import asyncio


class ConnectionManager:
    """Manage WebSocket connections."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        """Accept and store a new connection."""
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
        print(f"WebSocket connected. Total: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket):
        """Remove a connection."""
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        print(f"WebSocket disconnected. Total: {len(self.active_connections)}")

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send message to a specific client."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"Error sending personal message: {e}")

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients."""
        if not self.active_connections:
            return

        disconnected = []

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error broadcasting to client: {e}")
                disconnected.append(connection)

        # Remove disconnected clients
        for conn in disconnected:
            await self.disconnect(conn)

    async def broadcast_video_generated(self, video_id: int, video_data: dict):
        """Broadcast new video generation."""
        await self.broadcast({
            "type": "video_generated",
            "video_id": video_id,
            "data": video_data
        })

    async def broadcast_metrics_updated(self, video_id: int, metrics: dict):
        """Broadcast metrics update."""
        await self.broadcast({
            "type": "metrics_updated",
            "video_id": video_id,
            "metrics": metrics
        })

    async def broadcast_pipeline_status(self, running: bool, message: str = ""):
        """Broadcast pipeline status change."""
        await self.broadcast({
            "type": "pipeline_status",
            "running": running,
            "message": message
        })

    async def broadcast_claude_message(self, message: str, actions: list = None):
        """Broadcast Claude's message."""
        await self.broadcast({
            "type": "claude_message",
            "message": message,
            "actions": actions or []
        })


# Global connection manager
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint handler."""
    await manager.connect(websocket)

    try:
        # Send welcome message
        await manager.send_personal_message({
            "type": "connected",
            "message": "Connected to TikSimPro WebSocket"
        }, websocket)

        # Listen for messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)

                # Handle different message types
                msg_type = message.get("type", "")

                if msg_type == "ping":
                    await manager.send_personal_message({"type": "pong"}, websocket)

                elif msg_type == "subscribe":
                    # Client wants to subscribe to specific events
                    events = message.get("events", [])
                    await manager.send_personal_message({
                        "type": "subscribed",
                        "events": events
                    }, websocket)

                elif msg_type == "get_status":
                    # Client requests current status
                    # This would normally query the database
                    await manager.send_personal_message({
                        "type": "status",
                        "pipeline_running": False,
                        "connected_clients": len(manager.active_connections)
                    }, websocket)

                else:
                    # Echo unknown messages
                    await manager.send_personal_message({
                        "type": "echo",
                        "original": message
                    }, websocket)

            except json.JSONDecodeError:
                await manager.send_personal_message({
                    "type": "error",
                    "message": "Invalid JSON"
                }, websocket)

    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        await manager.disconnect(websocket)
