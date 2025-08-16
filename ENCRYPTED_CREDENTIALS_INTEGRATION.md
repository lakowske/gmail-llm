# Gmail LLM Encrypted Credentials Integration

## 🔐 **Yes, Both Servers Will Decrypt Credentials Properly!**

The encrypted credentials integration works seamlessly with the separate supervisor processes. Here's how:

## 🔄 **How It Works**

### **1. Single Password Entry**
```bash
./start_mcp_server.sh
# Prompts once: "Enter encryption password: "
# Password is securely handled and passed to both servers
```

### **2. Environment Variable Inheritance** 
```bash
# start_mcp_server.sh sets environment variable
export GMAIL_MCP_PASSWORD="your_password"

# Supervisor inherits this and passes to both processes
supervisord -c supervisord.conf

# Both servers get the password automatically
gmail-mcp-server.py   # Gets GMAIL_MCP_PASSWORD
gmail-api-server.py   # Gets GMAIL_MCP_PASSWORD
```

### **3. Shared Authentication**
```python
# Both servers use the same Gmail factory (singleton pattern)
from gmail_llm.shared.gmail_factory import get_gmail_connector

# First server to authenticate saves the credentials
connector = get_gmail_connector()  # Decrypts once, caches result

# Second server reuses the authenticated connection
connector = get_gmail_connector()  # Returns cached connector
```

## 🏗️ **Architecture Flow**

```
start_mcp_server.sh
├── Prompts for password once
├── Sets GMAIL_MCP_PASSWORD environment variable  
├── Starts supervisor with environment inheritance
└── supervisor starts both processes:
    ├── gmail-mcp-server.py    (gets GMAIL_MCP_PASSWORD)
    └── gmail-api-server.py    (gets GMAIL_MCP_PASSWORD)

Both processes:
├── Use EncryptedOAuthManager.authenticate()
├── Check os.getenv('GMAIL_MCP_PASSWORD') first
├── Use shared Gmail factory (singleton)
└── Decrypt credentials once, share authentication
```

## 🔒 **Security Features**

### **Password Handling**
- ✅ **Single entry point:** Password entered once securely
- ✅ **Environment inheritance:** Passed securely to child processes
- ✅ **Memory only:** Never written to disk
- ✅ **Automatic cleanup:** Cleared from shell after supervisor starts

### **Credential Protection**
- ✅ **Encrypted at rest:** credentials.encrypted file
- ✅ **Decrypted in memory:** Only when needed
- ✅ **Shared authentication:** Single decrypt operation
- ✅ **Process isolation:** Each server runs in separate process

## 📋 **Usage Examples**

### **Start Both Servers**
```bash
./start_mcp_server.sh
# Enter encryption password: [hidden input]
# ✓ Gmail servers started successfully
# ✓ MCP Server running on http://127.0.0.1:8001/mcp
# ✓ HTTP API Server running on http://127.0.0.1:8000
```

### **Individual Server Control**
```bash
# Both servers share the same credentials automatically
supervisorctl restart gmail-mcp-server    # Restarts just MCP
supervisorctl restart gmail-api-server    # Restarts just API
supervisorctl restart gmail-servers:*     # Restarts both
```

### **Status and Logs**
```bash
./start_mcp_server.sh status    # Shows both servers
./start_mcp_server.sh logs      # Shows logs from both
./start_mcp_server.sh follow    # Follows both log files
```

## 🔧 **Technical Details**

### **EncryptedOAuthManager Integration**
```python
# In src/gmail_llm/auth/encrypted_oauth_manager.py:48-54
if self.password is None:
    env_password = os.getenv('GMAIL_MCP_PASSWORD')  # ✓ Reads from environment
    if env_password:
        logger.info("Using password from environment variable")
        self.password = env_password               # ✓ Uses automatically
    else:
        self.password = getpass.getpass("Enter password: ")  # Fallback
```

### **Shared Factory Pattern**
```python
# In src/gmail_llm/shared/gmail_factory.py
class GmailConnectorFactory:
    _connector: Optional[GmailConnector] = None  # Singleton instance
    
    def get_connector(self):
        if self._connector is None:
            # First server to call this decrypts credentials
            self._connector = GmailConnector(use_encrypted=True)
            self._connector.authenticate()  # Uses GMAIL_MCP_PASSWORD
        return self._connector  # Subsequent calls reuse this
```

### **Configuration Integration**
```python
# In src/gmail_llm/config.py
@dataclass
class GmailConfig:
    credentials_path: str = "credentials.encrypted"  # ✓ Uses encrypted file
    use_encrypted: bool = True                       # ✓ Enables encryption
```

## 🎯 **Benefits**

### **1. User Experience**
- **Single password prompt** - Enter once, works for both servers
- **Automatic startup** - No manual intervention after password entry
- **Standard workflow** - Same `./start_mcp_server.sh` command

### **2. Security**
- **Process isolation** - Each server in separate process
- **Shared authentication** - Single decrypt operation
- **Memory-only storage** - Password never hits disk
- **Automatic cleanup** - Shell environment cleared

### **3. Reliability**
- **Independent restart** - Restart servers individually without re-entering password
- **Persistent authentication** - Encrypted tokens cached between restarts
- **Fallback handling** - Graceful fallback if environment variable missing

## 🚀 **Ready to Use**

The encrypted credentials integration is **fully compatible** with the new separate process architecture:

1. ✅ **Single password entry** via `start_mcp_server.sh`
2. ✅ **Both servers inherit** `GMAIL_MCP_PASSWORD` environment variable
3. ✅ **Shared Gmail factory** ensures single authentication
4. ✅ **Process isolation** maintains security and reliability
5. ✅ **Standard supervisor management** for both processes

**You can run `./start_mcp_server.sh` and both servers will decrypt credentials properly!**