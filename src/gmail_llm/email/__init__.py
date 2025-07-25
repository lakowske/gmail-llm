"""
Email operations module for Gmail API.
Handles reading and sending Gmail messages.
"""

from .message_reader import MessageReader
from .message_sender import MessageSender

__all__ = ["MessageReader", "MessageSender"]