"""Control Tower decision engine with multi-platform execution planning.

Computes a weighted risk score from six operational signals, classifies
the risk level against configurable bands, and generates platform-specific
execution tasks for AWS, Databricks, Snowflake, Palantir, and MariaDB.
The spec is loaded from disk and cached with mtime-based invalidation.
"""

import json
import uuid
from pathlib import Path
from typing import Dict, List, Tuple

from .config import settings
from .models import ControlTowerDecisionRequest

FACTOR_KEYS = (
    "demand_volatility",
    "inventory_pressure",
    "machine_health_risk",
    "sla_risk",
    "margin_pressure",
    "gpu_pressure",
)

DEFAULT_SPEC: Dict = {
    "version": "1.0.0",
    "weights": {
        "demand_volatility": 0.18,
        "inventory_pressure": 0.2,
        "machine_health_risk": 0.2,
        "sla_risk": 0.17,
        "margin_pressure": 0.15,
        "gpu_pressure": 0.1,
    },
    "thresholds": {
        "demand_delta_alert_ratio": 0.3,
        "inventory_days_alert": 7.0,
        "inventory_days_critical": 3.0,
        "machine_anomaly_alert": 0.7,
        "sla_breach_alert": 0.5,
        "target_margin_ratio": 0.2,
        "gpu_utilization_alert": 0.85,
    },
    "risk_bands": [
        {"level": "low", "min": 0.0, "max": 0.35},
        {"level": "medium", "min": 0.35, "max": 0.6},
        {"level": "high", "min": 0.6, "max": 0.8},
        {"level": "critical", "min": 0.8, "max": 1.01},
    ],
    "primary_actions": {
        "low": [
            "Keep current operating plan and monitor baseline drift.",
        ],
        "medium": [
            "Increase safety stock for top at-risk SKUs.",
            "Run targeted health checks on noisy machines.",
        ],
        "high": [
            "Trigger temporary capacity scale-out and expedite logistics.",
            "Prioritize at-risk orders and allocate fallback inventory.",
            "Launch focused model recalibration run.",
        ],
        "critical": [
            "Activate incident command and hourly control tower cadence.",
            "Freeze low-priority workloads and reserve GPU for SLA-critical jobs.",
            "Open executive escalation and execute contingency runbook.",
        ],
    },
    "platform_actions": {
        "aws": {
            "low": "No immediate scaling action. Keep EKS autoscaling policy unchanged.",
            "medium": "Raise EKS worker floor and pre-warm inference pods.",
            "high": "Scale EKS GPU node group and invoke incident Step Functions workflow.",
            "critical": "Execute regional failover playbook and lock capacity reservations.",
        },
        "databricks": {
            "low": "Continue scheduled feature freshness checks.",
            "medium": "Run incremental feature pipeline and drift diagnostics.",
            "high": "Run emergency retraining notebook and publish candidate model.",
            "critical": "Force supervised retraining workflow and block stale model promotion.",
        },
        "snowflake": {
            "low": "Persist daily KPI snapshot only.",
            "medium": "Increase KPI snapshot cadence to hourly.",
            "high": "Write incident KPI stream and expose high-risk dashboard view.",
            "critical": "Enable war-room dashboard and lock incident data mart branch.",
        },
        "palantir": {
            "low": "Keep ontology action queue in monitor mode.",
            "medium": "Create operator task objects for top risk entities.",
            "high": "Trigger ontology action set for expediting and maintenance dispatch.",
            "critical": "Launch executive decision app workflow with mandatory acknowledgements.",
        },
        "mariadb": {
            "low": "Store decision snapshot in control_tower_decisions table.",
            "medium": "Store decision snapshot and create follow-up task records.",
            "high": "Persist incident decision set and lock affected order rows for operator check.",
            "critical": "Persist emergency decision journal and activate strict write-audit mode.",
        },
    },
}

