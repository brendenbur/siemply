"""
Simple AES encryption for storing sensitive data at rest
"""
import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def get_encryption_key() -> bytes:
    """Get or create encryption key from environment variable"""
    secret_key = os.getenv("SIEMPLY_SECRET_KEY")
    if not secret_key:
        # Generate a random key if not set (for development only)
        secret_key = Fernet.generate_key().decode()
        print(f"⚠️  WARNING: SIEMPLY_SECRET_KEY not set. Using generated key: {secret_key}")
        print("Set SIEMPLY_SECRET_KEY environment variable for production!")
    
    # Derive key from secret using PBKDF2
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'siemply_salt',  # In production, use a random salt per key
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(secret_key.encode()))
    return key


def encrypt_value(value: str) -> str:
    """Encrypt a string value"""
    if not value:
        return ""
    
    f = Fernet(get_encryption_key())
    encrypted = f.encrypt(value.encode())
    return base64.urlsafe_b64encode(encrypted).decode()


def decrypt_value(encrypted_value: str) -> str:
    """Decrypt a string value"""
    if not encrypted_value:
        return ""
    
    try:
        f = Fernet(get_encryption_key())
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_value.encode())
        decrypted = f.decrypt(encrypted_bytes)
        return decrypted.decode()
    except Exception as e:
        print(f"Decryption error: {e}")
        return ""
