"""
MCP tools implementation for Gmail operations.
Implements the actual tool functions that handle email reading and sending.
"""

import logging
from typing import Dict, Any, List

from ..core.gmail_connector import GmailConnector
from .schemas import (
    ReadEmailsRequest, 
    SendEmailRequest, 
    ReadEmailsResponse, 
    SendEmailResponse,
    EmailInfo
)

logger = logging.getLogger(__name__)


class GmailMCPTools:
    """MCP tools implementation for Gmail operations."""
    
    def __init__(self, gmail_connector: GmailConnector):
        """
        Initialize Gmail MCP tools.
        
        Args:
            gmail_connector: Authenticated GmailConnector instance
        """
        self.gmail = gmail_connector
        logger.info("Initialized GmailMCPTools")
    
    async def read_emails(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Read emails from Gmail inbox.
        
        Args:
            arguments: Tool arguments containing query and max_results
            
        Returns:
            Dictionary with operation result and email data
        """
        try:
            # Parse and validate request
            request = ReadEmailsRequest(**arguments)
            logger.info(f"Reading emails with query='{request.query}', max_results={request.max_results}")
            
            # Check authentication
            if not self.gmail.is_authenticated():
                logger.error("Gmail connector not authenticated")
                return ReadEmailsResponse(
                    success=False,
                    message="Gmail connector not authenticated",
                    emails=[],
                    count=0
                ).dict()
            
            # Get messages from Gmail
            messages = self.gmail.get_messages(query=request.query, max_results=request.max_results)
            
            if messages is None:
                logger.error("Failed to retrieve messages from Gmail")
                return ReadEmailsResponse(
                    success=False,
                    message="Failed to retrieve messages from Gmail API",
                    emails=[],
                    count=0
                ).dict()
            
            # Process messages into EmailInfo objects
            email_list = []
            for message in messages:
                try:
                    info = self.gmail.extract_message_info(message)
                    if 'error' not in info:
                        email_info = EmailInfo(
                            id=info['id'],
                            thread_id=info['thread_id'],
                            from_address=info['from'],
                            to_address=info['to'],
                            subject=info['subject'],
                            date=info['date'],
                            snippet=info['snippet'],
                            label_ids=info['label_ids']
                        )
                        email_list.append(email_info)
                    else:
                        logger.warning(f"Error processing message: {info['error']}")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    continue
            
            logger.info(f"Successfully processed {len(email_list)} emails")
            return ReadEmailsResponse(
                success=True,
                message=f"Retrieved {len(email_list)} emails",
                emails=email_list,
                count=len(email_list)
            ).dict()
            
        except Exception as e:
            logger.error(f"Error in read_emails tool: {type(e).__name__}: {e}")
            return ReadEmailsResponse(
                success=False,
                message=f"Error reading emails: {str(e)}",
                emails=[],
                count=0
            ).dict()
    
    async def send_email(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send an email via Gmail.
        
        Args:
            arguments: Tool arguments containing email details
            
        Returns:
            Dictionary with operation result
        """
        try:
            # Parse and validate request
            request = SendEmailRequest(**arguments)
            logger.info(f"Sending email to={request.to}, subject='{request.subject}'")
            
            # Check authentication
            if not self.gmail.is_authenticated():
                logger.error("Gmail connector not authenticated")
                return SendEmailResponse(
                    success=False,
                    message="Gmail connector not authenticated"
                ).dict()
            
            # Send email
            success = self.gmail.send_email(
                to=request.to,
                subject=request.subject,
                message_text=request.message,
                html_content=request.html_content
            )
            
            if success:
                logger.info(f"Email sent successfully to {request.to}")
                return SendEmailResponse(
                    success=True,
                    message=f"Email sent successfully to {request.to}",
                    message_id="unknown"  # Gmail API doesn't return message ID in our current implementation
                ).dict()
            else:
                logger.error(f"Failed to send email to {request.to}")
                return SendEmailResponse(
                    success=False,
                    message=f"Failed to send email to {request.to}"
                ).dict()
                
        except Exception as e:
            logger.error(f"Error in send_email tool: {type(e).__name__}: {e}")
            return SendEmailResponse(
                success=False,
                message=f"Error sending email: {str(e)}"
            ).dict()
    
    def get_available_tools(self) -> List[str]:
        """
        Get list of available tool names.
        
        Returns:
            List of tool names
        """
        return ["read_emails", "send_email"]
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool by name with given arguments.
        
        Args:
            name: Tool name
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        logger.info(f"Calling tool: {name}")
        
        if name == "read_emails":
            return await self.read_emails(arguments)
        elif name == "send_email":
            return await self.send_email(arguments)
        else:
            logger.error(f"Unknown tool: {name}")
            return {
                "success": False,
                "message": f"Unknown tool: {name}",
                "available_tools": self.get_available_tools()
            }