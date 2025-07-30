"""
API Routes for Remote Agent Manager
"""

import sys
import uuid
from datetime import timedelta
from pathlib import Path
from typing import List, Optional

from auth import (
    User,
    UserCreate,
    UserLogin,
    create_access_token,
    get_current_active_user,
    get_current_admin_user,
    get_current_approved_user,
    get_password_hash,
    verify_password,
)
from fastapi import APIRouter, Depends, HTTPException, Request, Response

sys.path.append(str(Path(__file__).parent.parent / "Scripts"))
from shared import (
    AgentRegistration,
    CommandRequest,
    CustomerRegistration,
    HeartbeatRequest,
    ScriptExecutionRequest,
    ScriptRegistration,
    agent_manager,
    manager,
)

from database import db_manager

# Create router
router = APIRouter(prefix="/api", tags=["API"])


# Authentication API routes
@router.post("/auth/register")
async def register_user(user: UserCreate):
    """Register a new user via API"""
    try:
        # Check if user already exists
        existing_user = db_manager.get_user_by_username(user.username)
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")

        existing_email = db_manager.get_user_by_email(user.email)
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already exists")

        # Create user
        user_data = {
            "id": str(uuid.uuid4()),
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "hashed_password": get_password_hash(user.password),
            "is_active": True,
            "is_admin": False,
            "is_approved": False,
        }

        user_id = db_manager.create_user(user_data)
        return {"user_id": user_id, "message": "User registered successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@router.post("/auth/login")
async def login_user(user_credentials: UserLogin, request: Request):
    """Login user via API"""
    try:
        # Get client IP addresses
        client_ip = request.client.host if request.client else "unknown"
        forwarded_for = request.headers.get("X-Forwarded-For")
        real_ip = request.headers.get("X-Real-IP")

        # Determine external and internal IPs
        source_ip_external = forwarded_for or real_ip or client_ip
        source_ip_internal = client_ip

        # Get user agent
        user_agent = request.headers.get("User-Agent")

        # Get user with password
        user_data = db_manager.get_user_with_password(user_credentials.username)
        if not user_data:
            # Record failed login attempt
            db_manager.record_login_attempt(
                user_id="unknown",
                username=user_credentials.username,
                source_ip_external=source_ip_external,
                source_ip_internal=source_ip_internal,
                user_agent=user_agent,
                success=False,
                failure_reason="Invalid username",
            )
            raise HTTPException(status_code=401, detail="Invalid username or password")

        # Verify password
        if not verify_password(user_credentials.password, user_data["hashed_password"]):
            # Record failed login attempt
            db_manager.record_login_attempt(
                user_id=user_data["id"],
                username=user_data["username"],
                source_ip_external=source_ip_external,
                source_ip_internal=source_ip_internal,
                user_agent=user_agent,
                success=False,
                failure_reason="Invalid password",
            )
            raise HTTPException(status_code=401, detail="Invalid username or password")

        # Check if user is active
        if not user_data["is_active"]:
            # Record failed login attempt
            db_manager.record_login_attempt(
                user_id=user_data["id"],
                username=user_data["username"],
                source_ip_external=source_ip_external,
                source_ip_internal=source_ip_internal,
                user_agent=user_agent,
                success=False,
                failure_reason="Account disabled",
            )
            raise HTTPException(status_code=401, detail="Account is disabled")

        # Check if user is approved (unless they are an admin)
        if not user_data["is_admin"] and not user_data["is_approved"]:
            # Record failed login attempt
            db_manager.record_login_attempt(
                user_id=user_data["id"],
                username=user_data["username"],
                source_ip_external=source_ip_external,
                source_ip_internal=source_ip_internal,
                user_agent=user_agent,
                success=False,
                failure_reason="Account not approved",
            )
            raise HTTPException(
                status_code=401, detail="Account not yet approved by admin"
            )

        # Record successful login
        db_manager.record_login_attempt(
            user_id=user_data["id"],
            username=user_data["username"],
            source_ip_external=source_ip_external,
            source_ip_internal=source_ip_internal,
            user_agent=user_agent,
            success=True,
        )

        # Create access token
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": user_data["username"]}, expires_delta=access_token_expires
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user_data["id"],
                "username": user_data["username"],
                "email": user_data["email"],
                "full_name": user_data["full_name"],
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


# User management API routes
@router.get("/users")
async def list_users(current_user: User = Depends(get_current_active_user)):
    """List all users (admin only)"""
    try:
        users = db_manager.get_all_users()
        return {"users": users, "total": len(users)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list users: {str(e)}")


@router.get("/users/profile")
async def get_profile(current_user: User = Depends(get_current_active_user)):
    """Get current user's profile"""
    import logging

    logger = logging.getLogger(__name__)

    logger.info(f"🔍 Profile request for user: {current_user.username}")

    try:
        user_data = db_manager.get_user_by_username(current_user.username)
        if not user_data:
            logger.error(f"❌ User not found in database: {current_user.username}")
            raise HTTPException(status_code=404, detail="User not found")

        # Get login history information
        last_login = db_manager.get_user_last_login(user_data["id"])
        login_count = db_manager.get_user_login_count(user_data["id"])

        # Add real statistics
        user_data.update(
            {
                "total_logins": login_count,
                "session_time": "0h",  # TODO: Implement session tracking
                "commands_sent": 0,  # TODO: Implement command tracking
                "scripts_created": 0,  # TODO: Implement script tracking
                "last_login": last_login["login_time"] if last_login else None,
                "last_login_ip_external": (
                    last_login["source_ip_external"] if last_login else None
                ),
                "last_login_ip_internal": (
                    last_login["source_ip_internal"] if last_login else None
                ),
            }
        )

        logger.info(
            f"✅ Profile returned successfully for user: {current_user.username}"
        )
        return user_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting profile for {current_user.username}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get profile: {str(e)}")


@router.get("/users/{user_id}")
async def get_user(user_id: str, current_user: User = Depends(get_current_active_user)):
    """Get specific user"""
    try:
        # For now, only allow users to get their own info
        if current_user.id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        user_data = db_manager.get_user_by_username(current_user.username)
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")
        return user_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user: {str(e)}")


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str, current_user: User = Depends(get_current_admin_user)
):
    """Delete a user (admin only)"""
    try:
        # Prevent admin from deleting themselves
        if current_user.id == user_id:
            raise HTTPException(
                status_code=400, detail="Cannot delete your own account"
            )

        success = db_manager.delete_user(user_id)
        if success:
            return {"message": "User deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")


@router.put("/users/profile")
async def update_profile(
    profile_data: dict, current_user: User = Depends(get_current_active_user)
):
    """Update current user's profile"""
    try:
        updates = {}
        if "email" in profile_data:
            updates["email"] = profile_data["email"]
        if "full_name" in profile_data:
            updates["full_name"] = profile_data["full_name"]

        success = db_manager.update_user(current_user.id, updates)
        if success:
            return {"message": "Profile updated successfully"}
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update profile: {str(e)}"
        )


