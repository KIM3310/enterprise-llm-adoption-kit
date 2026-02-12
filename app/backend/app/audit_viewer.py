import json
from collections import Counter, deque
from pathlib import Path
from typing import Deque, Dict, List, Optional


def summarize_events(lines: List[str]) -> Dict:
    requests = 0
    users = Counter()
    tools = Counter()
    policy = Counter()
    total_cost = 0.0

    for line in lines:
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except Exception:
            continue
        requests += 1
        user_id = event.get("user_id", "unknown")
        users[user_id] += 1
        total_cost += float(event.get("cost_estimate", 0.0))

        for tool in event.get("tool_calls", []):
            name = tool.get("name", "unknown")
            tools[name] += 1

        policy_events = event.get("policy_events", {})
        for key, value in policy_events.items():
            if isinstance(value, bool) and value:
                policy[key] += 1

    return {
        "requests": requests,
        "top_users": users.most_common(5),
        "tools_used": tools.most_common(10),
        "policy_events": policy.most_common(10),
        "total_cost": round(total_cost, 6),
    }


def _empty_summary() -> Dict:
    return {
        "requests": 0,
        "top_users": [],
        "tools_used": [],
        "policy_events": [],
        "total_cost": 0.0,
    }


def _read_recent_lines(path: Path, max_lines: Optional[int]) -> List[str]:
    if max_lines is None:
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            return handle.read().splitlines()

    safe_limit = max(1, min(int(max_lines), 50000))
    recent: Deque[str] = deque(maxlen=safe_limit)
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            recent.append(line.rstrip("\n"))
    return list(recent)


def summarize_log(path: Path, max_lines: Optional[int] = None) -> Dict:
    if not path.exists():
        return _empty_summary()
    try:
        lines = _read_recent_lines(path, max_lines=max_lines)
    except OSError:
        return _empty_summary()
    return summarize_events(lines)
