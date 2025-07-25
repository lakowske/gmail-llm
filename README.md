# Gmail LLM Connector

A Python script to connect to Gmail inbox using the Gmail API with OAuth 2.0 authentication.

## Setup

1. **Create a Google Cloud Project**:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the Gmail API

2. **Create OAuth 2.0 Credentials**:
   - Go to "Credentials" in the Google Cloud Console
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop application"
   - Download the JSON file and save it as `credentials.json` in this directory

3. **Install Dependencies**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Encrypt Credentials (Recommended)**:
   ```bash
   python setup_encrypted_credentials.py
   ```
   This will encrypt your `credentials.json` file with a password you choose.

5. **Run the Script**:
   ```bash
   # Read emails (default command)
   python gmail_connector.py --encrypted
   
   # Send an email
   python gmail_connector.py --encrypted send --to "recipient@example.com" --subject "Test Subject" --message "Hello, this is a test message!"
   
   # Read emails with search query
   python gmail_connector.py --encrypted read --query "is:unread" --max-results 10
   ```

## Features

- OAuth 2.0 authentication with Gmail API
- **Send emails** directly from command line
- **Encrypted credential storage** with password protection
- Retrieve messages from Gmail inbox
- Extract key message information (sender, subject, date, snippet)
- **Advanced search queries** (unread, from specific senders, etc.)
- Comprehensive error handling and logging
- Token caching for subsequent runs

## Usage

### Command Line Interface

**Send Email:**
```bash
# Basic email
python gmail_connector.py --encrypted send --to "user@example.com" --subject "Hello" --message "This is a test email"

# Email with HTML content
python gmail_connector.py --encrypted send --to "user@example.com" --subject "Rich Email" --message "Plain text version" --html "<h1>HTML Version</h1><p>This is <b>bold</b>!</p>"
```

**Read Emails:**
```bash
# Read recent emails
python gmail_connector.py --encrypted read

# Search for unread emails
python gmail_connector.py --encrypted read --query "is:unread" --max-results 20

# Search emails from specific sender
python gmail_connector.py --encrypted read --query "from:example@gmail.com"
```

### Python API

The `GmailConnector` class provides methods to:
- `authenticate()`: Authenticate with Gmail API
- `send_email(to, subject, message_text, html_content)`: Send emails
- `get_messages(query, max_results)`: Retrieve messages with optional query
- `extract_message_info(message)`: Extract readable information from raw message data

## Credential Encryption

The system supports encrypted credential storage using:
- **Fernet encryption** (symmetric encryption)
- **PBKDF2** key derivation with 100,000 iterations
- **Salt-based security** to prevent rainbow table attacks
- **Automatic cleanup** of temporary credential files

### Manual Encryption/Decryption

```bash
# Encrypt credentials manually
python credential_manager.py encrypt credentials.json

# Test decryption
python credential_manager.py decrypt
```

## Security

- Uses OAuth 2.0 for secure authentication
- **Encrypted credential storage** with strong encryption
- Credentials and tokens are stored locally
- Read-only access to Gmail (gmail.readonly scope)
- **Automatic cleanup** of temporary files
- **Password-based encryption** for API credentials

## MCP Server

The project includes a FastAPI-based MCP (Model Context Protocol) server that allows LLMs to interact with Gmail through standardized tools.

### Starting the MCP Server

**Option 1: Simple Start**
```bash
# Install dependencies including FastAPI and MCP
pip install -r requirements.txt

# Start the MCP server directly
python mcp_server.py
```

**Option 2: Managed with Supervisor (Recommended for long-running)**
```bash
# Install supervisor
pip install supervisor

# Start with the management script
./start_mcp_server.sh start

# Other management commands
./start_mcp_server.sh status    # Check status
./start_mcp_server.sh logs      # View recent logs
./start_mcp_server.sh follow    # Follow logs in real-time
./start_mcp_server.sh restart   # Restart server
./start_mcp_server.sh stop      # Stop server
```

The server will start on `http://localhost:8000` with the following endpoints:

- `GET /` - Server status and information
- `GET /health` - Health check endpoint
- `POST /mcp/tools/list` - List available MCP tools
- `POST /mcp/tools/call` - Call MCP tools
- `POST /tools/{tool_name}` - Direct tool calling (non-MCP)

### Available MCP Tools

**`read_emails`** - Read emails from Gmail inbox
```json
{
  "name": "read_emails",
  "arguments": {
    "query": "is:unread",
    "max_results": 10
  }
}
```

**`send_email`** - Send an email via Gmail
```json
{
  "name": "send_email", 
  "arguments": {
    "to": "recipient@example.com",
    "subject": "Test Email",
    "message": "Hello from MCP server!",
    "html_content": "<h1>Hello from MCP server!</h1>"
  }
}
```

### Using with Claude Code

Add the MCP server to your Claude Code configuration:

```bash
# Add MCP server to Claude Code
claude mcp add-json gmail-llm-connector '{"command": "python", "args": ["mcp_server.py"], "env": {"PYTHONPATH": "./src"}}'
```

Or use the provided configuration file:
```bash
claude --mcp-config mcp_config.json
```

### MCP Server Features

- **Secure Authentication** - Uses encrypted Gmail credentials
- **Standard MCP Protocol** - Compatible with any MCP client
- **Comprehensive Logging** - Full request/response logging
- **Error Handling** - Graceful error handling and reporting
- **Health Monitoring** - Built-in health check endpoints
- **CORS Support** - Cross-origin requests enabled
- **Process Management** - Supervisor configuration for production use
- **Log Management** - Structured logging with rotation

### Logs and Monitoring

Server logs are stored in `./logs/` directory:
- `gmail-mcp-server.log` - Application logs
- `supervisord.log` - Supervisor process logs

Log files are automatically rotated when they reach 50MB, keeping 10 backup files.