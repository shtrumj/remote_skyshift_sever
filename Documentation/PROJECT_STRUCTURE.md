# Remote Agent Manager - Project Structure

## 📁 Root Directory (Clean & Organized)

```
Remote Agent Manager/
├── main.py                           # Main FastAPI application
├── run_servers.py                    # Dual server launcher (HTTP + HTTPS)
├── database.py                       # Database management
├── requirements.txt                  # Python dependencies
├── README.md                        # Main project documentation
├── .cursorrules                     # Development guidelines
├── .gitignore                       # Git ignore rules
├── agents.db                        # SQLite database
├── agents_backup.db                 # Database backup
├── templates/                       # HTML templates (Jinja2)
│   ├── base.html
│   ├── dashboard.html
│   ├── customers.html
│   └── scripts.html
├── static/                         # Static assets (CSS, JS)
│   └── js/
│       └── main.js
├── Testing/                        # Testing and development tools
│   ├── test_websocket_agent.py    # WebSocket agent test
│   ├── test_client.py             # Client testing script
│   ├── server.py                  # Alternative server implementation
│   ├── start_server.py            # Legacy server starter
│   ├── database_utils.py          # Database utilities
│   ├── system_info.ps1            # PowerShell system info script
│   ├── simple_system_info.bat     # Simple CMD system info
│   ├── improved_system_info.bat   # Improved CMD system info
│   ├── test_simple.bat            # Simple test script
│   ├── test_script.sh             # Bash test script
│   └── test_script.ps1            # PowerShell test script
├── CertificateConfiguration/       # SSL/TLS certificate management
│   ├── generate_certificates.py   # Certificate generator
│   ├── SSL_SETUP.md              # SSL setup documentation
│   └── certs/                    # SSL certificates
│       ├── server.crt
│       └── server.key
└── Documentation/                  # Additional documentation
    ├── rust_client_fix.md         # Rust client fixes
    ├── RUST_CLIENT_GUIDE.md      # Rust client guide
    ├── command_validation.md      # Command validation guide
    ├── offline_agent_analysis.md  # Offline agent analysis
    ├── command_examples.md        # Command examples
    ├── SQLITE_IMPLEMENTATION.md  # SQLite implementation
    └── DEBUG_ANALYSIS.md         # Debug analysis
```

## 🎯 Directory Purposes

### Root Directory

- **Clean and minimal** - Only essential production files
- **Easy navigation** - Clear file organization
- **Quick startup** - `python run_servers.py` starts everything

### Testing/

- **Development tools** - All testing and debugging scripts
- **Script examples** - Sample scripts for different platforms
- **Test utilities** - Database and client testing tools
- **Alternative implementations** - Backup server configurations

### CertificateConfiguration/

- **SSL/TLS management** - All certificate-related files
- **Self-contained** - Complete certificate generation process
- **Documentation** - SSL setup and security guidelines
- **Production ready** - Easy to replace with CA certificates

### Documentation/

- **Comprehensive guides** - Detailed implementation guides
- **Troubleshooting** - Debug and analysis documents
- **Client guides** - Rust client implementation
- **Best practices** - Security and validation guides

## 🚀 Quick Start Commands

### Start Both Servers

```bash
python run_servers.py
```

### Generate Certificates

```bash
python CertificateConfiguration/generate_certificates.py
```

### Test WebSocket Agent

```bash
python Testing/test_websocket_agent.py
```

### Test HTTP Server

```bash
curl http://remote.skyshift.dev:80/health
```

### Test HTTPS Server

```bash
curl -k https://remote.skyshift.dev:443/health
```

## 🔧 Development Workflow

### 1. Development

- Use `Testing/` for all development tools
- Keep root directory clean
- Test both HTTP and HTTPS endpoints

### 2. Certificate Management

- All certificates in `CertificateConfiguration/`
- Self-signed for development
- CA-signed for production

### 3. Documentation

- Main docs in root `README.md`
- Detailed guides in `Documentation/`
- SSL setup in `CertificateConfiguration/`

### 4. Testing

- All test scripts in `Testing/`
- Sample scripts for different platforms
- Database utilities for testing

## 📋 File Organization Rules

### ✅ Keep in Root

- `main.py` - Main application
- `run_servers.py` - Server launcher
- `database.py` - Database management
- `README.md` - Main documentation
- `requirements.txt` - Dependencies
- `.cursorrules` - Development guidelines

### ✅ Move to Testing/

- All test scripts
- Development utilities
- Sample scripts
- Alternative implementations

### ✅ Move to CertificateConfiguration/

- Certificate generation
- SSL documentation
- Certificate files

### ✅ Move to Documentation/

- Detailed guides
- Implementation docs
- Troubleshooting guides

## 🎉 Benefits of This Organization

### 1. Clean Root Directory

- Easy to find main files
- Clear project structure
- Professional appearance

### 2. Logical Grouping

- Related files together
- Easy to locate tools
- Clear separation of concerns

### 3. Development Friendly

- Testing tools organized
- Documentation centralized
- Certificate management isolated

### 4. Production Ready

- Clean deployment
- Easy maintenance
- Clear documentation

### 5. Scalable Structure

- Easy to add new features
- Organized testing
- Clear development guidelines
