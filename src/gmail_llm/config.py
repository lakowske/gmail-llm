"""
Configuration management for Gmail LLM application.
Centralizes all configuration settings with environment variable support.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class GmailConfig:
    """Gmail-specific configuration settings."""
    credentials_path: str = None
    use_encrypted: bool = True
    max_results_limit: int = 50
    
    def __post_init__(self):
        if self.credentials_path is None:
            self.credentials_path = os.getenv('GMAIL_CREDENTIALS_PATH', 'credentials.encrypted')


@dataclass 
class ServerConfig:
    """Server configuration for MCP and HTTP API."""
    mcp_host: str = None
    mcp_port: int = None
    api_host: str = None
    api_port: int = None
    log_level: str = None
    
    def __post_init__(self):
        if self.mcp_host is None:
            self.mcp_host = os.getenv('GMAIL_MCP_HOST', '127.0.0.1')
        if self.mcp_port is None:
            self.mcp_port = int(os.getenv('GMAIL_MCP_PORT', '8001'))
        if self.api_host is None:
            self.api_host = os.getenv('GMAIL_API_HOST', '127.0.0.1')
        if self.api_port is None:
            self.api_port = int(os.getenv('GMAIL_API_PORT', '8000'))
        if self.log_level is None:
            self.log_level = os.getenv('GMAIL_LOG_LEVEL', 'info')


@dataclass
class AppConfig:
    """Main application configuration combining all settings."""
    gmail: GmailConfig = None
    server: ServerConfig = None
    
    def __post_init__(self):
        if self.gmail is None:
            self.gmail = GmailConfig()
        if self.server is None:
            self.server = ServerConfig()


# Global configuration instance
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = AppConfig()
    return _config


def reload_config() -> AppConfig:
    """Reload configuration from environment variables."""
    global _config
    _config = AppConfig()
    return _config