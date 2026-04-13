from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import sys
import json
import asyncio
from typing import List

# Inject Root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

from src.core.meta_manager import MetaManager

# Setup App
app = FastAPI(title="AlphaEdge Holographic Gateway")

# The Singleton Meta-Manager (Brain)
meta = MetaManager()

# Connected WebSocket clients
connected_clients: List[WebSocket] = []

async def broadcast_to_all(message: str):
    """Push state updates to every connected holographic client."""
    dead = []
    for ws in connected_clients:
        try:
            await ws.send_text(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        connected_clients.remove(ws)

# Wire the Meta-Manager's broadcast function
meta.ws_broadcast = broadcast_to_all


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    connected_clients.append(ws)
    
    # Send initial state
    await ws.send_text(json.dumps({"state": "idle", "label": "Neural Link Established"}))
    
    try:
        while True:
            data = await ws.receive_text()
            payload = json.loads(data)
            
            if payload.get("type") == "voice_input":
                user_text = payload.get("text", "")
                if user_text.strip():
                    result = await meta.process(user_text)
                    await ws.send_text(json.dumps({
                        "state": "result",
                        "result": result
                    }))
    except WebSocketDisconnect:
        if ws in connected_clients:
            connected_clients.remove(ws)


# Serve Static Holographic UI
static_path = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")

@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(static_path, "index.html"))
