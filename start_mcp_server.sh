#!/bin/bash
# Start Gmail MCP Server with Supervisor
# This script helps manage the long-running MCP server

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Gmail FastMCP Server Management Script${NC}"
echo "======================================"

# Check if supervisor is installed in venv
if [ ! -f ".venv/bin/supervisord" ]; then
    echo -e "${RED}Error: supervisord is not installed in virtual environment${NC}"
    echo "Install with: .venv/bin/pip install supervisor"
    exit 1
fi

# Ensure logs directory exists
mkdir -p logs

# Function to start supervisor
start_supervisor() {
    echo -e "${YELLOW}Starting Gmail FastMCP Server with supervisor...${NC}"
    
    # Prompt for password securely
    echo -e "${YELLOW}Gmail credentials password required${NC}"
    read -s -p "Enter encryption password: " GMAIL_MCP_PASSWORD
    echo  # New line after password input
    
    # Validate password is not empty
    if [ -z "$GMAIL_MCP_PASSWORD" ]; then
        echo -e "${RED}Error: Password cannot be empty${NC}"
        exit 1
    fi
    
    # Export password for supervisor to inherit
    export GMAIL_MCP_PASSWORD
    
    # Stop any existing supervisord process
    if [ -f /tmp/supervisord.pid ]; then
        echo "Stopping existing supervisord process..."
        .venv/bin/supervisorctl -c supervisord.conf shutdown 2>/dev/null || true
        sleep 2
    fi
    
    # Start supervisord (it will inherit the environment variable)
    .venv/bin/supervisord -c supervisord.conf
    
    # Clear the password from current shell environment for security
    unset GMAIL_MCP_PASSWORD
    
    # Wait for startup (supervisor needs 10 seconds to confirm RUNNING status)
    sleep 12
    
    # Check status of both servers
    mcp_status=$(.venv/bin/supervisorctl -c supervisord.conf status gmail-mcp-server 2>/dev/null | grep -o "RUNNING" || echo "NOT_RUNNING")
    api_status=$(.venv/bin/supervisorctl -c supervisord.conf status gmail-api-server 2>/dev/null | grep -o "RUNNING" || echo "NOT_RUNNING")
    
    if [ "$mcp_status" = "RUNNING" ] && [ "$api_status" = "RUNNING" ]; then
        echo -e "${GREEN}✓ Gmail servers started successfully${NC}"
        echo -e "${GREEN}✓ MCP Server running on http://127.0.0.1:8001/mcp${NC}"
        echo -e "${GREEN}✓ HTTP API Server running on http://127.0.0.1:8000${NC}"
        echo -e "${GREEN}✓ API Documentation: http://127.0.0.1:8000/docs${NC}"
        echo -e "${GREEN}✓ Logs available in ./logs/gmail-mcp-server.log and ./logs/gmail-api-server.log${NC}"
        echo -e "${YELLOW}Note: Password is securely stored in server process memory${NC}"
    else
        echo -e "${RED}✗ Failed to start Gmail servers${NC}"
        echo "Status: MCP=$mcp_status, API=$api_status"
        echo "Check logs for details:"
        echo "  supervisord logs: ./logs/supervisord.log"
        echo "  mcp server logs: ./logs/gmail-mcp-server.log"
        echo "  api server logs: ./logs/gmail-api-server.log"
        exit 1
    fi
}

# Function to show status
show_status() {
    echo -e "${YELLOW}Gmail Servers Status:${NC}"
    .venv/bin/supervisorctl -c supervisord.conf status gmail-servers:*
}

# Function to stop server
stop_server() {
    echo -e "${YELLOW}Stopping Gmail servers...${NC}"
    .venv/bin/supervisorctl -c supervisord.conf stop gmail-servers:*
    .venv/bin/supervisorctl -c supervisord.conf shutdown
    echo -e "${GREEN}✓ Servers stopped${NC}"
}

# Function to restart server
restart_server() {
    echo -e "${YELLOW}Restarting Gmail servers...${NC}"
    .venv/bin/supervisorctl -c supervisord.conf restart gmail-servers:*
    echo -e "${GREEN}✓ Servers restarted${NC}"
}

# Function to show logs
show_logs() {
    echo -e "${YELLOW}Gmail MCP Server Logs (last 50 lines):${NC}"
    echo "=========================================="
    tail -n 50 ./logs/gmail-mcp-server.log
    echo ""
    echo -e "${YELLOW}Gmail API Server Logs (last 50 lines):${NC}"
    echo "=========================================="
    tail -n 50 ./logs/gmail-api-server.log
}

# Function to follow logs
follow_logs() {
    echo -e "${YELLOW}Following Gmail Server Logs (Ctrl+C to exit):${NC}"
    echo "==================================================="
    # Follow both log files simultaneously
    tail -f ./logs/gmail-mcp-server.log ./logs/gmail-api-server.log
}

# Parse command line arguments
case "${1:-start}" in
    start)
        start_supervisor
        ;;
    stop)
        stop_server
        ;;
    restart)
        restart_server
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    follow)
        follow_logs
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|follow}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the Gmail servers (MCP + HTTP API) (default)"
        echo "  stop    - Stop the Gmail servers"
        echo "  restart - Restart the Gmail servers" 
        echo "  status  - Show server status"
        echo "  logs    - Show recent server logs"
        echo "  follow  - Follow server logs in real-time"
        exit 1
        ;;
esac