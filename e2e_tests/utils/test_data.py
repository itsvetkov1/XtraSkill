"""
Test data generators for E2E tests.
"""
import uuid
import random
import string
import os
from datetime import datetime
from typing import Optional
from config.settings import settings


class TestDataGenerator:
    """Generate test data for E2E tests."""

    @staticmethod
    def unique_id() -> str:
        """Generate a unique identifier."""
        return str(uuid.uuid4())[:8]

    @staticmethod
    def timestamp() -> str:
        """Generate a timestamp string."""
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    @staticmethod
    def project_name(prefix: str = "Test Project") -> str:
        """Generate a unique project name."""
        return f"{prefix} {TestDataGenerator.unique_id()}"

    @staticmethod
    def project_description() -> str:
        """Generate a project description."""
        descriptions = [
            "A test project for E2E testing",
            "Automated test project",
            "Project created by Playwright tests",
            "E2E test automation project",
        ]
        return random.choice(descriptions)

    @staticmethod
    def thread_title(prefix: str = "Test Thread") -> str:
        """Generate a unique thread/chat title."""
        return f"{prefix} {TestDataGenerator.unique_id()}"

    @staticmethod
    def chat_message() -> str:
        """Generate a test chat message."""
        messages = [
            "Hello, this is a test message",
            "Can you help me with this task?",
            "What are the requirements for this project?",
            "Please analyze this document",
            "Generate a summary of the key points",
        ]
        return random.choice(messages)

    @staticmethod
    def document_name(extension: str = "txt") -> str:
        """Generate a unique document name."""
        return f"test_doc_{TestDataGenerator.unique_id()}.{extension}"

    @staticmethod
    def random_string(length: int = 10) -> str:
        """Generate a random alphanumeric string."""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    @staticmethod
    def random_text(words: int = 50) -> str:
        """Generate random lorem-ipsum style text."""
        lorem_words = [
            "lorem", "ipsum", "dolor", "sit", "amet", "consectetur",
            "adipiscing", "elit", "sed", "do", "eiusmod", "tempor",
            "incididunt", "ut", "labore", "et", "dolore", "magna",
            "aliqua", "enim", "ad", "minim", "veniam", "quis",
            "nostrud", "exercitation", "ullamco", "laboris", "nisi",
        ]
        return ' '.join(random.choices(lorem_words, k=words))

    @staticmethod
    def email() -> str:
        """Generate a test email address."""
        return f"test_{TestDataGenerator.unique_id()}@example.com"

    @staticmethod
    def create_test_file(
        filename: str = None,
        content: str = None,
        size_kb: int = None
    ) -> str:
        """
        Create a temporary test file.

        Args:
            filename: Optional filename (auto-generated if not provided)
            content: File content (auto-generated if not provided)
            size_kb: Target file size in KB (overrides content)

        Returns:
            Path to the created file
        """
        # Ensure test files directory exists
        os.makedirs(settings.TEST_FILES_DIR, exist_ok=True)

        filename = filename or TestDataGenerator.document_name()
        filepath = os.path.join(settings.TEST_FILES_DIR, filename)

        if size_kb:
            # Generate file of specific size
            content = 'x' * (size_kb * 1024)
        elif not content:
            content = TestDataGenerator.random_text(100)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        return filepath

    @staticmethod
    def create_pdf_test_file(filename: str = None) -> str:
        """
        Create a minimal valid PDF file for testing.

        Returns:
            Path to the created PDF file
        """
        os.makedirs(settings.TEST_FILES_DIR, exist_ok=True)

        filename = filename or f"test_{TestDataGenerator.unique_id()}.pdf"
        filepath = os.path.join(settings.TEST_FILES_DIR, filename)

        # Minimal valid PDF content
        pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
>>
endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
trailer
<<
/Size 4
/Root 1 0 R
>>
startxref
196
%%EOF
"""

        with open(filepath, 'wb') as f:
            f.write(pdf_content)

        return filepath

    @staticmethod
    def cleanup_test_files() -> None:
        """Remove all files from the test files directory."""
        if os.path.exists(settings.TEST_FILES_DIR):
            for filename in os.listdir(settings.TEST_FILES_DIR):
                filepath = os.path.join(settings.TEST_FILES_DIR, filename)
                try:
                    os.remove(filepath)
                except Exception:
                    pass


class TestScenarios:
    """Pre-defined test scenarios and data sets."""

    @staticmethod
    def simple_project() -> dict:
        """Basic project data for simple tests."""
        return {
            "name": TestDataGenerator.project_name("Simple"),
            "description": "A simple test project",
        }

    @staticmethod
    def project_with_threads() -> dict:
        """Project with multiple threads."""
        return {
            "name": TestDataGenerator.project_name("Multi-Thread"),
            "description": "Project with multiple threads",
            "threads": [
                {"title": "Requirements Discussion"},
                {"title": "Technical Analysis"},
                {"title": "Implementation Notes"},
            ]
        }

    @staticmethod
    def chat_conversation() -> list:
        """Sequence of messages for a conversation test."""
        return [
            "Hello, I need help analyzing a document",
            "What format is the document in?",
            "Can you summarize the main points?",
        ]

    @staticmethod
    def document_types() -> list:
        """List of document types to test."""
        return [
            {"extension": "txt", "mime": "text/plain"},
            {"extension": "pdf", "mime": "application/pdf"},
            {"extension": "md", "mime": "text/markdown"},
        ]
