"""
Main Gmail connector class that orchestrates authentication and email operations.
This is the primary interface for Gmail functionality.
"""

import logging
from typing import Optional, List, Dict, Any

from ..auth.oauth_manager import OAuthManager
from ..auth.encrypted_oauth_manager import EncryptedOAuthManager
from ..email.message_reader import MessageReader
from ..email.message_sender import MessageSender
from ..email.message_labeler import MessageLabeler

logger = logging.getLogger(__name__)


class GmailConnector:
    """Main Gmail connector that orchestrates all Gmail operations."""
    
    def __init__(self, credentials_path: str = 'credentials.json', use_encrypted: bool = False):
        """
        Initialize Gmail connector.
        
        Args:
            credentials_path: Path to credentials file (JSON or encrypted)
            use_encrypted: Whether to use encrypted credentials
        """
        self.credentials_path = credentials_path
        self.use_encrypted = use_encrypted
        
        # Initialize authentication manager
        if use_encrypted:
            self.auth_manager = EncryptedOAuthManager(credentials_path)
        else:
            self.auth_manager = OAuthManager(credentials_path)
        
        # Email operation handlers (initialized after authentication)
        self.message_reader = None
        self.message_sender = None
        self.message_labeler = None
        self.gmail_service = None
        
        logger.info(f"Initialized GmailConnector with credentials_path={credentials_path}, use_encrypted={use_encrypted}")
    
    def authenticate(self) -> bool:
        """
        Authenticate with Gmail API.
        
        Returns:
            True if authentication successful, False otherwise
        """
        logger.info("Starting Gmail authentication")
        
        # Perform OAuth authentication
        if not self.auth_manager.authenticate():
            logger.error("OAuth authentication failed")
            return False
        
        # Build Gmail service
        self.gmail_service = self.auth_manager.build_service('gmail', 'v1')
        if not self.gmail_service:
            logger.error("Failed to build Gmail service")
            return False
        
        # Initialize email operation handlers
        self.message_reader = MessageReader(self.gmail_service)
        self.message_sender = MessageSender(self.gmail_service)
        self.message_labeler = MessageLabeler(self.gmail_service)
        
        logger.info("Gmail authentication and initialization completed successfully")
        return True
    
    def is_authenticated(self) -> bool:
        """
        Check if currently authenticated.
        
        Returns:
            True if authenticated, False otherwise
        """
        return (self.auth_manager.is_authenticated() and 
                self.gmail_service is not None and
                self.message_reader is not None and
                self.message_sender is not None and
                self.message_labeler is not None)
    
    def get_messages(self, query: str = '', max_results: int = 10) -> Optional[List[Dict[str, Any]]]:
        """
        Retrieve messages from Gmail inbox.
        
        Args:
            query: Gmail search query (e.g., 'is:unread', 'from:example@gmail.com')
            max_results: Maximum number of messages to retrieve
            
        Returns:
            List of message dictionaries or None if error
        """
        if not self.is_authenticated():
            logger.error("Not authenticated. Call authenticate() first.")
            return None
        
        return self.message_reader.get_messages(query, max_results)
    
    def extract_message_info(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract key information from a Gmail message.
        
        Args:
            message: Gmail message dictionary
            
        Returns:
            Dictionary with extracted message information
        """
        if not self.is_authenticated():
            logger.error("Not authenticated. Call authenticate() first.")
            return {'error': 'Not authenticated'}
        
        return self.message_reader.extract_message_info(message)
    
    def send_email(self, to: str, subject: str, message_text: str, html_content: Optional[str] = None) -> bool:
        """
        Send an email using Gmail API.
        
        Args:
            to: Recipient email address
            subject: Email subject
            message_text: Plain text message content
            html_content: Optional HTML content for rich emails
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.is_authenticated():
            logger.error("Not authenticated. Call authenticate() first.")
            return False
        
        return self.message_sender.send_email(to, subject, message_text, html_content)
    
    def modify_labels(self, message_id: str, add_labels: List[str] = None, 
                     remove_labels: List[str] = None) -> Dict[str, Any]:
        """
        Modify labels on a Gmail message.
        
        Args:
            message_id: Gmail message ID
            add_labels: List of label IDs to add
            remove_labels: List of label IDs to remove
            
        Returns:
            Dictionary with success status and message
        """
        if not self.is_authenticated():
            logger.error("Not authenticated. Call authenticate() first.")
            return {"success": False, "message": "Not authenticated"}
        
        return self.message_labeler.modify_labels(message_id, add_labels, remove_labels)
    
    def mark_as_read(self, message_id: str) -> Dict[str, Any]:
        """Mark a message as read by removing the UNREAD label."""
        if not self.is_authenticated():
            logger.error("Not authenticated. Call authenticate() first.")
            return {"success": False, "message": "Not authenticated"}
        
        return self.message_labeler.mark_as_read(message_id)
    
    def mark_as_unread(self, message_id: str) -> Dict[str, Any]:
        """Mark a message as unread by adding the UNREAD label."""
        if not self.is_authenticated():
            logger.error("Not authenticated. Call authenticate() first.")
            return {"success": False, "message": "Not authenticated"}
        
        return self.message_labeler.mark_as_unread(message_id)
    
    def mark_as_spam(self, message_id: str) -> Dict[str, Any]:
        """Mark a message as spam by moving it to the spam folder."""
        if not self.is_authenticated():
            logger.error("Not authenticated. Call authenticate() first.")
            return {"success": False, "message": "Not authenticated"}
        
        return self.message_labeler.mark_as_spam(message_id)
    
    def move_to_trash(self, message_id: str) -> Dict[str, Any]:
        """Move a message to trash."""
        if not self.is_authenticated():
            logger.error("Not authenticated. Call authenticate() first.")
            return {"success": False, "message": "Not authenticated"}
        
        return self.message_labeler.move_to_trash(message_id)
    
    def add_star(self, message_id: str) -> Dict[str, Any]:
        """Add star to a message."""
        if not self.is_authenticated():
            logger.error("Not authenticated. Call authenticate() first.")
            return {"success": False, "message": "Not authenticated"}
        
        return self.message_labeler.add_star(message_id)
    
    def remove_star(self, message_id: str) -> Dict[str, Any]:
        """Remove star from a message."""
        if not self.is_authenticated():
            logger.error("Not authenticated. Call authenticate() first.")
            return {"success": False, "message": "Not authenticated"}
        
        return self.message_labeler.remove_star(message_id)
    
    def get_available_labels(self) -> Dict[str, Any]:
        """Get list of available labels in the Gmail account."""
        if not self.is_authenticated():
            logger.error("Not authenticated. Call authenticate() first.")
            return {"success": False, "message": "Not authenticated", "labels": []}
        
        return self.message_labeler.get_available_labels()
    
    def bulk_mark_as_read(self, message_ids: List[str]) -> Dict[str, Any]:
        """Mark multiple messages as read by removing the UNREAD label."""
        if not self.is_authenticated():
            logger.error("Not authenticated. Call authenticate() first.")
            return {"success": False, "message": "Not authenticated", "results": []}
        
        return self.message_labeler.bulk_mark_as_read(message_ids)
    
    def bulk_mark_as_spam(self, message_ids: List[str]) -> Dict[str, Any]:
        """Mark multiple messages as spam by moving them to the spam folder."""
        if not self.is_authenticated():
            logger.error("Not authenticated. Call authenticate() first.")
            return {"success": False, "message": "Not authenticated", "results": []}
        
        return self.message_labeler.bulk_mark_as_spam(message_ids)
    
    def bulk_move_to_trash(self, message_ids: List[str]) -> Dict[str, Any]:
        """Move multiple messages to trash."""
        if not self.is_authenticated():
            logger.error("Not authenticated. Call authenticate() first.")
            return {"success": False, "message": "Not authenticated", "results": []}
        
        return self.message_labeler.bulk_move_to_trash(message_ids)
    
    def bulk_add_star(self, message_ids: List[str]) -> Dict[str, Any]:
        """Add star to multiple messages."""
        if not self.is_authenticated():
            logger.error("Not authenticated. Call authenticate() first.")
            return {"success": False, "message": "Not authenticated", "results": []}
        
        return self.message_labeler.bulk_add_star(message_ids)
    
    def bulk_modify_labels(self, message_ids: List[str], add_labels: List[str] = None,
                          remove_labels: List[str] = None) -> Dict[str, Any]:
        """Modify labels on multiple Gmail messages."""
        if not self.is_authenticated():
            logger.error("Not authenticated. Call authenticate() first.")
            return {"success": False, "message": "Not authenticated", "results": []}
        
        return self.message_labeler.bulk_modify_labels(message_ids, add_labels, remove_labels)