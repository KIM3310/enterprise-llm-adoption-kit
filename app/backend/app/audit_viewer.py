import json
from collections import Counter
from pathlib import Path
from typing import Dict, List


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


def summarize_log(path: Path) -> Dict:
    if not path.exists():
        return {
            "requests": 0,
            "top_users": [],
            "tools_used": [],
            "policy_events": [],
            "total_cost": 0.0,
        }
    lines = path.read_text().splitlines()
    return summarize_events(lines)
