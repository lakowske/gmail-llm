"""
Main entry point for Gmail connector application.
Handles CLI parsing, authentication, and command execution.
"""

import logging
import sys

from .core.gmail_connector import GmailConnector
from .cli.argument_parser import ArgumentParser
from .cli.command_handler import CommandHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for Gmail connector."""
    try:
        # Parse command line arguments
        arg_parser = ArgumentParser()
        args = arg_parser.parse_args()
        
        logger.info(f"Starting Gmail connector with command: {args.command}")
        
        # Set up credentials path
        credentials_file = 'credentials.encrypted' if args.encrypted else 'credentials.json'
        
        # Initialize Gmail connector
        gmail = GmailConnector(credentials_path=credentials_file, use_encrypted=args.encrypted)
        
        # Authenticate
        if not gmail.authenticate():
            logger.error("Failed to authenticate with Gmail API")
            print("✗ Authentication failed")
            return False
        
        # Handle command
        command_handler = CommandHandler(gmail)
        success = command_handler.handle_command(args)
        
        logger.info(f"Gmail connector {args.command} command completed with success={success}")
        return success
        
    except KeyboardInterrupt:
        logger.info("Gmail connector interrupted by user")
        print("\nOperation cancelled by user")
        return False
    except Exception as e:
        logger.error(f"Unexpected error in main: {type(e).__name__}: {e}")
        print(f"Unexpected error: {e}")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)