from .base import DocumentParser

class WordParser(DocumentParser):
    """Word parser - will be implemented in Task 2."""

    def parse(self, file_bytes: bytes):
        raise NotImplementedError("WordParser.parse() - Task 2")

    def validate_security(self, file_bytes: bytes):
        raise NotImplementedError("WordParser.validate_security() - Task 2")
