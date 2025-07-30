# Remote Agent Manager - Interface Documentation

## Server Information

### Server Startup

- **Primary startup command**: `python run_servers.py`
- **HTTP Server**: `http://remote.skyshift.dev:80`
- **HTTPS Server**: `https://remote.skyshift.dev:443`
- **WebSocket Endpoint**: `ws://remote.skyshift.dev:80/ws/agent/{agent_id}` or `wss://remote.skyshift.dev:443/ws/agent/{agent_id}`

### Authentication

The server supports two types of authentication:

#### 1. User Authentication (JWT Bearer Token)

- **For**: Web interface users and administrators
- **Token Expiry**: 30 minutes
- **Flow**:
  1. **Register**: `POST /api/auth/register`
  2. **Login**: `POST /api/auth/login`
  3. **Use token**: Include `Authorization: Bearer <token>` header

#### 2. Customer Authentication (API Key)

- **For**: API clients and automated systems
- **API Key Format**: `sk_<random_string>`
- **Flow**:
  1. **Admin generates API key**: `POST /api/customers/{customer_uuid}/generate-api-key`
  2. **Use API key**: Include `Authorization: Bearer <api_key>` or `X-API-Key: <api_key>` header

## API Endpoints

### Authentication Endpoints

#### Register User

```http
POST /api/auth/register
Content-Type: application/json

{
  "username": "string",
  "email": "string",
  "password": "string",
  "full_name": "string (optional)"
}
```

**Response**:

```json
{
  "user_id": "uuid",
  "message": "User registered successfully"
}
```

#### Login User

```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "string",
  "password": "string"
}
```

**Response**:

```json
{
  "access_token": "jwt_token",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "username": "string",
    "email": "string",
    "full_name": "string"
  }
}
```

### User Management Endpoints

#### Get User Profile

```http
GET /api/users/profile
Authorization: Bearer <token>
```

#### Update Profile

```http
PUT /api/users/profile
Authorization: Bearer <token>
Content-Type: application/json

{
  "email": "string (optional)",
  "full_name": "string (optional)"
}
```

#### Change Password

```http
POST /api/users/change-password
Authorization: Bearer <token>
Content-Type: application/json

{
  "current_password": "string",
  "new_password": "string"
}
```

#### List All Users (Admin Only)

```http
GET /api/users
Authorization: Bearer <token>
```

#### Get Specific User

```http
GET /api/users/{user_id}
Authorization: Bearer <token>
```

#### Delete User (Admin Only)

```http
DELETE /api/users/{user_id}
Authorization: Bearer <token>
```

### Agent Management Endpoints

#### Register Agent

```http
POST /api/agents/register
Content-Type: application/json

{
  "hostname": "string",
  "ip_address": "string",
  "port": "integer",
  "capabilities": ["string"],
  "version": "string",
  "customer_uuid": "string (optional)"
}
```

**Response**:

```json
{
  "agent_id": "uuid",
  "status": "registered",
  "message": "Agent registered successfully"
}
```

#### Send Heartbeat

```http
POST /api/agents/{agent_id}/heartbeat
Content-Type: application/json

{
  "agent_id": "string",
  "status": "online"
}
```

#### List All Agents

```http
GET /api/agents
```

**Response**:

```json
{
  "agents": [
    {
      "agent_id": "uuid",
      "hostname": "string",
      "ip_address": "string",
      "port": "integer",
      "capabilities": ["string"],
      "version": "string",
      "registered_at": "datetime",
      "last_heartbeat": "datetime",
      "status": "online|offline",
      "customer_uuid": "string (optional)",
      "customer_name": "string (optional)",
      "websocket_connected": "boolean"
    }
  ],
  "total": "integer",
  "online": "integer",
  "offline": "integer"
}
```

#### List Online Agents

```http
GET /api/agents/online
```

#### Get Agent Status

```http
GET /api/agents/{agent_id}
```

#### Unregister Agent

```http
DELETE /api/agents/{agent_id}
```

### Command Execution Endpoints

#### Send Command to Agent

