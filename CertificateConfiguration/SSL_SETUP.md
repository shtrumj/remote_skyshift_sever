# SSL/TLS Setup for Remote Agent Manager

This document explains how to set up SSL/TLS encryption for the Remote Agent Manager.

## 🔐 SSL/TLS Support

The Remote Agent Manager now supports both HTTP and HTTPS:

- **HTTP (Port 4433)**: For internal debugging and development
- **HTTPS (Port 4434)**: For secure production use with SSL/TLS encryption

## 📋 Prerequisites

1. **OpenSSL**: Required for certificate generation
   - macOS: `brew install openssl`
   - Ubuntu/Debian: `sudo apt-get install openssl`
   - Windows: Download from https://slproweb.com/products/Win32OpenSSL.html

## 🚀 Quick Start

### 1. Generate SSL Certificates

```bash
python generate_certificates.py
```

This creates:
- `certs/server.crt` - SSL certificate
- `certs/server.key` - Private key

### 2. Start Both Servers

#### Option A: Run both servers simultaneously
```bash
python run_servers.py
```

#### Option B: Run servers individually
```bash
# HTTP server (port 4433)
python main.py

# HTTPS server (port 4434) - in another terminal
python main.py --https
```

## 🌐 Access URLs

Once started, you can access:

- **HTTP (Internal/Debug)**: http://localhost:4433
- **HTTPS (Secure)**: https://localhost:4434

## 🔧 Configuration

### Certificate Location
- Certificate: `certs/server.crt`
- Private Key: `certs/server.key`

### Port Configuration
- HTTP: Port 4433 (unencrypted)
- HTTPS: Port 4434 (SSL/TLS encrypted)

## ⚠️ Security Notes

### Self-Signed Certificates
- The generated certificates are **self-signed** for development/testing
- Browsers will show security warnings (this is normal)
- Use `-k` flag with curl: `curl -k https://localhost:4434/health`

### Production Use
For production environments:
1. Obtain certificates from a trusted Certificate Authority (CA)
2. Replace `certs/server.crt` and `certs/server.key` with your CA certificates
3. Ensure proper firewall rules for port 4434

## 🧪 Testing

### Test HTTP Server
```bash
curl http://localhost:4433/health
```

### Test HTTPS Server
```bash
curl -k https://localhost:4434/health
```

### Test Web Interface
- HTTP: http://localhost:4433
- HTTPS: https://localhost:4434

## 🔍 Troubleshooting

### Certificate Issues
```bash
# Regenerate certificates
python generate_certificates.py
```

### Port Conflicts
```bash
# Check if ports are in use
lsof -i :4433
lsof -i :4434
```

### SSL Context Errors
- Ensure OpenSSL is installed
- Check certificate file permissions
- Verify certificate paths in `main.py`

## 📝 File Structure

```
Remote Agent Manager/
├── main.py                    # Main application
├── generate_certificates.py   # Certificate generator
├── run_servers.py            # Dual server runner
├── certs/
│   ├── server.crt           # SSL certificate
│   └── server.key           # Private key
└── SSL_SETUP.md             # This file
```

## 🎯 Usage Examples

### Development (HTTP only)
```bash
python main.py
# Access: http://localhost:4433
```

### Production (HTTPS only)
```bash
python main.py --https
# Access: https://localhost:4434
```

### Both (Development + Production)
```bash
python run_servers.py
# Access: http://localhost:4433 (debug)
# Access: https://localhost:4434 (secure)
``` 