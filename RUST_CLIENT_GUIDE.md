# Rust Client Implementation Guide

This guide explains how to implement a Rust client that can register with the Remote Agent Manager server using customer UUIDs.

## 🎯 Overview

Your Rust client should:
1. Accept a customer UUID as a command-line argument
2. Register with the server using the customer UUID
3. Send periodic heartbeats
4. Execute commands received from the server
5. Report command results back to the server

## 📦 Dependencies

Add these to your `Cargo.toml`:

```toml
[dependencies]
tokio = { version = "1.0", features = ["full"] }
reqwest = { version = "0.11", features = ["json"] }
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
clap = { version = "4.0", features = ["derive"] }
uuid = { version = "1.0", features = ["v4"] }
hostname = "0.3"
local-ip-address = "0.5"
```

## 🔧 Command Line Arguments

```rust
use clap::Parser;

#[derive(Parser)]
#[command(name = "remote-agent")]
#[command(about = "Remote Agent Manager Client")]
struct Args {
    /// Customer UUID for agent registration
    #[arg(long, env = "CUSTOMER_UUID")]
    customer_uuid: Option<String>,
    
    /// Server URL
    #[arg(long, default_value = "http://localhost:4433")]
    server_url: String,
    
    /// Heartbeat interval in seconds
    #[arg(long, default_value = "30")]
    heartbeat_interval: u64,
    
    /// Agent port for command execution
    #[arg(long, default_value = "3000")]
    agent_port: u16,
}
```

## 📡 API Models

```rust
use serde::{Deserialize, Serialize};

#[derive(Serialize)]
struct AgentRegistration {
    hostname: String,
    ip_address: String,
    port: u16,
    capabilities: Vec<String>,
    version: String,
    customer_uuid: Option<String>, // Add this field
}

#[derive(Serialize)]
struct HeartbeatRequest {
    agent_id: String,
    status: String,
}

#[derive(Deserialize)]
struct CommandRequest {
    command: String,
    args: Option<Vec<String>>,
    shell_type: String,
    timeout: Option<u32>,
    working_directory: Option<String>,
    environment: Option<std::collections::HashMap<String, String>>,
}

#[derive(Serialize)]
struct CommandResponse {
    task_id: String,
    status: String,
    message: String,
}
```

## 🚀 Main Client Implementation

```rust
use std::process::Command;
use tokio::time::{sleep, Duration};
use uuid::Uuid;

struct AgentClient {
    server_url: String,
    agent_id: String,
    customer_uuid: Option<String>,
    heartbeat_interval: u64,
}

impl AgentClient {
    fn new(server_url: String, customer_uuid: Option<String>, heartbeat_interval: u64) -> Self {
        Self {
            server_url,
            agent_id: Uuid::new_v4().to_string(),
            customer_uuid,
            heartbeat_interval,
        }
    }

    async fn register(&self) -> Result<(), Box<dyn std::error::Error>> {
        let hostname = hostname::get()?.to_string_lossy().to_string();
        let ip_address = local_ip_address::local_ip()?.to_string();
        
        let registration = AgentRegistration {
            hostname,
            ip_address,
            port: 3000, // Your agent port
            capabilities: vec![
                "cmd".to_string(),
                "powershell".to_string(),
                "bash".to_string(),
                "queue_management".to_string(),
                "long_running_tasks".to_string(),
            ],
            version: "1.0.0".to_string(),
            customer_uuid: self.customer_uuid.clone(), // Include customer UUID
        };

        let client = reqwest::Client::new();
        let response = client
            .post(&format!("{}/api/agents/register", self.server_url))
            .json(&registration)
            .send()
            .await?;

        if response.status().is_success() {
            println!("✅ Agent registered successfully");
        } else {
            println!("❌ Registration failed: {}", response.text().await?);
        }

        Ok(())
    }

    async fn send_heartbeat(&self) -> Result<(), Box<dyn std::error::Error>> {
        let heartbeat = HeartbeatRequest {
            agent_id: self.agent_id.clone(),
            status: "online".to_string(),
        };

        let client = reqwest::Client::new();
        let response = client
            .post(&format!("{}/api/agents/{}/heartbeat", self.server_url, self.agent_id))
            .json(&heartbeat)
            .send()
            .await?;

        if response.status().is_success() {
            println!("💓 Heartbeat sent");
        } else {
            println!("❌ Heartbeat failed: {}", response.text().await?);
        }

        Ok(())
    }

    async fn start_command_server(&self) {
        // Start your HTTP server to receive commands
        // This is where you'd implement the command execution endpoint
        println!("🚀 Command server started on port 3000");
    }

    async fn run(&self) -> Result<(), Box<dyn std::error::Error>> {
        // Register with the server
        self.register().await?;
        
        // Start command server
        self.start_command_server().await;
        
        // Send periodic heartbeats
        loop {
            sleep(Duration::from_secs(self.heartbeat_interval)).await;
            if let Err(e) = self.send_heartbeat().await {
                println!("❌ Heartbeat error: {}", e);
            }
        }
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args = Args::parse();
    
    println!("🚀 Starting Remote Agent Client");
    println!("📡 Server URL: {}", args.server_url);
    if let Some(uuid) = &args.customer_uuid {
        println!("👤 Customer UUID: {}", uuid);
    } else {
        println!("⚠️  No customer UUID provided");
    }
    
    let client = AgentClient::new(
        args.server_url,
        args.customer_uuid,
        args.heartbeat_interval,
    );
    
    client.run().await
}
```

