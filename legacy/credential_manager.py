#!/usr/bin/env python3
"""
Secure credential manager for encrypting and decrypting Gmail API credentials.
Uses Fernet encryption with password-based key derivation.
"""

import os
import json
import logging
import getpass
from typing import Optional, Dict, Any

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

logger = logging.getLogger(__name__)


class CredentialManager:
    """Manages encrypted storage and retrieval of Google API credentials."""
    
    def __init__(self, encrypted_file: str = 'credentials.encrypted'):
        """
        Initialize credential manager.
        
        Args:
            encrypted_file: Path to encrypted credentials file
        """
        self.encrypted_file = encrypted_file
        self.salt_file = encrypted_file + '.salt'
        logger.info(f"Initializing CredentialManager with encrypted_file={encrypted_file}")
    
    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """
        Derive encryption key from password using PBKDF2.
        
        Args:
            password: User password
            salt: Salt bytes for key derivation
            
        Returns:
            Derived encryption key
        """
        logger.debug("Deriving encryption key from password")
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def _get_salt(self) -> bytes:
        """
        Get or create salt for key derivation.
        
        Returns:
            Salt bytes
        """
        if os.path.exists(self.salt_file):
            logger.debug(f"Loading existing salt from {self.salt_file}")
            with open(self.salt_file, 'rb') as f:
                return f.read()
        else:
            logger.info(f"Generating new salt and saving to {self.salt_file}")
            salt = os.urandom(16)
            with open(self.salt_file, 'wb') as f:
                f.write(salt)
            return salt
    
    def encrypt_credentials(self, credentials_path: str, password: Optional[str] = None) -> bool:
        """
        Encrypt credentials.json file with password.
        
        Args:
            credentials_path: Path to credentials.json file
            password: Password for encryption (will prompt if None)
            
        Returns:
            True if encryption successful, False otherwise
        """
        try:
            if not os.path.exists(credentials_path):
                logger.error(f"Credentials file not found: {credentials_path}")
                return False
            
            # Get password
            if password is None:
                password = getpass.getpass("Enter password to encrypt credentials: ")
            
            # Read credentials
            logger.info(f"Reading credentials from {credentials_path}")
            with open(credentials_path, 'r') as f:
                credentials_data = json.load(f)
            
            # Get salt and derive key
            salt = self._get_salt()
            key = self._derive_key(password, salt)
            
            # Encrypt data
            logger.info("Encrypting credentials data")
            fernet = Fernet(key)
            encrypted_data = fernet.encrypt(json.dumps(credentials_data).encode())
            
            # Save encrypted file
            logger.info(f"Saving encrypted credentials to {self.encrypted_file}")
            with open(self.encrypted_file, 'wb') as f:
                f.write(encrypted_data)
            
            logger.info("Credentials encrypted successfully")
            return True
            
        except FileNotFoundError as e:
            logger.error(f"File not found: {e}")
            return False
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in credentials file: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to encrypt credentials: {type(e).__name__}: {e}")
            return False
    
    def decrypt_credentials(self, password: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Decrypt and return credentials data.
        
        Args:
            password: Password for decryption (will prompt if None)
            
        Returns:
            Decrypted credentials dictionary or None if failed
        """
        try:
            if not os.path.exists(self.encrypted_file):
                logger.error(f"Encrypted credentials file not found: {self.encrypted_file}")
                return None
            
            if not os.path.exists(self.salt_file):
                logger.error(f"Salt file not found: {self.salt_file}")
                return None
            
            # Get password
            if password is None:
                password = getpass.getpass("Enter password to decrypt credentials: ")
            
            # Get salt and derive key
            salt = self._get_salt()
            key = self._derive_key(password, salt)
            
            # Read and decrypt data
            logger.info(f"Reading encrypted credentials from {self.encrypted_file}")
            with open(self.encrypted_file, 'rb') as f:
                encrypted_data = f.read()
            
            logger.info("Decrypting credentials data")
            fernet = Fernet(key)
            decrypted_data = fernet.decrypt(encrypted_data)
            
            # Parse JSON
            credentials_data = json.loads(decrypted_data.decode())
            logger.info("Credentials decrypted successfully")
            return credentials_data
            
        except FileNotFoundError as e:
            logger.error(f"File not found: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in decrypted data: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to decrypt credentials: {type(e).__name__}: {e}")
            return None
    
    def create_temp_credentials_file(self, password: Optional[str] = None) -> Optional[str]:
        """
        Create temporary unencrypted credentials file for API use.
        
        Args:
            password: Password for decryption (will prompt if None)
            
        Returns:
            Path to temporary credentials file or None if failed
        """
        try:
            credentials_data = self.decrypt_credentials(password)
            if credentials_data is None:
                return None
            
            temp_file = 'temp_credentials.json'
            logger.info(f"Creating temporary credentials file: {temp_file}")
            
            with open(temp_file, 'w') as f:
                json.dump(credentials_data, f, indent=2)
            
            return temp_file
            
        except Exception as e:
            logger.error(f"Failed to create temporary credentials file: {type(e).__name__}: {e}")
            return None
    
    def cleanup_temp_file(self, temp_file: str) -> None:
        """
        Securely remove temporary credentials file.
        
        Args:
            temp_file: Path to temporary file to remove
        """
        try:
            if os.path.exists(temp_file):
                logger.info(f"Removing temporary credentials file: {temp_file}")
                os.remove(temp_file)
        except Exception as e:
            logger.error(f"Failed to remove temporary file {temp_file}: {e}")
    
    def encrypt_token(self, token_data: bytes, password: Optional[str] = None) -> bool:
        """
        Encrypt OAuth token data.
        
        Args:
            token_data: Pickled token data to encrypt
            password: Password for encryption (will prompt if None)
            
        Returns:
            True if encryption successful, False otherwise
        """
        try:
            # Get password
            if password is None:
                password = getpass.getpass("Enter password to encrypt token: ")
            
            # Get salt and derive key
            salt = self._get_salt()
            key = self._derive_key(password, salt)
            
            # Encrypt data
            logger.info("Encrypting token data")
            fernet = Fernet(key)
            encrypted_data = fernet.encrypt(token_data)
            
            # Save encrypted token
            encrypted_token_path = self.encrypted_file.replace('.encrypted', '_token.encrypted')
            logger.info(f"Saving encrypted token to {encrypted_token_path}")
            with open(encrypted_token_path, 'wb') as f:
                f.write(encrypted_data)
            
            logger.info("Token encrypted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to encrypt token: {type(e).__name__}: {e}")
            return False
    
    def decrypt_token(self, password: Optional[str] = None) -> Optional[bytes]:
        """
        Decrypt OAuth token data.
        
        Args:
            password: Password for decryption (will prompt if None)
            
        Returns:
            Decrypted token data or None if failed
        """
        try:
            encrypted_token_path = self.encrypted_file.replace('.encrypted', '_token.encrypted')
            
            if not os.path.exists(encrypted_token_path):
                logger.info(f"Encrypted token file not found: {encrypted_token_path}")
                return None
            
            if not os.path.exists(self.salt_file):
                logger.error(f"Salt file not found: {self.salt_file}")
                return None
            
            # Get password
            if password is None:
                password = getpass.getpass("Enter password to decrypt token: ")
            
            # Get salt and derive key
            salt = self._get_salt()
            key = self._derive_key(password, salt)
            
            # Read and decrypt data
            logger.info(f"Reading encrypted token from {encrypted_token_path}")
            with open(encrypted_token_path, 'rb') as f:
                encrypted_data = f.read()
            
            logger.info("Decrypting token data")
            fernet = Fernet(key)
            decrypted_data = fernet.decrypt(encrypted_data)
            
            logger.info("Token decrypted successfully")
            return decrypted_data
            
        except FileNotFoundError as e:
            logger.info(f"Encrypted token file not found: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to decrypt token: {type(e).__name__}: {e}")
            return None


def main():
    """Main function to demonstrate credential manager usage."""
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    
    manager = CredentialManager()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python credential_manager.py encrypt <credentials.json>")
        print("  python credential_manager.py decrypt")
        return
    
    command = sys.argv[1]
    
    if command == 'encrypt':
        if len(sys.argv) < 3:
            print("Please provide path to credentials.json file")
            return
        
        credentials_path = sys.argv[2]
        success = manager.encrypt_credentials(credentials_path)
        if success:
            print("Credentials encrypted successfully!")
            print(f"You can now safely delete {credentials_path}")
        else:
            print("Failed to encrypt credentials")
    
    elif command == 'decrypt':
        credentials = manager.decrypt_credentials()
        if credentials:
            print("Credentials decrypted successfully!")
            print("Client ID:", credentials.get('installed', {}).get('client_id', 'Not found'))
        else:
            print("Failed to decrypt credentials")
    
    else:
        print(f"Unknown command: {command}")


if __name__ == '__main__':
    main()