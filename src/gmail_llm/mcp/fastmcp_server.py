"""
FastMCP-based Gmail MCP server library.
Provides proper MCP protocol implementation for Gmail operations.
Refactored to eliminate code duplication and use shared components.
"""

import logging
from typing import Dict, Any, List
from fastmcp import FastMCP

from ..shared.decorators import gmail_operation, retry_on_auth_failure, validate_message_ids
from ..shared.utils import (
    validate_max_results, format_email_info, parse_label_list, 
    create_success_response, create_error_response, create_bulk_operation_result,
    validate_email_address, sanitize_email_content
)

logger = logging.getLogger(__name__)


def create_gmail_mcp_server() -> FastMCP:
    """Create and configure a FastMCP server for Gmail operations."""
    
    # Initialize FastMCP server
    mcp = FastMCP("Gmail LLM Connector")

    @mcp.tool
    @gmail_operation("read_emails")
    @retry_on_auth_failure()
    def read_emails(connector, query: str = "", max_results: int = 10) -> Dict[str, Any]:
        """
        Read emails from Gmail inbox with optional search query and result limit.
        
        Args:
            query: Gmail search query (e.g., 'is:unread', 'from:user@example.com', 'subject:important')
            max_results: Maximum number of emails to retrieve (1-50)
        
        Returns:
            Dictionary containing success status, message, emails list, and count
        """
        # Validate max_results
        try:
            max_results = validate_max_results(max_results)
        except ValueError as e:
            return create_error_response(str(e), "read_emails", "ValidationError")
        
        # Read emails
        raw_emails = connector.get_messages(query=query, max_results=max_results)
        
        if not raw_emails:
            return create_success_response(
                "No emails found",
                emails=[],
                count=0
            )
        
        # Extract and format email information
        formatted_emails = []
        for raw_email in raw_emails:
            formatted_email = format_email_info(raw_email, connector)
            formatted_emails.append(formatted_email)
        
        return create_success_response(
            f"Retrieved {len(formatted_emails)} emails",
            emails=formatted_emails,
            count=len(formatted_emails)
        )

    @mcp.tool
    @gmail_operation("send_email")
    @retry_on_auth_failure()
    def send_email(connector, to: str, subject: str, message: str, html_content: str = None) -> Dict[str, Any]:
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
        # Validate email address
        if not validate_email_address(to):
            return create_error_response("Invalid recipient email address", "send_email", "ValidationError")
        
        # Validate inputs
        if not subject.strip():
            return create_error_response("Subject cannot be empty", "send_email", "ValidationError")
        
        if not message.strip():
            return create_error_response("Message content cannot be empty", "send_email", "ValidationError")
        
        # Send email
        result = connector.send_email(
            to=to,
            subject=subject,
            message_text=message,
            html_content=html_content
        )
        
        if result:
            return create_success_response(
                f"Email sent successfully to {to}",
                message_id=None  # GmailConnector doesn't return message_id
            )
        else:
            return create_error_response("Failed to send email", "send_email")

    @mcp.tool
    @gmail_operation("mark_as_read")
    @retry_on_auth_failure()
    def mark_as_read(connector, message_id: str) -> Dict[str, Any]:
        """
        Mark an email as read by removing the UNREAD label.
        
        Args:
            message_id: Gmail message ID to mark as read
        
        Returns:
            Dictionary containing success status and message
        """
        if not message_id.strip():
            return create_error_response("Message ID cannot be empty", "mark_as_read", "ValidationError")
        
        result = connector.mark_as_read(message_id)
        return result  # GmailConnector already returns standardized format

    @mcp.tool
    @gmail_operation("mark_as_spam")
    @retry_on_auth_failure()
    def mark_as_spam(connector, message_id: str) -> Dict[str, Any]:
        """
        Mark an email as spam by moving it to the spam folder.
        
        Args:
            message_id: Gmail message ID to mark as spam
        
        Returns:
            Dictionary containing success status and message
        """
        if not message_id.strip():
            return create_error_response("Message ID cannot be empty", "mark_as_spam", "ValidationError")
        
        result = connector.mark_as_spam(message_id)
        return result

    @mcp.tool
    @gmail_operation("move_to_trash")
    @retry_on_auth_failure()
    def move_to_trash(connector, message_id: str) -> Dict[str, Any]:
        """
        Move an email to trash.
        
        Args:
            message_id: Gmail message ID to move to trash
        
        Returns:
            Dictionary containing success status and message
        """
        if not message_id.strip():
            return create_error_response("Message ID cannot be empty", "move_to_trash", "ValidationError")
        
        result = connector.move_to_trash(message_id)
        return result

    @mcp.tool
    @gmail_operation("add_star")
    @retry_on_auth_failure()
    def add_star(connector, message_id: str) -> Dict[str, Any]:
        """
        Add a star to an email.
        
        Args:
            message_id: Gmail message ID to star
        
        Returns:
            Dictionary containing success status and message
        """
        if not message_id.strip():
            return create_error_response("Message ID cannot be empty", "add_star", "ValidationError")
        
        result = connector.add_star(message_id)
        return result

    @mcp.tool
    @gmail_operation("get_available_labels")
    @retry_on_auth_failure()
    def get_available_labels(connector) -> Dict[str, Any]:
        """
        Get list of available labels in the Gmail account.
        
        Returns:
            Dictionary containing success status, message, and list of labels
        """
        result = connector.get_available_labels()
        return result

    @mcp.tool
    @gmail_operation("modify_labels")
    @retry_on_auth_failure()
    def modify_labels(connector, message_id: str, add_labels: str = "", remove_labels: str = "") -> Dict[str, Any]:
        """
        Modify labels on an email by adding or removing specific labels.
        
        Args:
            message_id: Gmail message ID to modify
            add_labels: Comma-separated list of label IDs to add (e.g., "STARRED,IMPORTANT")
            remove_labels: Comma-separated list of label IDs to remove (e.g., "UNREAD,INBOX")
        
        Returns:
            Dictionary containing success status and message
        """
        if not message_id.strip():
            return create_error_response("Message ID cannot be empty", "modify_labels", "ValidationError")
        
        # Parse label lists
        add_list = parse_label_list(add_labels)
        remove_list = parse_label_list(remove_labels)
        
        if not add_list and not remove_list:
            return create_error_response("Must specify labels to add or remove", "modify_labels", "ValidationError")
        
        result = connector.modify_labels(message_id, add_list, remove_list)
        return result

    @mcp.tool
    @gmail_operation("bulk_mark_as_read")
    @retry_on_auth_failure()
    @validate_message_ids
    def bulk_mark_as_read(connector, message_ids: List[str]) -> Dict[str, Any]:
        """
        Mark multiple emails as read by removing the UNREAD label.
        
        Args:
            message_ids: List of Gmail message IDs to mark as read
        
        Returns:
            Dictionary containing success status, summary, and detailed results
        """
        result = connector.bulk_mark_as_read(message_ids)
        return result

    @mcp.tool
    @gmail_operation("bulk_mark_as_spam")
    @retry_on_auth_failure()
    @validate_message_ids
    def bulk_mark_as_spam(connector, message_ids: List[str]) -> Dict[str, Any]:
        """
        Mark multiple emails as spam by moving them to the spam folder.
        
        Args:
            message_ids: List of Gmail message IDs to mark as spam
        
        Returns:
            Dictionary containing success status, summary, and detailed results
        """
        result = connector.bulk_mark_as_spam(message_ids)
        return result

    @mcp.tool
    @gmail_operation("bulk_move_to_trash")
    @retry_on_auth_failure()
    @validate_message_ids
    def bulk_move_to_trash(connector, message_ids: List[str]) -> Dict[str, Any]:
        """
        Move multiple emails to trash.
        
        Args:
            message_ids: List of Gmail message IDs to move to trash
        
        Returns:
            Dictionary containing success status, summary, and detailed results
        """
        result = connector.bulk_move_to_trash(message_ids)
        return result

    @mcp.tool
    @gmail_operation("bulk_add_star")
    @retry_on_auth_failure()
    @validate_message_ids
    def bulk_add_star(connector, message_ids: List[str]) -> Dict[str, Any]:
        """
        Add star to multiple emails.
        
        Args:
            message_ids: List of Gmail message IDs to star
        
        Returns:
            Dictionary containing success status, summary, and detailed results
        """
        result = connector.bulk_add_star(message_ids)
        return result

    @mcp.tool
    @gmail_operation("bulk_modify_labels")
    @retry_on_auth_failure()
    @validate_message_ids
    def bulk_modify_labels(connector, message_ids: List[str], add_labels: str = "", remove_labels: str = "") -> Dict[str, Any]:
        """
        Modify labels on multiple emails by adding or removing specific labels.
        
        Args:
            message_ids: List of Gmail message IDs to modify
            add_labels: Comma-separated list of label IDs to add (e.g., "STARRED,IMPORTANT")
            remove_labels: Comma-separated list of label IDs to remove (e.g., "UNREAD,INBOX")
        
        Returns:
            Dictionary containing success status, summary, and detailed results
        """
        # Parse label lists
        add_list = parse_label_list(add_labels)
        remove_list = parse_label_list(remove_labels)
        
        if not add_list and not remove_list:
            return create_error_response("Must specify labels to add or remove", "bulk_modify_labels", "ValidationError")
        
        result = connector.bulk_modify_labels(message_ids, add_list, remove_list)
        return result
    
    return mcp