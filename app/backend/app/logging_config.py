"""Structured logging configuration with request correlation IDs.

Provides a JSON-based log formatter and a context-variable backed
correlation ID that is set per-request via FastAPI middleware.  Every
log record produced while a request is in flight automatically includes
the ``correlation_id`` field so operators can trace a single request
across all log lines.

Usage::

    from app.logging_config import configure_logging, correlation_id_ctx

    configure_logging()  # call once at startup

    # In middleware / lifespan:
    correlation_id_ctx.set("abc-123")
"""

from __future__ import annotations

import json
import logging
import sys
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Dict

# ---------------------------------------------------------------------------
# Correlation ID context variable -- set once per request in middleware
# ---------------------------------------------------------------------------
correlation_id_ctx: ContextVar[str] = ContextVar(
    "correlation_id", default=""
)


def generate_correlation_id() -> str:
    """Return a new unique correlation ID suitable for request tracing."""
    return uuid.uuid4().hex[:16]


# ---------------------------------------------------------------------------
# JSON formatter
# ---------------------------------------------------------------------------

class StructuredJSONFormatter(logging.Formatter):
    """Emit each log record as a single-line JSON object.

    Fields always present: ``timestamp``, ``level``, ``logger``, ``message``,
    ``correlation_id``.  If the record carries ``exc_info`` the formatted
    traceback is included as ``exception``.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format *record* as a JSON string with correlation context."""
        payload: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": correlation_id_ctx.get(""),
        }
        if record.exc_info and record.exc_info[1] is not None:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=True)


# ---------------------------------------------------------------------------
# Public helper
# ---------------------------------------------------------------------------

def configure_logging(*, level: int = logging.INFO) -> None:
    """Replace the root logger's handlers with a single structured JSON handler.

    Should be called exactly once during application startup, before any
    request processing begins.

    Args:
        level: The minimum log level to emit (default ``logging.INFO``).
    """
    root = logging.getLogger()
    root.setLevel(level)

    # Remove pre-existing handlers to avoid duplicate output.
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredJSONFormatter())
    root.addHandler(handler)
