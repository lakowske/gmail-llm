#!/usr/bin/env python3
"""
Startup script for running only the MCP server.
"""

import sys
import os
import argparse

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gmail_llm.mcp.fastmcp_server import create_gmail_mcp_server
from gmail_llm.config import get_config
from gmail_llm.shared.logging_config import setup_logging, get_logger

def main():
    """Main entry point for MCP server."""
    parser = argparse.ArgumentParser(description="Gmail LLM MCP Server")
    
    config = get_config()
    parser.add_argument("--host", default=config.server.mcp_host, help="MCP server host")
    parser.add_argument("--port", type=int, default=config.server.mcp_port, help="MCP server port")
    parser.add_argument("--log-level", default=config.server.log_level, help="Log level")
    parser.add_argument("--path", default="/mcp", help="MCP server path")
    
    args = parser.parse_args()
    
    # Setup structured logging
    setup_logging(
        log_level=args.log_level,
        structured=True,
        correlation_enabled=True
    )
    
    logger = get_logger(__name__)
    
    try:
        logger.info(f"Starting Gmail LLM MCP Server on {args.host}:{args.port}")
        
        # Create and run the MCP server
        mcp = create_gmail_mcp_server()
        mcp.run(
            transport="sse",
            host=args.host,
            port=args.port,
            path=args.path
        )
        
    except Exception as e:
        logger.error(f"Failed to start MCP server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()