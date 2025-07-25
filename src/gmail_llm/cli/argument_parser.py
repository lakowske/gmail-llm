"""
Command line argument parsing for Gmail connector.
Handles all CLI argument parsing and validation.
"""

import argparse
import logging

logger = logging.getLogger(__name__)


class ArgumentParser:
    """Handles command line argument parsing for Gmail connector."""
    
    def __init__(self):
        """Initialize argument parser."""
        self.parser = argparse.ArgumentParser(
            description='Gmail connector for reading and sending emails'
        )
        self._setup_arguments()
        logger.info("Initialized ArgumentParser")
    
    def _setup_arguments(self):
        """Set up command line arguments."""
        # Global arguments
        self.parser.add_argument(
            '--encrypted', 
            action='store_true', 
            help='Use encrypted credentials'
        )
        
        # Subcommands
        subparsers = self.parser.add_subparsers(dest='command', help='Available commands')
        
        # Read command
        read_parser = subparsers.add_parser('read', help='Read Gmail messages')
        read_parser.add_argument(
            '--max-results', 
            type=int, 
            default=5, 
            help='Maximum number of messages to retrieve'
        )
        read_parser.add_argument(
            '--query', 
            default='', 
            help='Gmail search query (e.g., "is:unread")'
        )
        
        # Send command
        send_parser = subparsers.add_parser('send', help='Send an email')
        send_parser.add_argument(
            '--to', 
            required=True, 
            help='Recipient email address'
        )
        send_parser.add_argument(
            '--subject', 
            required=True, 
            help='Email subject'
        )
        send_parser.add_argument(
            '--message', 
            required=True, 
            help='Email message content'
        )
        send_parser.add_argument(
            '--html', 
            help='Optional HTML content for rich emails'
        )
    
    def parse_args(self, args=None):
        """
        Parse command line arguments.
        
        Args:
            args: List of arguments to parse (defaults to sys.argv)
            
        Returns:
            Parsed arguments namespace
        """
        parsed_args = self.parser.parse_args(args)
        
        # Default to read command if none specified
        if parsed_args.command is None:
            parsed_args.command = 'read'
            parsed_args.max_results = 5
            parsed_args.query = ''
            
        logger.info(f"Parsed arguments: command={parsed_args.command}")
        return parsed_args
    
    def print_help(self):
        """Print help message."""
        self.parser.print_help()