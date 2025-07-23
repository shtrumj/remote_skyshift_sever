# Remote Agent Manager

A modern, real-time remote agent management system with WebSocket-based full-duplex communication, designed for managing distributed computing agents across networks.

## 🚀 Features

### Core Features
- **Real-time Communication**: WebSocket-based full-duplex communication between server and agents
- **Automatic Fallback**: HTTP fallback for agents without WebSocket support
- **Customer Management**: Organize agents by customers with UUID-based registration
- **Real-time Command Execution**: Send commands and receive live updates
- **Interactive UI**: Draggable, resizable command and result panels
- **Agent Health Monitoring**: Automatic heartbeat and connection status tracking
- **Multi-shell Support**: CMD, PowerShell, and Bash command execution
- **Network Resilience**: Handles network connectivity issues gracefully

### Advanced Features
- **WebSocket Priority**: Commands sent via WebSocket for instant delivery
- **HTTP Fallback**: Automatic fallback to HTTP for legacy agents
- **Connection Status**: Real-time display of WebSocket vs HTTP connections
- **Task Management**: Real-time task status updates and result streaming
- **Customer Filtering**: Filter agents by customer name
- **Agent Deduplication**: Automatic removal of duplicate registrations

## 🏗️ Architecture

### Server (Python/FastAPI)
- **WebSocket Server**: Real-time bidirectional communication
- **HTTP API**: RESTful endpoints for agent management
- **SQLite Database**: Persistent storage for agents, tasks, and customers
- **Background Tasks**: Automatic cleanup of offline agents
- **Connection Manager**: Manages WebSocket connections and agent mapping

### Client (Rust)
- **WebSocket Client**: Maintains persistent connection to server
- **HTTP Server**: Fallback command execution endpoint
- **Command Executor**: Multi-shell command execution
- **Heartbeat System**: Regular status updates to server
- **Customer Registration**: UUID-based customer association

## 📋 Prerequisites

### Server Requirements
- Python 3.8+
- FastAPI
- Uvicorn
- SQLAlchemy
- Pydantic

### Client Requirements
- Rust 1.70+
- Tokio (async runtime)
- Actix-web (HTTP server)
- Tungstenite (WebSocket client)

## 🛠️ Installation

### Server Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Inventory
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install fastapi uvicorn sqlalchemy pydantic python-multipart
   ```

4. **Run the server**
   ```bash
   python main.py
   ```

The server will start on `http://0.0.0.0:4433`

### Client Setup

1. **Create new Rust project**
   ```bash
   cargo new remote_agent_client
   cd remote_agent_client
   ```

2. **Add dependencies to `Cargo.toml`**
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
   ```

3. **Build the client**
   ```bash
   cargo build --release
   ```

## 🚀 Usage

### Starting the Server

```bash
python main.py
```

The server provides:
- **Web Dashboard**: `http://localhost:4433`
- **API Documentation**: `http://localhost:4433/docs`
- **Health Check**: `http://localhost:4433/health`

### Running the Client

#### Basic Registration
```bash
./target/release/remote_agent_client --server-url "http://remote.skyshift.dev:4433"
```

#### Customer Registration
```bash
./target/release/remote_agent_client \
  --server-url "http://remote.skyshift.dev:4433" \
  --customer-uuid "2ce998a3-3168-40ef-8ceb-b9a4404f6342"
```

#### Advanced Configuration
```bash
./target/release/remote_agent_client \
  --server-url "http://remote.skyshift.dev:4433" \
  --customer-uuid "2ce998a3-3168-40ef-8ceb-b9a4404f6342" \
  --heartbeat-interval 30 \
  --agent-port 3000
```

### WebSocket Communication

The client automatically establishes a WebSocket connection to the server:

```
ws://server:4433/ws/agent/{agent_id}
```

**Message Types:**
- `heartbeat`: Regular status updates
- `task_result`: Command execution results
- `task_status`: Real-time task progress

## 📡 API Endpoints

### Agent Management
- `POST /api/agents/register` - Register new agent
- `GET /api/agents` - List all agents
- `GET /api/agents/{agent_id}` - Get agent status
- `DELETE /api/agents/{agent_id}` - Unregister agent

### Command Execution
- `POST /api/agents/{agent_id}/commands` - Send command to agent
- `GET /api/agents/{agent_id}/tasks/{task_id}` - Get task status
- `POST /api/agents/{agent_id}/tasks/{task_id}/cancel` - Cancel task

