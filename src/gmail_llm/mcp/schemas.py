"""
MCP server schema definitions for Gmail operations.
Defines the data models and tool schemas for the MCP server.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# Request/Response Models
class ReadEmailsRequest(BaseModel):
    """Request model for reading emails."""
    query: Optional[str] = Field(default="", description="Gmail search query (e.g., 'is:unread', 'from:user@example.com')")
    max_results: Optional[int] = Field(default=10, ge=1, le=50, description="Maximum number of emails to retrieve (1-50)")


class SendEmailRequest(BaseModel):
    """Request model for sending emails."""
    to: str = Field(description="Recipient email address")
    subject: str = Field(description="Email subject line")
    message: str = Field(description="Plain text email content")
    html_content: Optional[str] = Field(default=None, description="Optional HTML email content")


class EmailInfo(BaseModel):
    """Email information model."""
    id: str = Field(description="Gmail message ID")
    thread_id: str = Field(description="Gmail thread ID")
    from_address: Optional[str] = Field(alias="from", default="Unknown", description="Sender email address")
    to_address: Optional[str] = Field(alias="to", default="Unknown", description="Recipient email address")
    subject: Optional[str] = Field(default="No Subject", description="Email subject")
    date: Optional[str] = Field(default="Unknown", description="Email date")
    snippet: Optional[str] = Field(default="", description="Email snippet/preview")
    label_ids: List[str] = Field(default=[], description="Gmail label IDs")


class ReadEmailsResponse(BaseModel):
    """Response model for reading emails."""
    success: bool = Field(description="Whether the operation was successful")
    message: str = Field(description="Status message")
    emails: List[EmailInfo] = Field(default=[], description="List of email information")
    count: int = Field(description="Number of emails retrieved")


class SendEmailResponse(BaseModel):
    """Response model for sending emails."""
    success: bool = Field(description="Whether the email was sent successfully")
    message: str = Field(description="Status message")
    message_id: Optional[str] = Field(default=None, description="Gmail message ID if successful")


# MCP Tool Definitions
MCP_TOOLS = [
    {
        "name": "read_emails",
        "description": "Read emails from Gmail inbox with optional search query and result limit",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Gmail search query (e.g., 'is:unread', 'from:user@example.com', 'subject:important')",
                    "default": ""
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of emails to retrieve (1-50)",
                    "minimum": 1,
                    "maximum": 50,
                    "default": 10
                }
            }
        }
    },
    {
        "name": "send_email",
        "description": "Send an email via Gmail",
        "inputSchema": {
            "type": "object",
            "properties": {
                "to": {
                    "type": "string",
                    "description": "Recipient email address"
                },
                "subject": {
                    "type": "string",
                    "description": "Email subject line"
                },
                "message": {
                    "type": "string",
                    "description": "Plain text email content"
                },
                "html_content": {
                    "type": "string",
                    "description": "Optional HTML email content for rich formatting"
                }
            },
            "required": ["to", "subject", "message"]
        }
    }
]


# MCP Server Info
MCP_SERVER_INFO = {
    "name": "gmail-llm-connector",
    "version": "1.0.0",
    "description": "MCP server for Gmail operations - read and send emails through Gmail API",
    "author": "Gmail LLM Connector",
    "homepage": "https://github.com/yourusername/gmail-llm-connector"
}