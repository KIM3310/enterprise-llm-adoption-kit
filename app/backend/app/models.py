from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class AuthRequest(BaseModel):
    user_id: str
    role: str = Field(pattern="^(Employee|Ops|Admin)$")


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class Citation(BaseModel):
    doc_id: str
    field_path: str


class HandoverRequest(BaseModel):
    query: str
    citation_only: bool = False
    system: Optional[str] = None
    env: Optional[str] = None


class HandoverResponse(BaseModel):
    answer: str
    citations: List[Citation]


class LogIntelRequest(BaseModel):
    logs: str
    system: Optional[str] = None
    env: Optional[str] = None


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
    sub: str
    email: Optional[str] = None
    groups: List[str] = Field(default_factory=list)
    roles: List[str] = Field(default_factory=list)
    issuer: Optional[str] = None


class OIDCTokenExchangeRequest(BaseModel):
    id_token: str


class SlackEvent(BaseModel):
    user_id: str
    text: str
    channel: Optional[str] = None
    role: str = Field(default="Employee", pattern="^(Employee|Ops|Admin)$")


class JiraTicket(BaseModel):
    ticket_id: str
    title: str
    description: str
    priority: Optional[str] = "Medium"
    reporter: Optional[str] = None
    role: str = Field(default="Ops", pattern="^(Employee|Ops|Admin)$")


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
    scenario_id: str
    region: str = "us-east-1"
    notes: str = ""
    system: Optional[str] = None
    env: Optional[str] = None
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
