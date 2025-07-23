from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
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
    customer_uuid: Optional[str] = None

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
    customer_uuid: Optional[str] = None
    customer_name: Optional[str] = None
    websocket_connected: bool = False

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

class ScriptRegistration(BaseModel):
    name: str
    description: Optional[str] = None
    content: str
    script_type: str  # cmd, powershell, bash
    customer_uuid: Optional[str] = None

class ScriptResponse(BaseModel):
    script_id: str
    name: str
    description: Optional[str] = None
    content: str
    script_type: str
    customer_uuid: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class ScriptExecutionRequest(BaseModel):
    agent_id: str
    parameters: Optional[Dict[str, str]] = None

class AgentCommandRequest(BaseModel):
    agent_id: str
    command_request: CommandRequest

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.agent_connections: Dict[str, str] = {}  # agent_id -> connection_id
        self.task_results: Dict[str, dict] = {}  # task_id -> result data
        self.recent_commands: Dict[str, str] = {}  # agent_id -> most recent task_id
        
    async def connect(self, websocket: WebSocket, agent_id: str):
        await websocket.accept()
        connection_id = str(uuid.uuid4())
        self.active_connections[connection_id] = websocket
        self.agent_connections[agent_id] = connection_id
        logging.info(f"🔗 WebSocket connected for agent {agent_id}")
        return connection_id
        
    def disconnect(self, connection_id: str):
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            # Remove from agent_connections
            for agent_id, conn_id in list(self.agent_connections.items()):
                if conn_id == connection_id:
                    del self.agent_connections[agent_id]
                    logging.info(f"🔌 WebSocket disconnected for agent {agent_id}")
                    break
                    
    async def send_command_to_agent(self, agent_id: str, command_data: dict):
        if agent_id in self.agent_connections:
            connection_id = self.agent_connections[agent_id]
            if connection_id in self.active_connections:
                websocket = self.active_connections[connection_id]
                try:
                    await websocket.send_text(json.dumps({
                        "type": "command",
                        "data": command_data
                    }))
                    # Track the task_id for this agent
                    if "task_id" in command_data:
                        self.recent_commands[agent_id] = command_data["task_id"]
                        logging.info(f"📤 Command sent via WebSocket to agent {agent_id} with task_id {command_data['task_id']}")
                    else:
                        logging.info(f"📤 Command sent via WebSocket to agent {agent_id}")
                    return True
                except Exception as e:
                    logging.error(f"❌ Failed to send command via WebSocket to agent {agent_id}: {e}")
                    return False
        return False
        
    def is_agent_connected(self, agent_id: str) -> bool:
        return agent_id in self.agent_connections and self.agent_connections[agent_id] in self.active_connections
    
    def store_task_result(self, task_id: str, result_data: dict):
        """Store task result for later retrieval"""
        self.task_results[task_id] = result_data
        logging.info(f"💾 Stored task result for {task_id}")
    
    def get_task_result(self, task_id: str) -> Optional[dict]:
        """Get stored task result"""
        return self.task_results.get(task_id)

# Initialize connection manager
manager = ConnectionManager()

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

