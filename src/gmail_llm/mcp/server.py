"""
FastAPI-based MCP server for Gmail operations.
Provides MCP-compliant endpoints for LLMs to interact with Gmail.
"""

import logging
import asyncio
from typing import Dict, Any, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ..core.gmail_connector import GmailConnector
from .tools import GmailMCPTools
from .schemas import MCP_TOOLS, MCP_SERVER_INFO

logger = logging.getLogger(__name__)

# Global variables for Gmail connector and tools
gmail_connector: GmailConnector = None
gmail_tools: GmailMCPTools = None


# MCP Protocol Models
class MCPListToolsRequest(BaseModel):
    """MCP list tools request."""
    method: str = "tools/list"


class MCPListToolsResponse(BaseModel):
    """MCP list tools response."""
    tools: List[Dict[str, Any]]


class MCPCallToolRequest(BaseModel):
    """MCP call tool request."""
    method: str = "tools/call"
    params: Dict[str, Any]


class MCPCallToolResponse(BaseModel):
    """MCP call tool response."""
    content: List[Dict[str, Any]]
    isError: bool = False


class MCPServerInfoResponse(BaseModel):
    """MCP server info response."""
    name: str
    version: str
    description: str
    author: str
    homepage: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown tasks."""
    # Startup
    logger.info("Starting Gmail MCP server...")
    
    global gmail_connector, gmail_tools
    
    try:
        # Initialize Gmail connector with encrypted credentials
        gmail_connector = GmailConnector(
            credentials_path='credentials.encrypted',
            use_encrypted=True
        )
        
        # Authenticate
        if not gmail_connector.authenticate():
            logger.error("Failed to authenticate Gmail connector")
            raise RuntimeError("Gmail authentication failed")
        
        # Initialize MCP tools
        gmail_tools = GmailMCPTools(gmail_connector)
        
        logger.info("Gmail MCP server started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start Gmail MCP server: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Gmail MCP server...")


# Create FastAPI app
app = FastAPI(
    title="Gmail LLM Connector MCP Server",
    description="MCP server for Gmail operations - read and send emails through Gmail API",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint with server information."""
    return {
        "message": "Gmail LLM Connector MCP Server",
        "status": "running",
        "authenticated": gmail_connector.is_authenticated() if gmail_connector else False
    }


@app.get("/info", response_model=MCPServerInfoResponse)
async def get_server_info():
    """Get MCP server information."""
    return MCPServerInfoResponse(**MCP_SERVER_INFO)


@app.post("/mcp/tools/list", response_model=MCPListToolsResponse)
async def list_tools(request: MCPListToolsRequest):
    """List available MCP tools."""
    logger.info("Received tools/list request")
    
    if not gmail_connector or not gmail_connector.is_authenticated():
        raise HTTPException(status_code=500, detail="Gmail connector not authenticated")
    
    return MCPListToolsResponse(tools=MCP_TOOLS)


@app.post("/mcp/tools/call", response_model=MCPCallToolResponse)
async def call_tool(request: MCPCallToolRequest):
    """Call an MCP tool."""
    logger.info(f"Received tools/call request for tool: {request.params.get('name')}")
    
    if not gmail_connector or not gmail_connector.is_authenticated():
        raise HTTPException(status_code=500, detail="Gmail connector not authenticated")
    
    if not gmail_tools:
        raise HTTPException(status_code=500, detail="Gmail tools not initialized")
    
    try:
        tool_name = request.params.get("name")
        tool_arguments = request.params.get("arguments", {})
        
        if not tool_name:
            raise ValueError("Tool name is required")
        
        # Call the tool
        result = await gmail_tools.call_tool(tool_name, tool_arguments)
        
        # Format response according to MCP protocol
        return MCPCallToolResponse(
            content=[
                {
                    "type": "text",
                    "text": str(result)
                }
            ],
            isError=not result.get("success", False)
        )
        
    except Exception as e:
        logger.error(f"Error calling tool: {e}")
        return MCPCallToolResponse(
            content=[
                {
                    "type": "text", 
                    "text": f"Error: {str(e)}"
                }
            ],
            isError=True
        )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "gmail_authenticated": gmail_connector.is_authenticated() if gmail_connector else False,
        "tools_available": len(gmail_tools.get_available_tools()) if gmail_tools else 0
    }


@app.post("/tools/{tool_name}")
async def call_tool_direct(tool_name: str, arguments: Dict[str, Any]):
    """Direct tool calling endpoint (non-MCP)."""
    logger.info(f"Direct tool call: {tool_name}")
    
    if not gmail_connector or not gmail_connector.is_authenticated():
        raise HTTPException(status_code=500, detail="Gmail connector not authenticated")
    
    if not gmail_tools:
        raise HTTPException(status_code=500, detail="Gmail tools not initialized")
    
    try:
        result = await gmail_tools.call_tool(tool_name, arguments)
        return result
    except Exception as e:
        logger.error(f"Error in direct tool call: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    
    # Run server
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )