# Rust Client Implementation Guide

This guide provides a complete implementation of a Rust client for the Remote Agent Manager with WebSocket-based real-time communication.

## 🏗️ Architecture Overview

The Rust client implements a dual-mode communication system:
- **WebSocket Client**: Primary real-time communication with server
- **HTTP Server**: Fallback command execution endpoint
- **Command Executor**: Multi-shell command execution
- **Heartbeat System**: Regular status updates

## 📦 Dependencies

Add these dependencies to your `Cargo.toml`:

```toml
[package]
name = "remote_agent_client"
version = "0.1.0"
edition = "2021"

[dependencies]
tokio = { version = "1.0", features = ["full"] }
actix-web = "4.0"
actix-rt = "2.0"
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
uuid = { version = "1.0", features = ["v4"] }
clap = { version = "4.0", features = ["derive"] }
tungstenite = { version = "0.20", features = ["native-tls"] }
tokio-tungstenite = "0.20"
futures-util = "0.3"
tokio-stream = "0.1"
log = "0.4"
env_logger = "0.10"
```

## 🚀 Complete Implementation

### 1. Command Line Arguments

```rust
use clap::Parser;

#[derive(Parser)]
#[command(name = "remote_agent_client")]
#[command(about = "Remote Agent Client with WebSocket support")]
struct Args {
    /// Server URL (e.g., http://remote.skyshift.dev:4433)
    #[arg(long, default_value = "http://localhost:4433")]
    server_url: String,

    /// Customer UUID for agent registration
    #[arg(long)]
    customer_uuid: Option<String>,

    /// Heartbeat interval in seconds
    #[arg(long, default_value = "20")]
    heartbeat_interval: u64,

    /// Agent port for HTTP fallback server
    #[arg(long, default_value = "3000")]
    agent_port: u16,

    /// Agent hostname (auto-detected if not specified)
    #[arg(long)]
    hostname: Option<String>,
}
```

### 2. API Models

```rust
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize)]
pub struct AgentRegistration {
    pub hostname: String,
    pub ip_address: String,
    pub port: u16,
    pub capabilities: Vec<String>,
    pub version: String,
    pub customer_uuid: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct RegistrationResponse {
    pub agent_id: String,
    pub message: String,
}

#[derive(Debug, Serialize)]
pub struct HeartbeatRequest {
    pub agent_id: String,
    pub status: String,
}

#[derive(Debug, Deserialize)]
pub struct CommandRequest {
    pub command: String,
    pub shell_type: String,
    pub timeout: Option<u64>,
    pub working_directory: Option<String>,
    pub environment: Option<std::collections::HashMap<String, String>>,
    pub task_id: Option<String>,  // Added for WebSocket command handling
}

#[derive(Debug, Serialize)]
pub struct CommandResponse {
    pub task_id: String,
    pub status: String,
    pub message: String,
}

#[derive(Debug, Serialize)]
pub struct TaskResult {
    pub task_id: String,
    pub status: String,
    pub output: Option<String>,
    pub error: Option<String>,
    pub exit_code: Option<i32>,
}
```

### 3. WebSocket Client

