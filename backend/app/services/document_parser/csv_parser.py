import csv
import io
from typing import Dict, Any
import chardet
from fastapi import HTTPException

from .base import DocumentParser


class CsvParser(DocumentParser):
    """CSV parser with automatic encoding detection."""

    def parse(self, file_bytes: bytes) -> Dict[str, Any]:
        """
        Extract text from CSV file with encoding detection.

        Returns dict with:
            - text: Full CSV content
            - summary: First 5000 chars for AI context
            - metadata: Row count, encoding, column headers
        """
        try:
            # Detect encoding using first 10KB
            detected = chardet.detect(file_bytes[:10240])
            encoding = detected.get("encoding") or "utf-8"
            confidence = detected.get("confidence", 0.0)

            # Decode with detected encoding
            try:
                text = file_bytes.decode(encoding, errors="replace")
            except (UnicodeDecodeError, LookupError):
                # Fallback to UTF-8 if detected encoding fails
                text = file_bytes.decode("utf-8", errors="replace")
                encoding = "utf-8"
                confidence = 0.0

            # Parse CSV
            csv_reader = csv.reader(io.StringIO(text))
            rows_data = []
            column_headers = []

            for row_idx, row in enumerate(csv_reader, start=1):
                # First row is typically column headers
                if row_idx == 1:
                    column_headers = row

                # Join cells with tab separator
                row_text = "\t".join(row)
                rows_data.append(row_text)

            # Join rows with newlines
            full_text = "\n".join(rows_data)

            metadata = {
                "row_count": len(rows_data),
                "encoding": encoding,
                "encoding_confidence": confidence,
                "column_headers": column_headers,
                "format": "CSV"
            }

            return {
                "text": full_text,
                "summary": self.create_ai_summary(full_text),
                "metadata": metadata
            }

        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to parse CSV file: {str(e)}"
            )

    def validate_security(self, file_bytes: bytes) -> None:
        """
        Validate CSV file security.

        Minimal validation - size already checked by file_validator.
        """
        # CSV files are plain text, no special security concerns
        # Encoding detection in parse() is safe
        pass
