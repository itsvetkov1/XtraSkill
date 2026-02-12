from typing import Dict, Any
from fastapi import HTTPException

from .base import DocumentParser


class TextParser(DocumentParser):
    """Plain text parser for text/plain and text/markdown files."""

    def parse(self, file_bytes: bytes) -> Dict[str, Any]:
        """
        Extract text from plain text file.

        Returns dict with:
            - text: Full text content
            - summary: First 5000 chars for AI context
            - metadata: Format and encoding
        """
        try:
            # Decode as UTF-8 with error replacement
            text = file_bytes.decode("utf-8", errors="replace")

            metadata = {
                "format": "Text",
                "encoding": "utf-8"
            }

            return {
                "text": text,
                "summary": self.create_ai_summary(text),
                "metadata": metadata
            }

        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to parse text file: {str(e)}"
            )

    def validate_security(self, file_bytes: bytes) -> None:
        """
        Validate text file security.

        Raises HTTPException if UTF-8 decoding fails completely.
        """
        try:
            # Try to decode as UTF-8
            _ = file_bytes.decode("utf-8", errors="replace")
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid text file encoding: {str(e)}"
            )
