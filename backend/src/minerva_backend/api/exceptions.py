"""Custom exceptions for the Minerva Backend API."""
import logging
from typing import Any, Dict, Optional, Callable, TypeVar
from functools import wraps

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)
T = TypeVar('T')


class MinervaHTTPException(HTTPException):
    """Enhanced HTTP exception with error codes and additional context."""

    def __init__(
            self,
            status_code: int,
            detail: str,
            error_code: Optional[str] = None,
            context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code, detail)
        self.error_code = error_code or f"HTTP_{status_code}"
        self.context = context or {}


class ValidationError(MinervaHTTPException):
    """Raised when request validation fails."""

    def __init__(self, detail: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(400, detail, "VALIDATION_ERROR", context)


class NotFoundError(MinervaHTTPException):
    """Raised when a requested resource is not found."""

    def __init__(self, resource: str, identifier: str):
        detail = f"{resource} with identifier '{identifier}' not found"
        context = {"resource": resource, "identifier": identifier}
        super().__init__(404, detail, "RESOURCE_NOT_FOUND", context)


class ServiceUnavailableError(MinervaHTTPException):
    """Raised when an external service is unavailable."""

    def __init__(self, service: str, detail: Optional[str] = None):
        message = detail or f"{service} service is currently unavailable"
        context = {"service": service}
        super().__init__(503, message, "SERVICE_UNAVAILABLE", context)


class ProcessingError(MinervaHTTPException):
    """Raised when processing operations fail."""

    def __init__(self, detail: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(422, detail, "PROCESSING_ERROR", context)


def handle_errors(default_status_code: int = 500):
    """Decorator for comprehensive error handling with logging and structured responses."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            try:
                return await func(*args, **kwargs)
            except MinervaHTTPException:
                # Re-raise our custom exceptions as-is
                raise
            except ValueError as e:
                logger.warning(f"Validation error in {func.__name__}: {e}")
                raise ValidationError(str(e))
            except ConnectionError as e:
                logger.error(f"Connection error in {func.__name__}: {e}")
                raise ServiceUnavailableError("Database", str(e))
            except FileNotFoundError as e:
                logger.error(f"File not found in {func.__name__}: {e}")
                raise NotFoundError("File", str(e))
            except Exception as e:
                logger.error(f"Unhandled error in {func.__name__}: {e}", exc_info=True)
                raise MinervaHTTPException(
                    default_status_code,
                    "An internal error occurred",
                    "INTERNAL_ERROR",
                    {"function": func.__name__}
                )

        return wrapper

    return decorator


async def minerva_exception_handler(request: Request, exc: MinervaHTTPException) -> JSONResponse:
    """Custom exception handler for MinervaHTTPException instances."""

    content = {
        "error": {
            "code": exc.error_code,
            "message": exc.detail,
            "status_code": exc.status_code
        }
    }

    # Add context if available and not sensitive
    if exc.context and not any(key in exc.context for key in ['password', 'token', 'secret']):
        content["error"]["context"] = exc.context

    # Add request information for debugging (in development only)
    from minerva_backend.config import settings
    if settings.debug:
        content["error"]["request"] = {
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path
        }

    return JSONResponse(
        status_code=exc.status_code,
        content=content
    )
