"""
FastMCP-based Gmail MCP server library.
Provides proper MCP protocol implementation for Gmail operations.
"""

import logging
from typing import Optional, Dict, Any
from fastmcp import FastMCP

from ..core.gmail_connector import GmailConnector

logger = logging.getLogger(__name__)


def create_gmail_mcp_server() -> FastMCP:
    """Create and configure a FastMCP server for Gmail operations."""
    
    # Initialize FastMCP server
    mcp = FastMCP("Gmail LLM Connector")
    
    # Global Gmail connector
    gmail_connector: Optional[GmailConnector] = None

    def initialize_gmail():
        """Initialize Gmail connector with authentication."""
        nonlocal gmail_connector
        
        if gmail_connector and gmail_connector.is_authenticated():
            return gmail_connector
        
        try:
            logger.info("Initializing Gmail connector...")
            gmail_connector = GmailConnector(
                credentials_path='credentials.encrypted',
                use_encrypted=True
            )
            
            if not gmail_connector.authenticate():
                logger.error("Failed to authenticate Gmail connector")
                raise RuntimeError("Gmail authentication failed")
                
            logger.info("Gmail connector initialized successfully")
            return gmail_connector
            
        except Exception as e:
            logger.error(f"Failed to initialize Gmail connector: {e}")
            raise

    @mcp.tool
    def read_emails(query: str = "", max_results: int = 10) -> Dict[str, Any]:
        """
        Read emails from Gmail inbox with optional search query and result limit.
        
        Args:
            query: Gmail search query (e.g., 'is:unread', 'from:user@example.com', 'subject:important')
            max_results: Maximum number of emails to retrieve (1-50)
        
        Returns:
            Dictionary containing success status, message, emails list, and count
        """
        try:
            # Validate max_results
            if not 1 <= max_results <= 50:
                return {
                    "success": False,
                    "message": "max_results must be between 1 and 50",
                    "emails": [],
                    "count": 0
                }
            
            # Initialize Gmail if needed
            connector = initialize_gmail()
            
            # Read emails
            raw_emails = connector.get_messages(query=query, max_results=max_results)
            
            if not raw_emails:
                return {
                    "success": True,
                    "message": "No emails found",
                    "emails": [],
                    "count": 0
                }
            
            # Extract and format email information
            formatted_emails = []
            for raw_email in raw_emails:
                # Use the connector's extract_message_info method to properly parse email data
                email_info = connector.extract_message_info(raw_email)
                formatted_email = {
                    "id": email_info.get("id", ""),
                    "thread_id": email_info.get("thread_id", ""),
                    "from": email_info.get("from", "Unknown"),
                    "to": email_info.get("to", "Unknown"), 
                    "subject": email_info.get("subject", "No Subject"),
                    "date": email_info.get("date", "Unknown"),
                    "snippet": email_info.get("snippet", ""),
                    "label_ids": email_info.get("label_ids", [])
                }
                formatted_emails.append(formatted_email)
            
            logger.info(f"Successfully read {len(formatted_emails)} emails")
            
            return {
                "success": True,
                "message": f"Retrieved {len(formatted_emails)} emails",
                "emails": formatted_emails,
                "count": len(formatted_emails)
            }
            
        except Exception as e:
            error_msg = f"Error reading emails: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "emails": [],
                "count": 0
            }

    @mcp.tool
    def send_email(to: str, subject: str, message: str, html_content: Optional[str] = None) -> Dict[str, Any]:
        """
        Send an email via Gmail.
        
        Args:
            to: Recipient email address
            subject: Email subject line
            message: Plain text email content
            html_content: Optional HTML email content for rich formatting
        
        Returns:
            Dictionary containing success status, message, and optional message_id
        """
        try:
            # Initialize Gmail if needed
            connector = initialize_gmail()
            
            # Send email
            result = connector.send_email(
                to=to,
                subject=subject,
                message_text=message,
                html_content=html_content
            )
            
            if result:
                logger.info(f"Successfully sent email to {to}")
                return {
                    "success": True,
                    "message": f"Email sent successfully to {to}",
                    "message_id": None  # GmailConnector doesn't return message_id
                }
            else:
                error_msg = "Failed to send email"
                logger.error(f"Failed to send email to {to}")
                return {
                    "success": False,
                    "message": error_msg,
                    "message_id": None
                }
                
        except Exception as e:
            error_msg = f"Error sending email: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "message_id": None
            }
    
    return mcp