"""
WebSocket API Routes - Real-time communication endpoints
"""

from typing import Dict, Any, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.websockets import WebSocketState
import json
import asyncio
import logging
from datetime import datetime

from ...core.orchestrator import Orchestrator
from ...core.inventory import Inventory
from ..dependencies import get_orchestrator, get_inventory


router = APIRouter()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_types: Dict[WebSocket, str] = {}
    
    async def connect(self, websocket: WebSocket, connection_type: str = "general"):
        """Accept a WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_types[websocket] = connection_type
        logging.info(f"WebSocket connected: {connection_type}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.connection_types:
            connection_type = self.connection_types.pop(websocket)
            logging.info(f"WebSocket disconnected: {connection_type}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket"""
        if websocket in self.active_connections:
            try:
                await websocket.send_text(message)
            except Exception as e:
                logging.error(f"Failed to send message: {e}")
                self.disconnect(websocket)
    
    async def broadcast(self, message: str, connection_type: str = None):
        """Broadcast a message to all connected WebSockets"""
        if connection_type:
            # Send to specific connection type
            for websocket in self.active_connections:
                if self.connection_types.get(websocket) == connection_type:
                    try:
                        await websocket.send_text(message)
                    except Exception as e:
                        logging.error(f"Failed to broadcast message: {e}")
                        self.disconnect(websocket)
        else:
            # Send to all connections
            for websocket in self.active_connections:
                try:
                    await websocket.send_text(message)
                except Exception as e:
                    logging.error(f"Failed to broadcast message: {e}")
                    self.disconnect(websocket)
    
    async def send_json(self, data: Dict[str, Any], websocket: WebSocket = None):
        """Send JSON data to WebSocket(s)"""
        message = json.dumps(data)
        if websocket:
            await self.send_personal_message(message, websocket)
        else:
            await self.broadcast(message)
    
    def get_connection_count(self) -> int:
        """Get the number of active connections"""
        return len(self.active_connections)
    
    def get_connections_by_type(self, connection_type: str) -> List[WebSocket]:
        """Get connections by type"""
        return [ws for ws in self.active_connections if self.connection_types.get(ws) == connection_type]


# Global connection manager
manager = ConnectionManager()


