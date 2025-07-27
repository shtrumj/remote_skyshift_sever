"""
Shared components for Remote Agent Manager
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Set
from pydantic import BaseModel, Field
from enum import Enum
import uuid
import logging
import asyncio
from fastapi import HTTPException
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

# Manager instances
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Any] = {}
        self.task_results: Dict[str, dict] = {}
        self.recent_commands: Dict[str, str] = {}

    async def connect(self, websocket, agent_id: str):
        connection_id = f"{agent_id}_{uuid.uuid4()}"
        self.active_connections[connection_id] = {
            "websocket": websocket,
            "agent_id": agent_id,
            "connected_at": datetime.utcnow()
        }
        return connection_id

    def disconnect(self, connection_id: str):
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]

    async def send_command_to_agent(self, agent_id: str, command_data: dict):
        # Find the connection for this agent
        for connection_id, connection in self.active_connections.items():
            if connection["agent_id"] == agent_id:
                websocket = connection["websocket"]
                await websocket.send_text(json.dumps(command_data))
                return True
        return False

    def is_agent_connected(self, agent_id: str) -> bool:
        return any(conn["agent_id"] == agent_id for conn in self.active_connections.values())

    def store_task_result(self, task_id: str, result_data: dict):
        self.task_results[task_id] = result_data

    def get_task_result(self, task_id: str) -> Optional[dict]:
        return self.task_results.get(task_id)

class AgentManager:
    def __init__(self):
        self.db = db_manager
        self.heartbeat_timeout = timedelta(minutes=2)
        self.logger = logging.getLogger(__name__)
        
    async def register_agent(self, registration: AgentRegistration) -> str:
        # Check if agent with same hostname already exists
        existing_agent = self.db.get_agent_by_hostname(registration.hostname)
        if existing_agent:
            # Remove old registration
            self.db.delete_agent(existing_agent['agent_id'])
            self.logger.info(f"🗑️ Removed old registration for hostname: {registration.hostname}")
        
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
        self.logger.info(f"🔗 Agent registered in database: {registration.hostname} ({saved_agent_id})")
        return saved_agent_id
    
    async def update_heartbeat(self, agent_id: str, heartbeat: HeartbeatRequest):
        success = self.db.update_heartbeat(agent_id, heartbeat.status)
        if success:
            agent = self.db.get_agent(agent_id)
            if agent:
                self.logger.info(f"💓 Heartbeat from {agent['hostname']}")
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
                    self.logger.info(f"🔄 Marked {offline_count} agents as offline")
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                self.logger.error(f"❌ Error in cleanup_offline_agents: {e}")
                await asyncio.sleep(60)
    
    async def unregister_agent(self, agent_id: str) -> bool:
        return self.db.delete_agent(agent_id)
    
    async def send_command_to_agent(self, agent_id: str, command_request: CommandRequest):
        import json
        
        agent = self.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")

        if agent.status != "online":
            raise ValueError(f"Agent {agent_id} is offline")

        # Generate task ID
        task_id = str(uuid.uuid4())
        
        # Prepare command data
        command_data = {
            "type": "command",
            "task_id": task_id,
            "command": command_request.command,
            "shell_type": command_request.shell_type,
            "timeout": command_request.timeout,
            "working_directory": command_request.working_directory,
            "environment": command_request.environment
        }

        # Try to send via WebSocket first
        if manager.is_agent_connected(agent_id):
            success = await manager.send_command_to_agent(agent_id, command_data)
            if success:
                # Store recent command for this agent
                manager.recent_commands[agent_id] = task_id
                return {
                    "task_id": task_id,
                    "status": "accepted",
                    "message": "Command sent via WebSocket"
                }

        # Fallback to HTTP (if agent supports it)
        # For now, we'll return a pending status
        return {
            "task_id": task_id,
            "status": "pending",
            "message": "Command queued for HTTP agent"
        }

# Create global instances
manager = ConnectionManager()
agent_manager = AgentManager() 