```http
POST /api/agents/{agent_id}/commands
Authorization: Bearer <token>
Content-Type: application/json

{
  "command": "string",
  "args": ["string"] (optional),
  "shell_type": "cmd|powershell|bash",
  "timeout": "integer (optional, default: 30)",
  "working_directory": "string (optional)",
  "environment": {"key": "value"} (optional)
}
```

**Response**:

```json
{
  "task_id": "uuid",
  "status": "accepted|pending",
  "message": "string"
}
```

#### Get Pending Commands (HTTP Agents)

```http
GET /api/agents/{agent_id}/commands
```

**Response**:

```json
{
  "commands": [
    {
      "task_id": "uuid",
      "agent_id": "uuid",
      "type": "command",
      "command": "string",
      "shell_type": "cmd|powershell|bash",
      "timeout": "integer",
      "working_directory": "string (optional)",
      "environment": {"key": "value"} (optional)
    }
  ],
  "count": "integer"
}
```

#### Get Agent Tasks

```http
GET /api/agents/{agent_id}/tasks
```

**Response**:

```json
{
  "tasks": [
    {
      "task_id": "uuid",
      "status": "pending|running|completed|failed",
      "output": "string",
      "error": "string (optional)",
      "exit_code": "integer (optional)"
    }
  ],
  "count": "integer"
}
```

#### Get Task Status

```http
GET /api/agents/{agent_id}/tasks/{task_id}
Authorization: Bearer <token>
```

**Response**:

```json
{
  "task_id": "uuid",
  "status": "pending|running|completed|failed",
  "output": "string (full command output, not truncated)",
  "error": "string (optional)",
  "exit_code": "integer (optional)"
}
```

**Note**: The output field contains the complete command output, not just the first line. The frontend will display this in a resizable, auto-adjusting text area.

#### Submit Task Result (HTTP Agents)

```http
POST /api/agents/{agent_id}/tasks/{task_id}/result
Content-Type: application/json

{
  "status": "completed|failed",
  "output": "string",
  "error": "string (optional)",
  "exit_code": "integer (optional)"
}
```

**Response**:

```json
{
  "message": "Task result submitted successfully"
}
```

### Customer Management Endpoints

#### Create Customer

```http
POST /api/customers
Content-Type: application/json

{
  "name": "string",
  "address": "string (optional)"
}
```

#### List Customers

```http
GET /api/customers
```

#### Get Customer

```http
GET /api/customers/{customer_uuid}
```

#### Update Customer

```http
PUT /api/customers/{customer_uuid}
Content-Type: application/json

{
  "name": "string",
  "address": "string (optional)"
}
```

#### Delete Customer

```http
DELETE /api/customers/{customer_uuid}
```

### Customer API Key Management Endpoints

#### Generate API Key (Admin Only)

```http
POST /api/customers/{customer_uuid}/generate-api-key
Authorization: Bearer <admin_token>
```

**Response**:

```json
{
  "customer_uuid": "uuid",
  "api_key": "sk_<random_string>",
  "message": "API key generated successfully"
}
```

#### Revoke API Key (Admin Only)

```http
POST /api/customers/{customer_uuid}/revoke-api-key
Authorization: Bearer <admin_token>
```

#### Get API Key Info (Admin Only)

```http
GET /api/customers/{customer_uuid}/api-key-info
Authorization: Bearer <admin_token>
```

**Response**:

```json
{
  "customer_uuid": "uuid",
  "has_api_key": "boolean",
  "api_key_created_at": "datetime (optional)",
  "api_key_last_used": "datetime (optional)"
}
```

#### Download Configuration File (Admin Only)

```http
GET /api/customers/{customer_uuid}/download-config
Authorization: Bearer <admin_token>
```

**Response**: Downloads a `id.ini` configuration file containing:

```ini
# Remote Agent Configuration File
# Copy this file to id.ini and update with your actual values

# Customer UUID - Required
# This identifies your customer account
customer_id = <customer_uuid>

# API Key - Required for authentication
# Format: sk_<random_string>
# Get this from your admin via POST /api/customers/{customer_uuid}/generate-api-key
api_key = <api_key>

# Agent Configuration - Optional
# These will be auto-detected if not specified
hostname = AUTO_DETECT
ip_address = AUTO_DETECT
port = 3002
version = 1.0.0

# Capabilities - Optional
# List of what this agent can do
capabilities = ["command_execution", "file_transfer", "system_monitoring"]
```

