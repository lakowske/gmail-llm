"""
Command line interface module for Gmail connector.
Handles argument parsing and command execution.
"""

from .argument_parser import ArgumentParser
from .command_handler import CommandHandler

__all__ = ["ArgumentParser", "CommandHandler"]