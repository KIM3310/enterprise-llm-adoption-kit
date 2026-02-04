import os
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"


@dataclass(frozen=True)
class Settings:
    app_name: str = "Enterprise LLM Adoption Kit (Korea)"
    jwt_secret: str = os.getenv("JWT_SECRET", "dev-secret-change")
    jwt_issuer: str = os.getenv("JWT_ISSUER", "enterprise-llm-adoption-kit")
    jwt_ttl_minutes: int = int(os.getenv("JWT_TTL_MINUTES", "60"))

    llm_provider: str = os.getenv("LLM_PROVIDER", "stub")
    llm_model: str = os.getenv("LLM_MODEL", "stub-llm")
    llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))
    llm_max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "512"))

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

    sqlite_path: str = os.getenv("SQLITE_PATH", str(DATA_DIR / "app.db"))

    rate_limit_capacity: int = int(os.getenv("RATE_LIMIT_CAPACITY", "10"))
    rate_limit_refill_per_sec: float = float(
        os.getenv("RATE_LIMIT_REFILL_PER_SEC", "0.5")
    )

    data_handling_mode: str = os.getenv("DATA_HANDLING_MODE", "demo")
    audit_retention_days: int = int(os.getenv("AUDIT_RETENTION_DAYS", "30"))


settings = Settings()
