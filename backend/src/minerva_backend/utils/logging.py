"""
Comprehensive logging configuration for Minerva Backend.

This module provides structured logging with consistent formatting,
performance metrics, and contextual information throughout the system.
"""

import logging
import logging.config
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from minerva_backend.config import settings


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging with context."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with structured context."""
        # Base log entry
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add all extra fields from the record
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "getMessage",
            ]:
                log_entry[key] = value

        # Add error details if available (truncated for Temporal compatibility)
        if record.exc_info and record.exc_info[0]:
            # Truncate traceback to prevent large error messages in Temporal
            full_traceback = self.formatException(record.exc_info)
            truncated_traceback = (
                full_traceback[:500] + "..."
                if len(full_traceback) > 500
                else full_traceback
            )

            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1])[:200],  # Truncate error message
                "traceback": truncated_traceback,
            }

        return f"{log_entry}"


class ContextualLogger:
    """Logger with contextual information for different components."""

    def __init__(self, name: str, context: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger(name)
        self.context = context or {}

    def _log_with_context(self, level: int, message: str, **kwargs):
        """Log with additional context."""
        extra = {**self.context, **kwargs}
        self.logger.log(level, message, extra=extra)

    def debug(self, message: str, **kwargs):
        """Log debug message with context."""
        self._log_with_context(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message with context."""
        self._log_with_context(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message with context."""
        self._log_with_context(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log error message with context."""
        self._log_with_context(logging.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message with context."""
        self._log_with_context(logging.CRITICAL, message, **kwargs)


class PerformanceLogger:
    """Logger for performance metrics and timing."""

    def __init__(self, logger_name: str):
        self.logger = logging.getLogger(logger_name)

    def log_processing_time(self, operation: str, duration_ms: float, **context):
        """Log processing time for an operation."""
        self.logger.info(
            f"Processing completed: {operation}",
            extra={
                "operation": operation,
                "duration_ms": duration_ms,
                "context": context,
            },
        )

    def log_entity_extraction(
        self, entity_type: str, count: int, duration_ms: float, **context
    ):
        """Log entity extraction metrics."""
        self.logger.info(
            f"Entity extraction completed: {entity_type}",
            extra={
                "entity_type": entity_type,
                "entity_count": count,
                "duration_ms": duration_ms,
                "context": context,
            },
        )

    def log_llm_request(self, model: str, tokens: int, duration_ms: float, **context):
        """Log LLM request metrics."""
        self.logger.info(
            f"LLM request completed: {model}",
            extra={
                "model": model,
                "tokens": tokens,
                "duration_ms": duration_ms,
                "context": context,
            },
        )


class LLMLogger:
    """Specialized logger for LLM requests and responses."""

    def __init__(self):
        self.logger = logging.getLogger("minerva_backend.processing.llm_service")

    def log_request(self, model: str, prompt: str, system_prompt: str = None):
        """Log LLM request submission with clean formatted user prompt."""
        # Clean up the prompt for better readability
        clean_prompt = prompt.replace("\n", "\n  ").strip()
        self.logger.info(f"LLM REQUEST [{model}]\n  Prompt: {clean_prompt}")

    def log_response(
        self, model: str, response: str, duration_ms: float, token_count: int = None
    ):
        """Log LLM response completion with separate content and stats logs."""
        # Clean up the response for better readability
        clean_response = response.replace("\n", "\n  ").strip()
        self.logger.info(f"LLM RESPONSE [{model}]\n  {clean_response}")

        # Log stats separately
        duration_mins = duration_ms / 60000
        duration_secs = (duration_ms % 60000) / 1000
        stats_parts = [f"Duration: {duration_mins:.0f}m{duration_secs:.0f}s"]
        if token_count:
            stats_parts.append(f"Tokens: {token_count}")
            if duration_ms > 0:
                tokens_per_sec = token_count / (duration_ms / 1000)
                stats_parts.append(f"Speed: {tokens_per_sec:.1f} tokens/sec")

        self.logger.info(f"LLM STATS [{model}] - {', '.join(stats_parts)}")


def setup_logging():
    """Configure logging for the entire application."""

    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Logging configuration
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "structured": {
                "()": StructuredFormatter,
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.log_level,
                "formatter": "structured",
                "stream": sys.stdout,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "detailed",
                "filename": "logs/minerva.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filename": "logs/minerva_errors.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
            },
            "performance_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "structured",
                "filename": "logs/minerva_performance.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 3,
            },
            "llm_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "detailed",
                "filename": "logs/minerva_llm.log",
                "maxBytes": 52428800,  # 50MB (LLM logs can be large)
                "backupCount": 5,
            },
        },
        "loggers": {
            "minerva_backend": {
                "level": "DEBUG",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "minerva_backend.api": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "minerva_backend.processing": {
                "level": "DEBUG",
                "handlers": ["console", "file", "performance_file"],
                "propagate": False,
            },
            "minerva_backend.graph": {
                "level": "DEBUG",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "minerva_backend.obsidian": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "performance": {
                "level": "INFO",
                "handlers": ["performance_file"],
                "propagate": False,
            },
            "minerva_backend.processing.llm_service": {
                "level": "DEBUG",
                "handlers": ["llm_file"],
                "propagate": False,
            },
            "uvicorn": {"level": "INFO", "handlers": ["console"], "propagate": False},
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
        },
        "root": {"level": "WARNING", "handlers": ["console", "error_file"]},
    }

    # Apply configuration
    logging.config.dictConfig(logging_config)

    # Set up performance logger
    performance_logger = PerformanceLogger("performance")

    return performance_logger


def get_logger(name: str, context: Optional[Dict[str, Any]] = None) -> ContextualLogger:
    """Get a contextual logger for a specific component."""
    return ContextualLogger(name, context)


def get_performance_logger() -> PerformanceLogger:
    """Get the performance logger."""
    return PerformanceLogger("performance")


def get_llm_logger() -> LLMLogger:
    """Get the LLM logger."""
    return LLMLogger()


# Initialize logging when module is imported
performance_logger = setup_logging()