**Note**: This endpoint requires the customer to have an API key generated first.

### Customer-Authenticated Endpoints

#### Get Customer Profile

```http
GET /api/customer/profile
Authorization: Bearer <api_key>
```

#### Get Customer Agents

```http
GET /api/customer/agents
Authorization: Bearer <api_key>
```

#### Get Customer Scripts

```http
GET /api/customer/scripts
Authorization: Bearer <api_key>
```

### Script Management Endpoints

#### Create Script

```http
POST /api/scripts
Content-Type: application/json

{
  "name": "string",
  "description": "string (optional)",
  "content": "string",
  "script_type": "cmd|powershell|bash",
  "customer_uuid": "string (optional)"
}
```

#### List Scripts

```http
GET /api/scripts
```

#### Get Script

```http
GET /api/scripts/{script_id}
```

#### Update Script

```http
PUT /api/scripts/{script_id}
Content-Type: application/json

{
  "name": "string",
  "description": "string (optional)",
  "content": "string",
  "script_type": "cmd|powershell|bash",
  "customer_uuid": "string (optional)"
}
```

#### Delete Script

```http
DELETE /api/scripts/{script_id}
```

#### Execute Script

```http
POST /api/scripts/{script_id}/execute
Authorization: Bearer <token>
Content-Type: application/json

{
  "agent_id": "string",
  "parameters": {"key": "value"} (optional)
}
```

### Admin Endpoints (Admin Only)

#### Get Pending Users

```http
GET /api/admin/pending-users
Authorization: Bearer <token>
```

#### Approve User

```http
POST /api/admin/users/{user_id}/approve
Authorization: Bearer <token>
```

#### Reject User

```http
POST /api/admin/users/{user_id}/reject
Authorization: Bearer <token>
```

#### Make User Admin

```http
POST /api/admin/users/{user_id}/make-admin
Authorization: Bearer <token>
```

#### Remove Admin Privileges

```http
POST /api/admin/users/{user_id}/remove-admin
Authorization: Bearer <token>
```

### Utility Endpoints

#### Health Check

```http
GET /api/health
```

**Response**:

```json
{
  "status": "healthy",
  "agents": {
    "total": "integer",
    "online": "integer",
    "offline": "integer"
  },
  "websocket_connections": "integer"
}
```

#### API Root

```http
GET /api
```

## WebSocket Protocol

### Agent WebSocket Connection

**Endpoint**: `ws://remote.skyshift.dev:80/ws/agent/{agent_id}` or `wss://remote.skyshift.dev:443/ws/agent/{agent_id}`

### Message Types

#### 1. Heartbeat (Agent → Server)

```json
{
  "type": "heartbeat"
}
```

**Server Response**:

```json
{
  "type": "heartbeat_ack",
  "timestamp": "datetime"
}
```

#### 2. Command (Server → Agent)

```json
{
  "type": "command",
  "task_id": "uuid",
  "command": "string",
  "shell_type": "cmd|powershell|bash",
  "timeout": "integer",
  "working_directory": "string (optional)",
  "environment": {"key": "value"} (optional)
}
```

#### 3. Task Result (Agent → Server)

```json
{
  "type": "task_result",
  "data": {
    "task_id": "uuid",
    "status": "completed|failed",
    "output": "string",
    "error": "string (optional)",
    "exit_code": "integer (optional)"
  }
}
```

#### 4. Task Status (Agent → Server)

```json
{
  "type": "task_status",
  "data": {
    "task_id": "uuid",
    "status": "running|completed|failed",
    "output": "string (partial)",
    "error": "string (optional)"
  }
}
```

## Data Models

### Shell Types

- `cmd` - Windows Command Prompt
- `powershell` - Windows PowerShell
- `bash` - Unix/Linux Bash

### Agent Status

- `online` - Agent is active and responding
- `offline` - Agent has not sent heartbeat recently

### Task Status

- `pending` - Task is queued
- `running` - Task is currently executing
- `completed` - Task finished successfully
- `failed` - Task failed with error

### User Roles

- **Regular User**: Can manage agents, execute commands, manage scripts
- **Admin User**: All regular user permissions plus user management and approval

