"""Audit logging subsystem with hash-mode support for enterprise data handling.

Provides structured audit event persistence to both file and stdout.  In
``enterprise`` data-handling mode, input/output payloads are replaced with
SHA-256 hashes so that raw PII is never written to the audit log.  An
automatic retention-based pruning mechanism removes events older than
``AUDIT_RETENTION_DAYS`` when operating in enterprise mode.
"""

import hashlib
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from .config import settings

logger = logging.getLogger("audit")
logger.setLevel(logging.INFO)

if not logger.handlers:
    formatter = logging.Formatter("%(message)s")

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    os.makedirs(os.path.dirname(settings.audit_log_path), exist_ok=True)
    file_handler = logging.FileHandler(settings.audit_log_path)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


def log_audit(event: Dict[str, Any]) -> None:
    """Persist a single audit event with an ISO-8601 UTC timestamp.

    Triggers retention-based pruning in enterprise mode before writing.

    Args:
        event: Arbitrary audit payload; a ``timestamp`` key is added automatically.
    """
    event["timestamp"] = datetime.now(timezone.utc).isoformat()
    _prune_if_needed()
    logger.info(json.dumps(event, ensure_ascii=True))


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_payload(input_text: str, output_text: str) -> Dict[str, str]:
    """Build an audit payload, hashing content when in enterprise mode.

    Args:
        input_text: The raw user input.
        output_text: The raw model output.

    Returns:
        A dict with either raw text or SHA-256 hashes depending on
        ``settings.data_handling_mode``.
    """
    if settings.data_handling_mode == "enterprise":
        return {
            "input_hash": _hash_text(input_text),
            "output_hash": _hash_text(output_text),
            "mode": "enterprise",
        }
    return {
        "input": input_text,
        "output": output_text,
        "mode": "demo",
    }


def _prune_if_needed() -> None:
    if settings.data_handling_mode != "enterprise":
        return
    if settings.audit_retention_days <= 0:
        return
    path = settings.audit_log_path
    if not os.path.exists(path):
        return

    cutoff = datetime.now(timezone.utc) - timedelta(days=settings.audit_retention_days)
    kept_lines = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                event = json.loads(line)
                ts = event.get("timestamp")
                if not ts:
                    continue
                event_time = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                if event_time >= cutoff:
                    kept_lines.append(line)
            except (json.JSONDecodeError, ValueError, KeyError):
                continue

    with open(path, "w", encoding="utf-8") as f:
        for line in kept_lines:
            f.write(line)
