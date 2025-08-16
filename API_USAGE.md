# Gmail LLM HTTP API Usage

This document describes how to use the HTTP API endpoints alongside the existing MCP server.

## Quick Start

### Start Both Servers
```bash
# Start both MCP and HTTP API servers
python start_dual_server.py

# Custom ports
python start_dual_server.py --mcp-port 8001 --api-port 8000
```

**Default URLs (localhost only):**
- MCP Server: `http://127.0.0.1:8001/mcp`
- HTTP API: `http://127.0.0.1:8000`
- API Documentation: `http://127.0.0.1:8000/docs`

## HTTP API Endpoints

### Health Check
```bash
curl http://127.0.0.1:8000/health
```

### Read Emails
```bash
# GET request
curl "http://127.0.0.1:8000/api/emails?query=is:unread&max_results=5"

# POST request
curl -X POST "http://127.0.0.1:8000/api/emails/read" \
  -H "Content-Type: application/json" \
  -d '{"query": "is:unread", "max_results": 10}'
```

### Send Email
```bash
curl -X POST "http://127.0.0.1:8000/api/emails/send" \
  -H "Content-Type: application/json" \
  -d '{
    "to": "recipient@example.com",
    "subject": "Test Email",
    "message": "This is a test email from the API",
    "html_content": "<p>This is a <b>test email</b> from the API</p>"
  }'
```

### Email Actions
```bash
# Mark as read
curl -X POST "http://127.0.0.1:8000/api/emails/{message_id}/mark-read"

# Mark as spam
curl -X POST "http://127.0.0.1:8000/api/emails/{message_id}/mark-spam"

# Move to trash
curl -X POST "http://127.0.0.1:8000/api/emails/{message_id}/trash"

# Add star
curl -X POST "http://127.0.0.1:8000/api/emails/{message_id}/star"

# Modify labels
curl -X POST "http://127.0.0.1:8000/api/emails/{message_id}/labels" \
  -H "Content-Type: application/json" \
  -d '{
    "add_labels": "STARRED,IMPORTANT",
    "remove_labels": "UNREAD"
  }'
```

### Bulk Operations
```bash
# Bulk mark as read
curl -X POST "http://127.0.0.1:8000/api/emails/bulk/mark-read" \
  -H "Content-Type: application/json" \
  -d '{"message_ids": "id1,id2,id3"}'

# Bulk mark as spam
curl -X POST "http://127.0.0.1:8000/api/emails/bulk/mark-spam" \
  -H "Content-Type: application/json" \
  -d '{"message_ids": "id1,id2,id3"}'

# Bulk move to trash
curl -X POST "http://127.0.0.1:8000/api/emails/bulk/trash" \
  -H "Content-Type: application/json" \
  -d '{"message_ids": "id1,id2,id3"}'

# Bulk add stars
curl -X POST "http://127.0.0.1:8000/api/emails/bulk/star" \
  -H "Content-Type: application/json" \
  -d '{"message_ids": "id1,id2,id3"}'

# Bulk modify labels
curl -X POST "http://127.0.0.1:8000/api/emails/bulk/labels" \
  -H "Content-Type: application/json" \
  -d '{
    "message_ids": "id1,id2,id3",
    "add_labels": "STARRED",
    "remove_labels": "UNREAD"
  }'
```

### Get Available Labels
```bash
curl "http://127.0.0.1:8000/api/labels"
```

## Integration Examples

### Python Client
```python
import requests

class GmailAPIClient:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url
    
    def read_emails(self, query="", max_results=10):
        response = requests.get(f"{self.base_url}/api/emails", 
                              params={"query": query, "max_results": max_results})
        return response.json()
    
    def send_email(self, to, subject, message, html_content=None):
        data = {"to": to, "subject": subject, "message": message}
        if html_content:
            data["html_content"] = html_content
        response = requests.post(f"{self.base_url}/api/emails/send", json=data)
        return response.json()

# Usage
client = GmailAPIClient()
emails = client.read_emails("is:unread", 5)
```

### Node.js Client
```javascript
const axios = require('axios');

class GmailAPIClient {
    constructor(baseUrl = 'http://127.0.0.1:8000') {
        this.baseUrl = baseUrl;
    }
    
    async readEmails(query = '', maxResults = 10) {
        const response = await axios.get(`${this.baseUrl}/api/emails`, {
            params: { query, max_results: maxResults }
        });
        return response.data;
    }
    
    async sendEmail(to, subject, message, htmlContent = null) {
        const data = { to, subject, message };
        if (htmlContent) data.html_content = htmlContent;
        
        const response = await axios.post(`${this.baseUrl}/api/emails/send`, data);
        return response.data;
    }
}

// Usage
const client = new GmailAPIClient();
client.readEmails('is:unread', 5).then(emails => console.log(emails));
```

### Shell Script Integration
```bash
#!/bin/bash

API_BASE="http://127.0.0.1:8000"

# Function to read unread emails
read_unread_emails() {
    curl -s "$API_BASE/api/emails?query=is:unread&max_results=10" | jq .
}

# Function to send notification email
send_notification() {
    local to="$1"
    local subject="$2"
    local message="$3"
    
    curl -s -X POST "$API_BASE/api/emails/send" \
        -H "Content-Type: application/json" \
        -d "{\"to\":\"$to\",\"subject\":\"$subject\",\"message\":\"$message\"}"
}

# Usage examples
read_unread_emails
send_notification "admin@example.com" "System Alert" "Service is running normally"
```

## Configuration

### Environment Variables
```bash
export GMAIL_MCP_HOST=localhost
export GMAIL_MCP_PORT=8001
export GMAIL_API_HOST=0.0.0.0
export GMAIL_API_PORT=8000
export GMAIL_LOG_LEVEL=info
```

### Production Deployment
For production use, consider:

1. **Security**: Add authentication/authorization middleware
2. **CORS**: Configure appropriate CORS origins
3. **Rate Limiting**: Add rate limiting to prevent abuse
4. **Monitoring**: Add health checks and metrics
5. **SSL**: Use HTTPS with proper certificates

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000 8001

CMD ["python", "start_dual_server.py", "--api-host", "0.0.0.0"]
```

## Maintenance

### MCP Server Access
The original MCP server remains fully functional at `http://localhost:8001/mcp`. Claude Code and other MCP clients can continue to use it as before.

### Monitoring Both Services
Both servers log to the same output stream with clear service identification. Monitor both for health and performance.

### Graceful Shutdown
The dual server launcher handles SIGINT and SIGTERM signals for graceful shutdown of both services.