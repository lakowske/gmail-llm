#!/usr/bin/env python3
"""
Simple CLI utility to verify if your GMAIL_MCP_PASSWORD is correct.
This checks if the password can decrypt the credentials without starting the full service.
"""

import os
import sys
import logging
import getpass
from src.gmail_llm.security.credential_manager import CredentialManager

def verify_password():
    """Verify if the password can decrypt credentials."""
    
    # Set up minimal logging
    logging.basicConfig(level=logging.WARNING)  # Only show warnings/errors
    
    # Get password from environment or prompt user
    password = os.getenv('GMAIL_MCP_PASSWORD')
    
    if not password:
        try:
            password = getpass.getpass("Enter password: ")
        except KeyboardInterrupt:
            print("\n❌ Cancelled by user")
            return False
        
        if not password:
            print("❌ No password provided")
            return False
    
    # Initialize credential manager
    credential_manager = CredentialManager('credentials.encrypted')
    
    # Try to decrypt credentials
    print("🔑 Verifying password...")
    try:
        credentials = credential_manager.decrypt_credentials(password)
        
        if credentials is not None:
            print("✅ Password is correct! Credentials decrypted successfully.")
            
            # Show some basic info about the credentials (without exposing sensitive data)
            client_info = credentials.get('installed', {})
            client_id = client_info.get('client_id', 'Not found')
            if client_id != 'Not found':
                # Only show first 20 chars for security
                masked_client_id = client_id[:20] + "..." if len(client_id) > 20 else client_id
                print(f"📧 Client ID: {masked_client_id}")
            
            return True
        else:
            print("❌ Password is incorrect! Could not decrypt credentials.")
            return False
            
    except Exception as e:
        print(f"❌ Password verification failed: {e}")
        return False

def main():
    """Main function."""
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print("Usage: python verify_password.py")
        print("")
        print("Verifies if a password can successfully decrypt the encrypted credentials file.")
        print("")
        print("The script will:")
        print("  1. Check for GMAIL_MCP_PASSWORD environment variable")
        print("  2. If not set, prompt securely for password (hidden input)")
        print("")
        print("Usage:")
        print("  python verify_password.py  # Will prompt for password")
        print("  GMAIL_MCP_PASSWORD='...' python verify_password.py  # Use env var")
        return
    
    success = verify_password()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()