#!/usr/bin/env python3
"""
Startup script for running only the HTTP API server.
"""

import sys
import os
import argparse
import uvicorn

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gmail_llm.api.rest_server import app
from gmail_llm.config import get_config
from gmail_llm.shared.logging_config import setup_logging, get_logger

def main():
    """Main entry point for HTTP API server."""
    parser = argparse.ArgumentParser(description="Gmail LLM HTTP API Server")
    
    config = get_config()
    parser.add_argument("--host", default=config.server.api_host, help="API server host")
    parser.add_argument("--port", type=int, default=config.server.api_port, help="API server port")
    parser.add_argument("--log-level", default=config.server.log_level, help="Log level")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")
    
    args = parser.parse_args()
    
    # Setup structured logging
    setup_logging(
        log_level=args.log_level,
        structured=True,
        correlation_enabled=True
    )
    
    logger = get_logger(__name__)
    
    try:
        logger.info(f"Starting Gmail LLM HTTP API Server on {args.host}:{args.port}")
        logger.info(f"API Documentation available at: http://{args.host}:{args.port}/docs")
        
        # Run the FastAPI server
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            log_level=args.log_level,
            access_log=True,
            workers=args.workers
        )
        
    except Exception as e:
        logger.error(f"Failed to start API server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()