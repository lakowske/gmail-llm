"""
Gmail message labeling functionality.
Handles adding/removing labels from Gmail messages.
"""

import logging
from typing import Optional, List, Dict, Any

from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


class MessageLabeler:
    """Handles labeling Gmail messages."""
    
    def __init__(self, gmail_service):
        """
        Initialize message labeler.
        
        Args:
            gmail_service: Authenticated Gmail API service client
        """
        self.service = gmail_service
        logger.info("Initializing MessageLabeler")
    
    def modify_labels(self, message_id: str, add_labels: List[str] = None, 
                     remove_labels: List[str] = None) -> Dict[str, Any]:
        """
        Modify labels on a Gmail message.
        
        Args:
            message_id: Gmail message ID
            add_labels: List of label IDs to add (e.g., ['SPAM', 'STARRED'])
            remove_labels: List of label IDs to remove (e.g., ['UNREAD', 'INBOX'])
            
        Returns:
            Dictionary with success status and message
        """
        if not self.service:
            logger.error("Gmail service not available")
            return {"success": False, "message": "Gmail service not available"}
        
        if not add_labels and not remove_labels:
            return {"success": False, "message": "No labels specified to add or remove"}
        
        try:
            # Prepare the modify request
            body = {}
            if add_labels:
                body['addLabelIds'] = add_labels
            if remove_labels:
                body['removeLabelIds'] = remove_labels
            
            logger.info(f"Modifying labels for message {message_id}: add={add_labels}, remove={remove_labels}")
            
            # Execute the modify request
            result = self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body=body
            ).execute()
            
            logger.info(f"Successfully modified labels for message {message_id}")
            return {
                "success": True,
                "message": f"Labels modified successfully for message {message_id}",
                "message_id": message_id,
                "current_labels": result.get('labelIds', [])
            }
            
        except HttpError as error:
            error_msg = f"Gmail API error modifying labels: {error}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error modifying labels: {type(e).__name__}: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}
    
    def mark_as_read(self, message_id: str) -> Dict[str, Any]:
        """
        Mark a message as read by removing the UNREAD label.
        
        Args:
            message_id: Gmail message ID
            
        Returns:
            Dictionary with success status and message
        """
        return self.modify_labels(message_id, remove_labels=['UNREAD'])
    
    def mark_as_unread(self, message_id: str) -> Dict[str, Any]:
        """
        Mark a message as unread by adding the UNREAD label.
        
        Args:
            message_id: Gmail message ID
            
        Returns:
            Dictionary with success status and message
        """
        return self.modify_labels(message_id, add_labels=['UNREAD'])
    
    def mark_as_spam(self, message_id: str) -> Dict[str, Any]:
        """
        Mark a message as spam by adding SPAM label and removing INBOX.
        
        Args:
            message_id: Gmail message ID
            
        Returns:
            Dictionary with success status and message
        """
        return self.modify_labels(message_id, add_labels=['SPAM'], remove_labels=['INBOX'])
    
    def move_to_trash(self, message_id: str) -> Dict[str, Any]:
        """
        Move a message to trash by adding TRASH label.
        
        Args:
            message_id: Gmail message ID
            
        Returns:
            Dictionary with success status and message
        """
        return self.modify_labels(message_id, add_labels=['TRASH'])
    
    def add_star(self, message_id: str) -> Dict[str, Any]:
        """
        Add star to a message by adding STARRED label.
        
        Args:
            message_id: Gmail message ID
            
        Returns:
            Dictionary with success status and message
        """
        return self.modify_labels(message_id, add_labels=['STARRED'])
    
    def remove_star(self, message_id: str) -> Dict[str, Any]:
        """
        Remove star from a message by removing STARRED label.
        
        Args:
            message_id: Gmail message ID
            
        Returns:
            Dictionary with success status and message
        """
        return self.modify_labels(message_id, remove_labels=['STARRED'])
    
    def get_available_labels(self) -> Dict[str, Any]:
        """
        Get list of available labels in the Gmail account.
        
        Returns:
            Dictionary with success status and list of labels
        """
        if not self.service:
            logger.error("Gmail service not available")
            return {"success": False, "message": "Gmail service not available", "labels": []}
        
        try:
            logger.info("Retrieving available labels")
            
            result = self.service.users().labels().list(userId='me').execute()
            labels = result.get('labels', [])
            
            # Format labels for easier use
            formatted_labels = []
            for label in labels:
                formatted_labels.append({
                    "id": label['id'],
                    "name": label['name'],
                    "type": label['type'],
                    "messages_total": label.get('messagesTotal', 0),
                    "messages_unread": label.get('messagesUnread', 0)
                })
            
            logger.info(f"Retrieved {len(formatted_labels)} labels")
            return {
                "success": True,
                "message": f"Retrieved {len(formatted_labels)} labels",
                "labels": formatted_labels
            }
            
        except HttpError as error:
            error_msg = f"Gmail API error retrieving labels: {error}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg, "labels": []}
        except Exception as e:
            error_msg = f"Unexpected error retrieving labels: {type(e).__name__}: {e}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg, "labels": []}
    
    def bulk_modify_labels(self, message_ids: List[str], add_labels: List[str] = None,
                          remove_labels: List[str] = None) -> Dict[str, Any]:
        """
        Modify labels on multiple Gmail messages in bulk.
        
        Args:
            message_ids: List of Gmail message IDs
            add_labels: List of label IDs to add to all messages
            remove_labels: List of label IDs to remove from all messages
            
        Returns:
            Dictionary with success status, message, and results for each message
        """
        if not self.service:
            logger.error("Gmail service not available")
            return {"success": False, "message": "Gmail service not available", "results": []}
        
        if not message_ids:
            return {"success": False, "message": "No message IDs provided", "results": []}
        
        if not add_labels and not remove_labels:
            return {"success": False, "message": "No labels specified to add or remove", "results": []}
        
        logger.info(f"Bulk modifying labels for {len(message_ids)} messages: add={add_labels}, remove={remove_labels}")
        
        results = []
        success_count = 0
        
        for message_id in message_ids:
            try:
                # Prepare the modify request
                body = {}
                if add_labels:
                    body['addLabelIds'] = add_labels
                if remove_labels:
                    body['removeLabelIds'] = remove_labels
                
                # Execute the modify request
                result = self.service.users().messages().modify(
                    userId='me',
                    id=message_id,
                    body=body
                ).execute()
                
                results.append({
                    "message_id": message_id,
                    "success": True,
                    "current_labels": result.get('labelIds', [])
                })
                success_count += 1
                logger.debug(f"Successfully modified labels for message {message_id}")
                
            except HttpError as error:
                error_msg = f"Gmail API error for message {message_id}: {error}"
                logger.error(error_msg)
                results.append({
                    "message_id": message_id,
                    "success": False,
                    "error": str(error)
                })
            except Exception as e:
                error_msg = f"Unexpected error for message {message_id}: {type(e).__name__}: {e}"
                logger.error(error_msg)
                results.append({
                    "message_id": message_id,
                    "success": False,
                    "error": error_msg
                })
        
        logger.info(f"Bulk operation completed: {success_count}/{len(message_ids)} successful")
        
        return {
            "success": success_count > 0,
            "message": f"Bulk operation completed: {success_count}/{len(message_ids)} successful",
            "total_messages": len(message_ids),
            "successful_count": success_count,
            "failed_count": len(message_ids) - success_count,
            "results": results
        }
    
    def bulk_mark_as_read(self, message_ids: List[str]) -> Dict[str, Any]:
        """
        Mark multiple messages as read by removing the UNREAD label.
        
        Args:
            message_ids: List of Gmail message IDs
            
        Returns:
            Dictionary with success status and results for each message
        """
        return self.bulk_modify_labels(message_ids, remove_labels=['UNREAD'])
    
    def bulk_mark_as_spam(self, message_ids: List[str]) -> Dict[str, Any]:
        """
        Mark multiple messages as spam by adding SPAM label and removing INBOX.
        
        Args:
            message_ids: List of Gmail message IDs
            
        Returns:
            Dictionary with success status and results for each message
        """
        return self.bulk_modify_labels(message_ids, add_labels=['SPAM'], remove_labels=['INBOX'])
    
    def bulk_move_to_trash(self, message_ids: List[str]) -> Dict[str, Any]:
        """
        Move multiple messages to trash by adding TRASH label.
        
        Args:
            message_ids: List of Gmail message IDs
            
        Returns:
            Dictionary with success status and results for each message
        """
        return self.bulk_modify_labels(message_ids, add_labels=['TRASH'])
    
    def bulk_add_star(self, message_ids: List[str]) -> Dict[str, Any]:
        """
        Add star to multiple messages by adding STARRED label.
        
        Args:
            message_ids: List of Gmail message IDs
            
        Returns:
            Dictionary with success status and results for each message
        """
        return self.bulk_modify_labels(message_ids, add_labels=['STARRED'])