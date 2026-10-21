from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.core.database import get_session
from app.services import PolicyService, SandboxService
from app.api.schemas import (
    PolicyRuleCreate, PolicyRuleUpdate, PolicyRuleResponse,
    SandboxCreate, SandboxUpdate, SandboxResponse,
    ExecutionCreate, ExecutionResponse,
    AuditLogResponse, PaginatedResponse,
)
from app.models import SandboxStatus, PolicyAction

router = APIRouter(prefix="/api/v1", tags=["sandboxes", "policies", "executions", "audit"])


# Policy Endpoints
@router.post("/policies", response_model=PolicyRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_policy(policy: PolicyRuleCreate, session: AsyncSession = Depends(get_session)):
    service = PolicyService(session)
    existing = await service.get_policy_by_name(policy.name)
    if existing:
        raise HTTPException(status_code=409, detail="Policy with this name already exists")
    return await service.create_policy(policy.model_dump())


@router.get("/policies", response_model=PaginatedResponse)
async def list_policies(
    enabled_only: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    service = PolicyService(session)
    policies, total = await service.list_policies(enabled_only, page, page_size)
    return PaginatedResponse(
        items=[PolicyRuleResponse.model_validate(p) for p in policies],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/policies/{policy_id}", response_model=PolicyRuleResponse)
async def get_policy(policy_id: int, session: AsyncSession = Depends(get_session)):
    service = PolicyService(session)
    policy = await service.get_policy(policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy


@router.patch("/policies/{policy_id}", response_model=PolicyRuleResponse)
async def update_policy(policy_id: int, updates: PolicyRuleUpdate, session: AsyncSession = Depends(get_session)):
    service = PolicyService(session)
    policy = await service.update_policy(policy_id, updates.model_dump(exclude_unset=True))
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy


@router.delete("/policies/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_policy(policy_id: int, session: AsyncSession = Depends(get_session)):
    service = PolicyService(session)
    deleted = await service.delete_policy(policy_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Policy not found")


# Sandbox Endpoints
@router.post("/sandboxes", response_model=SandboxResponse, status_code=status.HTTP_201_CREATED)
async def create_sandbox(sandbox: SandboxCreate, session: AsyncSession = Depends(get_session)):
    service = SandboxService(session)
    if sandbox.policy_id:
        policy_service = PolicyService(session)
        policy = await policy_service.get_policy(sandbox.policy_id)
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
    return await service.create_sandbox(sandbox.name, sandbox.policy_id, sandbox.config)


@router.get("/sandboxes", response_model=PaginatedResponse)
async def list_sandboxes(
    status: Optional[SandboxStatus] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    service = SandboxService(session)
    sandboxes, total = await service.list_sandboxes(status, page, page_size)
    return PaginatedResponse(
        items=[SandboxResponse.model_validate(s) for s in sandboxes],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/sandboxes/{sandbox_id}", response_model=SandboxResponse)
async def get_sandbox(sandbox_id: str, session: AsyncSession = Depends(get_session)):
    service = SandboxService(session)
    sandbox = await service.get_sandbox(sandbox_id)
    if not sandbox:
        raise HTTPException(status_code=404, detail="Sandbox not found")
    return sandbox


@router.post("/sandboxes/{sandbox_id}/start", response_model=SandboxResponse)
async def start_sandbox(sandbox_id: str, session: AsyncSession = Depends(get_session)):
    service = SandboxService(session)
    sandbox = await service.start_sandbox(sandbox_id)
    if not sandbox:
        raise HTTPException(status_code=404, detail="Sandbox not found")
    return sandbox


@router.post("/sandboxes/{sandbox_id}/stop", response_model=SandboxResponse)
async def stop_sandbox(sandbox_id: str, session: AsyncSession = Depends(get_session)):
    service = SandboxService(session)
    sandbox = await service.stop_sandbox(sandbox_id)
    if not sandbox:
        raise HTTPException(status_code=404, detail="Sandbox not found")
    return sandbox


@router.post("/sandboxes/{sandbox_id}/terminate", response_model=SandboxResponse)
async def terminate_sandbox(sandbox_id: str, session: AsyncSession = Depends(get_session)):
    service = SandboxService(session)
    sandbox = await service.terminate_sandbox(sandbox_id)
    if not sandbox:
        raise HTTPException(status_code=404, detail="Sandbox not found")
    return sandbox


@router.patch("/sandboxes/{sandbox_id}", response_model=SandboxResponse)
async def update_sandbox(sandbox_id: str, updates: SandboxUpdate, session: AsyncSession = Depends(get_session)):
    service = SandboxService(session)
    sandbox = await service.update_sandbox(
        sandbox_id, updates.name, updates.policy_id, updates.config
    )
    if not sandbox:
        raise HTTPException(status_code=404, detail="Sandbox not found")
    return sandbox


# Execution Endpoints
@router.post("/sandboxes/{sandbox_id}/execute", response_model=ExecutionResponse, status_code=status.HTTP_201_CREATED)
async def execute_command(
    sandbox_id: str,
    execution: ExecutionCreate,
    trace_id: Optional[str] = Query(None),
    span_id: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    service = SandboxService(session)
    try:
        result = await service.execute_command(
            sandbox_id, execution.command, execution.args, trace_id, span_id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sandboxes/{sandbox_id}/executions", response_model=PaginatedResponse)
async def list_executions(
    sandbox_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    service = SandboxService(session)
    executions, total = await service.get_executions(sandbox_id, page, page_size)
    return PaginatedResponse(
        items=[ExecutionResponse.model_validate(e) for e in executions],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


# Audit Log Endpoints
@router.get("/audit", response_model=PaginatedResponse)
async def list_audit_logs(
    event_type: Optional[str] = Query(None),
    sandbox_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    from sqlalchemy import select, desc
    from app.models import AuditLog

    query = select(AuditLog)
    if event_type:
        query = query.where(AuditLog.event_type == event_type)
    if sandbox_id:
        query = query.where(AuditLog.sandbox_id == sandbox_id)
    query = query.order_by(desc(AuditLog.timestamp))

    count_query = select(AuditLog.id)
    if event_type:
        count_query = count_query.where(AuditLog.event_type == event_type)
    if sandbox_id:
        count_query = count_query.where(AuditLog.sandbox_id == sandbox_id)
    count_result = await session.execute(count_query)
    total = len(count_result.scalars().all())

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(query)
    logs = result.scalars().all()

    return PaginatedResponse(
        items=[AuditLogResponse.model_validate(l) for l in logs],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )