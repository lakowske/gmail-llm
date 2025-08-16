"""
Server launcher that runs both MCP and HTTP API servers concurrently.
Allows maintaining MCP functionality while adding HTTP API access.
Refactored to use shared configuration and proper logging.
"""

import asyncio
import logging
import signal
import sys
from typing import Optional
import uvicorn
from concurrent.futures import ThreadPoolExecutor
import threading

from .mcp.fastmcp_server import create_gmail_mcp_server
from .api.rest_server import app as fastapi_app
from .config import get_config
from .shared.logging_config import setup_logging, get_logger

logger = get_logger(__name__)

class DualServerLauncher:
    """Manages both MCP and HTTP API servers."""
    
    def __init__(self, 
                 mcp_host: str = None, 
                 mcp_port: int = None,
                 api_host: str = None, 
                 api_port: int = None,
                 log_level: str = None):
        # Use configuration defaults if not provided
        config = get_config()
        self.mcp_host = mcp_host or config.server.mcp_host
        self.mcp_port = mcp_port or config.server.mcp_port
        self.api_host = api_host or config.server.api_host
        self.api_port = api_port or config.server.api_port
        self.log_level = log_level or config.server.log_level
        self.mcp_server = None
        self.api_server = None
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.shutdown_event = threading.Event()
        
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating shutdown...")
            self.shutdown_event.set()
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def run_mcp_server(self):
        """Run the MCP server using FastMCP."""
        try:
            logger.info(f"Starting MCP server on {self.mcp_host}:{self.mcp_port}")
            
            # Create the MCP server
            mcp = create_gmail_mcp_server()
            
            # Run the MCP server
            mcp.run(
                transport="sse",
                host=self.mcp_host,
                port=self.mcp_port,
                path="/mcp"
            )
            
        except Exception as e:
            logger.error(f"Error running MCP server: {e}")
            self.shutdown_event.set()
    
    def run_api_server(self):
        """Run the FastAPI HTTP server."""
        try:
            logger.info(f"Starting HTTP API server on {self.api_host}:{self.api_port}")
            
            # Configure uvicorn
            config = uvicorn.Config(
                app=fastapi_app,
                host=self.api_host,
                port=self.api_port,
                log_level=self.log_level,
                access_log=True
            )
            
            server = uvicorn.Server(config)
            server.run()
            
        except Exception as e:
            logger.error(f"Error running API server: {e}")
            self.shutdown_event.set()
    
    def start_servers(self):
        """Start both servers concurrently."""
        self.setup_signal_handlers()
        
        logger.info("Starting Gmail LLM Dual Server...")
        logger.info(f"MCP Server will be available at: http://{self.mcp_host}:{self.mcp_port}/mcp")
        logger.info(f"HTTP API Server will be available at: http://{self.api_host}:{self.api_port}")
        logger.info(f"API Documentation will be available at: http://{self.api_host}:{self.api_port}/docs")
        
        # Start MCP server in thread
        mcp_future = self.executor.submit(self.run_mcp_server)
        
        # Start API server in thread  
        api_future = self.executor.submit(self.run_api_server)
        
        try:
            # Wait for shutdown signal
            while not self.shutdown_event.is_set():
                # Check if either server has crashed
                if mcp_future.done():
                    if mcp_future.exception():
                        logger.error(f"MCP server crashed: {mcp_future.exception()}")
                        break
                        
                if api_future.done():
                    if api_future.exception():
                        logger.error(f"API server crashed: {api_future.exception()}")
                        break
                        
                self.shutdown_event.wait(1)  # Check every second
                
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        
        finally:
            logger.info("Shutting down servers...")
            self.shutdown_event.set()
            
            # Cancel futures
            mcp_future.cancel()
            api_future.cancel()
            
            # Shutdown executor
            self.executor.shutdown(wait=True, timeout=10)
            
            logger.info("Servers shutdown complete")

def main():
    """Main entry point for dual server launcher."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Gmail LLM Dual Server Launcher")
    config = get_config()
    parser.add_argument("--mcp-host", default=config.server.mcp_host, help="MCP server host")
    parser.add_argument("--mcp-port", type=int, default=config.server.mcp_port, help="MCP server port")
    parser.add_argument("--api-host", default=config.server.api_host, help="HTTP API server host")
    parser.add_argument("--api-port", type=int, default=config.server.api_port, help="HTTP API server port")
    parser.add_argument("--log-level", default=config.server.log_level, help="Log level")
    
    args = parser.parse_args()
    
    # Setup structured logging
    setup_logging(
        log_level=args.log_level,
        structured=True,
        correlation_enabled=True
    )
    
    # Create and start launcher
    launcher = DualServerLauncher(
        mcp_host=args.mcp_host,
        mcp_port=args.mcp_port,
        api_host=args.api_host,
        api_port=args.api_port,
        log_level=args.log_level
    )
    
    launcher.start_servers()

if __name__ == "__main__":
    main()