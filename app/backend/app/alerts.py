from typing import Dict, List

import requests

from .config import settings


def _policy_counts(summary: Dict) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for item in summary.get("policy_events", []):
        if (
            isinstance(item, (list, tuple))
            and len(item) == 2
            and isinstance(item[0], str)
        ):
            counts[item[0]] = int(item[1])
    return counts


def evaluate_ops_alerts(summary: Dict, daily_cost_usd: float) -> List[Dict]:
    alerts: List[Dict] = []
    requests_total = int(summary.get("requests", 0))
    policy = _policy_counts(summary)

    min_requests = max(1, int(getattr(settings, "ops_alert_min_requests", 20)))
    refusal_threshold = float(getattr(settings, "ops_alert_refusal_ratio_threshold", 0.2))
    injection_threshold = float(getattr(settings, "ops_alert_injection_ratio_threshold", 0.1))
    cost_threshold = float(getattr(settings, "ops_alert_daily_cost_threshold_usd", 50.0))

    if requests_total >= min_requests:
        refusal_count = int(policy.get("refusal", 0))
        refusal_ratio = refusal_count / requests_total if requests_total else 0.0
        if refusal_ratio >= refusal_threshold:
            alerts.append(
                {
                    "code": "high_refusal_ratio",
                    "severity": "warning",
                    "message": "Refusal ratio exceeded threshold.",
                    "value": round(refusal_ratio, 4),
                    "threshold": refusal_threshold,
                }
            )

        injection_count = int(policy.get("injection_detected", 0))
        injection_ratio = injection_count / requests_total if requests_total else 0.0
        if injection_ratio >= injection_threshold:
            alerts.append(
                {
                    "code": "high_injection_ratio",
                    "severity": "warning",
                    "message": "Prompt injection detection ratio exceeded threshold.",
                    "value": round(injection_ratio, 4),
                    "threshold": injection_threshold,
                }
            )

    if daily_cost_usd >= cost_threshold:
        alerts.append(
            {
                "code": "daily_cost_threshold_exceeded",
                "severity": "critical",
                "message": "Daily LLM cost exceeded threshold.",
                "value": round(daily_cost_usd, 6),
                "threshold": cost_threshold,
            }
        )

    return alerts


def dispatch_ops_alerts(alerts: List[Dict], summary: Dict, daily_cost_usd: float) -> Dict[str, int]:
    webhook_url = getattr(settings, "ops_alert_webhook_url", "").strip()
    if not webhook_url or not alerts:
        return {"sent": 0, "failed": 0}

    payload = {
        "alerts": alerts,
        "requests": int(summary.get("requests", 0)),
        "daily_cost_usd": round(float(daily_cost_usd), 6),
    }

    timeout_sec = float(getattr(settings, "ops_alert_webhook_timeout_sec", 5.0))
    try:
        response = requests.post(webhook_url, json=payload, timeout=max(1.0, timeout_sec))
        response.raise_for_status()
        return {"sent": len(alerts), "failed": 0}
    except requests.RequestException:
        return {"sent": 0, "failed": len(alerts)}
