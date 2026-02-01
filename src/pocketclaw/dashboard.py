"""PocketClaw Web Dashboard - API Server

Lightweight FastAPI server that serves the frontend and handles WebSocket communication.
"""

import asyncio
import base64
import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from pocketclaw.config import Settings
from pocketclaw.llm.router import LLMRouter
from pocketclaw.agents.router import AgentRouter

logger = logging.getLogger(__name__)

# Get frontend directory
FRONTEND_DIR = Path(__file__).parent / "frontend"

# Create FastAPI app
app = FastAPI(title="PocketClaw Dashboard")

# Allow CORS for WebSocket
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
async def index():
    """Serve the main dashboard page."""
    return FileResponse(FRONTEND_DIR / "index.html")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication."""
    await websocket.accept()
    
    # Send welcome notification (not chat message)
    await websocket.send_json({
        "type": "notification",
        "content": "👋 Connected to PocketClaw!"
    })
    
    # Load settings
    settings = Settings()
    
    # State
    agent_active = False
    llm_router: Optional[LLMRouter] = None
    agent_router: Optional[AgentRouter] = None
    
    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            
            # Handle tool requests
            if action == "tool":
                tool = data.get("tool")
                await handle_tool(websocket, tool, settings, data)
            
            # Handle agent toggle
            elif action == "toggle_agent":
                agent_active = data.get("active", False)
                
                if agent_active and not agent_router:
                    agent_router = AgentRouter(settings)
                
                await websocket.send_json({
                    "type": "notification",
                    "content": f"🧠 Agent Mode: {'ON' if agent_active else 'OFF'}"
                })
            
            # Handle chat
            elif action == "chat":
                message = data.get("message", "")
                
                if agent_active and agent_router:
                    # Stream agent responses
                    await websocket.send_json({"type": "stream_start"})
                    try:
                        async for chunk in agent_router.run(message):
                            await websocket.send_json(chunk)
                    finally:
                        await websocket.send_json({"type": "stream_end"})
                else:
                    # Simple LLM response
                    if not llm_router:
                        llm_router = LLMRouter(settings)
                    
                    await websocket.send_json({"type": "stream_start"})
                    try:
                        response = await llm_router.chat(message)
                        await websocket.send_json({
                            "type": "message",
                            "content": response
                        })
                    finally:
                        await websocket.send_json({"type": "stream_end"})
            
            # Handle settings update
            elif action == "settings":
                settings.agent_backend = data.get("agent_backend", settings.agent_backend)
                settings.llm_provider = data.get("llm_provider", settings.llm_provider)
                settings.save()
                
                # Reset routers to pick up new settings
                llm_router = None
                agent_router = None
                
                await websocket.send_json({
                    "type": "message",
                    "content": "⚙️ Settings updated"
                })
            
            # Handle API key save
            elif action == "save_api_key":
                provider = data.get("provider")
                key = data.get("key", "")
                
                if provider == "anthropic" and key:
                    settings.anthropic_api_key = key
                    settings.llm_provider = "anthropic"
                    settings.save()
                    llm_router = None
                    agent_router = None
                    await websocket.send_json({
                        "type": "message",
                        "content": "✅ Anthropic API key saved!"
                    })
                elif provider == "openai" and key:
                    settings.openai_api_key = key
                    settings.llm_provider = "openai"
                    settings.save()
                    llm_router = None
                    agent_router = None
                    await websocket.send_json({
                        "type": "message",
                        "content": "✅ OpenAI API key saved!"
                    })
                else:
                    await websocket.send_json({
                        "type": "error",
                        "content": "Invalid API key or provider"
                    })
            
            # Handle file navigation
            elif action == "navigate":
                path = data.get("path", "")
                await handle_file_navigation(websocket, path, settings)
    
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")


async def handle_tool(websocket: WebSocket, tool: str, settings: Settings, data: dict):
    """Handle tool execution."""
    
    if tool == "status":
        from pocketclaw.tools.status import get_system_status
        status = get_system_status()  # sync function
        await websocket.send_json({
            "type": "status",
            "content": status
        })
    
    elif tool == "screenshot":
        from pocketclaw.tools.screenshot import take_screenshot
        result = take_screenshot()  # sync function
        
        if isinstance(result, bytes):
            await websocket.send_json({
                "type": "screenshot",
                "image": base64.b64encode(result).decode()
            })
        else:
            await websocket.send_json({
                "type": "error",
                "content": result
            })
    
    elif tool == "fetch":
        from pocketclaw.tools.fetch import list_directory
        path = data.get("path") or str(Path.home())
        result = list_directory(path, settings.file_jail_path)  # sync function
        await websocket.send_json({
            "type": "message",
            "content": result
        })
    
    elif tool == "panic":
        await websocket.send_json({
            "type": "message",
            "content": "🛑 PANIC: All agent processes stopped!"
        })
        # TODO: Actually stop agent processes
    
    else:
        await websocket.send_json({
            "type": "error",
            "content": f"Unknown tool: {tool}"
        })


async def handle_file_navigation(websocket: WebSocket, path: str, settings: Settings):
    """Handle file browser navigation."""
    from pocketclaw.tools.fetch import list_directory
    
    result = list_directory(path, settings.file_jail_path)  # sync function
    await websocket.send_json({
        "type": "message",
        "content": result
    })


def run_dashboard(host: str = "127.0.0.1", port: int = 8888):
    """Run the dashboard server."""
    print("\n" + "=" * 50)
    print("🦀 POCKETCLAW WEB DASHBOARD")
    print("=" * 50)
    print(f"\n🌐 Open http://localhost:{port} in your browser\n")
    
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_dashboard()
