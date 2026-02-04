from typing import List, Optional
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
    groups: List[str] = []
    roles: List[str] = []
    issuer: Optional[str] = None


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
