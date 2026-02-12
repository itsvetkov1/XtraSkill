import sys
import defusedxml.ElementTree
# Monkey-patch xml.etree.ElementTree BEFORE importing openpyxl or python-docx
sys.modules['xml.etree.ElementTree'] = defusedxml.ElementTree

from .base import DocumentParser
from .excel_parser import ExcelParser
from .csv_parser import CsvParser
from .pdf_parser import PdfParser
from .word_parser import WordParser
from .text_parser import TextParser

class ParserFactory:
    """Route content types to appropriate parser implementations."""

    _parsers = {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ExcelParser,
        "text/csv": CsvParser,
        "application/pdf": PdfParser,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": WordParser,
        "text/plain": TextParser,
        "text/markdown": TextParser,
    }

    # Content types that are considered "rich" (binary) documents vs plain text
    RICH_CONTENT_TYPES = [
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/csv",
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ]

    # All supported content types (rich + text)
    ALL_CONTENT_TYPES = RICH_CONTENT_TYPES + ["text/plain", "text/markdown"]

    @classmethod
    def get_parser(cls, content_type: str) -> DocumentParser:
        parser_class = cls._parsers.get(content_type)
        if not parser_class:
            raise ValueError(f"Unsupported content type: {content_type}")
        return parser_class()

    @classmethod
    def is_supported(cls, content_type: str) -> bool:
        return content_type in cls._parsers

    @classmethod
    def is_rich_format(cls, content_type: str) -> bool:
        return content_type in cls.RICH_CONTENT_TYPES

__all__ = ["ParserFactory", "DocumentParser"]
