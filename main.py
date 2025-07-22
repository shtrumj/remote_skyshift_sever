from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
import asyncio
import httpx
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field
import uuid
import json
import logging
import sys
from contextlib import asynccontextmanager
from enum import Enum
from starlette.middleware.base import BaseHTTPMiddleware
from database import db_manager

# Models
class ShellType(str, Enum):
    cmd = "cmd"
    powershell = "powershell"
    bash = "bash"

class AgentRegistration(BaseModel):
    hostname: str
    ip_address: str
    port: int
    capabilities: List[str]
    version: str

class RegisteredAgent(BaseModel):
    agent_id: str
    hostname: str
    ip_address: str
    port: int
    capabilities: List[str]
    version: str
    registered_at: datetime
    last_heartbeat: datetime
    status: str = "online"

class HeartbeatRequest(BaseModel):
    agent_id: str
    status: str = "online"

class CommandRequest(BaseModel):
    command: str
    args: Optional[List[str]] = None
    shell_type: ShellType = ShellType.bash
    timeout: Optional[int] = 30
    working_directory: Optional[str] = None
    environment: Optional[Dict[str, str]] = None

class CommandResponse(BaseModel):
    task_id: str
    status: str
    message: str

class TaskStatus(BaseModel):
    id: str
    status: str
    command: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    exit_code: Optional[int] = None
    output: Optional[str] = None
    error: Optional[str] = None
    logs: List[str] = []

class CustomerRegistration(BaseModel):
    name: str
    address: Optional[str] = None

class CustomerResponse(BaseModel):
    uuid: str
    name: str
    address: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class AgentCommandRequest(BaseModel):
    agent_id: str
    command_request: CommandRequest

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

