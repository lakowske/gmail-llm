#!/usr/bin/env python3
"""
Setup script to encrypt Gmail API credentials for secure storage.
"""

import os
import logging
import sys
from credential_manager import CredentialManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main setup function to encrypt credentials."""
    print("Gmail Credentials Encryption Setup")
    print("=" * 40)
    
    # Check if credentials.json exists
    credentials_path = 'credentials.json'
    if not os.path.exists(credentials_path):
        print(f"Error: {credentials_path} not found!")
        print("Please download your OAuth 2.0 credentials from Google Cloud Console")
        print("and save them as 'credentials.json' in this directory.")
        return False
    
    # Initialize credential manager
    manager = CredentialManager('credentials.encrypted')
    
    # Check if encrypted file already exists
    if os.path.exists('credentials.encrypted'):
        overwrite = input("Encrypted credentials already exist. Overwrite? (y/N): ")
        if overwrite.lower() != 'y':
            print("Setup cancelled.")
            return False
    
    # Encrypt credentials
    print(f"Encrypting {credentials_path}...")
    success = manager.encrypt_credentials(credentials_path)
    
    if success:
        print("✓ Credentials encrypted successfully!")
        print("✓ Encrypted file saved as: credentials.encrypted")
        print("✓ Salt file saved as: credentials.encrypted.salt")
        print()
        
        # Ask about removing original file
        remove_original = input("Remove original credentials.json file? (Y/n): ")
        if remove_original.lower() != 'n':
            try:
                os.remove(credentials_path)
                print(f"✓ Removed {credentials_path}")
            except Exception as e:
                logger.error(f"Failed to remove {credentials_path}: {e}")
                print(f"Warning: Could not remove {credentials_path}")
        
        print()
        print("Setup complete! You can now use encrypted credentials:")
        print("  python gmail_connector.py --encrypted")
        print()
        print("IMPORTANT: Keep your password secure!")
        print("IMPORTANT: Back up both .encrypted and .salt files!")
        
        return True
    else:
        print("✗ Failed to encrypt credentials")
        return False


if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nSetup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Setup failed: {type(e).__name__}: {e}")
        print(f"Setup failed: {e}")
        sys.exit(1)