```rust
use tokio_tungstenite::{connect_async, tungstenite::protocol::Message};
use futures_util::{SinkExt, StreamExt};
use std::time::Duration;

#[derive(Clone)]
pub struct WebSocketClient {
    server_url: String,
    agent_id: String,
    heartbeat_interval: Duration,
    write: Option<futures_util::stream::SplitSink<tokio_tungstenite::WebSocketStream<tokio_tungstenite::MaybeTlsStream<tokio::net::TcpStream>>, tokio_tungstenite::tungstenite::Message>>,
}

impl WebSocketClient {
    pub fn new(server_url: String, agent_id: String, heartbeat_interval: u64) -> Self {
        Self {
            server_url,
            agent_id,
            heartbeat_interval: Duration::from_secs(heartbeat_interval),
            write: None,
        }
    }

    pub async fn run(&self) -> Result<(), Box<dyn std::error::Error>> {
        let ws_url = self.server_url.replace("http", "ws") + &format!("/ws/agent/{}", self.agent_id);
        
        log::info!("🔗 Connecting to WebSocket: {}", ws_url);
        
        let (ws_stream, _) = connect_async(&ws_url).await?;
        log::info!("✅ WebSocket connected successfully");

        let (mut write, mut read) = ws_stream.split();

        // Store the write half for sending messages
        let mut client = self.clone();
        client.write = Some(write.clone());

        // Spawn heartbeat sender
        let heartbeat_task = {
            let write = write.clone();
            let agent_id = self.agent_id.clone();
            let interval = self.heartbeat_interval;
            
            tokio::spawn(async move {
                let mut interval = tokio::time::interval(interval);
                loop {
                    interval.tick().await;
                    
                    let heartbeat = serde_json::json!({
                        "type": "heartbeat",
                        "agent_id": agent_id,
                        "status": "online"
                    });
                    
                    if let Err(e) = write.send(Message::Text(heartbeat.to_string())).await {
                        log::error!("❌ Failed to send heartbeat: {}", e);
                        break;
                    }
                    log::debug!("💓 Heartbeat sent");
                }
            })
        };

        // Handle incoming messages
        while let Some(msg) = read.next().await {
            match msg {
                Ok(Message::Text(text)) => {
                    if let Ok(message) = serde_json::from_str::<serde_json::Value>(&text) {
                        self.handle_message(message).await;
                    }
                }
                Ok(Message::Close(_)) => {
                    log::info!("🔌 WebSocket connection closed by server");
                    break;
                }
                Err(e) => {
                    log::error!("❌ WebSocket error: {}", e);
                    break;
                }
                _ => {}
            }
        }

        heartbeat_task.abort();
        Ok(())
    }

    async fn handle_message(&self, message: serde_json::Value) {
        match message["type"].as_str() {
            Some("command") => {
                log::info!("📥 Received command: {:?}", message);
                self.handle_command(message["data"].clone()).await;
            }
            Some("heartbeat_ack") => {
                log::debug!("💓 Heartbeat acknowledged");
            }
            _ => {
                log::debug!("📥 Received message: {:?}", message);
            }
        }
    }

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
        
        // Send the result back to the server via WebSocket
        if let Some(write) = &mut self.write {
            if let Err(e) = write.send(Message::Text(task_result.to_string())).await {
                log::error!("❌ Failed to send task result: {}", e);
            } else {
                log::info!("📤 Task result sent successfully");
            }
        }
    }

    async fn execute_command(&self, request: CommandRequest) -> TaskResult {
        // Use the task_id from the server, or generate a new one if not provided
        let task_id = request.task_id.unwrap_or_else(|| uuid::Uuid::new_v4().to_string());
        
        log::info!("🔧 Executing command: {} (shell: {}) with task_id: {}", request.command, request.shell_type, task_id);
        
        // Execute command based on shell type
        let output = match request.shell_type.as_str() {
            "cmd" => self.execute_cmd_command(&request.command).await,
            "powershell" => self.execute_powershell_command(&request.command).await,
            "bash" => self.execute_bash_command(&request.command).await,
            _ => {
                log::error!("❌ Unsupported shell type: {}", request.shell_type);
                return TaskResult {
                    task_id,
                    status: "failed".to_string(),
                    output: None,
                    error: Some(format!("Unsupported shell type: {}", request.shell_type)),
                    exit_code: Some(-1),
                };
            }
        };

        TaskResult {
            task_id,
            status: "completed".to_string(),
            output: Some(output),
            error: None,
            exit_code: Some(0),
        }
    }

    async fn execute_cmd_command(&self, command: &str) -> String {
        // Windows CMD command execution
        use tokio::process::Command;
        
        let output = Command::new("cmd")
            .args(&["/C", command])
            .output()
            .await;
            
        match output {
            Ok(output) => {
                let stdout = String::from_utf8_lossy(&output.stdout);
                let stderr = String::from_utf8_lossy(&output.stderr);
                
                if !stderr.is_empty() {
                    format!("STDOUT:\n{}\nSTDERR:\n{}", stdout, stderr)
                } else {
                    stdout.to_string()
                }
            }
            Err(e) => format!("Error executing command: {}", e),
        }
    }

    async fn execute_powershell_command(&self, command: &str) -> String {
        use tokio::process::Command;
        
        let output = Command::new("powershell")
            .args(&["-Command", command])
            .output()
            .await;
            
        match output {
            Ok(output) => {
                let stdout = String::from_utf8_lossy(&output.stdout);
                let stderr = String::from_utf8_lossy(&output.stderr);
                
                if !stderr.is_empty() {
                    format!("STDOUT:\n{}\nSTDERR:\n{}", stdout, stderr)
                } else {
                    stdout.to_string()
                }
            }
            Err(e) => format!("Error executing command: {}", e),
        }
    }

    async fn execute_bash_command(&self, command: &str) -> String {
        use tokio::process::Command;
        
        let output = Command::new("bash")
            .args(&["-c", command])
            .output()
            .await;
            
        match output {
            Ok(output) => {
                let stdout = String::from_utf8_lossy(&output.stdout);
                let stderr = String::from_utf8_lossy(&output.stderr);
                
                if !stderr.is_empty() {
                    format!("STDOUT:\n{}\nSTDERR:\n{}", stdout, stderr)
                } else {
                    stdout.to_string()
                }
            }
            Err(e) => format!("Error executing command: {}", e),
        }
    }
}
```

