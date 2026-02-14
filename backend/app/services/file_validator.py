import io
import zipfile
import logging
import filetype
from fastapi import HTTPException

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB (SEC-02)
MAX_UNCOMPRESSED_RATIO = 100      # Zip bomb detection threshold (SEC-04)

# Mapping from expected content_type to filetype library MIME types
# filetype may return slightly different MIME types than the client sends
MAGIC_TYPE_MAP = {
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ["application/zip", "application/x-zip-compressed", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"],
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ["application/zip", "application/x-zip-compressed", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
    "application/pdf": ["application/pdf"],
    # CSV and plain text don't have magic numbers — validated by extension + parsing
    "text/csv": None,
    "text/plain": None,
    "text/markdown": None,
}


def validate_file_security(file_bytes: bytes, content_type: str) -> None:
    """
    Orchestrator for security validation.

    Args:
        file_bytes: Raw file bytes
        content_type: Expected MIME type

    Raises:
        HTTPException: 413 for size/zip bomb, 400 for malformed/spoofed files
    """
    validate_file_size(file_bytes)
    validate_magic_number(file_bytes, content_type)

    # Zip bomb check for XLSX/DOCX (they are zip archives)
    if content_type in [
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]:
        validate_zip_bomb(file_bytes)


def validate_file_size(file_bytes: bytes) -> None:
    """
    Validate file doesn't exceed size limit.

    Raises:
        HTTPException(413): If file exceeds MAX_FILE_SIZE
    """
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE / (1024*1024):.1f}MB"
        )


def validate_magic_number(file_bytes: bytes, expected_content_type: str) -> None:
    """
    Validate file's magic bytes match expected content type.

    Args:
        file_bytes: Raw file bytes
        expected_content_type: Expected MIME type from client

    Raises:
        HTTPException(400): If magic bytes don't match (file extension spoofing)
    """
    expected_types = MAGIC_TYPE_MAP.get(expected_content_type)

    # Skip validation for text-based formats (no magic bytes)
    if expected_types is None:
        return

    # Detect actual file type using magic bytes
    detected = filetype.guess(file_bytes)

    if detected is None:
        # Could be a text file or corrupted binary
        # For binary formats, this is suspicious
        if expected_content_type.startswith("application/"):
            raise HTTPException(
                status_code=400,
                detail="Could not detect file type from magic bytes. File may be corrupted."
            )
        return

    # Check if detected type matches expected
    if detected.mime not in expected_types:
        logger.warning(
            f"Magic number mismatch: expected {expected_content_type}, "
            f"detected {detected.mime} (extension: {detected.extension})"
        )
        raise HTTPException(
            status_code=400,
            detail=f"File type mismatch. Expected {expected_content_type}, but file appears to be {detected.mime}"
        )


def validate_zip_bomb(file_bytes: bytes) -> None:
    """
    Validate zip archive doesn't have excessive compression ratio (zip bomb attack).

    Args:
        file_bytes: Raw zip archive bytes

    Raises:
        HTTPException(400): If malformed zip
        HTTPException(413): If compression ratio exceeds threshold
    """
    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
            compressed_size = len(file_bytes)
            uncompressed_size = sum(info.file_size for info in zf.infolist())

            if uncompressed_size == 0:
                # Empty zip or all files are 0 bytes
                return

            ratio = uncompressed_size / compressed_size

            if ratio > MAX_UNCOMPRESSED_RATIO:
                logger.warning(
                    f"Zip bomb detected: {ratio:.1f}:1 compression ratio "
                    f"(compressed: {compressed_size}, uncompressed: {uncompressed_size})"
                )
                raise HTTPException(
                    status_code=413,
                    detail=f"File rejected: compression ratio ({ratio:.1f}:1) exceeds safety limit ({MAX_UNCOMPRESSED_RATIO}:1)"
                )

    except zipfile.BadZipFile:
        raise HTTPException(
            status_code=400,
            detail="Malformed zip archive. File may be corrupted."
        )