_SPEC_CACHE: Dict[str, object] = {
    "path": "",
    "mtime": None,
    "spec": None,
    "validation_ok": False,
    "validation_error": "",
}


def _copy_spec(spec: Dict) -> Dict:
    return json.loads(json.dumps(spec))


def _write_default_spec(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(DEFAULT_SPEC, indent=2, ensure_ascii=True), encoding="utf-8")


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    if value < low:
        return low
    if value > high:
        return high
    return value


def _validate_spec(spec: Dict) -> Tuple[bool, str]:
    required_keys = {"version", "weights", "thresholds", "risk_bands", "primary_actions", "platform_actions"}
    missing = sorted(required_keys - set(spec.keys()))
    if missing:
        return False, f"missing keys: {', '.join(missing)}"

    weights = spec.get("weights", {})
    if not isinstance(weights, dict):
        return False, "weights must be a dict"
    for key in FACTOR_KEYS:
        if key not in weights:
            return False, f"weights missing key: {key}"
    total_weight = sum(float(weights.get(key, 0.0)) for key in FACTOR_KEYS)
    if total_weight <= 0:
        return False, "weights total must be > 0"

    thresholds = spec.get("thresholds", {})
    if not isinstance(thresholds, dict):
        return False, "thresholds must be a dict"
    required_thresholds = {
        "demand_delta_alert_ratio",
        "inventory_days_alert",
        "inventory_days_critical",
        "machine_anomaly_alert",
        "sla_breach_alert",
        "target_margin_ratio",
        "gpu_utilization_alert",
    }
    missing_thresholds = sorted(required_thresholds - set(thresholds.keys()))
    if missing_thresholds:
        return False, f"thresholds missing keys: {', '.join(missing_thresholds)}"

    risk_bands = spec.get("risk_bands", [])
    if not isinstance(risk_bands, list) or not risk_bands:
        return False, "risk_bands must be a non-empty list"
    previous_min = -1.0
    known_levels = set()
    for band in risk_bands:
        if not isinstance(band, dict):
            return False, "risk_bands entries must be dicts"
        if {"level", "min", "max"} - set(band.keys()):
            return False, "risk_bands entries require level/min/max"
        low = float(band["min"])
        high = float(band["max"])
        level = str(band["level"])
        if low > high:
            return False, "risk_bands min cannot exceed max"
        if low < previous_min:
            return False, "risk_bands must be sorted by min"
        known_levels.add(level)
        previous_min = low

    primary_actions = spec.get("primary_actions", {})
    if not isinstance(primary_actions, dict):
        return False, "primary_actions must be a dict"
    missing_levels = sorted(known_levels - set(primary_actions.keys()))
    if missing_levels:
        return False, f"primary_actions missing levels: {', '.join(missing_levels)}"

    platform_actions = spec.get("platform_actions", {})
    if not isinstance(platform_actions, dict):
        return False, "platform_actions must be a dict"
    required_platforms = {"aws", "databricks", "snowflake", "palantir", "mariadb"}
    missing_platforms = sorted(required_platforms - set(platform_actions.keys()))
    if missing_platforms:
        return False, f"platform_actions missing platforms: {', '.join(missing_platforms)}"
    for platform in required_platforms:
        action_map = platform_actions.get(platform, {})
        if not isinstance(action_map, dict):
            return False, f"platform_actions.{platform} must be a dict"
        missing_action_levels = sorted(known_levels - set(action_map.keys()))
        if missing_action_levels:
            return False, f"platform_actions.{platform} missing levels: {', '.join(missing_action_levels)}"

    return True, ""


def _normalized_weights(weights: Dict[str, float]) -> Dict[str, float]:
    values = {key: max(0.0, float(weights.get(key, 0.0))) for key in FACTOR_KEYS}
    total = sum(values.values())
    if total <= 0:
        even = 1.0 / float(len(FACTOR_KEYS))
        return {key: even for key in FACTOR_KEYS}
    return {key: values[key] / total for key in FACTOR_KEYS}


