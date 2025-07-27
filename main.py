from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
import uvicorn
import asyncio
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Set
from pydantic import BaseModel, Field
import uuid
import logging
import sys
from contextlib import asynccontextmanager
from enum import Enum
from starlette.middleware.base import BaseHTTPMiddleware
from database import db_manager

# Import shared components
from shared import manager, agent_manager, ShellType, AgentRegistration, RegisteredAgent, HeartbeatRequest, CommandRequest, CommandResponse, TaskStatus, CustomerRegistration, CustomerResponse, ScriptRegistration, ScriptResponse, ScriptExecutionRequest

# Import routes
from routes import ui, api

# Initialize connection manager (imported from shared)
manager = manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Request logging middleware
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Log incoming request details
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        url = str(request.url)
        headers = dict(request.headers)
        
        logger.info(f"📥 Incoming request: {method} {url} from {client_ip}")
        logger.debug(f"Headers: {headers}")
        
        try:
            # Process the request
            response = await call_next(request)
            logger.info(f"📤 Response: {response.status_code} for {method} {url}")
            return response
        except Exception as e:
            logger.error(f"❌ Error processing request {method} {url}: {str(e)}")
            logger.error(f"Client IP: {client_ip}")
            logger.error(f"Headers: {headers}")
            raise

# Initialize agent manager (imported from shared)
agent_manager = agent_manager

# Lifespan handler (replaces deprecated on_event)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Remote Agent Manager starting up...")
    # Start background task to cleanup offline agents
    cleanup_task = asyncio.create_task(agent_manager.cleanup_offline_agents())
    logger.info("🚀 Remote Agent Manager started")
    yield
    # Shutdown
    logger.info("🛑 Remote Agent Manager shutting down...")
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    logger.info("🛑 Remote Agent Manager shutdown complete")

# Initialize FastAPI app
app = FastAPI(
    title="Remote Agent Manager", 
    version="1.0.0",
    lifespan=lifespan
)

# Setup templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    client_ip = request.client.host if request.client else "unknown"
    logger.error(f"🚨 Validation error from {client_ip}: {request.method} {request.url}")
    logger.error(f"Validation errors: {exc.errors()}")
    logger.error(f"Body: {exc.body}")
    return Response(
        content=f"Validation error: {str(exc)}",
        status_code=422,
        media_type="text/plain"
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    client_ip = request.client.host if request.client else "unknown"
    logger.error(f"🚨 Unhandled exception from {client_ip}: {request.method} {request.url}")
    logger.error(f"Exception: {str(exc)}")
    logger.error(f"Exception type: {type(exc)}")
    return Response(
        content=f"Internal server error: {str(exc)}",
        status_code=500,
        media_type="text/plain"
    )

# WebSocket endpoint for agent connections
@app.websocket("/ws/agent/{agent_id}")
async def websocket_endpoint(websocket: WebSocket, agent_id: str):
    connection_id = await manager.connect(websocket, agent_id)
    try:
        while True:
            # Receive messages from agent
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "heartbeat":
                # Update heartbeat
                heartbeat = HeartbeatRequest(agent_id=agent_id, status="online")
                await agent_manager.update_heartbeat(agent_id, heartbeat)
                # Send acknowledgment
                await websocket.send_text(json.dumps({
                    "type": "heartbeat_ack",
                    "timestamp": datetime.utcnow().isoformat()
                }))
                
            elif message.get("type") == "task_result":
                # Handle task result from agent
                logger.info(f"📥 Task result from {agent_id}: {message.get('data', {})}")
                # Store the task result for later retrieval
                if "data" in message and "task_id" in message["data"]:
                    task_id = message["data"]["task_id"]
                    logger.info(f"💾 Storing task result for {task_id}")
                    manager.store_task_result(task_id, message["data"])
                    logger.info(f"💾 Stored task result. All stored results: {list(manager.task_results.keys())}")
                else:
                    logger.warning(f"⚠️ Task result missing task_id: {message}")
                    # Try to find the most recent command sent to this agent
                    # This is a fallback for clients that don't include task_id in response
                    logger.info(f"🔍 Attempting to match task result to recent command for agent {agent_id}")
                    if agent_id in manager.recent_commands:
                        fallback_task_id = manager.recent_commands[agent_id]
                        logger.info(f"💾 Storing task result with tracked task_id: {fallback_task_id}")
                        manager.store_task_result(fallback_task_id, message["data"])
                    else:
                        # For now, we'll store it with a generated task_id
                        fallback_task_id = f"fallback-{agent_id}-{int(datetime.utcnow().timestamp())}"
                        logger.info(f"💾 Storing task result with fallback task_id: {fallback_task_id}")
                        manager.store_task_result(fallback_task_id, message["data"])
                
            elif message.get("type") == "task_status":
                # Handle task status update
                logger.info(f"📥 Task status from {agent_id}: {message.get('data', {})}")
                # Store the task status for later retrieval
                if "data" in message and "task_id" in message["data"]:
                    manager.store_task_result(message["data"]["task_id"], message["data"])
                
    except WebSocketDisconnect:
        manager.disconnect(connection_id)
    except Exception as e:
        logger.error(f"❌ WebSocket error for agent {agent_id}: {e}")
        manager.disconnect(connection_id)

# Root redirect to UI
@app.get("/", response_class=HTMLResponse)
async def root_redirect():
    """Redirect root to UI dashboard"""
    return RedirectResponse(url="/ui/dashboard", status_code=302)

# API root endpoint
@app.get("/api")
def api_root():
    return {"message": "Remote Agent Manager API", "version": "1.0.0"}

# Legacy endpoint for compatibility
@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}

# Include routes
app.include_router(ui.router)
app.include_router(api.router)

if __name__ == "__main__":
    import sys
    import ssl
    from pathlib import Path
    
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--https":
        # HTTPS mode on port 4434
        cert_file = Path("CertificateConfiguration/certs/server.crt")
        key_file = Path("CertificateConfiguration/certs/server.key")
        
        if not cert_file.exists() or not key_file.exists():
            logger.error("❌ SSL certificates not found!")
            logger.error("Please run: python generate_certificates.py")
            sys.exit(1)
        
        logger.info("🔒 Starting HTTPS server on port 4434...")
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=4434,
            ssl_certfile=str(cert_file),
            ssl_keyfile=str(key_file)
        )
    else:
        # HTTP mode on port 4433 (default)
        logger.info("📡 Starting HTTP server on port 4433...")
        uvicorn.run(app, host="0.0.0.0", port=4433)