import json
import logging
from typing import List
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

class WebSocketConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Active clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Remaining clients: {len(self.active_connections)}")

    async def broadcast(self, event_type: str, payload: dict):
        message = {
            "event": event_type,
            "data": payload
        }
        json_msg = json.dumps(message, default=str)
        logger.info(f"Broadcasting event '{event_type}' to {len(self.active_connections)} clients")
        
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json_msg)
            except Exception as e:
                logger.warning(f"Error broadcasting to WS client: {e}")
                disconnected.append(connection)
                
        for conn in disconnected:
            self.disconnect(conn)

ws_manager = WebSocketConnectionManager()
