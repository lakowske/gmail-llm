"""
Command handling logic for Gmail connector CLI.
Processes parsed arguments and executes appropriate commands.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class CommandHandler:
    """Handles execution of Gmail connector commands."""
    
    def __init__(self, gmail_connector):
        """
        Initialize command handler.
        
        Args:
            gmail_connector: GmailConnector instance
        """
        self.connector = gmail_connector
        logger.info("Initialized CommandHandler")
    
    def handle_send_command(self, args: Any) -> bool:
        """
        Handle send email command.
        
        Args:
            args: Parsed arguments containing send parameters
            
        Returns:
            True if email sent successfully, False otherwise
        """
        logger.info(f"Handling send command to={args.to}, subject='{args.subject}'")
        
        success = self.connector.send_email(
            to=args.to,
            subject=args.subject,
            message_text=args.message,
            html_content=args.html
        )
        
        if success:
            print(f"✓ Email sent successfully to {args.to}")
            logger.info(f"Send command completed successfully")
        else:
            print(f"✗ Failed to send email to {args.to}")
            logger.error(f"Send command failed")
            
        return success
    
    def handle_read_command(self, args: Any) -> bool:
        """
        Handle read emails command.
        
        Args:
            args: Parsed arguments containing read parameters
            
        Returns:
            True if messages retrieved successfully, False otherwise
        """
        logger.info(f"Handling read command query='{args.query}', max_results={args.max_results}")
        
        # Get messages
        messages = self.connector.get_messages(query=args.query, max_results=args.max_results)
        if messages is None:
            print("✗ Failed to retrieve messages")
            logger.error("Read command failed - could not retrieve messages")
            return False
        
        # Display message information
        print(f"\nFound {len(messages)} messages:")
        print("-" * 80)
        
        for message in messages:
            info = self.connector.extract_message_info(message)
            if 'error' in info:
                print(f"Error processing message: {info['error']}")
                continue
                
            print(f"From: {info['from']}")
            print(f"Subject: {info['subject']}")
            print(f"Date: {info['date']}")
            print(f"Snippet: {info['snippet'][:100]}...")
            print("-" * 80)
        
        logger.info(f"Read command completed successfully - displayed {len(messages)} messages")
        return True
    
    def handle_command(self, args: Any) -> bool:
        """
        Route and handle the appropriate command.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            True if command executed successfully, False otherwise
        """
        logger.info(f"Routing command: {args.command}")
        
        if args.command == 'send':
            return self.handle_send_command(args)
        elif args.command == 'read':
            return self.handle_read_command(args)
        else:
            logger.error(f"Unknown command: {args.command}")
            print(f"Unknown command: {args.command}")
            return False