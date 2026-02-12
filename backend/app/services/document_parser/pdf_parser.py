from io import BytesIO
from typing import Dict, Any
import pdfplumber
from fastapi import HTTPException

from .base import DocumentParser


class PdfParser(DocumentParser):
    """PDF parser with page-level text extraction."""

    def parse(self, file_bytes: bytes) -> Dict[str, Any]:
        """
        Extract text from PDF file with page markers.

        Returns dict with:
            - text: Full PDF text with page markers
            - summary: First 5000 chars for AI context
            - metadata: Page count
        """
        try:
            with pdfplumber.open(BytesIO(file_bytes)) as pdf:
                pages_text = []

                for page in pdf.pages:
                    # Extract text from page (may be empty)
                    page_text = page.extract_text() or ""

                    # Add page marker
                    page_with_marker = f"[Page {page.page_number}]\n{page_text}"
                    pages_text.append(page_with_marker)

                # Join pages with double newline
                full_text = "\n\n".join(pages_text)

                metadata = {
                    "page_count": len(pdf.pages),
                    "format": "PDF"
                }

                return {
                    "text": full_text,
                    "summary": self.create_ai_summary(full_text),
                    "metadata": metadata
                }

        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to parse PDF file: {str(e)}"
            )

    def validate_security(self, file_bytes: bytes) -> None:
        """
        Validate PDF file security.

        Raises HTTPException for malformed PDFs.
        """
        try:
            with pdfplumber.open(BytesIO(file_bytes)) as pdf:
                # Try to access pages to verify PDF is valid
                _ = len(pdf.pages)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Malformed PDF file: {str(e)}"
            )