### Customer Management
- `POST /api/customers` - Create customer
- `GET /api/customers` - List customers
- `PUT /api/customers/{uuid}` - Update customer
- `DELETE /api/customers/{uuid}` - Delete customer

### WebSocket
- `WS /ws/agent/{agent_id}` - Real-time agent communication

## 🔧 Configuration

### Server Configuration
```python
# main.py
app = FastAPI(
    title="Remote Agent Manager",
    version="1.0.0",
    lifespan=lifespan
)

# Server runs on port 4433 by default
uvicorn.run(app, host="0.0.0.0", port=4433)
```

### Client Configuration
```rust
// Command line arguments
#[derive(Parser)]
struct Args {
    #[arg(long, default_value = "http://localhost:4433")]
    server_url: String,
    
    #[arg(long)]
    customer_uuid: Option<String>,
    
    #[arg(long, default_value = "20")]
    heartbeat_interval: u64,
    
    #[arg(long, default_value = "3000")]
    agent_port: u16,
}
```

## 🌐 Network Architecture

### WebSocket Communication Flow
1. **Client Registration**: Agent registers via HTTP
2. **WebSocket Connection**: Client establishes WebSocket connection
3. **Command Execution**: Server sends commands via WebSocket
4. **Real-time Updates**: Client sends task results via WebSocket
5. **Fallback**: HTTP used if WebSocket unavailable

### Connection Types
- **WebSocket**: Primary communication channel (real-time)
- **HTTP**: Fallback for legacy agents or network issues

## 📊 Dashboard Features

### Real-time Monitoring
- **Connection Status**: WebSocket vs HTTP indicators
- **Agent Health**: Live status updates
- **Command Execution**: Real-time task progress
- **Customer Filtering**: Filter agents by customer

### Interactive Panels
- **Command Panel**: Draggable command interface
- **Results Panel**: Real-time task results
- **System Status**: Live connection statistics

## 🔒 Security Considerations

### Network Security
- **Firewall Configuration**: Ensure port 4433 is accessible
- **VPN Requirements**: For cross-network communication
- **SSL/TLS**: Consider HTTPS/WSS for production

### Agent Security
- **Command Validation**: Server-side command sanitization
- **Timeout Limits**: Prevent long-running commands
- **Access Control**: Customer-based agent isolation

## 🐛 Troubleshooting

### Common Issues

#### Agent Not Connecting
```bash
# Check server connectivity
curl http://server:4433/health

# Test WebSocket connection
wscat -c ws://server:4433/ws/agent/test
```

#### Commands Not Executing
1. **Check Agent Status**: Verify agent is online
2. **Check Connection Type**: WebSocket vs HTTP
3. **Check Network**: Ensure server can reach agent
4. **Check Firewall**: Verify port 3000 is open

#### WebSocket Issues
```bash
# Check WebSocket endpoint
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
     -H "Sec-WebSocket-Version: 13" \
     -H "Sec-WebSocket-Key: x3JJHMbDL1EzLkh9GBhXDw==" \
     http://server:4433/ws/agent/test
```

### Debug Commands
```bash
# Test agent connection
curl http://server:4433/api/agents/{agent_id}/test-connection

# Check agent status
curl http://server:4433/api/agents/{agent_id}

# Send test command
curl -X POST http://server:4433/api/agents/{agent_id}/commands \
  -H "Content-Type: application/json" \
  -d '{"command": "whoami", "shell_type": "cmd"}'
```

## 📈 Performance

### Optimization Tips
- **WebSocket Priority**: Use WebSocket for real-time commands
- **Connection Pooling**: Reuse HTTP connections
- **Command Batching**: Send multiple commands efficiently
- **Result Streaming**: Stream large command outputs

### Monitoring
- **Connection Count**: Monitor WebSocket connections
- **Command Latency**: Track command execution times
- **Error Rates**: Monitor failed commands
- **Network Usage**: Track bandwidth consumption

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the API documentation at `/docs`

## 🔄 Migration from HTTP-only

If migrating from the HTTP-only version:

1. **Update Server**: Use the new WebSocket-enabled server
2. **Update Clients**: Deploy new Rust clients with WebSocket support
3. **Test Connectivity**: Verify WebSocket connections work
4. **Monitor**: Watch for improved real-time performance

The system maintains backward compatibility with HTTP-only agents while providing enhanced real-time capabilities for WebSocket-enabled clients. 