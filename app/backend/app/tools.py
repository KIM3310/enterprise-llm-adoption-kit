import json
import os
import re
from typing import Dict, List, Tuple

from .config import DATA_DIR

ALLOWED_TOOLS = {
    "runbook_lookup",
    "log_signature_extract",
    "knowledge_search",
}

RUNBOOK_PATH = str(DATA_DIR / "runbooks.json")


class ToolRouter:
    def __init__(self, knowledge_search_fn):
        self.knowledge_search_fn = knowledge_search_fn
        self.runbooks = _load_runbooks()

    def call(self, name: str, payload: Dict, role: str) -> Tuple[Dict, str]:
        if name not in ALLOWED_TOOLS:
            return {"error": "tool not allowed"}, "denied"
        if name == "runbook_lookup":
            return self.runbook_lookup(payload.get("query", "")), "ok"
        if name == "log_signature_extract":
            return self.log_signature_extract(payload.get("text", "")), "ok"
        if name == "knowledge_search":
            return self.knowledge_search_fn(payload.get("query", ""), role), "ok"
        return {"error": "unknown"}, "denied"

    def runbook_lookup(self, query: str) -> Dict:
        for item in self.runbooks:
            if item["signature"].lower() in query.lower():
                return {"steps": item["steps"], "signature": item["signature"]}
        return {"steps": ["No exact runbook found. Escalate to on-call."], "signature": "unknown"}

    def log_signature_extract(self, text: str) -> Dict:
        patterns = [
            r"OutOfMemoryError",
            r"Connection refused",
            r"Timeout while",
            r"Permission denied",
            r"5\d{2} Server Error",
        ]
        hits: List[str] = []
        for pat in patterns:
            if re.search(pat, text, re.IGNORECASE):
                hits.append(pat)
        return {"signatures": hits}


def _load_runbooks() -> List[Dict]:
    if not os.path.exists(RUNBOOK_PATH):
        return []
    with open(RUNBOOK_PATH, "r", encoding="utf-8") as f:
        return json.load(f)
