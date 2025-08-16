"""
Gmail connector factory for centralized Gmail connection management.
Implements singleton pattern to ensure single authenticated connection.
"""

import logging
from typing import Optional
from threading import Lock

from ..core.gmail_connector import GmailConnector
from ..config import get_config

logger = logging.getLogger(__name__)


class GmailConnectorFactory:
    """
    Factory for creating and managing Gmail connector instances.
    Implements singleton pattern to reuse authenticated connections.
    """
    
    _instance: Optional['GmailConnectorFactory'] = None
    _lock = Lock()
    _connector: Optional[GmailConnector] = None
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_connector(self, force_recreate: bool = False) -> GmailConnector:
        """
        Get an authenticated Gmail connector instance.
        
        Args:
            force_recreate: If True, force creation of a new connector instance
            
        Returns:
            Authenticated GmailConnector instance
            
        Raises:
            RuntimeError: If Gmail authentication fails
        """
        with self._lock:
            if (self._connector is None or 
                force_recreate or 
                not self._connector.is_authenticated()):
                
                logger.info("Creating new Gmail connector instance")
                config = get_config()
                
                try:
                    self._connector = GmailConnector(
                        credentials_path=config.gmail.credentials_path,
                        use_encrypted=config.gmail.use_encrypted
                    )
                    
                    if not self._connector.authenticate():
                        raise RuntimeError("Gmail authentication failed")
                        
                    logger.info("Gmail connector authenticated successfully")
                    
                except Exception as e:
                    logger.error(f"Failed to create Gmail connector: {e}")
                    self._connector = None
                    raise RuntimeError(f"Gmail connector creation failed: {e}")
            
            return self._connector
    
    def is_authenticated(self) -> bool:
        """Check if the current connector is authenticated."""
        return (self._connector is not None and 
                self._connector.is_authenticated())
    
    def reset(self):
        """Reset the factory, forcing recreation of connector on next access."""
        with self._lock:
            logger.info("Resetting Gmail connector factory")
            self._connector = None


# Global factory instance
_factory: Optional[GmailConnectorFactory] = None


def get_gmail_connector(force_recreate: bool = False) -> GmailConnector:
    """
    Convenience function to get a Gmail connector instance.
    
    Args:
        force_recreate: If True, force creation of a new connector
        
    Returns:
        Authenticated GmailConnector instance
    """
    global _factory
    if _factory is None:
        _factory = GmailConnectorFactory()
    
    return _factory.get_connector(force_recreate=force_recreate)


def reset_gmail_connector():
    """Reset the Gmail connector factory."""
    global _factory
    if _factory is not None:
        _factory.reset()