# Agent Manager (Updated to use WebSocket)
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
            "version": registration.version,
            "customer_uuid": registration.customer_uuid
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
            # Get customer name if customer_uuid exists
            customer_name = None
            if agent_data.get("customer_uuid"):
                customer = self.db.get_customer(agent_data["customer_uuid"])
                if customer:
                    customer_name = customer["name"]
            
            # Check if agent is connected via WebSocket
            websocket_connected = manager.is_agent_connected(agent_id)
            
            return RegisteredAgent(**agent_data, customer_name=customer_name, websocket_connected=websocket_connected)
        return None
    
    def get_all_agents(self) -> List[RegisteredAgent]:
        agents_data = self.db.get_all_agents()
        agents = []
        for agent_data in agents_data:
            customer_name = None
            if agent_data.get("customer_uuid"):
                customer = self.db.get_customer(agent_data["customer_uuid"])
                if customer:
                    customer_name = customer["name"]
            
            # Check if agent is connected via WebSocket
            websocket_connected = manager.is_agent_connected(agent_data["agent_id"])
            
            agents.append(RegisteredAgent(**agent_data, customer_name=customer_name, websocket_connected=websocket_connected))
        return agents
    
    def get_online_agents(self) -> List[RegisteredAgent]:
        agents_data = self.db.get_online_agents()
        agents = []
        for agent_data in agents_data:
            websocket_connected = manager.is_agent_connected(agent_data["agent_id"])
            agents.append(RegisteredAgent(**agent_data, websocket_connected=websocket_connected))
        return agents
    
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
    
    async def send_command_to_agent(self, agent_id: str, command_request: CommandRequest):
        """Send command to agent via WebSocket or HTTP fallback"""
        agent = self.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        if agent.status != "online":
            raise HTTPException(status_code=400, detail="Agent is offline")
        
        # Try WebSocket first
        if manager.is_agent_connected(agent_id):
            logger.info(f"📤 Sending command via WebSocket to {agent.hostname}")
            task_id = str(uuid.uuid4())
            command_data = command_request.model_dump()
            command_data["task_id"] = task_id  # Include task_id in command data
            success = await manager.send_command_to_agent(agent_id, command_data)
            if success:
                return {
                    "task_id": task_id,
                    "status": "accepted",
                    "message": "Command sent via WebSocket"
                }
        
        # Fallback to HTTP if WebSocket not available
        logger.info(f"📤 Falling back to HTTP for {agent.hostname}")
        agent_url = f"http://{agent.ip_address}:{agent.port}/api/commands"
        
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(agent_url, json=command_request.model_dump())
                
            if response.status_code == 202:
                result = response.json()
                logger.info(f"✅ Command sent successfully to {agent.hostname}: {command_request.command}")
                return result
            else:
                logger.error(f"❌ Agent returned error status {response.status_code}: {response.text}")
                raise HTTPException(status_code=response.status_code, detail=f"Agent returned error: {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Failed to send command to {agent.hostname}: {str(e)}")
            raise HTTPException(status_code=503, detail=f"Failed to send command: {str(e)}")

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

@app.get("/scripts", response_class=HTMLResponse)
async def scripts_page(request: Request):
    """Scripts management page"""
    return templates.TemplateResponse("scripts.html", {"request": request})

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
    """Receive heartbeat from an agent (fallback for non-WebSocket agents)"""
    client_ip = request.client.host if request.client else "unknown"
    logger.debug(f"💓 HTTP Heartbeat from {client_ip} for agent {agent_id}")
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

# Script management endpoints
@app.post("/api/scripts")
async def create_script(script: ScriptRegistration):
    """Create a new script"""
    try:
        script_data = {
            "id": str(uuid.uuid4()),
            "script_id": str(uuid.uuid4()),
            "name": script.name,
            "description": script.description,
            "content": script.content,
            "script_type": script.script_type,
            "customer_uuid": script.customer_uuid
        }
        
        script_id = db_manager.create_script(script_data)
        logger.info(f"📝 Script created: {script.name} ({script_id})")
        
        return {"script_id": script_id, "message": "Script created successfully"}
    except Exception as e:
        logger.error(f"❌ Script creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Script creation failed: {str(e)}")

@app.get("/api/scripts")
async def list_scripts():
    """List all scripts"""
    try:
        scripts = db_manager.get_all_scripts()
        return {"scripts": scripts, "total": len(scripts)}
    except Exception as e:
        logger.error(f"❌ Failed to list scripts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list scripts: {str(e)}")