@router.post("/users/change-password")
async def change_password(
    password_data: dict, current_user: User = Depends(get_current_active_user)
):
    """Change current user's password"""
    try:
        current_password = password_data.get("current_password")
        new_password = password_data.get("new_password")

        if not current_password or not new_password:
            raise HTTPException(
                status_code=400, detail="Current password and new password are required"
            )

        # Verify current password
        user_data = db_manager.get_user_with_password(current_user.username)
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")

        if not verify_password(current_password, user_data["hashed_password"]):
            raise HTTPException(status_code=400, detail="Current password is incorrect")

        # Update password
        hashed_password = get_password_hash(new_password)
        success = db_manager.update_user(
            current_user.id, {"hashed_password": hashed_password}
        )

        if success:
            return {"message": "Password changed successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to update password")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to change password: {str(e)}"
        )


# Agent management API routes
@router.post("/agents/register")
async def register_agent(request: Request, registration: AgentRegistration):
    """Register a new agent"""
    client_ip = request.client.host if request.client else "unknown"
    try:
        agent_id = await agent_manager.register_agent(registration)
        return {"agent_id": agent_id, "message": "Agent registered successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@router.post("/agents/{agent_id}/heartbeat")
async def agent_heartbeat(request: Request, agent_id: str, heartbeat: HeartbeatRequest):
    """Receive heartbeat from an agent"""
    try:
        await agent_manager.update_heartbeat(agent_id, heartbeat)
        return {"message": "Heartbeat received"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Heartbeat failed: {str(e)}")


@router.get("/agents")
async def list_agents():
    """List all registered agents"""
    try:
        agents = agent_manager.get_all_agents()
        online_count = len(agent_manager.get_online_agents())

        return {
            "agents": agents,
            "total": len(agents),
            "online": online_count,
            "offline": len(agents) - online_count,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list agents: {str(e)}")


@router.get("/agents/online")
async def list_online_agents():
    """List only online agents"""
    try:
        agents = agent_manager.get_online_agents()
        return {"agents": agents, "count": len(agents)}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list online agents: {str(e)}"
        )


@router.get("/agents/{agent_id}")
async def get_agent_status(agent_id: str):
    """Get specific agent status"""
    try:
        agent = agent_manager.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        return agent
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get agent: {str(e)}")


@router.delete("/agents/{agent_id}")
async def unregister_agent(agent_id: str):
    """Unregister/delete an agent"""
    try:
        success = await agent_manager.unregister_agent(agent_id)
        if success:
            return {"message": "Agent unregistered successfully"}
        else:
            raise HTTPException(status_code=404, detail="Agent not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to unregister agent: {str(e)}"
        )


# Customer management API routes
@router.post("/customers")
async def create_customer(customer: CustomerRegistration):
    """Create a new customer"""
    try:
        customer_data = {
            "id": str(uuid.uuid4()),
            "uuid": str(uuid.uuid4()),
            "name": customer.name,
            "address": customer.address,
        }

        customer_uuid = db_manager.create_customer(customer_data)
        return {"uuid": customer_uuid, "message": "Customer created successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Customer creation failed: {str(e)}"
        )


@router.get("/customers")
async def list_customers():
    """List all customers"""
    try:
        customers = db_manager.get_all_customers()
        return {"customers": customers, "total": len(customers)}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list customers: {str(e)}"
        )


@router.get("/customers/{customer_uuid}")
async def get_customer(customer_uuid: str):
    """Get specific customer"""
    try:
        customer = db_manager.get_customer(customer_uuid)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        return customer
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get customer: {str(e)}")


@router.put("/customers/{customer_uuid}")
async def update_customer(customer_uuid: str, customer: CustomerRegistration):
    """Update customer information"""
    try:
        updates = {"name": customer.name}
        if customer.address is not None:
            updates["address"] = customer.address

        success = db_manager.update_customer(customer_uuid, updates)
        if success:
            return {"message": "Customer updated successfully"}
        else:
            raise HTTPException(status_code=404, detail="Customer not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Customer update failed: {str(e)}")


@router.delete("/customers/{customer_uuid}")
async def delete_customer(customer_uuid: str):
    """Delete a customer"""
    try:
        success = db_manager.delete_customer(customer_uuid)
        if success:
            return {"message": "Customer deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Customer not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Customer deletion failed: {str(e)}"
        )


# Customer API Key Management Endpoints
@router.post("/customers/{customer_uuid}/generate-api-key")
async def generate_customer_api_key(
    customer_uuid: str, current_user: User = Depends(get_current_admin_user)
):
    """Generate API key for a customer (admin only)"""
    try:
        api_key = db_manager.generate_api_key(customer_uuid)
        if api_key:
            return {"api_key": api_key, "message": "API key generated successfully"}
        else:
            raise HTTPException(status_code=404, detail="Customer not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"API key generation failed: {str(e)}"
        )


@router.delete("/customers/{customer_uuid}/revoke-api-key")
async def revoke_customer_api_key(
    customer_uuid: str, current_user: User = Depends(get_current_admin_user)
):
    """Revoke API key for a customer (admin only)"""
    try:
        success = db_manager.revoke_api_key(customer_uuid)
        if success:
            return {"message": "API key revoked successfully"}
        else:
            raise HTTPException(status_code=404, detail="Customer not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"API key revocation failed: {str(e)}"
        )


@router.get("/customers/{customer_uuid}/download-config")
async def download_customer_config(
    customer_uuid: str, current_user: User = Depends(get_current_admin_user)
):
    """Download customer configuration file (admin only)"""
    try:
        customer = db_manager.get_customer(customer_uuid)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        # Generate configuration content
        config_content = f"""# Remote Agent Configuration File
# Copy this file to id.ini and update with your actual values

# Customer UUID - Required
# This identifies your customer account
customer_id = {customer['uuid']}

# API Key - Required for authentication
# Format: sk_<random_string>
# Get this from your admin via POST /api/customers/{customer_uuid}/generate-api-key
api_key = {customer.get('api_key', 'NOT_GENERATED')}

# Agent Configuration - Optional
# These will be auto-detected if not specified
hostname = AUTO_DETECT
ip_address = AUTO_DETECT
port = 3002
version = 1.0.0

# Capabilities - Optional
# List of what this agent can do
capabilities = ["command_execution", "file_transfer", "system_monitoring"]
"""

        return Response(
            content=config_content,
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename=id_{customer_uuid}.ini"
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Config download failed: {str(e)}")


# Script management API routes
@router.post("/scripts")
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
            "customer_uuid": script.customer_uuid,
        }

        script_id = db_manager.create_script(script_data)
        return {"script_id": script_id, "message": "Script created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Script creation failed: {str(e)}")


@router.get("/scripts")
async def list_scripts():
    """List all scripts"""
    try:
        scripts = db_manager.get_all_scripts()
        return {"scripts": scripts, "total": len(scripts)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list scripts: {str(e)}")


@router.get("/scripts/{script_id}")
async def get_script(script_id: str):
    """Get specific script"""
    try:
        script = db_manager.get_script(script_id)
        if not script:
            raise HTTPException(status_code=404, detail="Script not found")
        return script
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get script: {str(e)}")


@router.put("/scripts/{script_id}")
async def update_script(script_id: str, script: ScriptRegistration):
    """Update script information"""
    try:
        updates = {
            "name": script.name,
            "description": script.description,
            "content": script.content,
            "script_type": script.script_type,
            "customer_uuid": script.customer_uuid,
        }

        success = db_manager.update_script(script_id, updates)
        if success:
            return {"message": "Script updated successfully"}
        else:
            raise HTTPException(status_code=404, detail="Script not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Script update failed: {str(e)}")


@router.delete("/scripts/{script_id}")
async def delete_script(script_id: str):
    """Delete a script"""
    try:
        success = db_manager.delete_script(script_id)
        if success:
            return {"message": "Script deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Script not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Script deletion failed: {str(e)}")


@router.post("/scripts/{script_id}/execute")
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
            command=script_content, shell_type=script["script_type"], timeout=30
        )

        # Execute the command
        result = await agent_manager.send_command_to_agent(
            execution_request.agent_id, command_request
        )

        return {
            "script_id": script_id,
            "agent_id": execution_request.agent_id,
            "task_id": result.get("task_id"),
            "message": "Script execution started",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Script execution failed: {str(e)}"
        )


# Command execution API routes
@router.post("/agents/{agent_id}/commands")
async def send_command_to_agent(agent_id: str, command_request: CommandRequest):
    """Send a command to a specific agent"""
    try:
        result = await agent_manager.send_command_to_agent(agent_id, command_request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Command execution failed: {str(e)}"
        )


@router.get("/agents/{agent_id}/commands")
async def get_agent_commands(agent_id: str):
    """Get pending commands for an agent (HTTP agent polling)"""
    try:
        commands = manager.get_pending_commands(agent_id)
        return {"commands": commands, "count": len(commands)}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get agent commands: {str(e)}"
        )


