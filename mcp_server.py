#!/usr/bin/env python3
"""
Gmail MCP Server startup script.
Starts the FastAPI-based MCP server for Gmail operations.
"""

import sys
import os
import logging

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import uvicorn
from gmail_llm.mcp.server import app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main function to start the MCP server."""
    logger.info("Starting Gmail MCP Server...")
    
    try:
        # Run the FastAPI server
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        logger.info("MCP server stopped by user")
    except Exception as e:
        logger.error(f"Failed to start MCP server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()