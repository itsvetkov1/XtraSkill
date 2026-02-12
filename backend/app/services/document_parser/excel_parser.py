from .base import DocumentParser

class ExcelParser(DocumentParser):
    """Excel parser - will be implemented in Task 2."""

    def parse(self, file_bytes: bytes):
        raise NotImplementedError("ExcelParser.parse() - Task 2")

    def validate_security(self, file_bytes: bytes):
        raise NotImplementedError("ExcelParser.validate_security() - Task 2")
