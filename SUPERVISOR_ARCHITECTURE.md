# Gmail LLM Supervisor Architecture

## 🏗️ **Correct Architecture: Separate Processes**

You were absolutely right! The original `start_dual_server.py` was running **two separate servers in threads** within a single process. This is suboptimal compared to having **separate supervisor-managed processes**.

## 📊 **Architecture Comparison**

### **Before: Single Process with Threads** ❌
```
start_dual_server.py
├── Thread 1: MCP Server (FastMCP on port 8001)
└── Thread 2: HTTP API Server (FastAPI on port 8000)
```

**Problems:**
- Single point of failure (if process dies, both servers die)
- Harder to restart individual servers
- Shared memory space can cause issues
- Complex error handling and monitoring

### **After: Separate Supervisor Processes** ✅
```
Supervisor
├── gmail-mcp-server (port 8001)
└── gmail-api-server (port 8000)
```

**Benefits:**
- **Process isolation** - servers can't interfere with each other
- **Independent restart** - restart just MCP or API server
- **Better monitoring** - supervisor tracks each server separately
- **Separate logging** - dedicated log files for each server
- **Resource isolation** - better CPU/memory management

## 🚀 **New Implementation**

### **Separate Startup Scripts**
```bash
start_mcp_server.py   # Runs only MCP server (FastMCP)
start_api_server.py   # Runs only HTTP API server (FastAPI)
```

### **Updated Supervisor Configuration**
```ini
[program:gmail-mcp-server]
command=python start_mcp_server.py
priority=100  # Start first

[program:gmail-api-server] 
command=python start_api_server.py
priority=200  # Start second

[group:gmail-servers]
programs=gmail-mcp-server,gmail-api-server
```

## 🎛️ **Supervisor Management**

### **Start Both Services**
```bash
supervisorctl start gmail-servers:*
```

### **Individual Control**
```bash
# Control individual servers
supervisorctl start gmail-mcp-server
supervisorctl start gmail-api-server
supervisorctl restart gmail-api-server  # Restart just API server
supervisorctl stop gmail-mcp-server     # Stop just MCP server

# Check status
supervisorctl status
```

### **Logs**
```bash
# Separate log files
tail -f logs/gmail-mcp-server.log
tail -f logs/gmail-api-server.log
```

## 🔧 **Server Details**

### **MCP Server (gmail-mcp-server)**
- **Purpose:** Provides MCP protocol for Claude Code
- **Technology:** FastMCP with SSE transport
- **Port:** 8001 (configurable via `GMAIL_MCP_PORT`)
- **Endpoint:** `http://127.0.0.1:8001/mcp`

### **HTTP API Server (gmail-api-server)**
- **Purpose:** REST API for other services on the host
- **Technology:** FastAPI with uvicorn
- **Port:** 8000 (configurable via `GMAIL_API_PORT`)
- **Endpoints:** `http://127.0.0.1:8000/api/*`
- **Docs:** `http://127.0.0.1:8000/docs`

## 📈 **Benefits of This Architecture**

### **1. Better Reliability**
- If MCP server crashes, HTTP API continues serving other services
- If HTTP API has issues, MCP server still works for Claude Code
- Independent restart capabilities

### **2. Easier Operations**
```bash
# Deploy new API version without affecting MCP
supervisorctl stop gmail-api-server
# ... update code ...
supervisorctl start gmail-api-server

# MCP server continues running for Claude Code
```

### **3. Better Monitoring**
- Separate process metrics for each server
- Individual log files for troubleshooting
- Supervisor provides separate status for each

### **4. Resource Management**
- Each server gets its own process space
- Better memory isolation
- CPU usage tracked separately

## 🔄 **Shared Components Still Work**

Both servers still share the refactored components:
- **Gmail Factory:** Single authenticated connection via singleton pattern
- **Configuration:** Shared `config.py` with environment variables
- **Error Handling:** Shared decorators and utilities
- **Logging:** Structured logging with correlation IDs

## 📝 **Migration Path**

### **Old Way:**
```bash
python start_dual_server.py
```

### **New Way:**
```bash
# Manual start
python start_mcp_server.py &
python start_api_server.py &

# Or via supervisor (recommended)
supervisorctl start gmail-servers:*
```

## 🎯 **Result**

This architecture is much more robust and follows standard practices:
- ✅ **Proper process separation**
- ✅ **Individual server control**
- ✅ **Better fault tolerance**
- ✅ **Standard supervisor patterns**
- ✅ **Maintained shared components**
- ✅ **Same functionality**

The servers are truly independent processes now, which is the correct architecture for this use case!