## Error Responses

All endpoints return standard HTTP status codes:

- `200` - Success
- `400` - Bad Request (validation error)
- `401` - Unauthorized (invalid/missing token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `422` - Validation Error (invalid request body)
- `500` - Internal Server Error

Error response format:

```json
{
  "detail": "Error message description"
}
```

## Security Notes

1. **JWT Tokens**: User tokens expire after 30 minutes
2. **API Keys**: Customer API keys are long-lived and should be kept secure
3. **User Approval**: New users require admin approval before login
4. **Admin Functions**: User management and API key generation require admin privileges
5. **Customer Isolation**: Customers can only access their own resources
6. **SSL/TLS**: HTTPS server available on port 443
7. **CORS**: Server allows all origins (configure for production)

## Example Usage

### Python Client Example

#### User Authentication (JWT Token)

```python
import requests
import json

# Base URL
base_url = "https://remote.skyshift.dev:443"

# Register and login
register_data = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123",
    "full_name": "Test User"
}

response = requests.post(f"{base_url}/api/auth/register", json=register_data)
print(response.json())

# Login
login_data = {
    "username": "testuser",
    "password": "password123"
}

response = requests.post(f"{base_url}/api/auth/login", json=login_data)
token = response.json()["access_token"]

# Use token for authenticated requests
headers = {"Authorization": f"Bearer {token}"}

# List agents
response = requests.get(f"{base_url}/api/agents", headers=headers)
agents = response.json()
print(agents)

# Send command to agent
command_data = {
    "command": "dir",
    "shell_type": "cmd",
    "timeout": 30
}

response = requests.post(
    f"{base_url}/api/agents/{agent_id}/commands",
    json=command_data,
    headers=headers
)
result = response.json()
print(result)
```

#### Customer Authentication (API Key)

```python
import requests
import json

# Base URL
base_url = "https://remote.skyshift.dev:443"

# Customer API key (obtained from admin)
api_key = "sk_your_customer_api_key_here"

# Use API key for authenticated requests
headers = {"Authorization": f"Bearer {api_key}"}
# Alternative: headers = {"X-API-Key": api_key}

# Get customer profile
response = requests.get(f"{base_url}/api/customer/profile", headers=headers)
profile = response.json()
print(profile)

# Get customer's agents
response = requests.get(f"{base_url}/api/customer/agents", headers=headers)
agents = response.json()
print(agents)

# Get customer's scripts
response = requests.get(f"{base_url}/api/customer/scripts", headers=headers)
scripts = response.json()
print(scripts)
```

### WebSocket Client Example

```python
import asyncio
import websockets
import json

async def agent_websocket(agent_id):
    uri = f"wss://remote.skyshift.dev:443/ws/agent/{agent_id}"

    async with websockets.connect(uri) as websocket:
        # Send heartbeat
        await websocket.send(json.dumps({"type": "heartbeat"}))

        # Listen for commands
        async for message in websocket:
            data = json.loads(message)

            if data["type"] == "command":
                # Execute command and send result
                result = {
                    "type": "task_result",
                    "data": {
                        "task_id": data["task_id"],
                        "status": "completed",
                        "output": "Command output here",
                        "exit_code": 0
                    }
                }
                await websocket.send(json.dumps(result))

# Run the agent
asyncio.run(agent_websocket("your-agent-id"))
```

## Notes

1. **Server Startup**: Always use `python run_servers.py` to start both HTTP and HTTPS servers
2. **Certificate Generation**: SSL certificates are automatically generated on first run
3. **Database**: Uses SQLite database for persistence
4. **Logging**: Comprehensive logging for debugging and monitoring
5. **Background Tasks**: Automatic cleanup of offline agents every minute
6. **Agent Types**:
   - **WebSocket Agents**: Receive commands via WebSocket and return results immediately
   - **HTTP Agents**: Receive commands via HTTP and must submit results using the task result endpoint
7. **Command Execution**: HTTP agents should execute commands locally and submit results via `POST /api/agents/{agent_id}/tasks/{task_id}/result`
8. **Output Display**: Task results display the complete command output in a resizable, auto-adjusting text area on the frontend
