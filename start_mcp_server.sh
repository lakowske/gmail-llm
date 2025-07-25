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

# Check if supervisor is installed
if ! command -v supervisord &> /dev/null; then
    echo -e "${RED}Error: supervisord is not installed${NC}"
    echo "Install with: pip install supervisor"
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
        supervisorctl -c supervisord.conf shutdown 2>/dev/null || true
        sleep 2
    fi
    
    # Start supervisord (it will inherit the environment variable)
    supervisord -c supervisord.conf
    
    # Clear the password from current shell environment for security
    unset GMAIL_MCP_PASSWORD
    
    # Wait a moment for startup
    sleep 3
    
    # Check status
    if supervisorctl -c supervisord.conf status gmail-fastmcp-server | grep -q "RUNNING"; then
        echo -e "${GREEN}✓ Gmail FastMCP Server started successfully${NC}"
        echo -e "${GREEN}✓ Server running on http://localhost:8001/mcp/${NC}"
        echo -e "${GREEN}✓ Logs available in ./logs/gmail-fastmcp-server.log${NC}"
        echo -e "${YELLOW}Note: Password is securely stored in server process memory${NC}"
    else
        echo -e "${RED}✗ Failed to start Gmail FastMCP Server${NC}"
        echo "Check logs for details:"
        echo "  supervisord logs: ./logs/supervisord.log"
        echo "  server logs: ./logs/gmail-fastmcp-server.log"
        exit 1
    fi
}

# Function to show status
show_status() {
    echo -e "${YELLOW}Gmail FastMCP Server Status:${NC}"
    supervisorctl -c supervisord.conf status gmail-fastmcp-server
}

# Function to stop server
stop_server() {
    echo -e "${YELLOW}Stopping Gmail FastMCP Server...${NC}"
    supervisorctl -c supervisord.conf stop gmail-fastmcp-server
    supervisorctl -c supervisord.conf shutdown
    echo -e "${GREEN}✓ Server stopped${NC}"
}

# Function to restart server
restart_server() {
    echo -e "${YELLOW}Restarting Gmail FastMCP Server...${NC}"
    supervisorctl -c supervisord.conf restart gmail-fastmcp-server
    echo -e "${GREEN}✓ Server restarted${NC}"
}

# Function to show logs
show_logs() {
    echo -e "${YELLOW}Gmail FastMCP Server Logs (last 50 lines):${NC}"
    echo "=========================================="
    tail -n 50 ./logs/gmail-fastmcp-server.log
}

# Function to follow logs
follow_logs() {
    echo -e "${YELLOW}Following Gmail FastMCP Server Logs (Ctrl+C to exit):${NC}"
    echo "==================================================="
    tail -f ./logs/gmail-fastmcp-server.log
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
        echo "  start   - Start the Gmail FastMCP Server (default)"
        echo "  stop    - Stop the Gmail FastMCP Server"
        echo "  restart - Restart the Gmail FastMCP Server"
        echo "  status  - Show server status"
        echo "  logs    - Show recent server logs"
        echo "  follow  - Follow server logs in real-time"
        exit 1
        ;;
esac