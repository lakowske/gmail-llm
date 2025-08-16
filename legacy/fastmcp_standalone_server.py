#!/usr/bin/env python3
"""
Standalone FastMCP server for Gmail operations.
Runs as HTTP server for persistent connections with password authentication.
"""

import logging
from src.gmail_llm.mcp.fastmcp_server import create_gmail_mcp_server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
)

if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logger.info("Starting Gmail FastMCP HTTP server on http://127.0.0.1:8001")
    
    # Create and run the MCP server with HTTP transport
    mcp = create_gmail_mcp_server()
    mcp.run(
        transport="http",
        host="127.0.0.1", 
        port=8001,
        log_level="info"
    )