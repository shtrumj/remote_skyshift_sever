# Remote Agent Manager

A secure, scalable remote agent management system with SSL/TLS support for managing distributed agents across networks.

## 🚀 Quick Start

### 1. Start Both Servers (HTTP + HTTPS) - **RECOMMENDED**

```bash
python run_servers.py
```

This will:

- Start HTTP server on port 4433 (for internal debugging)
- Start HTTPS server on port 4434 (for secure production use)
- Automatically generate SSL certificates if needed
- Handle dual server management and graceful shutdown

### 2. Access the Application

- **HTTP (Internal)**: http://localhost:4433
- **HTTPS (Secure)**: https://localhost:4434

## 📁 Project Structure

```
Remote Agent Manager/
├── main.py                           # Main FastAPI application
├── run_servers.py                    # Dual server launcher (HTTP + HTTPS)
├── database.py                       # Database management
├── templates/                        # HTML templates
│   ├── base.html
│   ├── dashboard.html
│   ├── customers.html
│   └── scripts.html
├── static/                          # Static assets (CSS, JS)
├── Testing/                         # Testing and development tools
│   ├── test_websocket_agent.py     # WebSocket agent test
│   ├── server.py                    # Alternative server implementation
│   └── start_server.py             # Legacy server starter
├── CertificateConfiguration/        # SSL/TLS certificate management
│   ├── generate_certificates.py    # Certificate generator
│   ├── SSL_SETUP.md               # SSL setup documentation
│   └── certs/                     # SSL certificates
│       ├── server.crt
│       └── server.key
└── README.md                       # This file
```

## 🔧 Server Options

### Option 1: Both Servers (Recommended) - **USE THIS**

```bash
python run_servers.py
```

- HTTP: http://localhost:4433
- HTTPS: https://localhost:4434
- **Handles certificate generation automatically**
- **Manages dual server processes**

### Option 2: HTTP Only (Development) - **NOT RECOMMENDED**

```bash
python main.py
```

- HTTP: http://localhost:4433
- **Does not handle certificates**
- **Single server only**

### Option 3: HTTPS Only (Production) - **NOT RECOMMENDED**

```bash
python main.py --https
```

- HTTPS: https://localhost:4434
- **Manual certificate management required**
- **Single server only**

## 🔐 SSL/TLS Configuration

### Generate Certificates

```bash
python CertificateConfiguration/generate_certificates.py
```

### Certificate Location

- Certificate: `CertificateConfiguration/certs/server.crt`
- Private Key: `CertificateConfiguration/certs/server.key`

### Security Notes

- Self-signed certificates for development/testing
- Use `-k` flag with curl: `curl -k https://localhost:4434/health`
- For production, replace with CA-signed certificates

## 🧪 Testing

### Test HTTP Server

```bash
curl http://localhost:4433/health
```

### Test HTTPS Server

```bash
curl -k https://localhost:4434/health
```

### Test WebSocket Agent

```bash
python Testing/test_websocket_agent.py
```

## 📋 Features

### Core Features

- ✅ Agent registration and management
- ✅ Real-time WebSocket communication
- ✅ Script execution and management
- ✅ Customer management
- ✅ SSL/TLS encryption support
- ✅ Dual server support (HTTP + HTTPS)

### Security Features

- ✅ SSL/TLS encryption on port 4434
- ✅ Self-signed certificate generation
- ✅ Secure WebSocket connections
- ✅ Input validation and sanitization

### Management Features

- ✅ Dashboard with real-time agent status
- ✅ Script library with upload support
- ✅ Customer assignment and management
- ✅ Command execution with output capture

## 🔍 API Endpoints

### Agent Management

- `GET /api/agents` - List all agents
- `POST /api/agents/register` - Register new agent
- `GET /api/agents/{agent_id}` - Get agent status
- `DELETE /api/agents/{agent_id}` - Unregister agent

### Script Management

- `GET /api/scripts` - List all scripts
- `POST /api/scripts` - Create new script
- `POST /api/scripts/{script_id}/execute` - Execute script

### Customer Management

- `GET /api/customers` - List all customers
- `POST /api/customers` - Create new customer

### Health & Status

- `GET /health` - Health check
- `GET /api/agents/{agent_id}/test-connection` - Test agent connectivity

## 🛠️ Development

### Prerequisites

- Python 3.8+
- OpenSSL (for certificate generation)
- FastAPI
- Uvicorn

### Installation

```bash
# Install dependencies
pip install fastapi uvicorn jinja2 python-multipart

# Generate certificates (first time)
python CertificateConfiguration/generate_certificates.py
```

### Development Workflow

1. **Start servers: `python run_servers.py`** (always use this)
2. Access dashboard: http://localhost:4433
3. Test HTTPS: https://localhost:4434
4. Run tests: `python Testing/test_websocket_agent.py`
5. **For external access, use HTTPS: https://localhost:4434**

## 📚 Documentation

- [SSL/TLS Setup](CertificateConfiguration/SSL_SETUP.md) - Complete SSL configuration guide
- [Testing Guide](Testing/) - Testing tools and examples

## 🔧 Troubleshooting

### Port Conflicts

```bash
# Check if ports are in use
lsof -i :4433
lsof -i :4434
```

### Certificate Issues

```bash
# Regenerate certificates
python CertificateConfiguration/generate_certificates.py
```

### WebSocket Issues

```bash
# Test WebSocket connection
python Testing/test_websocket_agent.py
```

## 📄 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For issues and questions:

1. Check the troubleshooting section
2. Review the SSL setup documentation
3. Test with the provided testing tools
4. Create an issue with detailed information
