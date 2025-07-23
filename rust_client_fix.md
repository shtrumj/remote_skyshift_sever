# Rust Client Fix for WebSocket Command Output

## Issue
The Rust client is failing with:
```
called `Result::unwrap()` on an `Err` value: Error("missing field `task_id`", line: 0, column: 0)
```

## Root Cause
The server is now sending `task_id` in the command data, but the Rust client's `CommandRequest` struct doesn't include this field.

## Fix

### 1. Update CommandRequest struct
Add the `task_id` field to your `CommandRequest` struct:

```rust
#[derive(Debug, Deserialize)]
pub struct CommandRequest {
    pub command: String,
    pub shell_type: String,
    pub timeout: Option<u64>,
    pub working_directory: Option<String>,
    pub environment: Option<std::collections::HashMap<String, String>>,
    pub task_id: Option<String>,  // Add this field
}
```

### 2. Update command execution
Use the task_id from the server instead of generating a new one:

```rust
async fn execute_command(&self, request: CommandRequest) -> TaskResult {
    // Use the task_id from the server, or generate a new one if not provided
    let task_id = request.task_id.unwrap_or_else(|| uuid::Uuid::new_v4().to_string());
    
    log::info!("🔧 Executing command: {} (shell: {}) with task_id: {}", 
               request.command, request.shell_type, task_id);
    
    // ... rest of your command execution logic
}
```

### 3. Send task result back via WebSocket
Make sure your task result includes the correct task_id:

```rust
async fn handle_command(&self, command_data: serde_json::Value) {
    let command_request: CommandRequest = serde_json::from_value(command_data).unwrap();
    
    log::info!("🔧 Executing command: {}", command_request.command);
    
    // Execute command
    let result = self.execute_command(command_request).await;
    
    // Send result back via WebSocket
    let task_result = serde_json::json!({
        "type": "task_result",
        "data": result
    });
    
    // Send the result back to the server
    if let Err(e) = self.websocket.send(Message::Text(task_result.to_string())).await {
        log::error!("❌ Failed to send task result: {}", e);
    } else {
        log::info!("📤 Task result sent successfully");
    }
}
```

## Testing
After making these changes:

1. Rebuild your Rust client
2. Restart the agent
3. Send a command from the web dashboard
4. Check that the command output appears in the task results panel

The server should now receive the task result with the correct task_id and display the actual command output instead of the mock message. 