def _load_spec_from_disk(path: Path) -> Tuple[Dict, bool, str]:
    if not path.exists():
        _write_default_spec(path)

    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return _copy_spec(DEFAULT_SPEC), False, f"failed to load spec: {exc}"

    valid, error = _validate_spec(loaded)
    if not valid:
        return _copy_spec(DEFAULT_SPEC), False, error

    return loaded, True, ""


def get_control_tower_spec_snapshot() -> Tuple[Dict, bool, str]:
    """Return the cached spec, validation details, and any validation error message."""
    path = Path(settings.control_tower_spec_path)
    mtime = path.stat().st_mtime if path.exists() else None
    cache_hit = (
        _SPEC_CACHE["spec"] is not None
        and _SPEC_CACHE["path"] == str(path)
        and _SPEC_CACHE["mtime"] == mtime
    )
    if cache_hit:
        return (
            _copy_spec(_SPEC_CACHE["spec"]),  # type: ignore[arg-type]
            bool(_SPEC_CACHE["validation_ok"]),
            str(_SPEC_CACHE["validation_error"]),
        )

    spec, validation_ok, validation_error = _load_spec_from_disk(path)
    mtime = path.stat().st_mtime if path.exists() else None
    _SPEC_CACHE["path"] = str(path)
    _SPEC_CACHE["mtime"] = mtime
    _SPEC_CACHE["spec"] = _copy_spec(spec)
    _SPEC_CACHE["validation_ok"] = validation_ok
    _SPEC_CACHE["validation_error"] = validation_error
    return _copy_spec(spec), validation_ok, validation_error


def clear_control_tower_spec_cache() -> None:
    """Invalidate the cached spec so the next call reloads from disk."""
    _SPEC_CACHE["path"] = ""
    _SPEC_CACHE["mtime"] = None
    _SPEC_CACHE["spec"] = None
    _SPEC_CACHE["validation_ok"] = False
    _SPEC_CACHE["validation_error"] = ""


def _inventory_pressure(inventory_days: float, alert_days: float, critical_days: float) -> float:
    safe_alert = max(alert_days, critical_days + 0.001)
    if inventory_days >= safe_alert:
        return 0.0
    if inventory_days <= critical_days:
        return 1.0
    return _clamp((safe_alert - inventory_days) / (safe_alert - critical_days))


def _margin_pressure(unit_margin_ratio: float, target_margin_ratio: float) -> float:
    safe_target = max(0.01, target_margin_ratio)
    if unit_margin_ratio >= safe_target:
        return 0.0
    return _clamp((safe_target - unit_margin_ratio) / safe_target)


def _gpu_pressure(gpu_utilization: float, alert_ratio: float) -> float:
    safe_alert = _clamp(alert_ratio, low=0.01, high=0.99)
    if gpu_utilization <= safe_alert:
        return 0.0
    return _clamp((gpu_utilization - safe_alert) / (1.0 - safe_alert))


def _classify_risk(score: float, risk_bands: List[Dict]) -> str:
    for idx, band in enumerate(risk_bands):
        low = float(band["min"])
        high = float(band["max"])
        is_last = idx == len(risk_bands) - 1
        if score >= low and (score < high or (is_last and score <= high)):
            return str(band["level"])
    return "critical" if score >= 0.8 else "low"


def _build_execution_plan(
    payload: ControlTowerDecisionRequest,
    risk_level: str,
    spec: Dict,
) -> List[Dict[str, str]]:
    selected = {
        "aws": payload.targets.aws,
        "databricks": payload.targets.databricks,
        "snowflake": payload.targets.snowflake,
        "palantir": payload.targets.palantir,
        "mariadb": payload.targets.mariadb,
    }
    priority_by_level = {
        "low": "P3",
        "medium": "P2",
        "high": "P1",
        "critical": "P0",
    }
    plan: List[Dict[str, str]] = []
    platform_actions = spec.get("platform_actions", {})
    for platform, enabled in selected.items():
        if not enabled:
            continue
        action_map = platform_actions.get(platform, {})
        action = action_map.get(risk_level)
        if not action:
            continue
        plan.append(
            {
                "platform": platform,
                "action": str(action),
                "priority": priority_by_level.get(risk_level, "P2"),
                "payload": json.dumps(
                    {
                        "scenario_id": payload.scenario_id,
                        "region": payload.region,
                        "risk_level": risk_level,
                        "spec_version": spec.get("version", "unknown"),
                    },
                    ensure_ascii=True,
                ),
            }
        )
    return plan


