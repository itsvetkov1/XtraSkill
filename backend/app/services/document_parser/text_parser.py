from .base import DocumentParser

class TextParser(DocumentParser):
    """Text parser - will be implemented in Task 2."""

    def parse(self, file_bytes: bytes):
        raise NotImplementedError("TextParser.parse() - Task 2")

    def validate_security(self, file_bytes: bytes):
        raise NotImplementedError("TextParser.validate_security() - Task 2")