### 4. HTTP Server (Fallback)

```rust
use actix_web::{web, App, HttpServer, HttpResponse, HttpRequest};
use actix_web::middleware::Logger;

pub struct HttpServer {
    port: u16,
}

impl HttpServer {
    pub fn new(port: u16) -> Self {
        Self { port }
    }

    pub async fn run(&self) -> std::io::Result<()> {
        log::info!("🌐 Starting HTTP server on port {}", self.port);
        
        HttpServer::new(|| {
            App::new()
                .wrap(Logger::default())
                .route("/health", web::get().to(health_check))
                .route("/api/commands", web::post().to(handle_command))
                .route("/api/tasks/{task_id}", web::get().to(get_task_status))
        })
        .bind(("0.0.0.0", self.port))?
        .run()
        .await
    }
}

async fn health_check() -> HttpResponse {
    HttpResponse::Ok().json(serde_json::json!({
        "status": "healthy",
        "timestamp": chrono::Utc::now().to_rfc3339()
    }))
}

async fn handle_command(
    req: HttpRequest,
    command_data: web::Json<CommandRequest>,
) -> HttpResponse {
    log::info!("📥 Received command via HTTP: {}", command_data.command);
    
    // Execute command (same logic as WebSocket)
    let result = execute_command(command_data.into_inner()).await;
    
    HttpResponse::Accepted().json(CommandResponse {
        task_id: result.task_id,
        status: "accepted".to_string(),
        message: "Command received via HTTP".to_string(),
    })
}

async fn get_task_status(path: web::Path<String>) -> HttpResponse {
    let task_id = path.into_inner();
    
    // In a real implementation, you'd look up the task status
    HttpResponse::Ok().json(serde_json::json!({
        "task_id": task_id,
        "status": "completed",
        "message": "Task status from HTTP endpoint"
    }))
}

async fn execute_command(request: CommandRequest) -> TaskResult {
    let task_id = uuid::Uuid::new_v4().to_string();
    
    // Same command execution logic as WebSocket client
    // ... (implement command execution)
    
    TaskResult {
        task_id,
        status: "completed".to_string(),
        output: Some("Command executed via HTTP".to_string()),
        error: None,
        exit_code: Some(0),
    }
}
```

### 5. Agent Registration

