"""
Gmail message reading functionality.
Handles retrieving and parsing Gmail messages.
"""

import logging
from typing import Optional, List, Dict, Any

from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


class MessageReader:
    """Handles reading Gmail messages."""
    
    def __init__(self, gmail_service):
        """
        Initialize message reader.
        
        Args:
            gmail_service: Authenticated Gmail API service client
        """
        self.service = gmail_service
        logger.info("Initializing MessageReader")
    
    def get_messages(self, query: str = '', max_results: int = 10) -> Optional[List[Dict[str, Any]]]:
        """
        Retrieve messages from Gmail inbox.
        
        Args:
            query: Gmail search query (e.g., 'is:unread', 'from:example@gmail.com')
            max_results: Maximum number of messages to retrieve
            
        Returns:
            List of message dictionaries or None if error
        """
        if not self.service:
            logger.error("Gmail service not available")
            return None
        
        try:
            logger.info(f"Retrieving messages with query='{query}', max_results={max_results}")
            
            # Get message list
            result = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = result.get('messages', [])
            logger.info(f"Found {len(messages)} messages")
            
            if not messages:
                logger.info("No messages found")
                return []
            
            # Get full message details
            detailed_messages = []
            for message in messages:
                try:
                    msg = self.service.users().messages().get(
                        userId='me',
                        id=message['id']
                    ).execute()
                    detailed_messages.append(msg)
                    logger.debug(f"Retrieved message id={message['id']}")
                except HttpError as e:
                    logger.error(f"Failed to retrieve message {message['id']}: {e}")
                    continue
            
            logger.info(f"Successfully retrieved {len(detailed_messages)} detailed messages")
            return detailed_messages
            
        except HttpError as error:
            logger.error(f"Gmail API error: {error}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error retrieving messages: {type(e).__name__}: {e}")
            return None
    
    def extract_message_info(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract key information from a Gmail message.
        
        Args:
            message: Gmail message dictionary
            
        Returns:
            Dictionary with extracted message information
        """
        try:
            headers = message['payload'].get('headers', [])
            header_dict = {h['name']: h['value'] for h in headers}
            
            info = {
                'id': message['id'],
                'thread_id': message['threadId'],
                'from': header_dict.get('From', 'Unknown'),
                'to': header_dict.get('To', 'Unknown'),
                'subject': header_dict.get('Subject', 'No Subject'),
                'date': header_dict.get('Date', 'Unknown'),
                'snippet': message.get('snippet', ''),
                'label_ids': message.get('labelIds', [])
            }
            
            logger.debug(f"Extracted info for message {info['id']}: subject='{info['subject']}'")
            return info
            
        except KeyError as e:
            logger.error(f"Missing key in message structure: {e}")
            return {'error': f'Missing key: {e}'}
        except Exception as e:
            logger.error(f"Error extracting message info: {type(e).__name__}: {e}")
            return {'error': str(e)}