## 🔄 Command Execution Endpoint

Your Rust client should also implement an HTTP server to receive commands:

```rust
use axum::{
    routing::{get, post},
    http::StatusCode,
    Json, Router,
};

async fn handle_command(Json(command): Json<CommandRequest>) -> (StatusCode, Json<CommandResponse>) {
    let task_id = Uuid::new_v4().to_string();
    
    // Execute the command
    let output = match execute_command(&command.command, &command.shell_type).await {
        Ok(output) => output,
        Err(e) => {
            return (
                StatusCode::INTERNAL_SERVER_ERROR,
                Json(CommandResponse {
                    task_id: task_id.clone(),
                    status: "failed".to_string(),
                    message: e.to_string(),
                }),
            );
        }
    };
    
    (
        StatusCode::ACCEPTED,
        Json(CommandResponse {
            task_id,
            status: "completed".to_string(),
            message: "Command executed successfully".to_string(),
        }),
    )
}

async fn execute_command(command: &str, shell_type: &str) -> Result<String, Box<dyn std::error::Error>> {
    let output = match shell_type {
        "cmd" => Command::new("cmd")
            .args(["/C", command])
            .output()?,
        "powershell" => Command::new("powershell")
            .args(["-Command", command])
            .output()?,
        "bash" => Command::new("bash")
            .args(["-c", command])
            .output()?,
        _ => return Err("Unsupported shell type".into()),
    };
    
    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);
    
    Ok(format!("STDOUT:\n{}\nSTDERR:\n{}", stdout, stderr))
}

async fn start_command_server() {
    let app = Router::new()
        .route("/api/commands", post(handle_command))
        .route("/health", get(|| async { "OK" }));
    
    let listener = tokio::net::TcpListener::bind("0.0.0.0:3000").await.unwrap();
    println!("🚀 Command server listening on port 3000");
    
    axum::serve(listener, app).await.unwrap();
}
```

## 🎯 Usage Examples

### Basic Usage (No Customer)
```bash
cargo run --release
```

### With Customer UUID
```bash
cargo run --release --customer-uuid "123e4567-e89b-12d3-a456-426614174000"
```

### Full Configuration
```bash
cargo run --release \
  --customer-uuid "123e4567-e89b-12d3-a456-426614174000" \
  --server-url "http://localhost:4433" \
  --heartbeat-interval 30 \
  --agent-port 3000
```

### Environment Variables
```bash
export CUSTOMER_UUID="123e4567-e89b-12d3-a456-426614174000"
cargo run --release
```

## 🔧 Build and Deploy

### Build for Release
```bash
cargo build --release
```

### Create Executable
```bash
# The executable will be in target/release/
./target/release/your_client_name --customer-uuid "your-uuid-here"
```

### Cross-Platform Build
```bash
# For Windows
cargo build --release --target x86_64-pc-windows-gnu

# For Linux
cargo build --release --target x86_64-unknown-linux-gnu

# For macOS
cargo build --release --target x86_64-apple-darwin
```

## 🧪 Testing

### Test Registration
```bash
# Test without customer UUID
./target/release/your_client_name --server-url "http://localhost:4433"

# Test with customer UUID
./target/release/your_client_name \
  --customer-uuid "test-uuid" \
  --server-url "http://localhost:4433"
```

### Test Command Execution
```bash
# Send a test command to your agent
curl -X POST "http://localhost:4433/api/agents/{agent_id}/commands" \
  -H "Content-Type: application/json" \
  -d '{"command": "whoami", "shell_type": "cmd"}'
```

## 🔍 Debugging

### Enable Debug Logging
```rust
use tracing::{info, warn, error};

// Add to your main function
tracing_subscriber::fmt::init();

// Use in your code
info!("Agent starting up");
warn!("Connection issue");
error!("Registration failed");
```

### Check Agent Status
```bash
# Check if agent is registered
curl "http://localhost:4433/api/agents"

# Check specific agent
curl "http://localhost:4433/api/agents/{agent_id}"
```

## 📋 Checklist

- [ ] Add customer UUID support to command line arguments
- [ ] Include customer UUID in registration payload
- [ ] Implement command execution server
- [ ] Add proper error handling
- [ ] Test with and without customer UUID
- [ ] Build release executable
- [ ] Test cross-platform compatibility

## 🚀 Next Steps

1. **Implement the command server** using axum or actix-web
2. **Add proper logging** with tracing
3. **Implement command queuing** for long-running tasks
4. **Add security features** like authentication
5. **Create deployment scripts** for different platforms

This guide provides the foundation for implementing a Rust client that can register with the Remote Agent Manager using customer UUIDs. The client will be associated with the specified customer and can be managed through the web dashboard. 