def build_control_tower_decision(payload: ControlTowerDecisionRequest) -> Dict:
    """Build a complete control-tower decision from the given operational signals."""
    spec, _, _ = get_control_tower_spec_snapshot()
    thresholds = spec["thresholds"]
    weights = _normalized_weights(spec["weights"])

    demand_risk = _clamp(
        abs(payload.signals.demand_delta_ratio)
        / max(float(thresholds["demand_delta_alert_ratio"]), 0.01)
    )
    inventory_risk = _inventory_pressure(
        payload.signals.inventory_days,
        float(thresholds["inventory_days_alert"]),
        float(thresholds["inventory_days_critical"]),
    )
    machine_risk = _clamp(payload.signals.machine_anomaly_score)
    sla_risk = _clamp(payload.signals.sla_breach_risk)
    margin_risk = _margin_pressure(
        payload.signals.unit_margin_ratio,
        float(thresholds["target_margin_ratio"]),
    )
    gpu_risk = _gpu_pressure(
        payload.signals.gpu_utilization,
        float(thresholds["gpu_utilization_alert"]),
    )

    factors = {
        "demand_volatility": round(demand_risk, 4),
        "inventory_pressure": round(inventory_risk, 4),
        "machine_health_risk": round(machine_risk, 4),
        "sla_risk": round(sla_risk, 4),
        "margin_pressure": round(margin_risk, 4),
        "gpu_pressure": round(gpu_risk, 4),
    }

    weighted_score = 0.0
    for key in FACTOR_KEYS:
        weighted_score += factors[key] * weights[key]
    risk_score = round(_clamp(weighted_score), 4)
    risk_level = _classify_risk(risk_score, spec["risk_bands"])

    primary_actions = spec.get("primary_actions", {}).get(
        risk_level, ["Check control tower metrics and monitor drift."]
    )

    raw_plan = _build_execution_plan(payload, risk_level, spec)
    execution_plan = []
    for step in raw_plan:
        execution_plan.append(
            {
                "platform": step["platform"],
                "action": step["action"],
                "priority": step["priority"],
                "payload": json.loads(step["payload"]),
            }
        )

    top_factors = sorted(factors.items(), key=lambda item: item[1], reverse=True)[:2]
    dominant = ", ".join(f"{name}={value:.2f}" for name, value in top_factors)

    cot_trace = [
        {
            "step": "normalize_inputs",
            "summary": "Normalized input signals into bounded risk factors in [0, 1].",
        },
        {
            "step": "risk_scoring",
            "summary": f"Computed weighted score {risk_score:.4f} with dominant factors: {dominant}.",
        },
        {
            "step": "risk_classification",
            "summary": f"Mapped score to risk level '{risk_level}' using spec risk bands.",
        },
        {
            "step": "action_planning",
            "summary": f"Selected {len(primary_actions)} primary actions for level '{risk_level}'.",
        },
        {
            "step": "orchestration",
            "summary": f"Generated {len(execution_plan)} platform execution tasks.",
        },
    ]

    return {
        "decision_id": f"ct-{uuid.uuid4().hex[:12]}",
        "risk_score": risk_score,
        "risk_level": risk_level,
        "factor_breakdown": factors,
        "primary_actions": primary_actions,
        "execution_plan": execution_plan,
        "cot_trace": cot_trace,
        "spec_version": str(spec.get("version", "unknown")),
    }
