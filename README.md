# Gmail LLM Connector

A robust, production-ready Gmail integration system providing both MCP (Model Context Protocol) and HTTP API access to Gmail operations with encrypted credential management.

## 🚀 **Quick Start**

```bash
# Clone and setup
git clone <repository>
cd gmail-llm
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Encrypt your Gmail credentials
python setup_encrypted_credentials.py

# Start both MCP and HTTP API servers
./start_mcp_server.sh
```

**Servers will be available at:**
- 🔗 **MCP Server:** `http://127.0.0.1:8001/mcp` (for Claude Code)
- 🌐 **HTTP API:** `http://127.0.0.1:8000` (for other services)
- 📚 **API Docs:** `http://127.0.0.1:8000/docs`

## 🏗️ **Architecture**

### **Dual-Server Design**
- **MCP Server** (port 8001): Claude Code integration via Model Context Protocol
- **HTTP API Server** (port 8000): REST API for other services and applications
- **Shared Gmail Factory**: Single authentication across both servers
- **Supervisor Management**: Independent process control and monitoring

### **Key Features**
✅ **Encrypted Credentials** - Password-protected OAuth tokens and API credentials  
✅ **Dual Protocol Support** - Both MCP and HTTP API access  
✅ **Process Isolation** - Separate supervisor-managed processes  
✅ **Structured Logging** - JSON logs with correlation tracking  
✅ **Environment Configuration** - Configurable via environment variables  
✅ **Production Ready** - Error handling, retries, and monitoring  

## 🔧 **Setup Guide**

### **1. Google Cloud Setup**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project and enable the Gmail API
3. Create OAuth 2.0 credentials (Desktop application)
4. Download `credentials.json` to this directory

### **2. Credential Encryption**
```bash
python setup_encrypted_credentials.py
# Enter your desired encryption password
# This creates credentials.encrypted and credentials_token.encrypted
```

### **3. Server Deployment**
```bash
# Start both servers with supervisor
./start_mcp_server.sh

# Or use individual startup scripts
python start_mcp_server.py    # MCP only
python start_api_server.py    # HTTP API only
```

## 📡 **HTTP API Usage**

### **Check Emails**
```bash
# Get unread emails
curl "http://127.0.0.1:8000/api/emails?query=is:unread&max_results=5" | jq .

# Search by sender
curl "http://127.0.0.1:8000/api/emails?query=from:example.com&max_results=10" | jq .
```

### **Send Email**
```bash
curl -X POST "http://127.0.0.1:8000/api/emails/send" \
  -H "Content-Type: application/json" \
  -d '{
    "to": "recipient@example.com",
    "subject": "Hello from API",
    "message": "This email was sent via the Gmail LLM HTTP API!"
  }'
```

### **Email Management**
```bash
# Mark as read
curl -X POST "http://127.0.0.1:8000/api/emails/{message_id}/mark-read"

# Move to trash
curl -X POST "http://127.0.0.1:8000/api/emails/{message_id}/trash"

# Add star
curl -X POST "http://127.0.0.1:8000/api/emails/{message_id}/star"
```

## 🔌 **MCP Integration (Claude Code)**

### **Add to Claude Code**
```bash
# Using the .mcp.json configuration
claude mcp add-json gmail-llm-connector '{"command": "python", "args": ["start_mcp_server.py"], "env": {"PYTHONPATH": "./src"}}'
```

### **Usage in Claude Code**
```
# Check your inbox
Can you check my Gmail inbox?

# Send emails
Send an email to john@example.com with subject "Meeting Tomorrow" 

# Email management
Mark the latest email from HR as read
```

## 🛠️ **Management Commands**

### **Server Control**
```bash
# Start/stop/restart
./start_mcp_server.sh start
./start_mcp_server.sh stop  
./start_mcp_server.sh restart

# Check status
./start_mcp_server.sh status

# View logs
./start_mcp_server.sh logs
./start_mcp_server.sh follow  # Real-time logs
```

### **Individual Server Control**
```bash
# Using supervisor directly
supervisorctl start gmail-servers:*
supervisorctl restart gmail-mcp-server
supervisorctl restart gmail-api-server
supervisorctl status gmail-servers:*
```

## ⚙️ **Configuration**

### **Environment Variables**
```bash
export GMAIL_CREDENTIALS_PATH="credentials.encrypted"
export GMAIL_MCP_HOST="127.0.0.1"
export GMAIL_MCP_PORT="8001"
export GMAIL_API_HOST="127.0.0.1" 
export GMAIL_API_PORT="8000"
export GMAIL_LOG_LEVEL="info"
export GMAIL_MCP_PASSWORD="your_encryption_password"  # For non-interactive use
```

### **Configuration Files**
- `supervisord.conf` - Supervisor process management
- `.mcp.json` - MCP server configuration for Claude Code
- `src/gmail_llm/config.py` - Centralized application configuration

## 📁 **Project Structure**

```
gmail-llm/
├── src/gmail_llm/           # Main application code
│   ├── api/                 # HTTP API server
│   ├── auth/                # OAuth and encryption
│   ├── core/                # Gmail connector
│   ├── email/               # Email operations  
│   ├── mcp/                 # MCP server
│   ├── security/            # Credential management
│   └── shared/              # Shared utilities
├── start_mcp_server.py      # MCP server startup
├── start_api_server.py      # HTTP API startup
├── start_mcp_server.sh      # Management script
├── supervisord.conf         # Process management
├── legacy/                  # Archived old files
└── docs/                    # Documentation
```

## 🔍 **Monitoring & Debugging**

### **Health Checks**
```bash
# API health
curl http://127.0.0.1:8000/health

# Check server status
supervisorctl status gmail-servers:*
```

### **Logs**
```bash
# Structured JSON logs
tail -f logs/gmail-mcp-server.log
tail -f logs/gmail-api-server.log
tail -f logs/supervisord.log
```

### **Troubleshooting**
- **Authentication issues**: Check encrypted credentials and password
- **Port conflicts**: Modify ports in environment variables
- **Permission errors**: Ensure proper file permissions on credential files
- **API errors**: Check logs for detailed error messages with correlation IDs

## 📖 **Additional Documentation**

- [API Usage Guide](API_USAGE.md) - Comprehensive HTTP API documentation
- [Supervisor Architecture](SUPERVISOR_ARCHITECTURE.md) - Process management details
- [Encrypted Credentials](ENCRYPTED_CREDENTIALS_INTEGRATION.md) - Security implementation
- [Refactoring Summary](REFACTORING_SUMMARY.md) - Technical improvements made

## 🧪 **Development**

### **Adding New Features**
1. Use the shared Gmail factory for authentication
2. Follow the established decorator patterns for error handling
3. Add structured logging with correlation IDs
4. Update both MCP and HTTP API endpoints as needed

### **Testing**
```bash
# Test HTTP API
curl -s "http://127.0.0.1:8000/api/emails?max_results=1" | jq .

# Test MCP via Claude Code
# Use Claude Code to check your inbox
```

## 🔒 **Security**

- **Encrypted Credentials**: OAuth tokens and API credentials encrypted at rest
- **Password Protection**: Master password required for credential access
- **Localhost Only**: Servers bind to 127.0.0.1 (no external access)
- **Environment Isolation**: Separate processes for better security boundaries
- **Audit Logging**: All operations logged with correlation tracking

## 📝 **License**

[Add your license information here]

---

**Gmail LLM Connector** - Secure, scalable Gmail integration for AI applications