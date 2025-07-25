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

    @mcp.tool
    def mark_as_read(message_id: str) -> Dict[str, Any]:
        """
        Mark an email as read by removing the UNREAD label.
        
        Args:
            message_id: Gmail message ID to mark as read
        
        Returns:
            Dictionary containing success status and message
        """
        try:
            # Initialize Gmail if needed
            connector = initialize_gmail()
            
            # Mark as read
            result = connector.mark_as_read(message_id)
            
            logger.info(f"Mark as read result for {message_id}: {result}")
            return result
            
        except Exception as e:
            error_msg = f"Error marking email as read: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg
            }

    @mcp.tool
    def mark_as_spam(message_id: str) -> Dict[str, Any]:
        """
        Mark an email as spam by moving it to the spam folder.
        
        Args:
            message_id: Gmail message ID to mark as spam
        
        Returns:
            Dictionary containing success status and message
        """
        try:
            # Initialize Gmail if needed
            connector = initialize_gmail()
            
            # Mark as spam
            result = connector.mark_as_spam(message_id)
            
            logger.info(f"Mark as spam result for {message_id}: {result}")
            return result
            
        except Exception as e:
            error_msg = f"Error marking email as spam: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg
            }

    @mcp.tool
    def move_to_trash(message_id: str) -> Dict[str, Any]:
        """
        Move an email to trash.
        
        Args:
            message_id: Gmail message ID to move to trash
        
        Returns:
            Dictionary containing success status and message
        """
        try:
            # Initialize Gmail if needed
            connector = initialize_gmail()
            
            # Move to trash
            result = connector.move_to_trash(message_id)
            
            logger.info(f"Move to trash result for {message_id}: {result}")
            return result
            
        except Exception as e:
            error_msg = f"Error moving email to trash: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg
            }

    @mcp.tool
    def add_star(message_id: str) -> Dict[str, Any]:
        """
        Add a star to an email.
        
        Args:
            message_id: Gmail message ID to star
        
        Returns:
            Dictionary containing success status and message
        """
        try:
            # Initialize Gmail if needed
            connector = initialize_gmail()
            
            # Add star
            result = connector.add_star(message_id)
            
            logger.info(f"Add star result for {message_id}: {result}")
            return result
            
        except Exception as e:
            error_msg = f"Error adding star to email: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg
            }

    @mcp.tool
    def get_available_labels() -> Dict[str, Any]:
        """
        Get list of available labels in the Gmail account.
        
        Returns:
            Dictionary containing success status, message, and list of labels
        """
        try:
            # Initialize Gmail if needed
            connector = initialize_gmail()
            
            # Get labels
            result = connector.get_available_labels()
            
            logger.info(f"Retrieved {len(result.get('labels', []))} labels")
            return result
            
        except Exception as e:
            error_msg = f"Error retrieving labels: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "labels": []
            }

    @mcp.tool
    def modify_labels(message_id: str, add_labels: str = "", remove_labels: str = "") -> Dict[str, Any]:
        """
        Modify labels on an email by adding or removing specific labels.
        
        Args:
            message_id: Gmail message ID to modify
            add_labels: Comma-separated list of label IDs to add (e.g., "STARRED,IMPORTANT")
            remove_labels: Comma-separated list of label IDs to remove (e.g., "UNREAD,INBOX")
        
        Returns:
            Dictionary containing success status and message
        """
        try:
            # Initialize Gmail if needed
            connector = initialize_gmail()
            
            # Parse label lists
            add_list = [label.strip() for label in add_labels.split(",") if label.strip()] if add_labels else None
            remove_list = [label.strip() for label in remove_labels.split(",") if label.strip()] if remove_labels else None
            
            # Modify labels
            result = connector.modify_labels(message_id, add_list, remove_list)
            
            logger.info(f"Modify labels result for {message_id}: {result}")
            return result
            
        except Exception as e:
            error_msg = f"Error modifying email labels: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg
            }

    @mcp.tool
    def bulk_mark_as_read(message_ids: str) -> Dict[str, Any]:
        """
        Mark multiple emails as read by removing the UNREAD label.
        
        Args:
            message_ids: Comma-separated list of Gmail message IDs to mark as read
        
        Returns:
            Dictionary containing success status, summary, and detailed results
        """
        try:
            # Initialize Gmail if needed
            connector = initialize_gmail()
            
            # Parse message IDs
            id_list = [msg_id.strip() for msg_id in message_ids.split(",") if msg_id.strip()]
            
            if not id_list:
                return {"success": False, "message": "No message IDs provided"}
            
            # Bulk mark as read
            result = connector.bulk_mark_as_read(id_list)
            
            logger.info(f"Bulk mark as read result for {len(id_list)} messages: {result['successful_count']}/{result['total_messages']} successful")
            return result
            
        except Exception as e:
            error_msg = f"Error bulk marking emails as read: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg
            }

    @mcp.tool
    def bulk_mark_as_spam(message_ids: str) -> Dict[str, Any]:
        """
        Mark multiple emails as spam by moving them to the spam folder.
        
        Args:
            message_ids: Comma-separated list of Gmail message IDs to mark as spam
        
        Returns:
            Dictionary containing success status, summary, and detailed results
        """
        try:
            # Initialize Gmail if needed
            connector = initialize_gmail()
            
            # Parse message IDs
            id_list = [msg_id.strip() for msg_id in message_ids.split(",") if msg_id.strip()]
            
            if not id_list:
                return {"success": False, "message": "No message IDs provided"}
            
            # Bulk mark as spam
            result = connector.bulk_mark_as_spam(id_list)
            
            logger.info(f"Bulk mark as spam result for {len(id_list)} messages: {result['successful_count']}/{result['total_messages']} successful")
            return result
            
        except Exception as e:
            error_msg = f"Error bulk marking emails as spam: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg
            }

    @mcp.tool
    def bulk_move_to_trash(message_ids: str) -> Dict[str, Any]:
        """
        Move multiple emails to trash.
        
        Args:
            message_ids: Comma-separated list of Gmail message IDs to move to trash
        
        Returns:
            Dictionary containing success status, summary, and detailed results
        """
        try:
            # Initialize Gmail if needed
            connector = initialize_gmail()
            
            # Parse message IDs
            id_list = [msg_id.strip() for msg_id in message_ids.split(",") if msg_id.strip()]
            
            if not id_list:
                return {"success": False, "message": "No message IDs provided"}
            
            # Bulk move to trash
            result = connector.bulk_move_to_trash(id_list)
            
            logger.info(f"Bulk move to trash result for {len(id_list)} messages: {result['successful_count']}/{result['total_messages']} successful")
            return result
            
        except Exception as e:
            error_msg = f"Error bulk moving emails to trash: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg
            }

    @mcp.tool
    def bulk_add_star(message_ids: str) -> Dict[str, Any]:
        """
        Add star to multiple emails.
        
        Args:
            message_ids: Comma-separated list of Gmail message IDs to star
        
        Returns:
            Dictionary containing success status, summary, and detailed results
        """
        try:
            # Initialize Gmail if needed
            connector = initialize_gmail()
            
            # Parse message IDs
            id_list = [msg_id.strip() for msg_id in message_ids.split(",") if msg_id.strip()]
            
            if not id_list:
                return {"success": False, "message": "No message IDs provided"}
            
            # Bulk add star
            result = connector.bulk_add_star(id_list)
            
            logger.info(f"Bulk add star result for {len(id_list)} messages: {result['successful_count']}/{result['total_messages']} successful")
            return result
            
        except Exception as e:
            error_msg = f"Error bulk adding stars to emails: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg
            }

    @mcp.tool
    def bulk_modify_labels(message_ids: str, add_labels: str = "", remove_labels: str = "") -> Dict[str, Any]:
        """
        Modify labels on multiple emails by adding or removing specific labels.
        
        Args:
            message_ids: Comma-separated list of Gmail message IDs to modify
            add_labels: Comma-separated list of label IDs to add (e.g., "STARRED,IMPORTANT")
            remove_labels: Comma-separated list of label IDs to remove (e.g., "UNREAD,INBOX")
        
        Returns:
            Dictionary containing success status, summary, and detailed results
        """
        try:
            # Initialize Gmail if needed
            connector = initialize_gmail()
            
            # Parse message IDs
            id_list = [msg_id.strip() for msg_id in message_ids.split(",") if msg_id.strip()]
            
            if not id_list:
                return {"success": False, "message": "No message IDs provided"}
            
            # Parse label lists
            add_list = [label.strip() for label in add_labels.split(",") if label.strip()] if add_labels else None
            remove_list = [label.strip() for label in remove_labels.split(",") if label.strip()] if remove_labels else None
            
            # Bulk modify labels
            result = connector.bulk_modify_labels(id_list, add_list, remove_list)
            
            logger.info(f"Bulk modify labels result for {len(id_list)} messages: {result['successful_count']}/{result['total_messages']} successful")
            return result
            
        except Exception as e:
            error_msg = f"Error bulk modifying email labels: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg
            }
    
    return mcp