"""
Authentication module for Gmail API.
Handles OAuth 2.0 authentication with optional encryption.
"""

from .oauth_manager import OAuthManager
from .encrypted_oauth_manager import EncryptedOAuthManager

__all__ = ["OAuthManager", "EncryptedOAuthManager"]