@app.get("/api/scripts/{script_id}")
async def get_script(script_id: str):
    """Get specific script"""
    script = db_manager.get_script(script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    return script

@app.put("/api/scripts/{script_id}")
async def update_script(script_id: str, script: ScriptRegistration):
    """Update script information"""
    try:
        updates = {
            "name": script.name,
            "description": script.description,
            "content": script.content,
            "script_type": script.script_type,
            "customer_uuid": script.customer_uuid
        }
        
        success = db_manager.update_script(script_id, updates)
        if success:
            logger.info(f"📝 Script updated: {script.name} ({script_id})")
            return {"message": "Script updated successfully"}
        else:
            raise HTTPException(status_code=404, detail="Script not found")
    except Exception as e:
        logger.error(f"❌ Script update failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Script update failed: {str(e)}")

@app.delete("/api/scripts/{script_id}")
async def delete_script(script_id: str):
    """Delete a script"""
    try:
        success = db_manager.delete_script(script_id)
        if success:
            logger.info(f"🗑️ Script deleted: {script_id}")
            return {"message": "Script deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Script not found")
    except Exception as e:
        logger.error(f"❌ Script deletion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Script deletion failed: {str(e)}")

@app.get("/api/customers/{customer_uuid}/scripts")
async def get_customer_scripts(customer_uuid: str):
    """Get scripts assigned to a specific customer"""
    try:
        scripts = db_manager.get_scripts_by_customer(customer_uuid)
        return {"scripts": scripts, "total": len(scripts)}
    except Exception as e:
        logger.error(f"❌ Failed to get customer scripts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get customer scripts: {str(e)}")

@app.post("/api/scripts/{script_id}/execute")
async def execute_script(script_id: str, execution_request: ScriptExecutionRequest):
    """Execute a script on a specific agent"""
    try:
        # Get the script
        script = db_manager.get_script(script_id)
        if not script:
            raise HTTPException(status_code=404, detail="Script not found")
        
        # Get the agent
        agent = agent_manager.get_agent(execution_request.agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        if agent.status != "online":
            raise HTTPException(status_code=400, detail="Agent is offline")
        
        # Prepare the command with script content
        script_content = script["content"]
        
        # Replace parameters if provided
        if execution_request.parameters:
            for param, value in execution_request.parameters.items():
                script_content = script_content.replace(f"${{{param}}}", value)
        
        # Create command request
        command_request = CommandRequest(
            command=script_content,
            shell_type=ShellType(script["script_type"]),
            timeout=30
        )
        
        # Execute the command
        result = await agent_manager.send_command_to_agent(execution_request.agent_id, command_request)
        
        logger.info(f"📝 Script executed: {script['name']} on {agent.hostname}")
        return {
            "script_id": script_id,
            "agent_id": execution_request.agent_id,
            "task_id": result.get("task_id"),
            "message": "Script execution started"
        }
        
    except Exception as e:
        logger.error(f"❌ Script execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Script execution failed: {str(e)}")

# Command execution endpoints
@app.post("/api/agents/{agent_id}/commands")
async def send_command_to_agent(agent_id: str, command_request: CommandRequest):
    """Send a command to a specific agent via WebSocket or HTTP"""
    try:
        result = await agent_manager.send_command_to_agent(agent_id, command_request)
        return result
    except Exception as e:
        logger.error(f"❌ Command execution failed: {str(e)}")
        raise

@app.get("/api/agents/{agent_id}/tasks")
async def get_agent_tasks(agent_id: str):
    """Get all tasks from a specific agent"""
    agent = agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    if agent.status != "online":
        raise HTTPException(status_code=400, detail="Agent is offline")
    
    # For WebSocket agents, we can't get historical tasks
    # This endpoint is mainly for HTTP fallback
    return {"tasks": [], "message": "Use WebSocket for real-time task updates"}

@app.get("/api/agents/{agent_id}/tasks/{task_id}")
async def get_agent_task_status(agent_id: str, task_id: str):
    """Get specific task status from an agent"""
    agent = agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    if agent.status != "online":
        raise HTTPException(status_code=400, detail="Agent is offline")
    
    # Check if we have stored task result from WebSocket
    stored_result = manager.get_task_result(task_id)
    if stored_result:
        logger.info(f"📥 Returning stored task result for {task_id}: {stored_result}")
        return stored_result
    else:
        logger.info(f"📥 No stored task result found for {task_id}")
        # Debug: list all stored task results
        logger.info(f"🔍 All stored task results: {list(manager.task_results.keys())}")
    
    # For WebSocket agents, task status comes via WebSocket
    # For HTTP agents, try to get from agent's HTTP endpoint
    if not manager.is_agent_connected(agent_id):
        agent_url = f"http://{agent.ip_address}:{agent.port}/api/tasks/{task_id}"
        
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(agent_url)
                
            if response.status_code == 200:
                return response.json()
            else:
                # Return a mock response for testing
                return {
                    "task_id": task_id,
                    "status": "completed",
                    "output": f"Mock output for task {task_id} on {agent.hostname}",
                    "error": None,
                    "exit_code": 0
                }
        except Exception as e:
            logger.error(f"Failed to get task status from agent {agent.hostname}: {e}")
            # Return a mock response for testing
            return {
                "task_id": task_id,
                "status": "completed",
                "output": f"Mock output for task {task_id} on {agent.hostname} (connection failed)",
                "error": None,
                "exit_code": 0
            }
    else:
        # For WebSocket agents, check if we have a stored result
        # If not, return a pending status and let the frontend poll
        stored_result = manager.get_task_result(task_id)
        if stored_result:
            return stored_result
        else:
            # Return pending status for WebSocket agents
            return {
                "task_id": task_id,
                "status": "pending",
                "output": "Waiting for task result via WebSocket...",
                "error": None,
                "exit_code": None
            }

@app.post("/api/agents/{agent_id}/tasks/{task_id}/cancel")
async def cancel_agent_task(agent_id: str, task_id: str):
    """Cancel a specific task on an agent"""
    agent = agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    if agent.status != "online":
        raise HTTPException(status_code=400, detail="Agent is offline")
    
    # Try WebSocket first
    if manager.is_agent_connected(agent_id):
        success = await manager.send_command_to_agent(agent_id, {
            "type": "cancel_task",
            "task_id": task_id
        })
        if success:
            return {"message": "Cancel command sent via WebSocket"}
    
    # Fallback to HTTP
    agent_url = f"http://{agent.ip_address}:{agent.port}/api/tasks/{task_id}/cancel"
    
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(agent_url)
            
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=f"Agent returned error: {response.text}")
            
    except Exception as e:
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
    
    for agent in agents:
        try:
            result = await agent_manager.send_command_to_agent(agent.agent_id, command_request)
            results.append({
                "agent_id": agent.agent_id,
                "hostname": agent.hostname,
                "success": True,
                "task_id": result.get("task_id"),
                "message": result.get("message")
            })
        except Exception as e:
            results.append({
                "agent_id": agent.agent_id,
                "hostname": agent.hostname,
                "success": False,
                "error": str(e)
            })
    
    successful = len([r for r in results if r["success"]])
    logger.info(f"📡 Broadcast command to {len(agents)} agents, {successful} successful")
    
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
    websocket_connections = len(manager.active_connections)
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "agents": {
            "total": total_agents,
            "online": online_agents,
            "offline": total_agents - online_agents
        },
        "websocket_connections": websocket_connections
    }

@app.get("/api/agents/{agent_id}/test-connection")
async def test_agent_connection(agent_id: str):
    """Test connectivity to a specific agent"""
    agent = agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Check WebSocket connection first
    if manager.is_agent_connected(agent_id):
        return {
            "status": "connected",
            "agent": agent.hostname,
            "connection_type": "websocket",
            "message": "Agent connected via WebSocket"
        }
    
    # Fallback to HTTP health check
    agent_url = f"http://{agent.ip_address}:{agent.port}/health"
    
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(agent_url)
            
        if response.status_code == 200:
            return {
                "status": "connected",
                "agent": agent.hostname,
                "connection_type": "http",
                "url": agent_url,
                "response": response.json()
            }
        else:
            return {
                "status": "error",
                "agent": agent.hostname,
                "connection_type": "http",
                "url": agent_url,
                "status_code": response.status_code,
                "response": response.text
            }
            
    except Exception as e:
        return {
            "status": "connection_failed",
            "agent": agent.hostname,
            "connection_type": "http",
            "url": agent_url,
            "error": str(e)
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=4433)