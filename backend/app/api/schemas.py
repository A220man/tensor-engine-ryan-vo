from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator
from app.models import SandboxStatus, PolicyAction

# Policy Schemas
class PolicyRuleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    action: PolicyAction = PolicyAction.DENY
    destination_host: Optional[str] = Field(None, max_length=255)
    destination_port: Optional[int] = Field(None, ge=1, le=65535)
    protocol: Optional[str] = Field(None, max_length=50)
    command_pattern: Optional[str] = Field(None, max_length=500)
    priority: int = 0
    enabled: bool = True


class PolicyRuleCreate(PolicyRuleBase):
    pass


class PolicyRuleUpdate(BaseModel):
    description: Optional[str] = None
    action: Optional[PolicyAction] = None
    destination_host: Optional[str] = Field(None, max_length=255)
    destination_port: Optional[int] = Field(None, ge=1, le=65535)
    protocol: Optional[str] = Field(None, max_length=50)
    command_pattern: Optional[str] = Field(None, max_length=500)
    priority: Optional[int] = None
    enabled: Optional[bool] = None


class PolicyRuleResponse(PolicyRuleBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime


# Sandbox Schemas
class SandboxBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    policy_id: Optional[int] = None
    config: Optional[str] = None


class SandboxCreate(SandboxBase):
    pass


class SandboxUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    policy_id: Optional[int] = None
    config: Optional[str] = None


class SandboxResponse(SandboxBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sandbox_id: str
    status: SandboxStatus
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    policy: Optional[PolicyRuleResponse] = None


# Execution Schemas
class ExecutionBase(BaseModel):
    command: str = Field(..., min_length=1)
    args: Optional[List[str]] = None


class ExecutionCreate(ExecutionBase):
    pass


class ExecutionResponse(ExecutionBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sandbox_id: int
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    exit_code: Optional[int] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None

    @field_validator('args', mode='before')
    @classmethod
    def parse_args(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        return v
# Audit Log Schemas
class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    event_type: str
    sandbox_id: Optional[str] = None
    policy_id: Optional[int] = None
    decision: Optional[str] = None
    details: Optional[str] = None
    trace_id: Optional[str] = None
    timestamp: datetime


# Health Schema
class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    database: str
    telemetry: str


# Pagination
class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int