"""
Gmail LLM Connector Package.
A modular Gmail API connector with encrypted credential support.
"""

from .core.gmail_connector import GmailConnector
from .auth.oauth_manager import OAuthManager
from .auth.encrypted_oauth_manager import EncryptedOAuthManager
from .email.message_reader import MessageReader
from .email.message_sender import MessageSender
from .security.credential_manager import CredentialManager

__version__ = "1.0.0"
__author__ = "Gmail LLM Connector"

__all__ = [
    "GmailConnector",
    "OAuthManager", 
    "EncryptedOAuthManager",
    "MessageReader",
    "MessageSender",
    "CredentialManager"
]