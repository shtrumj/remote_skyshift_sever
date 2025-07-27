#!/usr/bin/env python3
"""
Test client for the Remote Agent Manager API
This script demonstrates how to interact with the agent management system.
"""

import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost:4433"

class AgentManagerClient:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        
    async def list_agents(self):
        """List all registered agents"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/agents")
            return response.json()
    
    async def list_online_agents(self):
        """List only online agents"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/agents/online")
            return response.json()
    
    async def send_command(self, agent_id: str, command: str, shell_type: str = "bash"):
        """Send a command to a specific agent"""
        command_data = {
            "command": command,
            "shell_type": shell_type,
            "timeout": 30
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/agents/{agent_id}/commands",
                json=command_data
            )
            return response.status_code, response.json()
    
    async def get_task_status(self, agent_id: str, task_id: str):
        """Get status of a specific task"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/agents/{agent_id}/tasks/{task_id}"
            )
            return response.status_code, response.json()
    
    async def broadcast_command(self, command: str, shell_type: str = "bash"):
        """Broadcast a command to all online agents"""
        command_data = {
            "command": command,
            "shell_type": shell_type,
            "timeout": 30
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/commands/broadcast",
                json=command_data
            )
            return response.status_code, response.json()
    
    async def health_check(self):
        """Get system health status"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/health")
            return response.json()

def print_json(data, title=""):
    """Pretty print JSON data"""
    if title:
        print(f"\n{'=' * 50}")
        print(f"{title}")
        print(f"{'=' * 50}")
    print(json.dumps(data, indent=2, default=str))

async def main():
    """Main demo function"""
    client = AgentManagerClient()
    
    try:
        print("🚀 Testing Remote Agent Manager API")
        
        # Health check
        health = await client.health_check()
        print_json(health, "HEALTH STATUS")
        
        # List all agents
        agents = await client.list_agents()
        print_json(agents, "ALL REGISTERED AGENTS")
        
        # List online agents
        online_agents = await client.list_online_agents()
        print_json(online_agents, "ONLINE AGENTS")
        
        # If we have online agents, try to send commands
        if online_agents["count"] > 0:
            agent = online_agents["agents"][0]
            agent_id = agent["agent_id"]
            hostname = agent["hostname"]
            
            print(f"\n🎯 Testing commands on {hostname} ({agent_id})")
            
            # Send a simple command
            status, result = await client.send_command(agent_id, "echo 'Hello from remote manager!'")
            print_json(result, f"COMMAND RESULT (Status: {status})")
            
            if status == 202 and "task_id" in result:
                task_id = result["task_id"]
                
                # Wait a bit and check task status
                await asyncio.sleep(2)
                status, task_status = await client.get_task_status(agent_id, task_id)
                print_json(task_status, f"TASK STATUS (Status: {status})")
            
            # Test broadcast command
            print(f"\n📡 Testing broadcast command to all online agents...")
            status, broadcast_result = await client.broadcast_command("hostname")
            print_json(broadcast_result, f"BROADCAST RESULT (Status: {status})")
        
        else:
            print("\n⚠️  No online agents found. Make sure your Rust agents are running and registered.")
        
    except httpx.RequestError as e:
        print(f"❌ Failed to connect to agent manager: {e}")
        print(f"Make sure the server is running on {BASE_URL}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 