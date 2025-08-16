#!/usr/bin/env python3
"""
Gmail API connector script for reading Gmail inbox.
Requires Google API credentials and OAuth 2.0 authentication.
"""

import os
import logging
import pickle
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List, Dict, Any

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from credential_manager import CredentialManager

# Gmail API scopes for reading and sending emails
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send'
]

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
)
logger = logging.getLogger(__name__)


class GmailConnector:
    """Gmail API connector for reading inbox messages."""
    
    def __init__(self, credentials_path: str = 'credentials.json', token_path: str = 'token.pickle', use_encrypted: bool = False):
        """
        Initialize Gmail connector.
        
        Args:
            credentials_path: Path to Google API credentials JSON file or encrypted file
            token_path: Path to store OAuth token pickle file
            use_encrypted: Whether to use encrypted credentials
        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.use_encrypted = use_encrypted
        self.service = None
        self.credential_manager = None
        self.temp_credentials_file = None
        self.password = None  # Cache password for session
        
        if use_encrypted:
            self.credential_manager = CredentialManager(credentials_path)
        
        logger.info(f"Initializing GmailConnector with credentials_path={credentials_path}, token_path={token_path}, use_encrypted={use_encrypted}")
    
    def authenticate(self) -> bool:
        """
        Authenticate with Gmail API using OAuth 2.0.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            creds = None
            
            # Load existing token if available
            if self.use_encrypted:
                # Try to load encrypted token
                if self.password is None:
                    import getpass
                    self.password = getpass.getpass("Enter password: ")
                
                token_data = self.credential_manager.decrypt_token(self.password)
                if token_data:
                    logger.info("Loading existing encrypted token")
                    creds = pickle.loads(token_data)
                else:
                    logger.info("No encrypted token found or failed to decrypt")
            else:
                # Load regular token
                if os.path.exists(self.token_path):
                    logger.info(f"Loading existing token from {self.token_path}")
                    with open(self.token_path, 'rb') as token:
                        creds = pickle.load(token)
            
            # If no valid credentials, get new ones
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    logger.info("Refreshing expired credentials")
                    creds.refresh(Request())
                else:
                    # Handle encrypted vs regular credentials
                    credentials_file = self.credentials_path
                    
                    if self.use_encrypted:
                        logger.info("Using encrypted credentials")
                        self.temp_credentials_file = self.credential_manager.create_temp_credentials_file(self.password)
                        if not self.temp_credentials_file:
                            logger.error("Failed to decrypt credentials")
                            return False
                        credentials_file = self.temp_credentials_file
                    else:
                        if not os.path.exists(self.credentials_path):
                            logger.error(f"Credentials file not found at {self.credentials_path}")
                            return False
                    
                    logger.info("Starting OAuth flow for new credentials")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        credentials_file, SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                
                # Save credentials for next run
                if self.use_encrypted:
                    logger.info("Saving encrypted token")
                    token_data = pickle.dumps(creds)
                    self.credential_manager.encrypt_token(token_data, self.password)
                else:
                    logger.info(f"Saving credentials to {self.token_path}")
                    with open(self.token_path, 'wb') as token:
                        pickle.dump(creds, token)
            
            # Build Gmail service
            self.service = build('gmail', 'v1', credentials=creds)
            logger.info("Gmail API service successfully authenticated and built")
            
            # Clean up temporary credentials file if used
            if self.temp_credentials_file:
                self.credential_manager.cleanup_temp_file(self.temp_credentials_file)
                self.temp_credentials_file = None
            
            return True
            
        except FileNotFoundError as e:
            logger.error(f"Credentials file not found: {e}")
            # Clean up temporary file on error
            if self.temp_credentials_file:
                self.credential_manager.cleanup_temp_file(self.temp_credentials_file)
                self.temp_credentials_file = None
            return False
        except Exception as e:
            logger.error(f"Authentication failed: {type(e).__name__}: {e}")
            # Clean up temporary file on error
            if self.temp_credentials_file:
                self.credential_manager.cleanup_temp_file(self.temp_credentials_file)
                self.temp_credentials_file = None
            return False
    
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
            logger.error("Gmail service not authenticated. Call authenticate() first.")
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
            logger.error("Gmail service not authenticated. Call authenticate() first.")
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


def main():
    """Main function to handle Gmail connector commands."""
    import sys
    import argparse
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Gmail connector for reading and sending emails')
    parser.add_argument('--encrypted', action='store_true', help='Use encrypted credentials')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Read command (default)
    read_parser = subparsers.add_parser('read', help='Read Gmail messages')
    read_parser.add_argument('--max-results', type=int, default=5, help='Maximum number of messages to retrieve')
    read_parser.add_argument('--query', default='', help='Gmail search query (e.g., "is:unread")')
    
    # Send command
    send_parser = subparsers.add_parser('send', help='Send an email')
    send_parser.add_argument('--to', required=True, help='Recipient email address')
    send_parser.add_argument('--subject', required=True, help='Email subject')
    send_parser.add_argument('--message', required=True, help='Email message content')
    send_parser.add_argument('--html', help='Optional HTML content for rich emails')
    
    args = parser.parse_args()
    
    # Default to read if no command specified
    if args.command is None:
        args.command = 'read'
        args.max_results = 5
        args.query = ''
    
    logger.info(f"Starting Gmail connector with command: {args.command}")
    
    # Set up credentials
    credentials_file = 'credentials.encrypted' if args.encrypted else 'credentials.json'
    
    # Initialize connector
    gmail = GmailConnector(credentials_path=credentials_file, use_encrypted=args.encrypted)
    
    # Authenticate
    if not gmail.authenticate():
        logger.error("Failed to authenticate with Gmail API")
        return
    
    # Handle commands
    if args.command == 'send':
        success = gmail.send_email(
            to=args.to,
            subject=args.subject,
            message_text=args.message,
            html_content=args.html
        )
        
        if success:
            print(f"✓ Email sent successfully to {args.to}")
        else:
            print(f"✗ Failed to send email to {args.to}")
            
    elif args.command == 'read':
        # Get messages
        messages = gmail.get_messages(query=args.query, max_results=args.max_results)
        if messages is None:
            logger.error("Failed to retrieve messages")
            return
        
        # Display message information
        print(f"\nFound {len(messages)} messages:")
        print("-" * 80)
        
        for message in messages:
            info = gmail.extract_message_info(message)
            if 'error' in info:
                print(f"Error processing message: {info['error']}")
                continue
                
            print(f"From: {info['from']}")
            print(f"Subject: {info['subject']}")
            print(f"Date: {info['date']}")
            print(f"Snippet: {info['snippet'][:100]}...")
            print("-" * 80)
    
    logger.info(f"Gmail connector {args.command} command completed")


if __name__ == '__main__':
    main()