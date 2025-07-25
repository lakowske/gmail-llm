"""
Gmail message sending functionality.
Handles composing and sending Gmail messages.
"""

import logging
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


class MessageSender:
    """Handles sending Gmail messages."""
    
    def __init__(self, gmail_service):
        """
        Initialize message sender.
        
        Args:
            gmail_service: Authenticated Gmail API service client
        """
        self.service = gmail_service
        logger.info("Initializing MessageSender")
    
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
        if not self.service:
            logger.error("Gmail service not available")
            return False
        
        try:
            logger.info(f"Preparing to send email to={to}, subject='{subject}'")
            
            # Create message
            if html_content:
                # Multipart message with both text and HTML
                msg = MIMEMultipart('alternative')
                text_part = MIMEText(message_text, 'plain')
                html_part = MIMEText(html_content, 'html')
                msg.attach(text_part)
                msg.attach(html_part)
            else:
                # Simple text message
                msg = MIMEText(message_text)
            
            msg['To'] = to
            msg['Subject'] = subject
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            
            # Send message
            logger.info(f"Sending email via Gmail API to {to}")
            result = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            message_id = result.get('id')
            logger.info(f"Email sent successfully. Message ID: {message_id}")
            
            return True
            
        except HttpError as error:
            logger.error(f"Gmail API error sending email: {error}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending email: {type(e).__name__}: {e}")
            return False