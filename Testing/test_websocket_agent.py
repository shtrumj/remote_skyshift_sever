#!/usr/bin/env python3
"""
Test WebSocket Agent - Simulates a WebSocket agent for testing command output
"""

import asyncio
import json
import websockets
import uuid
import time
import subprocess
import platform
from datetime import datetime

class TestWebSocketAgent:
    def __init__(self, server_url, agent_id, hostname="test-agent"):
        self.server_url = server_url
        self.agent_id = agent_id
        self.hostname = hostname
        self.websocket = None
        
    async def connect(self):
        """Connect to the WebSocket endpoint"""
        ws_url = f"{self.server_url.replace('http', 'ws')}/ws/agent/{self.agent_id}"
        print(f"🔗 Connecting to WebSocket: {ws_url}")
        
        self.websocket = await websockets.connect(ws_url)
        print("✅ WebSocket connected successfully")
        
    async def send_heartbeat(self):
        """Send heartbeat message"""
        heartbeat = {
            "type": "heartbeat",
            "agent_id": self.agent_id,
            "status": "online"
        }
        await self.websocket.send(json.dumps(heartbeat))
        print("💓 Heartbeat sent")
        
    async def handle_message(self, message):
        """Handle incoming messages from server"""
        try:
            data = json.loads(message)
            print(f"📥 Received message: {data}")
            
            if data.get("type") == "command":
                print(f"🔧 Received command: {data.get('data', {})}")
                # Execute the actual command
                await self.execute_command(data.get("data", {}))
            elif data.get("type") == "heartbeat_ack":
                print("💓 Heartbeat acknowledged")
                
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON message: {message}")
            
    async def execute_command(self, command_data):
        """Actually execute the command and capture real output"""
        task_id = command_data.get("task_id", str(uuid.uuid4()))
        command = command_data.get("command", "unknown")
        shell_type = command_data.get("shell_type", "bash")
        
        print(f"🔧 Executing command: {command} (shell: {shell_type})")
        
        # Send task status update
        status_update = {
            "type": "task_status",
            "data": {
                "task_id": task_id,
                "status": "running",
                "command": command,
                "started_at": datetime.utcnow().isoformat()
            }
        }
        await self.websocket.send(json.dumps(status_update))
        print("📤 Sent task status: running")
        
        try:
            # Execute the command based on shell type
            if shell_type == "cmd":
                # Windows CMD
                process = await asyncio.create_subprocess_exec(
                    "cmd", "/C", command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
            elif shell_type == "powershell":
                # Windows PowerShell
                process = await asyncio.create_subprocess_exec(
                    "powershell", "-Command", command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
            else:
                # Bash/Linux
                process = await asyncio.create_subprocess_exec(
                    "bash", "-c", command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
            
            # Wait for completion
            stdout, stderr = await process.communicate()
            exit_code = process.returncode
            
            # Decode output
            output = stdout.decode('utf-8', errors='ignore')
            error = stderr.decode('utf-8', errors='ignore')
            
            print(f"✅ Command completed with exit code: {exit_code}")
            print(f"📤 Output: {output[:100]}...")  # Show first 100 chars
            
            # Send task result
            result = {
                "type": "task_result",
                "data": {
                    "task_id": task_id,
                    "status": "completed",
                    "command": command,
                    "output": output if output else None,
                    "error": error if error else None,
                    "exit_code": exit_code,
                    "completed_at": datetime.utcnow().isoformat()
                }
            }
            await self.websocket.send(json.dumps(result))
            print("📤 Sent task result: completed")
            
        except Exception as e:
            print(f"❌ Command execution failed: {e}")
            # Send error result
            result = {
                "type": "task_result",
                "data": {
                    "task_id": task_id,
                    "status": "failed",
                    "command": command,
                    "output": None,
                    "error": str(e),
                    "exit_code": -1,
                    "completed_at": datetime.utcnow().isoformat()
                }
            }
            await self.websocket.send(json.dumps(result))
            print("📤 Sent task result: failed")
        
    async def run(self):
        """Main run loop"""
        try:
            await self.connect()
            
            # Send initial heartbeat
            await self.send_heartbeat()
            
            # Main message loop
            while True:
                try:
                    message = await self.websocket.recv()
                    await self.handle_message(message)
                except websockets.exceptions.ConnectionClosed:
                    print("🔌 WebSocket connection closed")
                    break
                    
        except Exception as e:
            print(f"❌ WebSocket error: {e}")
        finally:
            if self.websocket:
                await self.websocket.close()

async def main():
    """Main function"""
    server_url = "http://localhost:4433"
    agent_id = "test-websocket-agent-001"
    
    agent = TestWebSocketAgent(server_url, agent_id)
    
    # Send heartbeat every 20 seconds
    async def heartbeat_loop():
        while True:
            try:
                await agent.send_heartbeat()
                await asyncio.sleep(20)
            except Exception as e:
                print(f"❌ Heartbeat error: {e}")
                break
    
    # Start heartbeat loop
    heartbeat_task = asyncio.create_task(heartbeat_loop())
    
    # Run the agent
    try:
        await agent.run()
    finally:
        heartbeat_task.cancel()

if __name__ == "__main__":
    print("🚀 Starting Test WebSocket Agent...")
    asyncio.run(main()) 