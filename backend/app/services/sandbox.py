import uuid
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Sandbox, SandboxStatus, Execution, PolicyRule, PolicyAction
from app.services.policy import PolicyService
from app.core.telemetry import get_tracer


class SandboxService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.policy_service = PolicyService(session)
        self.tracer = get_tracer(__name__)

    async def create_sandbox(self, name: str, policy_id: Optional[int] = None, config: Optional[str] = None) -> Sandbox:
        with self.tracer.start_as_current_span("sandbox.create") as span:
            sandbox_id = f"sb-{uuid.uuid4().hex[:12]}"
            sandbox = Sandbox(
                name=name,
                sandbox_id=sandbox_id,
                status=SandboxStatus.CREATING,
                policy_id=policy_id,
                config=config,
            )
            self.session.add(sandbox)
            await self.session.flush()
            # Load policy relationship if policy_id provided
            if policy_id:
                result = await self.session.execute(
                    select(Sandbox)
                    .options(selectinload(Sandbox.policy))
                    .where(Sandbox.id == sandbox.id)
                )
                sandbox = result.scalar_one()
            span.set_attribute("sandbox.id", sandbox.sandbox_id)
            span.set_attribute("sandbox.name", name)
            return sandbox
    async def get_sandbox(self, sandbox_id: str) -> Optional[Sandbox]:
        with self.tracer.start_as_current_span("sandbox.get") as span:
            span.set_attribute("sandbox.id", sandbox_id)
            result = await self.session.execute(
                select(Sandbox)
                .options(selectinload(Sandbox.policy))
                .where(Sandbox.sandbox_id == sandbox_id)
            )
            sandbox = result.scalar_one_or_none()
            if sandbox:
                # Force load the policy relationship
                _ = sandbox.policy
            return sandbox

    async def get_sandbox_by_id(self, id: int) -> Optional[Sandbox]:
        result = await self.session.execute(
            select(Sandbox)
            .options(selectinload(Sandbox.policy))
            .where(Sandbox.id == id)
        )
        sandbox = result.scalar_one_or_none()
        if sandbox:
            _ = sandbox.policy
        return sandbox

    async def list_sandboxes(
        self, status: Optional[SandboxStatus] = None, page: int = 1, page_size: int = 20
    ) -> tuple[List[Sandbox], int]:
        with self.tracer.start_as_current_span("sandbox.list") as span:
            query = select(Sandbox).options(selectinload(Sandbox.policy))
            if status:
                query = query.where(Sandbox.status == status)
            query = query.order_by(Sandbox.created_at.desc())

            count_query = select(Sandbox.id)
            if status:
                count_query = count_query.where(Sandbox.status == status)
            count_result = await self.session.execute(count_query)
            total = len(count_result.scalars().all())

            query = query.offset((page - 1) * page_size).limit(page_size)
            result = await self.session.execute(query)
            sandboxes = result.scalars().all()

            # Force load policy relationships
            for s in sandboxes:
                _ = s.policy

            span.set_attribute("sandbox.count", len(sandboxes))
            span.set_attribute("sandbox.total", total)
            return list(sandboxes), total

    async def start_sandbox(self, sandbox_id: str) -> Optional[Sandbox]:
        with self.tracer.start_as_current_span("sandbox.start") as span:
            sandbox = await self.get_sandbox(sandbox_id)
            if not sandbox:
                return None
            sandbox.status = SandboxStatus.RUNNING
            sandbox.started_at = datetime.now(timezone.utc)
            await self.session.flush()
            span.set_attribute("sandbox.id", sandbox.sandbox_id)
            span.set_attribute("sandbox.status", sandbox.status.value)
            return sandbox

    async def stop_sandbox(self, sandbox_id: str) -> Optional[Sandbox]:
        with self.tracer.start_as_current_span("sandbox.stop") as span:
            sandbox = await self.get_sandbox(sandbox_id)
            if not sandbox:
                return None
            sandbox.status = SandboxStatus.STOPPED
            sandbox.stopped_at = datetime.now(timezone.utc)
            await self.session.flush()
            span.set_attribute("sandbox.id", sandbox.sandbox_id)
            span.set_attribute("sandbox.status", sandbox.status.value)
            return sandbox

    async def terminate_sandbox(self, sandbox_id: str) -> Optional[Sandbox]:
        with self.tracer.start_as_current_span("sandbox.terminate") as span:
            sandbox = await self.get_sandbox(sandbox_id)
            if not sandbox:
                return None
            sandbox.status = SandboxStatus.TERMINATED
            sandbox.stopped_at = datetime.now(timezone.utc)
            await self.session.flush()
            span.set_attribute("sandbox.id", sandbox.sandbox_id)
            span.set_attribute("sandbox.status", sandbox.status.value)
            return sandbox

    async def update_sandbox(
        self, sandbox_id: str, name: Optional[str] = None, policy_id: Optional[int] = None, config: Optional[str] = None
    ) -> Optional[Sandbox]:
        with self.tracer.start_as_current_span("sandbox.update") as span:
            sandbox = await self.get_sandbox(sandbox_id)
            if not sandbox:
                return None
            if name is not None:
                sandbox.name = name
            if policy_id is not None:
                sandbox.policy_id = policy_id
            if config is not None:
                sandbox.config = config
            await self.session.flush()
            span.set_attribute("sandbox.id", sandbox.sandbox_id)
            return sandbox

    async def execute_command(
        self,
        sandbox_id: str,
        command: str,
        args: Optional[List[str]] = None,
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None,
    ) -> Execution:
        with self.tracer.start_as_current_span("sandbox.execute") as span:
            sandbox = await self.get_sandbox(sandbox_id)
            if not sandbox:
                raise ValueError(f"Sandbox {sandbox_id} not found")

            if sandbox.status != SandboxStatus.RUNNING:
                raise ValueError(f"Sandbox {sandbox_id} is not running (status: {sandbox.status.value})")

            # Build full command line for policy evaluation
            full_command = command
            if args:
                full_command = f"{command} {' '.join(args)}"

            # Evaluate policy
            decision, policy = await self.policy_service.evaluate_command(sandbox, full_command)
            span.set_attribute("policy.decision", decision.value)

            # Log audit
            await self.policy_service.log_audit(
                event_type="command_execution",
                sandbox_id=sandbox.sandbox_id,
                policy_id=policy.id if policy else None,
                decision=decision.value,
                details=f"command={full_command}",
                trace_id=trace_id,
            )
            if decision == PolicyAction.DENY:
                # Create execution record with denial
                execution = Execution(
                    sandbox_id=sandbox.id,
                    command=command,
                    args=str(args) if args else None,
                    stdout="",
                    stderr="Command denied by policy",
                    exit_code=-1,
                    trace_id=trace_id,
                    span_id=span_id,
                )
                self.session.add(execution)
                await self.session.flush()
                span.set_attribute("execution.denied", True)
                return execution

            # Simulate execution (in real implementation, this would run in container)
            execution = Execution(
                sandbox_id=sandbox.id,
                command=command,
                args=str(args) if args else None,
                stdout=f"Executed: {command} {' '.join(args) if args else ''}\n",
                stderr="",
                exit_code=0,
                trace_id=trace_id,
                span_id=span_id,
            )
            self.session.add(execution)
            await self.session.flush()
            span.set_attribute("execution.id", execution.id)
            span.set_attribute("execution.exit_code", 0)
            return execution

    async def get_executions(
        self, sandbox_id: str, page: int = 1, page_size: int = 20
    ) -> tuple[List[Execution], int]:
        sandbox = await self.get_sandbox(sandbox_id)
        if not sandbox:
            return [], 0

        with self.tracer.start_as_current_span("sandbox.get_executions") as span:
            query = select(Execution).where(Execution.sandbox_id == sandbox.id).order_by(Execution.started_at.desc())
            count_result = await self.session.execute(select(Execution.id).where(Execution.sandbox_id == sandbox.id))
            total = len(count_result.scalars().all())

            query = query.offset((page - 1) * page_size).limit(page_size)
            result = await self.session.execute(query)
            executions = result.scalars().all()

            span.set_attribute("execution.count", len(executions))
            return list(executions), total