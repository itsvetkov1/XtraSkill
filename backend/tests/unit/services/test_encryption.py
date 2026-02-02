"""Unit tests for encryption service."""

import pytest
from app.services.encryption import EncryptionService, get_encryption_service


class TestEncryptionService:
    """Tests for EncryptionService class."""

    def test_encrypt_decrypt_roundtrip(self):
        """Encrypted content can be decrypted back to original."""
        service = EncryptionService()
        original = "Hello, World! This is a test document."

        encrypted = service.encrypt_document(original)
        decrypted = service.decrypt_document(encrypted)

        assert decrypted == original

    def test_encrypt_returns_bytes(self):
        """Encryption returns bytes."""
        service = EncryptionService()
        result = service.encrypt_document("test")

        assert isinstance(result, bytes)

    def test_decrypt_returns_string(self):
        """Decryption returns string."""
        service = EncryptionService()
        encrypted = service.encrypt_document("test")
        decrypted = service.decrypt_document(encrypted)

        assert isinstance(decrypted, str)

    def test_handles_unicode_content(self):
        """Handles Unicode characters correctly."""
        service = EncryptionService()
        original = "Hello \u4e16\u754c \U0001f600"  # Chinese + emoji

        encrypted = service.encrypt_document(original)
        decrypted = service.decrypt_document(encrypted)

        assert decrypted == original

    def test_handles_empty_content(self):
        """Handles empty string."""
        service = EncryptionService()

        encrypted = service.encrypt_document("")
        decrypted = service.decrypt_document(encrypted)

        assert decrypted == ""

    def test_handles_large_content(self):
        """Handles large documents."""
        service = EncryptionService()
        original = "x" * 100_000  # 100KB

        encrypted = service.encrypt_document(original)
        decrypted = service.decrypt_document(encrypted)

        assert decrypted == original

    def test_different_encryptions_produce_different_ciphertext(self):
        """Same plaintext produces different ciphertext each time."""
        service = EncryptionService()
        plaintext = "test content"

        encrypted1 = service.encrypt_document(plaintext)
        encrypted2 = service.encrypt_document(plaintext)

        # Fernet uses random IV, so ciphertexts differ
        assert encrypted1 != encrypted2

    def test_invalid_ciphertext_raises_error(self):
        """Invalid ciphertext raises exception."""
        service = EncryptionService()

        with pytest.raises(Exception):  # InvalidToken from cryptography
            service.decrypt_document(b"not-valid-ciphertext")


class TestGetEncryptionService:
    """Tests for singleton get_encryption_service function."""

    def test_returns_encryption_service(self):
        """Returns an EncryptionService instance."""
        service = get_encryption_service()
        assert isinstance(service, EncryptionService)

    def test_returns_same_instance(self):
        """Returns the same singleton instance."""
        service1 = get_encryption_service()
        service2 = get_encryption_service()
        assert service1 is service2