# Agent Manager (Updated to use SQLite database)
class AgentManager:
    def __init__(self):
        self.db = db_manager
        self.heartbeat_timeout = timedelta(minutes=2)
        
    async def register_agent(self, registration: AgentRegistration) -> str:
        # Check if agent with same hostname already exists
        existing_agent = self.db.get_agent_by_hostname(registration.hostname)
        if existing_agent:
            # Remove old registration
            self.db.delete_agent(existing_agent['agent_id'])
            logger.info(f"🗑️ Removed old registration for hostname: {registration.hostname}")
        
        agent_id = str(uuid.uuid4())
        
        # Prepare agent data for database
        agent_data = {
            "id": str(uuid.uuid4()),
            "agent_id": agent_id,
            "hostname": registration.hostname,
            "ip_address": registration.ip_address,
            "port": registration.port,
            "capabilities": registration.capabilities,
            "version": registration.version
        }
        
        # Save to database
        saved_agent_id = self.db.register_agent(agent_data)
        logger.info(f"🔗 Agent registered in database: {registration.hostname} ({saved_agent_id})")
        return saved_agent_id
    
    async def update_heartbeat(self, agent_id: str, heartbeat: HeartbeatRequest):
        success = self.db.update_heartbeat(agent_id, heartbeat.status)
        if success:
            agent = self.db.get_agent(agent_id)
            if agent:
                logger.info(f"💓 Heartbeat from {agent['hostname']}")
        else:
            raise HTTPException(status_code=404, detail="Agent not found")
    
    def get_agent(self, agent_id: str) -> Optional[RegisteredAgent]:
        agent_data = self.db.get_agent(agent_id)
        if agent_data:
            return RegisteredAgent(**agent_data)
        return None
    
    def get_all_agents(self) -> List[RegisteredAgent]:
        agents_data = self.db.get_all_agents()
        return [RegisteredAgent(**agent_data) for agent_data in agents_data]
    
    def get_online_agents(self) -> List[RegisteredAgent]:
        agents_data = self.db.get_online_agents()
        return [RegisteredAgent(**agent_data) for agent_data in agents_data]
    
    async def cleanup_offline_agents(self):
        """Background task to mark agents as offline if they haven't sent heartbeat"""
        while True:
            try:
                offline_count = self.db.cleanup_offline_agents()
                if offline_count > 0:
                    logger.info(f"❌ Marked {offline_count} agents as offline")
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
            await asyncio.sleep(30)  # Check every 30 seconds
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent by ID"""
        return self.db.delete_agent(agent_id)

# Initialize agent manager
agent_manager = AgentManager()

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

# Dashboard endpoint
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

# Customers endpoint
@app.get("/customers", response_class=HTMLResponse)
async def customers_page(request: Request):
    """Customers management page"""
    return templates.TemplateResponse("customers.html", {"request": request})

# API root endpoint
@app.get("/api")
def api_root():
    return {"message": "Remote Agent Manager API", "version": "1.0.0"}

# Legacy endpoint for compatibility
@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}

# Agent management endpoints
@app.post("/api/agents/register")
async def register_agent(request: Request, registration: AgentRegistration):
    """Register a new agent"""
    client_ip = request.client.host if request.client else "unknown"
    logger.info(f"🔗 Agent registration request from {client_ip}: {registration.hostname}")
    try:
        agent_id = await agent_manager.register_agent(registration)
        logger.info(f"✅ Agent registered successfully: {registration.hostname} -> {agent_id}")
        return {"agent_id": agent_id, "message": "Agent registered successfully"}
    except Exception as e:
        logger.error(f"❌ Agent registration failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.post("/api/agents/{agent_id}/heartbeat")
async def agent_heartbeat(request: Request, agent_id: str, heartbeat: HeartbeatRequest):
    """Receive heartbeat from an agent"""
    client_ip = request.client.host if request.client else "unknown"
    logger.debug(f"💓 Heartbeat from {client_ip} for agent {agent_id}")
    try:
        await agent_manager.update_heartbeat(agent_id, heartbeat)
        return {"message": "Heartbeat received"}
    except Exception as e:
        logger.error(f"❌ Heartbeat failed for agent {agent_id}: {str(e)}")
        raise

@app.get("/api/agents")
async def list_agents():
    """List all registered agents"""
    agents = agent_manager.get_all_agents()
    online_count = len(agent_manager.get_online_agents())
    
    return {
        "agents": agents,
        "total": len(agents),
        "online": online_count,
        "offline": len(agents) - online_count
    }

@app.get("/api/agents/online")
async def list_online_agents():
    """List only online agents"""
    agents = agent_manager.get_online_agents()
    return {
        "agents": agents,
        "count": len(agents)
    }

@app.get("/api/agents/{agent_id}")
async def get_agent_status(agent_id: str):
    """Get specific agent status"""
    agent = agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@app.delete("/api/agents/{agent_id}")
async def unregister_agent(agent_id: str):
    """Unregister/delete an agent"""
    logger.info(f"🗑️ Attempting to unregister agent: {agent_id}")
    success = await agent_manager.unregister_agent(agent_id)
    if success:
        logger.info(f"🗑️ Agent unregistered: {agent_id}")
        return {"message": "Agent unregistered successfully"}
    else:
        logger.error(f"❌ Failed to unregister agent: {agent_id}")
        raise HTTPException(status_code=404, detail="Agent not found")

# Customer management endpoints
@app.post("/api/customers")
async def create_customer(customer: CustomerRegistration):
    """Create a new customer"""
    try:
        customer_data = {
            "id": str(uuid.uuid4()),
            "uuid": str(uuid.uuid4()),
            "name": customer.name,
            "address": customer.address
        }
        
        customer_uuid = db_manager.create_customer(customer_data)
        logger.info(f"👤 Customer created: {customer.name} ({customer_uuid})")
        
        return {"uuid": customer_uuid, "message": "Customer created successfully"}
    except Exception as e:
        logger.error(f"❌ Customer creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Customer creation failed: {str(e)}")

@app.get("/api/customers")
async def list_customers():
    """List all customers"""
    try:
        customers = db_manager.get_all_customers()
        return {"customers": customers, "total": len(customers)}
    except Exception as e:
        logger.error(f"❌ Failed to list customers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list customers: {str(e)}")

@app.get("/api/customers/{customer_uuid}")
async def get_customer(customer_uuid: str):
    """Get specific customer"""
    customer = db_manager.get_customer(customer_uuid)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

@app.put("/api/customers/{customer_uuid}")
async def update_customer(customer_uuid: str, customer: CustomerRegistration):
    """Update customer information"""
    try:
        updates = {"name": customer.name}
        if customer.address is not None:
            updates["address"] = customer.address
        
        success = db_manager.update_customer(customer_uuid, updates)
        if success:
            logger.info(f"👤 Customer updated: {customer.name} ({customer_uuid})")
            return {"message": "Customer updated successfully"}
        else:
            raise HTTPException(status_code=404, detail="Customer not found")
    except Exception as e:
        logger.error(f"❌ Customer update failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Customer update failed: {str(e)}")

@app.delete("/api/customers/{customer_uuid}")
async def delete_customer(customer_uuid: str):
    """Delete a customer"""
    try:
        success = db_manager.delete_customer(customer_uuid)
        if success:
            logger.info(f"🗑️ Customer deleted: {customer_uuid}")
            return {"message": "Customer deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Customer not found")
    except Exception as e:
        logger.error(f"❌ Customer deletion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Customer deletion failed: {str(e)}")

# Command execution endpoints
@app.post("/api/agents/{agent_id}/commands")
async def send_command_to_agent(agent_id: str, command_request: CommandRequest):
    """Send a command to a specific agent"""
    agent = agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    if agent.status != "online":
        raise HTTPException(status_code=400, detail="Agent is offline")
    
    # Forward command to agent
    agent_url = f"http://{agent.ip_address}:{agent.port}/api/commands"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(agent_url, json=command_request.model_dump())
            
        if response.status_code == 202:  # Accepted
            result = response.json()
            print(f"📤 Command sent to {agent.hostname}: {command_request.command}")
            return result
        else:
            raise HTTPException(status_code=response.status_code, detail=f"Agent returned error: {response.text}")
            
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Failed to connect to agent: {str(e)}")

@app.get("/api/agents/{agent_id}/tasks")
async def get_agent_tasks(agent_id: str):
    """Get all tasks from a specific agent"""
    agent = agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    if agent.status != "online":
        raise HTTPException(status_code=400, detail="Agent is offline")
    
    agent_url = f"http://{agent.ip_address}:{agent.port}/api/tasks"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(agent_url)
            
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=f"Agent returned error: {response.text}")
            
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Failed to connect to agent: {str(e)}")

@app.get("/api/agents/{agent_id}/tasks/{task_id}")
async def get_agent_task_status(agent_id: str, task_id: str):
    """Get specific task status from an agent"""
    agent = agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    if agent.status != "online":
        raise HTTPException(status_code=400, detail="Agent is offline")
    
    agent_url = f"http://{agent.ip_address}:{agent.port}/api/tasks/{task_id}"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(agent_url)
            
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=f"Agent returned error: {response.text}")
            
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Failed to connect to agent: {str(e)}")

@app.post("/api/agents/{agent_id}/tasks/{task_id}/cancel")
async def cancel_agent_task(agent_id: str, task_id: str):
    """Cancel a specific task on an agent"""
    agent = agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    if agent.status != "online":
        raise HTTPException(status_code=400, detail="Agent is offline")
    
    agent_url = f"http://{agent.ip_address}:{agent.port}/api/tasks/{task_id}/cancel"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(agent_url)
            
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=f"Agent returned error: {response.text}")
            
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Failed to connect to agent: {str(e)}")

# Broadcast command to multiple agents
@app.post("/api/commands/broadcast")
async def broadcast_command(command_request: CommandRequest, agent_ids: Optional[List[str]] = None):
    """Broadcast a command to all online agents or specific agents"""
    if agent_ids:
        agents = [agent_manager.get_agent(aid) for aid in agent_ids]
        agents = [a for a in agents if a and a.status == "online"]
    else:
        agents = agent_manager.get_online_agents()
    
    if not agents:
        raise HTTPException(status_code=400, detail="No online agents available")
    
    results = []
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for agent in agents:
            agent_url = f"http://{agent.ip_address}:{agent.port}/api/commands"
            try:
                response = await client.post(agent_url, json=command_request.model_dump())
                if response.status_code == 202:
                    result = response.json()
                    results.append({
                        "agent_id": agent.agent_id,
                        "hostname": agent.hostname,
                        "success": True,
                        "task_id": result.get("task_id"),
                        "message": result.get("message")
                    })
                else:
                    results.append({
                        "agent_id": agent.agent_id,
                        "hostname": agent.hostname,
                        "success": False,
                        "error": f"Status {response.status_code}: {response.text}"
                    })
            except httpx.RequestError as e:
                results.append({
                    "agent_id": agent.agent_id,
                    "hostname": agent.hostname,
                    "success": False,
                    "error": f"Connection failed: {str(e)}"
                })
    
    successful = len([r for r in results if r["success"]])
    print(f"📡 Broadcast command to {len(agents)} agents, {successful} successful")
    
    return {
        "command": command_request.command,
        "total_agents": len(agents),
        "successful": successful,
        "results": results
    }

# Debug endpoints
@app.api_route("/debug/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def debug_catch_all(request: Request, path: str):
    """Catch-all endpoint to debug invalid requests"""
    client_ip = request.client.host if request.client else "unknown"
    method = request.method
    url = str(request.url)
    headers = dict(request.headers)
    
    logger.warning(f"🔍 Debug endpoint hit: {method} {url} from {client_ip}")
    logger.warning(f"Path: {path}")
    logger.warning(f"Headers: {headers}")
    
    try:
        body = await request.body()
        if body:
            logger.warning(f"Body: {body.decode('utf-8', errors='ignore')}")
    except Exception as e:
        logger.warning(f"Could not read body: {e}")
    
    return {
        "debug": True,
        "method": method,
        "path": path,
        "url": str(request.url),
        "client_ip": client_ip,
        "headers": headers,
        "message": f"This is a debug endpoint. Request details logged."
    }

# Health check
@app.get("/health")
async def health_check():
    online_agents = len(agent_manager.get_online_agents())
    total_agents = len(agent_manager.get_all_agents())
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "agents": {
            "total": total_agents,
            "online": online_agents,
            "offline": total_agents - online_agents
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=4433)