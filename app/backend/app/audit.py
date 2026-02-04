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
    event["timestamp"] = datetime.now(timezone.utc).isoformat()
    _prune_if_needed()
    logger.info(json.dumps(event, ensure_ascii=True))


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_payload(input_text: str, output_text: str) -> Dict[str, str]:
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
            except Exception:
                continue

    with open(path, "w", encoding="utf-8") as f:
        for line in kept_lines:
            f.write(line)
