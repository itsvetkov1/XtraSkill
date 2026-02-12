"""
Encryption service for document content.

Uses Fernet symmetric encryption for encrypting/decrypting documents at rest.
"""

from cryptography.fernet import Fernet
from app.config import settings


class EncryptionService:
    """Service for encrypting and decrypting document content."""

    def __init__(self):
        """Initialize encryption service with key from settings."""
        key = settings.fernet_key
        if not key:
            raise ValueError("FERNET_KEY must be set in configuration")
        self.fernet = Fernet(key.encode())

    def encrypt_document(self, plaintext: str) -> bytes:
        """
        Encrypt document content.

        Args:
            plaintext: Document content as string

        Returns:
            Encrypted content as bytes
        """
        return self.fernet.encrypt(plaintext.encode('utf-8'))

    def decrypt_document(self, ciphertext: bytes) -> str:
        """
        Decrypt document content.

        Args:
            ciphertext: Encrypted content as bytes

        Returns:
            Decrypted content as string
        """
        return self.fernet.decrypt(ciphertext).decode('utf-8')

    def encrypt_binary(self, data: bytes) -> bytes:
        """
        Encrypt binary file content (for rich documents like PDF, XLSX, DOCX).

        Args:
            data: Raw file bytes

        Returns:
            Encrypted content as bytes
        """
        return self.fernet.encrypt(data)

    def decrypt_binary(self, ciphertext: bytes) -> bytes:
        """
        Decrypt binary file content.

        Args:
            ciphertext: Encrypted content as bytes

        Returns:
            Original raw file bytes
        """
        return self.fernet.decrypt(ciphertext)


# Singleton pattern to avoid initializing at import time
_encryption_service_instance = None


def get_encryption_service() -> EncryptionService:
    """Get or create the singleton encryption service instance."""
    global _encryption_service_instance
    if _encryption_service_instance is None:
        _encryption_service_instance = EncryptionService()
    return _encryption_service_instance
