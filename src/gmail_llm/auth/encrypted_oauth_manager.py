"""
Encrypted OAuth authentication manager for Gmail API.
Extends OAuthManager with encryption support for credentials and tokens.
"""

import os
import logging
import pickle
import getpass
from typing import Optional

from .oauth_manager import OAuthManager, SCOPES
from ..security.credential_manager import CredentialManager

logger = logging.getLogger(__name__)


class EncryptedOAuthManager(OAuthManager):
    """OAuth manager with encrypted credential and token storage."""
    
    def __init__(self, encrypted_credentials_path: str):
        """
        Initialize encrypted OAuth manager.
        
        Args:
            encrypted_credentials_path: Path to encrypted credentials file
        """
        # Don't call parent __init__ since we handle paths differently
        self.encrypted_credentials_path = encrypted_credentials_path
        self.credential_manager = CredentialManager(encrypted_credentials_path)
        self.credentials = None
        self.password = None  # Cache password for session
        self.temp_credentials_file = None
        
        logger.info(f"Initializing EncryptedOAuthManager with encrypted_credentials_path={encrypted_credentials_path}")
    
    def authenticate(self) -> bool:
        """
        Perform OAuth 2.0 authentication with encrypted credentials.
        
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            creds = None
            
            # Get password from environment or prompt
            if self.password is None:
                env_password = os.getenv('GMAIL_MCP_PASSWORD')
                if env_password:
                    logger.info("Using password from environment variable")
                    self.password = env_password
                else:
                    self.password = getpass.getpass("Enter password: ")
            
            # Try to load encrypted token
            token_data = self.credential_manager.decrypt_token(self.password)
            if token_data:
                logger.info("Loading existing encrypted token")
                creds = pickle.loads(token_data)
            else:
                logger.info("No encrypted token found or failed to decrypt")
            
            # If no valid credentials, get new ones
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    logger.info("Refreshing expired credentials")
                    from google.auth.transport.requests import Request
                    creds.refresh(Request())
                else:
                    # Decrypt credentials for OAuth flow
                    logger.info("Using encrypted credentials for OAuth flow")
                    self.temp_credentials_file = self.credential_manager.create_temp_credentials_file(self.password)
                    if not self.temp_credentials_file:
                        logger.error("Failed to decrypt credentials")
                        return False
                    
                    logger.info("Starting OAuth flow with decrypted credentials")
                    from google_auth_oauthlib.flow import InstalledAppFlow
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.temp_credentials_file, SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                
                # Save encrypted token
                logger.info("Saving encrypted token")
                token_data = pickle.dumps(creds)
                self.credential_manager.encrypt_token(token_data, self.password)
            
            self.credentials = creds
            
            # Clean up temporary credentials file if used
            if self.temp_credentials_file:
                self.credential_manager.cleanup_temp_file(self.temp_credentials_file)
                self.temp_credentials_file = None
            
            logger.info("Encrypted OAuth authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"Encrypted OAuth authentication failed: {type(e).__name__}: {e}")
            # Clean up temporary file on error
            if self.temp_credentials_file:
                self.credential_manager.cleanup_temp_file(self.temp_credentials_file)
                self.temp_credentials_file = None
            return False