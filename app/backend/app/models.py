"""Pydantic request/response models for all API endpoints.

Every model enforces strict field validation (length, pattern, range)
at the serialization boundary to prevent malformed data from reaching
business logic.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

USER_ID_PATTERN = r"^[A-Za-z0-9._:@-]+$"
IDENTIFIER_PATTERN = r"^[A-Za-z0-9._:-]+$"
REGION_PATTERN = r"^[A-Za-z0-9._-]+$"


class AuthRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=128, pattern=USER_ID_PATTERN)
    role: str = Field(pattern="^(Employee|Ops|Admin)$")
    login_code: Optional[str] = Field(default=None, max_length=128)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class Citation(BaseModel):
    doc_id: str
    field_path: str


class HandoverRequest(BaseModel):
    query: str = Field(min_length=1, max_length=12000)
    citation_only: bool = False
    system: Optional[str] = Field(default=None, max_length=128)
    env: Optional[str] = Field(default=None, max_length=128)

    @field_validator("query")
    @classmethod
    def _query_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("query must not be blank")
        return value


class HandoverResponse(BaseModel):
    answer: str
    citations: List[Citation]


class LogIntelRequest(BaseModel):
    logs: str = Field(min_length=1, max_length=20000)
    system: Optional[str] = Field(default=None, max_length=128)
    env: Optional[str] = Field(default=None, max_length=128)

    @field_validator("logs")
    @classmethod
    def _logs_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("logs must not be blank")
        return value


class ToolCall(BaseModel):
    name: str
    input: dict
    status: str


class LogIntelResponse(BaseModel):
    summary: str
    root_causes: List[str]
    runbook_steps: List[str]
    tool_calls: List[ToolCall]


class UserContext(BaseModel):
    user_id: str
    roles: List[str]


class OIDCLoginRequest(BaseModel):
    sub: str = Field(min_length=1, max_length=256)
    email: Optional[str] = Field(default=None, max_length=256)
    groups: List[str] = Field(default_factory=list)
    roles: List[str] = Field(default_factory=list)
    issuer: Optional[str] = Field(default=None, max_length=256)

    @field_validator("sub")
    @classmethod
    def _sub_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("sub must not be blank")
        return value


class OIDCTokenExchangeRequest(BaseModel):
    id_token: str = Field(min_length=20, max_length=8192)


class SlackEvent(BaseModel):
    user_id: str = Field(min_length=1, max_length=128, pattern=USER_ID_PATTERN)
    text: str = Field(min_length=1, max_length=4000)
    channel: Optional[str] = Field(default=None, max_length=128)
    role: str = Field(default="Employee", pattern="^(Employee|Ops|Admin)$")

    @field_validator("text")
    @classmethod
    def _text_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("text must not be blank")
        return value


class JiraTicket(BaseModel):
    ticket_id: str = Field(min_length=1, max_length=64, pattern=IDENTIFIER_PATTERN)
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=12000)
    priority: Optional[str] = Field(default="Medium", max_length=32)
    reporter: Optional[str] = Field(default=None, max_length=128, pattern=USER_ID_PATTERN)
    role: str = Field(default="Ops", pattern="^(Employee|Ops|Admin)$")

    @field_validator("title", "description")
    @classmethod
    def _jira_fields_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("jira field must not be blank")
        return value


class PlatformTargets(BaseModel):
    aws: bool = True
    databricks: bool = True
    snowflake: bool = True
    palantir: bool = True
    mariadb: bool = True


class ControlTowerSignals(BaseModel):
    demand_delta_ratio: float = Field(
        description="Forecast demand delta ratio vs baseline. Range -1.0 to 1.0.",
        ge=-1.0,
        le=1.0,
    )
    inventory_days: float = Field(
        description="Estimated days of inventory coverage.",
        ge=0.0,
    )
    machine_anomaly_score: float = Field(
        description="Anomaly score from model output. Range 0.0 to 1.0.",
        ge=0.0,
        le=1.0,
    )
    sla_breach_risk: float = Field(
        description="Predicted probability of SLA breach. Range 0.0 to 1.0.",
        ge=0.0,
        le=1.0,
    )
    unit_margin_ratio: float = Field(
        description="Current unit margin ratio. Range -1.0 to 1.0.",
        ge=-1.0,
        le=1.0,
    )
    gpu_utilization: float = Field(
        description="GPU utilization ratio for inference/training pools. Range 0.0 to 1.0.",
        ge=0.0,
        le=1.0,
    )


class ControlTowerDecisionRequest(BaseModel):
    scenario_id: str = Field(min_length=1, max_length=128, pattern=IDENTIFIER_PATTERN)
    region: str = Field(default="us-east-1", min_length=1, max_length=64, pattern=REGION_PATTERN)
    notes: str = Field(default="", max_length=8000)
    system: Optional[str] = Field(default=None, max_length=128)
    env: Optional[str] = Field(default=None, max_length=128)
    signals: ControlTowerSignals
    targets: PlatformTargets = Field(default_factory=PlatformTargets)


class CoTStep(BaseModel):
    step: str
    summary: str


class ExecutionTask(BaseModel):
    platform: str
    action: str
    priority: str
    payload: Dict[str, str]


class ControlTowerDecisionResponse(BaseModel):
    decision_id: str
    risk_score: float
    risk_level: str
    factor_breakdown: Dict[str, float]
    primary_actions: List[str]
    execution_plan: List[ExecutionTask]
    cot_trace: List[CoTStep]
    spec_version: str
    policy_events: Dict[str, bool]


class ControlTowerSpecResponse(BaseModel):
    spec_version: str
    validation_ok: bool
    validation_error: Optional[str] = None
    spec: Dict


class OpsAlert(BaseModel):
    code: str
    severity: str
    message: str
    value: Optional[float] = None
    threshold: Optional[float] = None


class OpsAlertsResponse(BaseModel):
    requests: int
    daily_cost_usd: float
    alerts: List[OpsAlert]
    webhook_sent: int = 0
    webhook_failed: int = 0


class OpsServiceEvent(BaseModel):
    id: int
    created_at: str
    level: str
    component: str
    message: str
    context: Dict = Field(default_factory=dict)


class OpsRecentDecision(BaseModel):
    decision_id: str
    created_at: str
    scenario_id: str
    user_id: str
    role: str
    risk_score: float
    risk_level: str
    spec_version: str
    refusal: bool


class OpsRuntimeResponse(BaseModel):
    startup_status: str
    startup_report: Dict
    audit_summary: Dict
    daily_cost_usd: float
    alerts: List[OpsAlert]
    service_events: List[OpsServiceEvent]
    recent_decisions: List[OpsRecentDecision]


class OpsDiagnosticsRefreshResponse(BaseModel):
    startup_status: str
    startup_report: Dict


class ServiceBriefArtifact(BaseModel):
    label: str
    path: str
    kind: str = Field(pattern="^(doc|test|dataset|report|endpoint)$")


class ServiceBriefStage(BaseModel):
    key: str = Field(pattern="^(discovery|security|evals|deployment|operations)$")
    label: str
    readiness: str = Field(pattern="^(ready|in_progress|attention)$")
    artifact_count: int = Field(ge=0)
    highlights: List[ServiceBriefArtifact] = Field(default_factory=list)


class ServiceBriefReviewStep(BaseModel):
    order: int = Field(ge=1)
    title: str
    endpoint: str
    evidence_path: Optional[str] = None
    persona: str = Field(pattern="^(stakeholder|operator|security|platform|exec)$")


class ServiceBriefRuntime(BaseModel):
    auth_mode: str
    data_handling_mode: str
    storage_backend: str
    llm_provider: str
    llm_model: str
    openai_api_key_configured: bool
    login_code_required: bool
    integrations_require_auth: bool
    startup_status: str
    startup_ready: bool
    llm_circuit_state: str
    deploymentMode: str = Field(
        pattern="^(public-capped-live|review-only-live|artifact-refresh-only)$"
    )
    publicLiveApi: bool
    liveModel: str
    dailyBudgetUsd: float = Field(ge=0.0)
    monthlyBudgetUsd: float = Field(ge=0.0)
    killSwitch: bool
    moderationEnabled: bool


class ServiceBriefEvidence(BaseModel):
    test_files: int = Field(ge=0)
    blueprint_docs: int = Field(ge=0)
    module_packs: int = Field(ge=0)
    eval_datasets: int = Field(ge=0)
    eval_reports: int = Field(ge=0)
    application_artifacts: int = Field(ge=0)
    resource_packs: int = Field(ge=0)


class ServiceBriefRolePath(BaseModel):
    role: str
    goal: str
    first_surface: str
    follow_up: str
    proof_assets: List[str] = Field(default_factory=list)


class ServiceBriefResponse(BaseModel):
    service: str
    contract_version: str
    tagline: str
    maturity_stage: str
    audiences: List[str] = Field(default_factory=list)
    runtime: ServiceBriefRuntime
    evidence: ServiceBriefEvidence
    run_modes: List[str] = Field(default_factory=list)
    platform_targets: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    watchouts: List[str] = Field(default_factory=list)
    role_paths: List[ServiceBriefRolePath] = Field(default_factory=list)
    stages: List[ServiceBriefStage] = Field(default_factory=list)
    review_flow: List[ServiceBriefReviewStep] = Field(default_factory=list)
    links: Dict[str, str] = Field(default_factory=dict)


class AdminLLMRuntimeView(BaseModel):
    provider: str
    model: str
    temperature: float
    max_tokens: int
    timeout_sec: float
    openai_base_url: str
    ollama_base_url: str
    openai_org: str
    openai_api_key_configured: bool


class AdminLLMRuntimeUpdate(BaseModel):
    provider: Optional[str] = Field(default=None, pattern="^(stub|openai|openai_compatible|ollama|bedrock)$")
    model: Optional[str] = None
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1, le=8192)
    timeout_sec: Optional[float] = Field(default=None, ge=1.0, le=600.0)
    openai_base_url: Optional[str] = None
    ollama_base_url: Optional[str] = None
    openai_org: Optional[str] = None
    openai_api_key: Optional[str] = None
    reset_to_env: bool = False


class UserLLMApiKeyUpdate(BaseModel):
    openai_api_key: str = Field(min_length=20, max_length=512)


class UserLLMApiKeyView(BaseModel):
    user_id: str
    openai_api_key_configured: bool
    effective_provider: str
    effective_model: str
    effective_openai_base_url: str


class ArchitectureImportRequest(BaseModel):
    jsonl: str = Field(min_length=2)


class ArchitectureCatalogResponse(BaseModel):
    source_path: str
    doc_count: int
    chunk_count: int
    systems: List[str]
    envs: List[str]
    access_groups: List[str]