@router.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for general communication"""
    await manager.connect(websocket, "general")
    
    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get("type", "unknown")
                
                if message_type == "ping":
                    # Respond to ping
                    await manager.send_json({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }, websocket)
                
                elif message_type == "subscribe":
                    # Subscribe to specific events
                    event_type = message.get("event_type", "all")
                    await manager.send_json({
                        "type": "subscribed",
                        "event_type": event_type,
                        "timestamp": datetime.now().isoformat()
                    }, websocket)
                
                elif message_type == "get_status":
                    # Get current status
                    await manager.send_json({
                        "type": "status",
                        "connections": manager.get_connection_count(),
                        "timestamp": datetime.now().isoformat()
                    }, websocket)
                
                else:
                    # Echo back unknown message
                    await manager.send_json({
                        "type": "echo",
                        "original_message": message,
                        "timestamp": datetime.now().isoformat()
                    }, websocket)
                    
            except json.JSONDecodeError:
                await manager.send_json({
                    "type": "error",
                    "message": "Invalid JSON",
                    "timestamp": datetime.now().isoformat()
                }, websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@router.websocket("/runs")
async def websocket_runs(websocket: WebSocket):
    """WebSocket endpoint for run monitoring"""
    await manager.connect(websocket, "runs")
    
    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get("type", "unknown")
                
                if message_type == "subscribe_run":
                    # Subscribe to specific run updates
                    run_id = message.get("run_id")
                    await manager.send_json({
                        "type": "run_subscribed",
                        "run_id": run_id,
                        "timestamp": datetime.now().isoformat()
                    }, websocket)
                
                elif message_type == "get_runs":
                    # Get current runs
                    await manager.send_json({
                        "type": "runs_list",
                        "runs": [],  # Would get from orchestrator
                        "timestamp": datetime.now().isoformat()
                    }, websocket)
                
                else:
                    # Echo back unknown message
                    await manager.send_json({
                        "type": "echo",
                        "original_message": message,
                        "timestamp": datetime.now().isoformat()
                    }, websocket)
                    
            except json.JSONDecodeError:
                await manager.send_json({
                    "type": "error",
                    "message": "Invalid JSON",
                    "timestamp": datetime.now().isoformat()
                }, websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logging.error(f"WebSocket runs error: {e}")
        manager.disconnect(websocket)


@router.websocket("/hosts")
async def websocket_hosts(websocket: WebSocket):
    """WebSocket endpoint for host monitoring"""
    await manager.connect(websocket, "hosts")
    
    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get("type", "unknown")
                
                if message_type == "subscribe_host":
                    # Subscribe to specific host updates
                    host_name = message.get("host_name")
                    await manager.send_json({
                        "type": "host_subscribed",
                        "host_name": host_name,
                        "timestamp": datetime.now().isoformat()
                    }, websocket)
                
                elif message_type == "get_hosts":
                    # Get current hosts
                    await manager.send_json({
                        "type": "hosts_list",
                        "hosts": [],  # Would get from inventory
                        "timestamp": datetime.now().isoformat()
                    }, websocket)
                
                else:
                    # Echo back unknown message
                    await manager.send_json({
                        "type": "echo",
                        "original_message": message,
                        "timestamp": datetime.now().isoformat()
                    }, websocket)
                    
            except json.JSONDecodeError:
                await manager.send_json({
                    "type": "error",
                    "message": "Invalid JSON",
                    "timestamp": datetime.now().isoformat()
                }, websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logging.error(f"WebSocket hosts error: {e}")
        manager.disconnect(websocket)


@router.websocket("/logs")
async def websocket_logs(websocket: WebSocket):
    """WebSocket endpoint for log streaming"""
    await manager.connect(websocket, "logs")
    
    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get("type", "unknown")
                
                if message_type == "subscribe_logs":
                    # Subscribe to log streaming
                    log_type = message.get("log_type", "all")
                    await manager.send_json({
                        "type": "logs_subscribed",
                        "log_type": log_type,
                        "timestamp": datetime.now().isoformat()
                    }, websocket)
                
                elif message_type == "get_logs":
                    # Get recent logs
                    await manager.send_json({
                        "type": "logs_data",
                        "logs": [],  # Would get from audit logger
                        "timestamp": datetime.now().isoformat()
                    }, websocket)
                
                else:
                    # Echo back unknown message
                    await manager.send_json({
                        "type": "echo",
                        "original_message": message,
                        "timestamp": datetime.now().isoformat()
                    }, websocket)
                    
            except json.JSONDecodeError:
                await manager.send_json({
                    "type": "error",
                    "message": "Invalid JSON",
                    "timestamp": datetime.now().isoformat()
                }, websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logging.error(f"WebSocket logs error: {e}")
        manager.disconnect(websocket)


# Utility functions for broadcasting updates
async def broadcast_run_update(run_id: str, status: str, progress: float, message: str = None):
    """Broadcast run update to all run subscribers"""
    await manager.broadcast(json.dumps({
        "type": "run_update",
        "run_id": run_id,
        "status": status,
        "progress": progress,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }), "runs")


async def broadcast_host_update(host_name: str, status: str, message: str = None):
    """Broadcast host update to all host subscribers"""
    await manager.broadcast(json.dumps({
        "type": "host_update",
        "host_name": host_name,
        "status": status,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }), "hosts")


async def broadcast_log_entry(log_entry: Dict[str, Any]):
    """Broadcast log entry to all log subscribers"""
    await manager.broadcast(json.dumps({
        "type": "log_entry",
        "log": log_entry,
        "timestamp": datetime.now().isoformat()
    }), "logs")


async def broadcast_system_alert(alert_type: str, message: str, severity: str = "info"):
    """Broadcast system alert to all connections"""
    await manager.broadcast(json.dumps({
        "type": "system_alert",
        "alert_type": alert_type,
        "message": message,
        "severity": severity,
        "timestamp": datetime.now().isoformat()
    }))


# Background task for periodic updates
async def periodic_updates():
    """Send periodic updates to connected clients"""
    while True:
        try:
            # Send heartbeat to all connections
            await manager.broadcast(json.dumps({
                "type": "heartbeat",
                "timestamp": datetime.now().isoformat(),
                "connections": manager.get_connection_count()
            }))
            
            # Wait 30 seconds before next update
            await asyncio.sleep(30)
            
        except Exception as e:
            logging.error(f"Periodic update error: {e}")
            await asyncio.sleep(30)


# Periodic updates will be started when the FastAPI app starts