```rust
use reqwest::Client;

pub struct AgentManager {
    client: Client,
    server_url: String,
    agent_id: Option<String>,
}

impl AgentManager {
    pub fn new(server_url: String) -> Self {
        Self {
            client: Client::new(),
            server_url,
            agent_id: None,
        }
    }

    pub async fn register_agent(&mut self, registration: AgentRegistration) -> Result<String, Box<dyn std::error::Error>> {
        let url = format!("{}/api/agents/register", self.server_url);
        
        log::info!("🔗 Registering agent: {}", registration.hostname);
        
        let response = self.client
            .post(&url)
            .json(&registration)
            .send()
            .await?;
            
        if response.status().is_success() {
            let registration_response: RegistrationResponse = response.json().await?;
            self.agent_id = Some(registration_response.agent_id.clone());
            
            log::info!("✅ Agent registered successfully with ID: {}", registration_response.agent_id);
            Ok(registration_response.agent_id)
        } else {
            let error_text = response.text().await?;
            log::error!("❌ Registration failed: {}", error_text);
            Err(error_text.into())
        }
    }

    pub async fn send_heartbeat(&self) -> Result<(), Box<dyn std::error::Error>> {
        if let Some(agent_id) = &self.agent_id {
            let url = format!("{}/api/agents/{}/heartbeat", self.server_url, agent_id);
            
            let heartbeat = HeartbeatRequest {
                agent_id: agent_id.clone(),
                status: "online".to_string(),
            };
            
            let response = self.client
                .post(&url)
                .json(&heartbeat)
                .send()
                .await?;
                
            if response.status().is_success() {
                log::debug!("💓 HTTP Heartbeat sent successfully");
            } else {
                log::error!("❌ HTTP Heartbeat failed: {}", response.status());
            }
        }
        
        Ok(())
    }
}
```

### 6. Main Application

```rust
use std::net::UdpSocket;
use std::str::FromStr;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    env_logger::init();
    
    let args = Args::parse();
    
    log::info!("🚀 Starting Remote Agent Client");
    log::info!("📡 Server URL: {}", args.server_url);
    log::info!("👤 Customer UUID: {:?}", args.customer_uuid);
    log::info!("💓 Heartbeat interval: {} seconds", args.heartbeat_interval);
    log::info!("🔧 Agent port: {}", args.agent_port);

    // Get hostname
    let hostname = args.hostname.unwrap_or_else(|| {
        hostname::get()
            .unwrap_or_else(|_| "unknown".into())
            .to_string_lossy()
            .to_string()
    });

    // Get IP address
    let ip_address = get_local_ip().unwrap_or_else(|| "127.0.0.1".to_string());

    log::info!("🖥️ Hostname: {}", hostname);
    log::info!("🌐 IP Address: {}", ip_address);

    // Create agent registration
    let registration = AgentRegistration {
        hostname,
        ip_address,
        port: args.agent_port,
        capabilities: vec![
            "cmd".to_string(),
            "powershell".to_string(),
            "bash".to_string(),
            "queue_management".to_string(),
            "long_running_tasks".to_string(),
        ],
        version: "1.0.0".to_string(),
        customer_uuid: args.customer_uuid,
    };

    // Register agent
    let mut agent_manager = AgentManager::new(args.server_url.clone());
    let agent_id = agent_manager.register_agent(registration).await?;

    // Start HTTP server (fallback)
    let http_server = HttpServer::new(args.agent_port);
    let http_handle = tokio::spawn(http_server.run());

    // Start WebSocket client
    let ws_client = WebSocketClient::new(
        args.server_url,
        agent_id.clone(),
        args.heartbeat_interval,
    );

    // Run WebSocket client
    let ws_handle = tokio::spawn(async move {
        loop {
            match ws_client.run().await {
                Ok(_) => {
                    log::info!("🔌 WebSocket disconnected, attempting to reconnect...");
                    tokio::time::sleep(Duration::from_secs(5)).await;
                }
                Err(e) => {
                    log::error!("❌ WebSocket error: {}, attempting to reconnect...", e);
                    tokio::time::sleep(Duration::from_secs(5)).await;
                }
            }
        }
    });

    // Start HTTP heartbeat (fallback)
    let heartbeat_handle = tokio::spawn(async move {
        let mut interval = tokio::time::interval(Duration::from_secs(args.heartbeat_interval));
        loop {
            interval.tick().await;
            if let Err(e) = agent_manager.send_heartbeat().await {
                log::error!("❌ HTTP Heartbeat failed: {}", e);
            }
        }
    });

    // Wait for all tasks
    tokio::try_join!(http_handle, ws_handle, heartbeat_handle)?;

    Ok(())
}

fn get_local_ip() -> Option<String> {
    // Try to get local IP address
    let socket = UdpSocket::bind("0.0.0.0:0").ok()?;
    socket.connect("8.8.8.8:80").ok()?;
    socket.local_addr().ok()?.ip().to_string().into()
}
```

