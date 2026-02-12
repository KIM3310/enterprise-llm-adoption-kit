import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"


def _read_secret_file(path: str) -> str:
    if not path:
        return ""
    try:
        return Path(path).read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def _load_env_or_file(value_env: str, file_env: str) -> str:
    value = os.getenv(value_env, "").strip()
    if value:
        return value
    file_path = os.getenv(file_env, "").strip()
    return _read_secret_file(file_path)


def _parse_csv_env(name: str, fallback: List[str]) -> List[str]:
    raw = os.getenv(name, "").strip()
    if not raw:
        return fallback
    items = [part.strip() for part in raw.split(",")]
    return [item for item in items if item]


def _load_jwt_secrets(default_secret: str) -> Dict[str, str]:
    # Format: JWT_SECRETS="v1:secret1,v2:secret2"
    raw = os.getenv("JWT_SECRETS", "").strip()
    parsed: Dict[str, str] = {}
    if raw:
        for part in raw.split(","):
            item = part.strip()
            if not item or ":" not in item:
                continue
            kid, secret = item.split(":", 1)
            kid = kid.strip()
            secret = secret.strip()
            if kid and secret:
                parsed[kid] = secret

    json_path = os.getenv("JWT_SECRETS_FILE", "").strip()
    if json_path:
        try:
            payload = json.loads(Path(json_path).read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                for kid, secret in payload.items():
                    if isinstance(kid, str) and isinstance(secret, str):
                        kid_norm = kid.strip()
                        secret_norm = secret.strip()
                        if kid_norm and secret_norm:
                            parsed[kid_norm] = secret_norm
        except Exception:
            pass

    if not parsed:
        parsed = {"v1": default_secret}
    return parsed


@dataclass(frozen=True)
class Settings:
    app_name: str = "Enterprise LLM Adoption Kit (Korea)"
    jwt_secret: str = os.getenv("JWT_SECRET", "dev-secret-change")
    jwt_active_kid: str = os.getenv("JWT_ACTIVE_KID", "v1")
    jwt_secrets: Dict[str, str] = field(default_factory=lambda: _load_jwt_secrets(
        os.getenv("JWT_SECRET", "dev-secret-change")
    ))
    jwt_issuer: str = os.getenv("JWT_ISSUER", "enterprise-llm-adoption-kit")
    jwt_ttl_minutes: int = int(os.getenv("JWT_TTL_MINUTES", "60"))
    auth_mode: str = os.getenv("AUTH_MODE", "local_jwt").strip().lower()

    oidc_issuer: str = os.getenv("OIDC_ISSUER", "").strip()
    oidc_audience: str = os.getenv("OIDC_AUDIENCE", "").strip()
    oidc_jwks_url: str = os.getenv("OIDC_JWKS_URL", "").strip()
    oidc_algorithms: List[str] = field(
        default_factory=lambda: _parse_csv_env("OIDC_ALGORITHMS", ["RS256"])
    )

    llm_provider: str = os.getenv("LLM_PROVIDER", "stub")
    llm_model: str = os.getenv("LLM_MODEL", "stub-llm")
    llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))
    llm_max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "512"))
    llm_timeout_sec: float = float(os.getenv("LLM_TIMEOUT_SEC", "30"))
    llm_openai_base_url: str = os.getenv("LLM_OPENAI_BASE_URL", "https://api.openai.com/v1").strip()
    llm_openai_org: str = os.getenv("LLM_OPENAI_ORG", "").strip()
    llm_openai_api_key: str = _load_env_or_file("LLM_OPENAI_API_KEY", "LLM_OPENAI_API_KEY_FILE")

    cost_per_1k_input_tokens: float = float(
        os.getenv("COST_PER_1K_INPUT_TOKENS", "0.003")
    )
    cost_per_1k_output_tokens: float = float(
        os.getenv("COST_PER_1K_OUTPUT_TOKENS", "0.015")
    )

    chroma_persist_dir: str = os.getenv(
        "CHROMA_PERSIST_DIR", str(DATA_DIR / "chroma")
    )

    audit_log_path: str = os.getenv(
        "AUDIT_LOG_PATH", str(DATA_DIR / "audit.log")
    )
    audit_summary_max_lines: int = int(os.getenv("AUDIT_SUMMARY_MAX_LINES", "5000"))

    sqlite_path: str = os.getenv("SQLITE_PATH", str(DATA_DIR / "app.db"))
    control_tower_spec_path: str = os.getenv(
        "CONTROL_TOWER_SPEC_PATH", str(DATA_DIR / "control_tower_spec.json")
    )

    rate_limit_capacity: int = int(os.getenv("RATE_LIMIT_CAPACITY", "10"))
    rate_limit_refill_per_sec: float = float(
        os.getenv("RATE_LIMIT_REFILL_PER_SEC", "0.5")
    )

    data_handling_mode: str = os.getenv("DATA_HANDLING_MODE", "demo")
    audit_retention_days: int = int(os.getenv("AUDIT_RETENTION_DAYS", "30"))

    allowed_tools: List[str] = field(
        default_factory=lambda: _parse_csv_env(
            "ALLOWED_TOOLS",
            ["runbook_lookup", "log_signature_extract", "knowledge_search"],
        )
    )

    event_storage_backend: str = os.getenv("EVENT_STORAGE_BACKEND", "sqlite").strip().lower()
    service_events_jsonl_path: str = os.getenv(
        "SERVICE_EVENTS_JSONL_PATH", str(DATA_DIR / "service_events.jsonl")
    )
    control_tower_decisions_jsonl_path: str = os.getenv(
        "CONTROL_TOWER_DECISIONS_JSONL_PATH",
        str(DATA_DIR / "control_tower_decisions.jsonl"),
    )
    daily_cost_json_path: str = os.getenv(
        "DAILY_COST_JSON_PATH", str(DATA_DIR / "daily_costs.json")
    )

    ops_alert_min_requests: int = int(os.getenv("OPS_ALERT_MIN_REQUESTS", "20"))
    ops_alert_refusal_ratio_threshold: float = float(
        os.getenv("OPS_ALERT_REFUSAL_RATIO_THRESHOLD", "0.2")
    )
    ops_alert_injection_ratio_threshold: float = float(
        os.getenv("OPS_ALERT_INJECTION_RATIO_THRESHOLD", "0.1")
    )
    ops_alert_daily_cost_threshold_usd: float = float(
        os.getenv("OPS_ALERT_DAILY_COST_THRESHOLD_USD", "50")
    )
    ops_alert_webhook_url: str = os.getenv("OPS_ALERT_WEBHOOK_URL", "").strip()
    ops_alert_webhook_timeout_sec: float = float(
        os.getenv("OPS_ALERT_WEBHOOK_TIMEOUT_SEC", "5")
    )


settings = Settings()
