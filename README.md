# Remote Agent Manager

A comprehensive remote agent management system built with FastAPI backend and Rust clients, featuring customer management, agent registration, and command execution capabilities.

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Rust Client   │◄──►│  FastAPI Server  │◄──►│   Web Dashboard │
│   (Agent)       │    │   (Port 4433)    │    │   (Port 4433)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   SQLite DB      │
                       │   (agents.db)    │
                       └──────────────────┘
```

## 🚀 Features

### Core Functionality
- **Agent Registration**: Rust clients register with unique hostnames
- **Heartbeat Monitoring**: Real-time agent status tracking
- **Command Execution**: Execute commands on remote agents
- **Customer Management**: Register and manage customers with UUIDs
- **Resizable UI**: Dynamic command panels and task results
- **Soft Delete**: Agents are marked inactive instead of hard deletion

### Customer Management
- **Customer Registration**: Create customers with UUID, name, and optional address
- **Customer Table**: View all registered customers with CRUD operations
- **UUID Assignment**: Each customer gets a unique UUID for agent association

### Agent Management
- **Hostname Deduplication**: Prevents duplicate agent registrations
- **Status Monitoring**: Real-time online/offline status
- **Command Execution**: Send commands to specific agents
- **Task Tracking**: Monitor command execution progress

## 📋 Prerequisites

### Server Requirements
- Python 3.8+
- pip (Python package manager)

### Client Requirements
- Rust 1.70+
- Cargo (Rust package manager)

## 🛠️ Installation

### 1. Server Setup

```bash
# Clone the repository
git clone https://github.com/shtrumj/remote_skyshift_sever.git
cd remote_skyshift_sever

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python main.py
```

The server will start on `http://localhost:4433`

### 2. Client Setup

```bash
# Navigate to your Rust client directory
cd your-rust-client-directory

# Build the client
cargo build --release

# The executable will be in target/release/
```

## 🎯 Usage

### Server Dashboard

1. **Access Dashboard**: Open `http://localhost:4433` in your browser
2. **View Agents**: See all registered agents in the left panel
3. **Send Commands**: Click "Command" button on any agent to send commands
4. **Manage Customers**: Click "Customers" in the navbar to manage customers

### Customer Management

1. **Register Customer**: Fill out the customer form with name and optional address
2. **Get Customer UUID**: Copy the UUID from the customer table
3. **Use UUID**: Pass this UUID to your Rust client for registration

### Rust Client Usage

#### Basic Usage (Without Customer)
```bash
# Run the client without customer association
./target/release/your_client_name
```

#### With Customer UUID
```bash
# Run the client with customer UUID
./target/release/your_client_name --customer-uuid "123e4567-e89b-12d3-a456-426614174000"
```

#### Command Line Options
```bash
# Available options
./target/release/your_client_name --help

# Example with all options
./target/release/your_client_name \
  --customer-uuid "123e4567-e89b-12d3-a456-426614174000" \
  --server-url "http://localhost:4433" \
  --heartbeat-interval 30
```

## 🔧 Configuration

### Server Configuration

The server runs on port 4433 by default. You can modify this in `main.py`:

```python
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=4433)
```

### Client Configuration

Your Rust client should include these configuration options:

```rust
#[derive(Parser)]
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
}
```

## 📡 API Endpoints

### Agent Management
- `POST /api/agents/register` - Register new agent
- `POST /api/agents/{agent_id}/heartbeat` - Send heartbeat
- `GET /api/agents` - List all agents
- `DELETE /api/agents/{agent_id}` - Unregister agent

### Customer Management
- `POST /api/customers` - Create new customer
- `GET /api/customers` - List all customers
- `GET /api/customers/{uuid}` - Get specific customer
- `PUT /api/customers/{uuid}` - Update customer
- `DELETE /api/customers/{uuid}` - Delete customer

### Command Execution
- `POST /api/agents/{agent_id}/commands` - Send command to agent
- `GET /api/agents/{agent_id}/tasks/{task_id}` - Get task status
- `POST /api/agents/{agent_id}/tasks/{task_id}/cancel` - Cancel task

## 🔄 Agent Registration Process

### 1. Customer Registration
```bash
# First, register a customer via the web interface
# Or use the API directly:
curl -X POST "http://localhost:4433/api/customers" \
  -H "Content-Type: application/json" \
  -d '{"name": "My Company", "address": "123 Main St"}'
```

### 2. Get Customer UUID
```bash
# Retrieve the customer UUID
curl "http://localhost:4433/api/customers"
```

### 3. Run Client with UUID
```bash
# Run your Rust client with the customer UUID
./target/release/your_client_name --customer-uuid "customer-uuid-here"
```

## 🎨 Web Interface Features

### Dashboard
- **Real-time Agent Status**: See online/offline agents
- **Command Execution**: Send commands to specific agents
- **Task Results**: View command output and logs
- **Resizable Panels**: Adjust command and result panel sizes

### Customer Management
- **Customer Registration**: Add new customers with UUIDs
- **Customer Table**: View all customers with actions
- **Edit/Delete**: Manage existing customers

## 🔍 Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Kill existing processes on port 4433
   lsof -ti:4433 | xargs kill -9
   ```

2. **Agent Not Registering**
   - Check server is running on correct port
   - Verify customer UUID is valid
   - Check network connectivity

3. **Commands Not Executing**
   - Ensure agent is online (green status)
   - Check command syntax for target shell
   - Verify agent capabilities

### Debug Endpoints
- `GET /health` - Server health check
- `GET /debug/{path}` - Debug endpoint for testing

## 📊 Database Schema

### Agents Table
```sql
CREATE TABLE agents (
    id TEXT PRIMARY KEY,
    agent_id TEXT UNIQUE,
    hostname TEXT,
    ip_address TEXT,
    port INTEGER,
    capabilities TEXT,
    version TEXT,
    registered_at DATETIME,
    last_heartbeat DATETIME,
    status TEXT,
    is_active BOOLEAN
);
```

### Customers Table
```sql
CREATE TABLE customers (
    id TEXT PRIMARY KEY,
    uuid TEXT UNIQUE,
    name TEXT NOT NULL,
    address TEXT,
    created_at DATETIME,
    updated_at DATETIME
);
```

### Tasks Table
```sql
CREATE TABLE tasks (
    id TEXT PRIMARY KEY,
    agent_id TEXT,
    task_id TEXT UNIQUE,
    command TEXT,
    status TEXT,
    created_at DATETIME,
    started_at DATETIME,
    completed_at DATETIME,
    exit_code INTEGER,
    output TEXT,
    error TEXT,
    logs TEXT
);
```

## 🚀 Deployment

### Production Setup
1. Use a production WSGI server (Gunicorn)
2. Set up reverse proxy (Nginx)
3. Configure SSL certificates
4. Set up database backups
5. Configure logging

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 4433

CMD ["python", "main.py"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the API documentation

---

**Note**: This system is designed for internal use and should be deployed behind appropriate security measures in production environments. 