"""
Async-safe structured logging service using structlog.

Uses QueueHandler + QueueListener pattern to prevent blocking FastAPI's event loop
during file I/O operations. Logs are written to rotating files in JSON format
for easy parsing and AI analysis.

Key features:
- Structured JSON logging with custom fields (category, correlation_id, etc.)
- Async-safe via queue-based logging (no blocking I/O in request handlers)
- Automatic log rotation (daily, with configurable retention)
- Singleton pattern for consistent logging across application
"""
import logging
import logging.handlers
import queue
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import structlog
from app.config import settings


class LoggingService:
    """
    Centralized logging service with async-safe file handlers.

    Uses Python's logging.handlers.QueueHandler to avoid blocking the event loop:
    - Log calls put messages in a queue (fast, non-blocking)
    - Background QueueListener thread writes to file (isolated from async code)
    """

    _instance: Optional['LoggingService'] = None

    def __new__(cls):
        """Singleton pattern - only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize logging infrastructure on first instantiation."""
        if self._initialized:
            return

        self._initialized = True
        self._setup_logging()

    def _setup_logging(self) -> None:
        """
        Configure structlog with async-safe file handlers.

        Architecture:
        1. Application code calls structlog logger
        2. structlog processors format to JSON
        3. structlog forwards to Python stdlib logging
        4. QueueHandler puts message in queue (non-blocking)
        5. QueueListener thread writes to file (background)
        """
        # Ensure log directory exists
        log_dir = settings.log_dir_path
        log_dir.mkdir(parents=True, exist_ok=True)

        # Create log file path
        log_file = log_dir / "app.log"

        # Configure rotating file handler (rotates daily, keeps N days)
        file_handler = logging.handlers.TimedRotatingFileHandler(
            filename=str(log_file),
            when='midnight',
            interval=1,
            backupCount=settings.log_rotation_days,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, settings.log_level.upper()))

        # Console handler for development visibility
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.WARNING)  # Only warnings/errors to console

        # Create queue for async-safe logging (P-01 prevention)
        log_queue: queue.Queue = queue.Queue(-1)  # No size limit
        queue_handler = logging.handlers.QueueHandler(log_queue)

        # QueueListener runs in background thread, writes to file
        self.queue_listener = logging.handlers.QueueListener(
            log_queue,
            file_handler,
            console_handler,
            respect_handler_level=True
        )
        self.queue_listener.start()

        # Configure Python stdlib logging
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)  # Capture all levels
        root_logger.addHandler(queue_handler)

        # Configure structlog
        structlog.configure(
            processors=[
                # Add timestamp
                structlog.processors.TimeStamper(fmt="iso", utc=True),
                # Add log level
                structlog.stdlib.add_log_level,
                # Add logger name
                structlog.stdlib.add_logger_name,
                # Render as JSON
                structlog.processors.JSONRenderer()
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

        self.logger = structlog.get_logger("ba_assistant")

    def log(
        self,
        level: str,
        message: str,
        category: str,
        **kwargs: Any
    ) -> None:
        """
        Write a structured log entry.

        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: Human-readable message
            category: Log category (api, ai, db, auth, etc.)
            **kwargs: Additional structured fields (correlation_id, user_id, etc.)

        Example:
            logging_service.log(
                'INFO',
                'User authenticated',
                'auth',
                user_id='user123',
                correlation_id='abc-def',
                provider='google'
            )
        """
        log_method = getattr(self.logger, level.lower())
        log_method(message, category=category, **kwargs)

    def shutdown(self) -> None:
        """
        Gracefully shutdown logging service.

        Flushes queue and stops listener thread. Call during application shutdown.
        """
        if hasattr(self, 'queue_listener'):
            self.queue_listener.stop()


# Module-level singleton instance (like settings object)
_logging_service: Optional[LoggingService] = None


def get_logging_service() -> LoggingService:
    """
    Get the singleton LoggingService instance.

    Returns:
        LoggingService: Configured logging service

    Example:
        from app.services.logging_service import get_logging_service

        ls = get_logging_service()
        ls.log('INFO', 'Request received', 'api', endpoint='/chat')
    """
    global _logging_service
    if _logging_service is None:
        _logging_service = LoggingService()
    return _logging_service