@router.get("/agents/{agent_id}/tasks")
async def get_agent_tasks(agent_id: str):
    """Get all tasks for an agent"""
    try:
        tasks = db_manager.get_agent_tasks(agent_id)
        return {"tasks": tasks, "count": len(tasks)}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get agent tasks: {str(e)}"
        )


@router.get("/agents/{agent_id}/tasks/{task_id}")
async def get_agent_task_status(agent_id: str, task_id: str):
    """Get specific task status from an agent"""
    try:
        agent = agent_manager.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        if agent.status != "online":
            raise HTTPException(status_code=400, detail="Agent is offline")

        # Check if we have stored task result from WebSocket
        from main import manager

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
                "exit_code": None,
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get task status: {str(e)}"
        )


# Health check
@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        online_agents = len(agent_manager.get_online_agents())
        total_agents = len(agent_manager.get_all_agents())
        from main import manager

        websocket_connections = len(manager.active_connections)

        return {
            "status": "healthy",
            "agents": {
                "total": total_agents,
                "online": online_agents,
                "offline": total_agents - online_agents,
            },
            "websocket_connections": websocket_connections,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


# Admin-only endpoints
@router.get("/admin/pending-users")
async def get_pending_users(current_user: User = Depends(get_current_admin_user)):
    """Get all users waiting for approval (admin only)"""
    import logging

    logger = logging.getLogger(__name__)

    logger.info(f"🔍 Pending users request from admin: {current_user.username}")

    try:
        pending_users = db_manager.get_pending_users()
        logger.info(f"✅ Found {len(pending_users)} pending users")
        return {"pending_users": pending_users, "total": len(pending_users)}
    except Exception as e:
        logger.error(f"❌ Error getting pending users: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get pending users: {str(e)}"
        )


@router.post("/admin/users/{user_id}/approve")
async def approve_user(
    user_id: str, current_user: User = Depends(get_current_admin_user)
):
    """Approve a user (admin only)"""
    try:
        success = db_manager.approve_user(user_id, current_user.username)
        if success:
            return {"message": "User approved successfully"}
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to approve user: {str(e)}")


@router.post("/admin/users/{user_id}/reject")
async def reject_user(
    user_id: str, current_user: User = Depends(get_current_admin_user)
):
    """Reject a user (admin only)"""
    try:
        success = db_manager.reject_user(user_id)
        if success:
            return {"message": "User rejected successfully"}
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reject user: {str(e)}")


@router.post("/admin/users/{user_id}/make-admin")
async def make_user_admin(
    user_id: str, current_user: User = Depends(get_current_admin_user)
):
    """Make a user an admin (admin only)"""
    try:
        success = db_manager.make_admin(user_id)
        if success:
            return {"message": "User made admin successfully"}
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to make user admin: {str(e)}"
        )


@router.post("/admin/users/{user_id}/remove-admin")
async def remove_user_admin(
    user_id: str, current_user: User = Depends(get_current_admin_user)
):
    """Remove admin privileges from a user (admin only)"""
    try:
        success = db_manager.remove_admin(user_id)
        if success:
            return {"message": "Admin privileges removed successfully"}
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to remove admin privileges: {str(e)}"
        )