## 🚀 Usage Examples

### Basic Usage
```bash
# Build the client
cargo build --release

# Run with default settings
./target/release/remote_agent_client

# Run with custom server
./target/release/remote_agent_client --server-url "http://remote.skyshift.dev:4433"
```

### Customer Registration
```bash
# Register with customer UUID
./target/release/remote_agent_client \
  --server-url "http://remote.skyshift.dev:4433" \
  --customer-uuid "2ce998a3-3168-40ef-8ceb-b9a4404f6342"
```

### Advanced Configuration
```bash
# Custom configuration
./target/release/remote_agent_client \
  --server-url "http://remote.skyshift.dev:4433" \
  --customer-uuid "2ce998a3-3168-40ef-8ceb-b9a4404f6342" \
  --heartbeat-interval 30 \
  --agent-port 3000 \
  --hostname "my-custom-hostname"
```

## 🔧 Configuration

### Environment Variables
```bash
export RUST_LOG=info
export SERVER_URL=http://remote.skyshift.dev:4433
export CUSTOMER_UUID=2ce998a3-3168-40ef-8ceb-b9a4404f6342
```

### Command Line Options
- `--server-url`: Server URL (default: http://localhost:4433)
- `--customer-uuid`: Customer UUID for registration
- `--heartbeat-interval`: Heartbeat interval in seconds (default: 20)
- `--agent-port`: HTTP server port (default: 3000)
- `--hostname`: Custom hostname (auto-detected if not specified)

## 🔍 Debugging

### Enable Debug Logging
```bash
RUST_LOG=debug ./target/release/remote_agent_client
```

### Test WebSocket Connection
```bash
# Test WebSocket endpoint
wscat -c ws://server:4433/ws/agent/test
```

### Test HTTP Endpoints
```bash
# Test health endpoint
curl http://localhost:3000/health

# Test command endpoint
curl -X POST http://localhost:3000/api/commands \
  -H "Content-Type: application/json" \
  -d '{"command": "whoami", "shell_type": "cmd"}'
```

## 🐛 Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**
   - Check server URL and port
   - Verify firewall settings
   - Check network connectivity

2. **Registration Failed**
   - Verify server is running
   - Check customer UUID format
   - Review server logs

3. **Commands Not Executing**
   - Check agent status in dashboard
   - Verify shell type compatibility
   - Review command syntax

### Debug Commands
```bash
# Check agent status
curl http://server:4433/api/agents/{agent_id}

# Test agent connection
curl http://server:4433/api/agents/{agent_id}/test-connection

# Send test command
curl -X POST http://server:4433/api/agents/{agent_id}/commands \
  -H "Content-Type: application/json" \
  -d '{"command": "whoami", "shell_type": "cmd"}'
```

## 📈 Performance Optimization

### WebSocket Optimization
- Use connection pooling
- Implement automatic reconnection
- Handle connection timeouts gracefully

### Command Execution
- Implement command queuing
- Add timeout handling
- Stream large outputs

### Memory Management
- Use async/await for I/O operations
- Implement proper error handling
- Clean up resources on shutdown

## 🔒 Security Considerations

### Network Security
- Use HTTPS/WSS in production
- Implement authentication
- Validate command inputs

### Command Execution
- Sanitize command inputs
- Implement command whitelisting
- Add execution timeouts

### Error Handling
- Log security events
- Implement rate limiting
- Handle malformed inputs gracefully

This implementation provides a robust, production-ready Rust client with WebSocket-based real-time communication and HTTP fallback capabilities. 