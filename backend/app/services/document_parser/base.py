from abc import ABC, abstractmethod
from typing import Dict, Any

class DocumentParser(ABC):
    """Base parser for all document formats."""

    @abstractmethod
    def parse(self, file_bytes: bytes) -> Dict[str, Any]:
        """
        Extract text and metadata from document.

        Returns:
            {
                "text": str,        # Full extracted text for FTS5 indexing
                "summary": str,     # First 5000 chars for AI context
                "metadata": dict    # Format-specific metadata
            }
        """
        pass

    @abstractmethod
    def validate_security(self, file_bytes: bytes) -> None:
        """
        Validate file against security threats.
        Raises HTTPException(400) for malformed, HTTPException(413) for oversized/zip bombs.
        """
        pass

    @staticmethod
    def create_ai_summary(full_text: str, max_chars: int = 5000) -> str:
        """Create truncated summary for AI context to prevent token explosion."""
        if len(full_text) <= max_chars:
            return full_text
        return full_text[:max_chars] + "\n\n[Document truncated for AI context. Full text indexed for search.]"
