"""
SQLite Database Module for Agent Registration
"""

import json

# Database setup
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Get the project root directory (parent of Scripts)
project_root = Path(__file__).parent.parent
data_dir = project_root / "Data"
data_dir.mkdir(exist_ok=True)  # Ensure Data directory exists

DATABASE_URL = f"sqlite:///{data_dir}/agents.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Agent(Base):
    """Agent registration model"""

    __tablename__ = "agents"

    id = Column(String, primary_key=True, index=True)
    agent_id = Column(String, unique=True, index=True)
    hostname = Column(String, index=True)
    ip_address = Column(String)
    port = Column(Integer)
    capabilities = Column(Text)  # JSON string
    version = Column(String)
    registered_at = Column(DateTime, default=datetime.utcnow)
    last_heartbeat = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="online")
    is_active = Column(Boolean, default=True)
    customer_uuid = Column(String, nullable=True)


class Task(Base):
    """Task execution model"""

    __tablename__ = "tasks"

    id = Column(String, primary_key=True, index=True)
    agent_id = Column(String, index=True)
    task_id = Column(String, unique=True, index=True)
    command = Column(Text)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    exit_code = Column(Integer, nullable=True)
    output = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    logs = Column(Text, nullable=True)  # JSON string


class Customer(Base):
    """Customer model"""

    __tablename__ = "customers"

    id = Column(String, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True)
    name = Column(String, nullable=False)
    address = Column(Text, nullable=True)  # Optional address
    api_key = Column(
        String, unique=True, index=True, nullable=True
    )  # API key for authentication
    api_key_created_at = Column(DateTime, nullable=True)  # When API key was created
    api_key_last_used = Column(DateTime, nullable=True)  # Last time API key was used
    is_active = Column(Boolean, default=True)  # Whether customer account is active
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Script(Base):
    __tablename__ = "scripts"

    id = Column(String, primary_key=True)
    script_id = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String)
    content = Column(Text, nullable=False)
    script_type = Column(String, nullable=False)  # cmd, powershell, bash
    customer_uuid = Column(String, ForeignKey("customers.uuid"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)


class User(Base):
    """User model for authentication"""

    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    is_approved = Column(Boolean, default=False)
    approved_by = Column(String, nullable=True)  # Admin who approved
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LoginHistory(Base):
    """Login history model for tracking user logins"""

    __tablename__ = "login_history"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    username = Column(String, nullable=False)
    source_ip_external = Column(String, nullable=True)  # External IP address
    source_ip_internal = Column(String, nullable=True)  # Internal IP address
    login_time = Column(DateTime, default=datetime.utcnow)
    user_agent = Column(String, nullable=True)  # Browser/Client info
    success = Column(Boolean, default=True)  # Whether login was successful
    failure_reason = Column(String, nullable=True)  # Reason for failed login
    created_at = Column(DateTime, default=datetime.utcnow)


class DatabaseManager:
    """Database manager for agent and task operations"""

    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
        self.create_tables()

    def create_tables(self):
        """Create database tables"""
        Base.metadata.create_all(bind=self.engine)

    def get_session(self):
        """Get database session"""
        return self.SessionLocal()

    def register_agent(self, agent_data: dict) -> str:
        """Register a new agent in the database"""
        session = self.get_session()
        try:
            # Check if agent already exists
            existing_agent = (
                session.query(Agent)
                .filter(Agent.agent_id == agent_data["agent_id"])
                .first()
            )

            if existing_agent:
                # Update existing agent
                existing_agent.hostname = agent_data["hostname"]
                existing_agent.ip_address = agent_data["ip_address"]
                existing_agent.port = agent_data["port"]
                existing_agent.capabilities = json.dumps(agent_data["capabilities"])
                existing_agent.version = agent_data["version"]
                existing_agent.last_heartbeat = datetime.utcnow()
                existing_agent.status = "online"
                existing_agent.is_active = True
                existing_agent.customer_uuid = agent_data.get("customer_uuid")
                session.commit()
                return existing_agent.agent_id
            else:
                # Create new agent
                agent = Agent(
                    id=agent_data["id"],
                    agent_id=agent_data["agent_id"],
                    hostname=agent_data["hostname"],
                    ip_address=agent_data["ip_address"],
                    port=agent_data["port"],
                    capabilities=json.dumps(agent_data["capabilities"]),
                    version=agent_data["version"],
                    registered_at=datetime.utcnow(),
                    last_heartbeat=datetime.utcnow(),
                    status="online",
                    is_active=True,
                    customer_uuid=agent_data.get("customer_uuid"),
                )
                session.add(agent)
                session.commit()
                session.refresh(agent)
                return agent.agent_id
        finally:
            session.close()

    def update_heartbeat(self, agent_id: str, status: str = "online"):
        """Update agent heartbeat"""
        session = self.get_session()
        try:
            agent = session.query(Agent).filter(Agent.agent_id == agent_id).first()
            if agent:
                agent.last_heartbeat = datetime.utcnow()
                agent.status = status
                session.commit()
                return True
            return False
        finally:
            session.close()

    def get_agent(self, agent_id: str) -> Optional[dict]:
        """Get agent by ID"""
        session = self.get_session()
        try:
            agent = session.query(Agent).filter(Agent.agent_id == agent_id).first()
            if agent:
                return {
                    "agent_id": agent.agent_id,
                    "hostname": agent.hostname,
                    "ip_address": agent.ip_address,
                    "port": agent.port,
                    "capabilities": json.loads(agent.capabilities),
                    "version": agent.version,
                    "registered_at": agent.registered_at,
                    "last_heartbeat": agent.last_heartbeat,
                    "status": agent.status,
                    "customer_uuid": agent.customer_uuid,
                }
            return None
        finally:
            session.close()

    def get_agent_by_hostname(self, hostname: str) -> Optional[dict]:
        """Get agent by hostname (only active agents)"""
        session = self.get_session()
        try:
            agent = (
                session.query(Agent)
                .filter(Agent.hostname == hostname, Agent.is_active.is_(True))
                .first()
            )
            if agent:
                return {
                    "agent_id": agent.agent_id,
                    "hostname": agent.hostname,
                    "ip_address": agent.ip_address,
                    "port": agent.port,
                    "capabilities": json.loads(agent.capabilities),
                    "version": agent.version,
                    "registered_at": agent.registered_at,
                    "last_heartbeat": agent.last_heartbeat,
                    "status": agent.status,
                    "customer_uuid": agent.customer_uuid,
                }
            return None
        finally:
            session.close()

    def delete_agent(self, agent_id: str) -> bool:
        """Delete agent by ID (soft delete - sets is_active to False)"""
        session = self.get_session()
        try:
            agent = session.query(Agent).filter(Agent.agent_id == agent_id).first()
            if agent:
                agent.is_active = False
                session.commit()
                return True
            return False
        except Exception as e:
            print(f"❌ Error deleting agent {agent_id}: {e}")
            return False
        finally:
            session.close()

    def get_all_agents(self) -> List[dict]:
        """Get all active agents"""
        session = self.get_session()
        try:
            agents = session.query(Agent).filter(Agent.is_active == True).all()
            return [
                {
                    "agent_id": agent.agent_id,
                    "hostname": agent.hostname,
                    "ip_address": agent.ip_address,
                    "port": agent.port,
                    "capabilities": json.loads(agent.capabilities),
                    "version": agent.version,
                    "registered_at": agent.registered_at,
                    "last_heartbeat": agent.last_heartbeat,
                    "status": agent.status,
                    "customer_uuid": agent.customer_uuid,
                }
                for agent in agents
            ]
        finally:
            session.close()

    def get_online_agents(self, timeout_minutes: int = 2) -> List[dict]:
        """Get online agents (heartbeat within timeout)"""
        session = self.get_session()
        try:
            timeout_threshold = datetime.utcnow() - timedelta(minutes=timeout_minutes)
            agents = (
                session.query(Agent)
                .filter(
                    Agent.is_active == True, Agent.last_heartbeat >= timeout_threshold
                )
                .all()
            )
            return [
                {
                    "agent_id": agent.agent_id,
                    "hostname": agent.hostname,
                    "ip_address": agent.ip_address,
                    "port": agent.port,
                    "capabilities": json.loads(agent.capabilities),
                    "version": agent.version,
                    "registered_at": agent.registered_at,
                    "last_heartbeat": agent.last_heartbeat,
                    "status": agent.status,
                }
                for agent in agents
            ]
        finally:
            session.close()

    def mark_agent_offline(self, agent_id: str):
        """Mark agent as offline"""
        session = self.get_session()
        try:
            agent = session.query(Agent).filter(Agent.agent_id == agent_id).first()
            if agent:
                agent.status = "offline"
                session.commit()
        finally:
            session.close()

    def create_task(self, task_data: dict) -> str:
        """Create a new task"""
        session = self.get_session()
        try:
            task = Task(
                id=task_data["id"],
                agent_id=task_data["agent_id"],
                task_id=task_data["task_id"],
                command=task_data["command"],
                status=task_data["status"],
                created_at=datetime.utcnow(),
            )
            session.add(task)
            session.commit()
            session.refresh(task)
            return task.task_id
        finally:
            session.close()

    def update_task(self, task_id: str, updates: dict):
        """Update task status"""
        session = self.get_session()
        try:
            task = session.query(Task).filter(Task.task_id == task_id).first()
            if task:
                for key, value in updates.items():
                    if hasattr(task, key):
                        if key == "logs" and isinstance(value, list):
                            setattr(task, key, json.dumps(value))
                        else:
                            setattr(task, key, value)
                session.commit()
        finally:
            session.close()

    def get_task(self, task_id: str) -> Optional[dict]:
        """Get task by ID"""
        session = self.get_session()
        try:
            task = session.query(Task).filter(Task.task_id == task_id).first()
            if task:
                return {
                    "id": task.id,
                    "agent_id": task.agent_id,
                    "task_id": task.task_id,
                    "command": task.command,
                    "status": task.status,
                    "created_at": task.created_at,
                    "started_at": task.started_at,
                    "completed_at": task.completed_at,
                    "exit_code": task.exit_code,
                    "output": task.output,
                    "error": task.error,
                    "logs": json.loads(task.logs) if task.logs else [],
                }
            return None
        finally:
            session.close()

    def get_agent_tasks(self, agent_id: str) -> List[dict]:
        """Get all tasks for an agent"""
        session = self.get_session()
        try:
            tasks = session.query(Task).filter(Task.agent_id == agent_id).all()
            return [
                {
                    "id": task.id,
                    "agent_id": task.agent_id,
                    "task_id": task.task_id,
                    "command": task.command,
                    "status": task.status,
                    "created_at": task.created_at,
                    "started_at": task.started_at,
                    "completed_at": task.completed_at,
                    "exit_code": task.exit_code,
                    "output": task.output,
                    "error": task.error,
                    "logs": json.loads(task.logs) if task.logs else [],
                }
                for task in tasks
            ]
        finally:
            session.close()

    def cleanup_offline_agents(self, timeout_minutes: int = 2):
        """Mark agents as offline if they haven't sent heartbeat"""
        session = self.get_session()
        try:
            timeout_threshold = datetime.utcnow() - timedelta(minutes=timeout_minutes)
            offline_agents = (
                session.query(Agent)
                .filter(
                    Agent.is_active == True,
                    Agent.last_heartbeat < timeout_threshold,
                    Agent.status == "online",
                )
                .all()
            )

            for agent in offline_agents:
                agent.status = "offline"

            session.commit()
            return len(offline_agents)
        finally:
            session.close()

    # Customer management methods
    def create_customer(self, customer_data: dict) -> str:
        """Create a new customer"""
        session = self.get_session()
        try:
            customer = Customer(
                id=customer_data["id"],
                uuid=customer_data["uuid"],
                name=customer_data["name"],
                address=customer_data.get("address"),
            )
            session.add(customer)
            session.commit()
            return customer.uuid
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_customer(self, customer_uuid: str) -> Optional[dict]:
        """Get customer by UUID"""
        session = self.get_session()
        try:
            customer = (
                session.query(Customer).filter(Customer.uuid == customer_uuid).first()
            )

            if customer:
                return {
                    "id": customer.id,
                    "uuid": customer.uuid,
                    "name": customer.name,
                    "address": customer.address,
                    "api_key": customer.api_key,
                    "api_key_created_at": (
                        customer.api_key_created_at.isoformat()
                        if customer.api_key_created_at
                        else None
                    ),
                    "api_key_last_used": (
                        customer.api_key_last_used.isoformat()
                        if customer.api_key_last_used
                        else None
                    ),
                    "is_active": customer.is_active,
                    "created_at": customer.created_at.isoformat(),
                    "updated_at": customer.updated_at.isoformat(),
                }
            return None
        finally:
            session.close()

    def get_all_customers(self) -> List[dict]:
        """Get all customers"""
        session = self.get_session()
        try:
            customers = (
                session.query(Customer).order_by(Customer.created_at.desc()).all()
            )
            return [
                {
                    "id": customer.id,
                    "uuid": customer.uuid,
                    "name": customer.name,
                    "address": customer.address,
                    "api_key": customer.api_key,
                    "api_key_created_at": (
                        customer.api_key_created_at.isoformat()
                        if customer.api_key_created_at
                        else None
                    ),
                    "api_key_last_used": (
                        customer.api_key_last_used.isoformat()
                        if customer.api_key_last_used
                        else None
                    ),
                    "is_active": customer.is_active,
                    "created_at": customer.created_at.isoformat(),
                    "updated_at": customer.updated_at.isoformat(),
                }
                for customer in customers
            ]
        finally:
            session.close()

    def update_customer(self, customer_uuid: str, updates: dict) -> bool:
        """Update customer information"""
        session = self.get_session()
        try:
            customer = (
                session.query(Customer).filter(Customer.uuid == customer_uuid).first()
            )

            if customer:
                if "name" in updates:
                    customer.name = updates["name"]
                if "address" in updates:
                    customer.address = updates["address"]
                customer.updated_at = datetime.utcnow()
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def delete_customer(self, customer_uuid: str) -> bool:
        """Delete customer by UUID"""
        session = self.get_session()
        try:
            customer = (
                session.query(Customer).filter(Customer.uuid == customer_uuid).first()
            )

            if customer:
                session.delete(customer)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def generate_api_key(self, customer_uuid: str) -> Optional[str]:
        """Generate a new API key for a customer"""
        import secrets

        session = self.get_session()
        try:
            customer = (
                session.query(Customer).filter(Customer.uuid == customer_uuid).first()
            )

            if customer:
                # Generate a secure API key
                api_key = f"sk_{secrets.token_urlsafe(32)}"
                customer.api_key = api_key
                customer.api_key_created_at = datetime.utcnow()
                customer.api_key_last_used = None
                session.commit()
                return api_key
            return None
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_customer_by_api_key(self, api_key: str) -> Optional[dict]:
        """Get customer by API key"""
        session = self.get_session()
        try:
            customer = (
                session.query(Customer)
                .filter(Customer.api_key == api_key, Customer.is_active == True)
                .first()
            )

            if customer:
                # Update last used timestamp
                customer.api_key_last_used = datetime.utcnow()
                session.commit()

                return {
                    "id": customer.id,
                    "uuid": customer.uuid,
                    "name": customer.name,
                    "address": customer.address,
                    "api_key": customer.api_key,
                    "api_key_created_at": (
                        customer.api_key_created_at.isoformat()
                        if customer.api_key_created_at
                        else None
                    ),
                    "api_key_last_used": (
                        customer.api_key_last_used.isoformat()
                        if customer.api_key_last_used
                        else None
                    ),
                    "is_active": customer.is_active,
                    "created_at": customer.created_at.isoformat(),
                    "updated_at": customer.updated_at.isoformat(),
                }
            return None
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def revoke_api_key(self, customer_uuid: str) -> bool:
        """Revoke API key for a customer"""
        session = self.get_session()
        try:
            customer = (
                session.query(Customer).filter(Customer.uuid == customer_uuid).first()
            )

            if customer:
                customer.api_key = None
                customer.api_key_created_at = None
                customer.api_key_last_used = None
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def update_customer_api_key_usage(self, customer_uuid: str) -> bool:
        """Update the last used timestamp for a customer's API key"""
        session = self.get_session()
        try:
            customer = (
                session.query(Customer).filter(Customer.uuid == customer_uuid).first()
            )

            if customer:
                customer.api_key_last_used = datetime.utcnow()
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    # Script Management Methods
    def create_script(self, script_data: dict) -> str:
        """Create a new script"""
        session = self.get_session()
        try:
            script = Script(**script_data)
            session.add(script)
            session.commit()
            session.refresh(script)
            return script.script_id
        except Exception as e:
            session.rollback()
            print(f"❌ Error creating script: {e}")
            raise
        finally:
            session.close()

    def get_all_scripts(self) -> List[dict]:
        """Get all active scripts"""
        session = self.get_session()
        try:
            scripts = session.query(Script).filter(Script.is_active == True).all()
            return [
                {
                    "id": script.id,
                    "script_id": script.script_id,
                    "name": script.name,
                    "description": script.description,
                    "content": script.content,
                    "script_type": script.script_type,
                    "customer_uuid": script.customer_uuid,
                    "created_at": script.created_at,
                    "updated_at": script.updated_at,
                }
                for script in scripts
            ]
        except Exception as e:
            print(f"❌ Error getting scripts: {e}")
            return []
        finally:
            session.close()

    def get_script(self, script_id: str) -> Optional[dict]:
        """Get a specific script"""
        session = self.get_session()
        try:
            script = (
                session.query(Script)
                .filter(Script.script_id == script_id, Script.is_active == True)
                .first()
            )

            if script:
                return {
                    "id": script.id,
                    "script_id": script.script_id,
                    "name": script.name,
                    "description": script.description,
                    "content": script.content,
                    "script_type": script.script_type,
                    "customer_uuid": script.customer_uuid,
                    "created_at": script.created_at,
                    "updated_at": script.updated_at,
                }
            return None
        except Exception as e:
            print(f"❌ Error getting script: {e}")
            return None
        finally:
            session.close()

    def update_script(self, script_id: str, updates: dict) -> bool:
        """Update a script"""
        session = self.get_session()
        try:
            script = (
                session.query(Script)
                .filter(Script.script_id == script_id, Script.is_active == True)
                .first()
            )

            if script:
                for key, value in updates.items():
                    if hasattr(script, key):
                        setattr(script, key, value)
                script.updated_at = datetime.utcnow()
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            print(f"❌ Error updating script: {e}")
            return False
        finally:
            session.close()

    def delete_script(self, script_id: str) -> bool:
        """Soft delete a script"""
        session = self.get_session()
        try:
            script = (
                session.query(Script)
                .filter(Script.script_id == script_id, Script.is_active == True)
                .first()
            )

            if script:
                script.is_active = False
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            print(f"❌ Error deleting script: {e}")
            return False
        finally:
            session.close()

    def get_scripts_by_customer(self, customer_uuid: str) -> List[dict]:
        """Get scripts assigned to a specific customer"""
        session = self.get_session()
        try:
            scripts = (
                session.query(Script)
                .filter(Script.customer_uuid == customer_uuid, Script.is_active == True)
                .all()
            )

            return [
                {
                    "id": script.id,
                    "script_id": script.script_id,
                    "name": script.name,
                    "description": script.description,
                    "content": script.content,
                    "script_type": script.script_type,
                    "customer_uuid": script.customer_uuid,
                    "created_at": script.created_at,
                    "updated_at": script.updated_at,
                }
                for script in scripts
            ]
        except Exception as e:
            print(f"❌ Error getting scripts by customer: {e}")
            return []
        finally:
            session.close()

    # User management methods
    def create_user(self, user_data: dict) -> str:
        """Create a new user"""
        session = self.get_session()
        try:
            # Check if user already exists
            existing_user = (
                session.query(User)
                .filter(
                    (User.username == user_data["username"])
                    | (User.email == user_data["email"])
                )
                .first()
            )

            if existing_user:
                raise ValueError("User with this username or email already exists")

            user = User(
                id=user_data["id"],
                username=user_data["username"],
                email=user_data["email"],
                full_name=user_data.get("full_name"),
                hashed_password=user_data["hashed_password"],
                is_active=user_data.get("is_active", True),
                is_admin=user_data.get("is_admin", False),
                is_approved=user_data.get("is_approved", False),
            )

            session.add(user)
            session.commit()
            session.refresh(user)
            return user.id
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_user_by_username(self, username: str) -> Optional[dict]:
        """Get user by username"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.username == username).first()
            if user:
                return {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "is_active": user.is_active,
                    "is_admin": user.is_admin,
                    "is_approved": user.is_approved,
                    "approved_by": user.approved_by,
                    "approved_at": (
                        user.approved_at.isoformat() if user.approved_at else None
                    ),
                    "created_at": user.created_at.isoformat(),
                    "updated_at": user.updated_at.isoformat(),
                }
            return None
        except Exception as e:
            print(f"Error getting user by username: {e}")
            return None
        finally:
            session.close()

    def get_user_by_email(self, email: str) -> Optional[dict]:
        """Get user by email"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.email == email).first()
            if user:
                return {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "is_active": user.is_active,
                    "is_admin": user.is_admin,
                    "is_approved": user.is_approved,
                    "approved_by": user.approved_by,
                    "approved_at": (
                        user.approved_at.isoformat() if user.approved_at else None
                    ),
                    "created_at": user.created_at.isoformat(),
                    "updated_at": user.updated_at.isoformat(),
                }
            return None
        except Exception as e:
            print(f"Error getting user by email: {e}")
            return None
        finally:
            session.close()

    def get_user_with_password(self, username: str) -> Optional[dict]:
        """Get user with password hash for authentication"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.username == username).first()
            if user:
                return {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "hashed_password": user.hashed_password,
                    "is_active": user.is_active,
                    "is_admin": user.is_admin,
                    "is_approved": user.is_approved,
                    "approved_by": user.approved_by,
                    "approved_at": (
                        user.approved_at.isoformat() if user.approved_at else None
                    ),
                    "created_at": user.created_at.isoformat(),
                    "updated_at": user.updated_at.isoformat(),
                }
            return None
        except Exception as e:
            print(f"Error getting user with password: {e}")
            return None
        finally:
            session.close()

    def get_all_users(self) -> List[dict]:
        """Get all users"""
        session = self.get_session()
        try:
            users = session.query(User).all()
            return [
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "is_active": user.is_active,
                    "is_admin": user.is_admin,
                    "is_approved": user.is_approved,
                    "approved_by": user.approved_by,
                    "approved_at": (
                        user.approved_at.isoformat() if user.approved_at else None
                    ),
                    "created_at": user.created_at.isoformat(),
                    "updated_at": user.updated_at.isoformat(),
                }
                for user in users
            ]
        except Exception as e:
            print(f"Error getting all users: {e}")
            return []
        finally:
            session.close()

    def update_user(self, user_id: str, updates: dict) -> bool:
        """Update user information"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return False

            for key, value in updates.items():
                if hasattr(user, key):
                    setattr(user, key, value)

            user.updated_at = datetime.utcnow()
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error updating user: {e}")
            return False
        finally:
            session.close()

    def delete_user(self, user_id: str) -> bool:
        """Delete a user"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return False

            session.delete(user)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error deleting user: {e}")
            return False
        finally:
            session.close()

    def get_pending_users(self) -> List[dict]:
        """Get all users waiting for approval"""
        session = self.get_session()
        try:
            users = (
                session.query(User)
                .filter(User.is_approved == False, User.is_active == True)
                .all()
            )
            return [
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "is_active": user.is_active,
                    "is_admin": user.is_admin,
                    "is_approved": user.is_approved,
                    "approved_by": user.approved_by,
                    "approved_at": (
                        user.approved_at.isoformat() if user.approved_at else None
                    ),
                    "created_at": user.created_at.isoformat(),
                    "updated_at": user.updated_at.isoformat(),
                }
                for user in users
            ]
        except Exception as e:
            print(f"Error getting pending users: {e}")
            return []
        finally:
            session.close()

    def approve_user(self, user_id: str, approved_by: str) -> bool:
        """Approve a user"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                user.is_approved = True
                user.approved_by = approved_by
                user.approved_at = datetime.utcnow()
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            print(f"Error approving user: {e}")
            return False
        finally:
            session.close()

    def reject_user(self, user_id: str) -> bool:
        """Reject a user (deactivate)"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                user.is_active = False
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            print(f"Error rejecting user: {e}")
            return False
        finally:
            session.close()

    def make_admin(self, user_id: str) -> bool:
        """Make a user an admin"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                user.is_admin = True
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            print(f"Error making user admin: {e}")
            return False
        finally:
            session.close()

    def remove_admin(self, user_id: str) -> bool:
        """Remove admin privileges from a user"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                user.is_admin = False
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            print(f"Error removing admin privileges: {e}")
            return False
        finally:
            session.close()

    def record_login_attempt(
        self,
        user_id: str,
        username: str,
        source_ip_external: str = None,
        source_ip_internal: str = None,
        user_agent: str = None,
        success: bool = True,
        failure_reason: str = None,
    ) -> str:
        """Record a login attempt in the login history"""
        session = self.get_session()
        try:
            login_record = LoginHistory(
                id=str(uuid.uuid4()),
                user_id=user_id,
                username=username,
                source_ip_external=source_ip_external,
                source_ip_internal=source_ip_internal,
                user_agent=user_agent,
                success=success,
                failure_reason=failure_reason,
            )
            session.add(login_record)
            session.commit()
            session.refresh(login_record)
            return login_record.id
        finally:
            session.close()

    def get_user_login_history(self, user_id: str, limit: int = 10) -> List[dict]:
        """Get login history for a specific user"""
        session = self.get_session()
        try:
            login_records = (
                session.query(LoginHistory)
                .filter(LoginHistory.user_id == user_id)
                .order_by(LoginHistory.login_time.desc())
                .limit(limit)
                .all()
            )
            return [
                {
                    "id": record.id,
                    "username": record.username,
                    "source_ip_external": record.source_ip_external,
                    "source_ip_internal": record.source_ip_internal,
                    "login_time": record.login_time,
                    "user_agent": record.user_agent,
                    "success": record.success,
                    "failure_reason": record.failure_reason,
                    "created_at": record.created_at,
                }
                for record in login_records
            ]
        finally:
            session.close()

    def get_user_last_login(self, user_id: str) -> Optional[dict]:
        """Get the last successful login for a user"""
        session = self.get_session()
        try:
            last_login = (
                session.query(LoginHistory)
                .filter(
                    LoginHistory.user_id == user_id,
                    LoginHistory.success.is_(True),
                )
                .order_by(LoginHistory.login_time.desc())
                .first()
            )
            if last_login:
                return {
                    "id": last_login.id,
                    "username": last_login.username,
                    "source_ip_external": last_login.source_ip_external,
                    "source_ip_internal": last_login.source_ip_internal,
                    "login_time": last_login.login_time,
                    "user_agent": last_login.user_agent,
                    "success": last_login.success,
                    "created_at": last_login.created_at,
                }
            return None
        finally:
            session.close()

    def get_user_login_count(self, user_id: str) -> int:
        """Get the total number of successful logins for a user"""
        session = self.get_session()
        try:
            count = (
                session.query(LoginHistory)
                .filter(
                    LoginHistory.user_id == user_id,
                    LoginHistory.success.is_(True),
                )
                .count()
            )
            return count
        finally:
            session.close()


# Initialize database manager
db_manager = DatabaseManager()
