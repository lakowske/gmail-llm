"""
MCP (Model Context Protocol) server module for Gmail operations.
Provides FastAPI-based MCP server for LLM integration.
"""

from .server import app
from .tools import GmailMCPTools
from .schemas import MCP_TOOLS, MCP_SERVER_INFO

__all__ = ["app", "GmailMCPTools", "MCP_TOOLS", "MCP_SERVER_INFO"]