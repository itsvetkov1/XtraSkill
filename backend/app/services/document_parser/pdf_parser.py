from .base import DocumentParser

class PdfParser(DocumentParser):
    """PDF parser - will be implemented in Task 2."""

    def parse(self, file_bytes: bytes):
        raise NotImplementedError("PdfParser.parse() - Task 2")

    def validate_security(self, file_bytes: bytes):
        raise NotImplementedError("PdfParser.validate_security() - Task 2")
