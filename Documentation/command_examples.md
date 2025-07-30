# Command Execution Guide for Registered Agents

## 🎯 **How to Send Commands to Registered Agents**

### **Method 1: Send Command to Specific Agent**

```bash
# Send command to a specific agent by ID
curl -X POST "https://remote.skyshift.dev:443/api/agents/{AGENT_ID}/commands" \
  -H "Content-Type: application/json" \
  -d '{
    "command": "echo \"Hello from remote manager!\"",
    "shell_type": "bash",
    "timeout": 30
  }'
```

**Example with real agent ID:**

```bash
curl -X POST "https://remote.skyshift.dev:443/api/agents/2ee09ba5-e227-400b-993e-6a97faaff50d/commands" \
  -H "Content-Type: application/json" \
  -d '{
    "command": "hostname && whoami",
    "shell_type": "bash",
    "timeout": 30
  }'
```

### **Method 2: Broadcast Command to All Online Agents**

```bash
# Send command to ALL online agents
curl -X POST "https://remote.skyshift.dev:443/api/commands/broadcast" \
  -H "Content-Type: application/json" \
  -d '{
    "command": "echo \"Broadcast message\"",
    "shell_type": "bash",
    "timeout": 30
  }'
```

### **Method 3: Check Task Status**

```bash
# Get status of a specific task
curl -X GET "https://remote.skyshift.dev:443/api/agents/{AGENT_ID}/tasks/{TASK_ID}"

# Example:
curl -X GET "https://remote.skyshift.dev:443/api/agents/2ee09ba5-e227-400b-993e-6a97faaff50d/tasks/abc123"
```

### **Method 4: List All Tasks for an Agent**

```bash
# Get all tasks for a specific agent
curl -X GET "https://remote.skyshift.dev:443/api/agents/{AGENT_ID}/tasks"

# Example:
curl -X GET "https://remote.skyshift.dev:443/api/agents/2ee09ba5-e227-400b-993e-6a97faaff50d/tasks"
```

## 📋 **Command Request Format**

```json
{
  "command": "your command here",
  "args": ["optional", "arguments"],
  "shell_type": "bash|cmd|powershell",
  "timeout": 30,
  "working_directory": "/optional/path",
  "environment": {
    "VAR1": "value1",
    "VAR2": "value2"
  }
}
```

## 🎯 **Available Shell Types**

- `"bash"` - Linux/macOS bash shell
- `"cmd"` - Windows Command Prompt
- `"powershell"` - Windows PowerShell

## 📊 **Response Format**

**Successful Command Submission:**

```json
{
  "task_id": "uuid-task-id",
  "status": "pending",
  "message": "Command submitted successfully"
}
```

**Task Status Response:**

```json
{
  "id": "task-id",
  "status": "completed|running|failed",
  "command": "echo hello",
  "created_at": "2025-07-20T12:00:00",
  "started_at": "2025-07-20T12:00:01",
  "completed_at": "2025-07-20T12:00:05",
  "exit_code": 0,
  "output": "hello\n",
  "error": null,
  "logs": ["[STDOUT] hello"]
}
```

## 🔍 **Step-by-Step Example**

### **1. List Available Agents**

```bash
curl -X GET "https://remote.skyshift.dev:443/api/agents"
```

### **2. Send Command to Agent**

```bash
curl -X POST "https://remote.skyshift.dev:443/api/agents/2ee09ba5-e227-400b-993e-6a97faaff50d/commands" \
  -H "Content-Type: application/json" \
  -d '{
    "command": "ls -la",
    "shell_type": "bash"
  }'
```

### **3. Check Task Status**

```bash
# Use the task_id from step 2
curl -X GET "https://remote.skyshift.dev:443/api/agents/2ee09ba5-e227-400b-993e-6a97faaff50d/tasks/{TASK_ID}"
```

## 🚀 **Advanced Examples**

### **Long-Running Command**

```bash
curl -X POST "https://remote.skyshift.dev:443/api/agents/{AGENT_ID}/commands" \
  -H "Content-Type: application/json" \
  -d '{
    "command": "sleep 10 && echo \"Long task completed\"",
    "shell_type": "bash",
    "timeout": 60
  }'
```

### **Command with Environment Variables**

```bash
curl -X POST "https://remote.skyshift.dev:443/api/agents/{AGENT_ID}/commands" \
  -H "Content-Type: application/json" \
  -d '{
    "command": "echo $CUSTOM_VAR",
    "shell_type": "bash",
    "environment": {
      "CUSTOM_VAR": "Hello from environment!"
    }
  }'
```

### **Windows PowerShell Command**

```bash
curl -X POST "https://remote.skyshift.dev:443/api/agents/{AGENT_ID}/commands" \
  -H "Content-Type: application/json" \
  -d '{
    "command": "Get-Process | Select-Object Name, CPU",
    "shell_type": "powershell"
  }'
```

## ⚠️ **Important Notes**

1. **Agent must be online** - Commands only work on agents with "online" status
2. **Task ID tracking** - Always save the task_id from the response to check status
3. **Timeout handling** - Commands will timeout after the specified seconds
4. **Error handling** - Check both `output` and `error` fields in task status
5. **Logs** - All stdout/stderr is captured in the logs array
