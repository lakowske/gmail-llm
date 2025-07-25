"""
OAuth authentication manager for Gmail API.
Handles OAuth 2.0 flow, token storage, and refresh logic.
"""

import os
import logging
import pickle
from typing import Optional

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

# Gmail API scopes for reading and sending emails
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send'
]


class OAuthManager:
    """Manages OAuth 2.0 authentication for Gmail API."""
    
    def __init__(self, credentials_path: str, token_path: str = 'token.pickle'):
        """
        Initialize OAuth manager.
        
        Args:
            credentials_path: Path to Google API credentials JSON file
            token_path: Path to store OAuth token pickle file
        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.credentials = None
        logger.info(f"Initializing OAuthManager with credentials_path={credentials_path}, token_path={token_path}")
    
    def authenticate(self) -> bool:
        """
        Perform OAuth 2.0 authentication.
        
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            creds = None
            
            # Load existing token if available
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
                    if not os.path.exists(self.credentials_path):
                        logger.error(f"Credentials file not found at {self.credentials_path}")
                        return False
                    
                    logger.info("Starting OAuth flow for new credentials")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                
                # Save credentials for next run
                logger.info(f"Saving credentials to {self.token_path}")
                with open(self.token_path, 'wb') as token:
                    pickle.dump(creds, token)
            
            self.credentials = creds
            logger.info("OAuth authentication successful")
            return True
            
        except FileNotFoundError as e:
            logger.error(f"Credentials file not found: {e}")
            return False
        except Exception as e:
            logger.error(f"OAuth authentication failed: {type(e).__name__}: {e}")
            return False
    
    def build_service(self, service_name: str = 'gmail', version: str = 'v1'):
        """
        Build Google API service client.
        
        Args:
            service_name: Name of the Google API service
            version: Version of the API
            
        Returns:
            Google API service client or None if failed
        """
        if not self.credentials:
            logger.error("Not authenticated. Call authenticate() first.")
            return None
        
        try:
            service = build(service_name, version, credentials=self.credentials)
            logger.info(f"Built {service_name} {version} service successfully")
            return service
        except Exception as e:
            logger.error(f"Failed to build service: {type(e).__name__}: {e}")
            return None
    
    def is_authenticated(self) -> bool:
        """
        Check if currently authenticated with valid credentials.
        
        Returns:
            True if authenticated, False otherwise
        """
        return self.credentials is not None and self.credentials.valid