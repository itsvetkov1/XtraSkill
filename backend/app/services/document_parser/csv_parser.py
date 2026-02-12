from .base import DocumentParser

class CsvParser(DocumentParser):
    """CSV parser - will be implemented in Task 2."""

    def parse(self, file_bytes: bytes):
        raise NotImplementedError("CsvParser.parse() - Task 2")

    def validate_security(self, file_bytes: bytes):
        raise NotImplementedError("CsvParser.validate_security() - Task 2")
