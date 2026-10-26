import uuid
import subprocess
import shlex
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy import select, func
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
        self.execution_timeout = 30  # seconds

    async def create_sandbox(self, name: str, policy_id: Optional[int] = None, config: Optional[str] = None) -> Sandbox:
        with self.tracer.start_as_current_span("sandbox.create") as span:
            sandbox_id = f"sb-{uuid.uuid4().hex[:12]}"
            sandbox = Sandbox(
                sandbox_id=sandbox_id,
                name=name,
                policy_id=policy_id,
                config=config,
                status=SandboxStatus.CREATING,
            )
            self.session.add(sandbox)
            await self.session.flush()
            # Reload with policy relationship if policy_id provided
            if policy_id:
                result = await self.session.execute(
                    select(Sandbox)
                    .where(Sandbox.id == sandbox.id)
                    .options(selectinload(Sandbox.policy))
                )
                sandbox = result.scalar_one()
            span.set_attribute("sandbox.id", sandbox_id)
            return sandbox

    async def get_sandbox(self, sandbox_id: str) -> Optional[Sandbox]:
        with self.tracer.start_as_current_span("sandbox.get") as span:
            result = await self.session.execute(
                select(Sandbox)
                .where(Sandbox.sandbox_id == sandbox_id)
                .options(selectinload(Sandbox.policy))
            )
            sandbox = result.scalar_one_or_none()
            if sandbox:
                span.set_attribute("sandbox.id", sandbox.sandbox_id)
            return sandbox

    async def get_sandbox_by_id(self, id: int) -> Optional[Sandbox]:
        result = await self.session.execute(
            select(Sandbox)
            .where(Sandbox.id == id)
            .options(selectinload(Sandbox.policy))
        )
        return result.scalar_one_or_none()

    async def list_sandboxes(
        self, status: Optional[SandboxStatus] = None, page: int = 1, page_size: int = 20
    ) -> tuple[List[Sandbox], int]:
        with self.tracer.start_as_current_span("sandbox.list") as span:
            query = select(Sandbox).options(selectinload(Sandbox.policy))
            count_query = select(func.count(Sandbox.id))

            if status:
                query = query.where(Sandbox.status == status)
                count_query = count_query.where(Sandbox.status == status)

            total_result = await self.session.execute(count_query)
            total = total_result.scalar_one()

            offset = (page - 1) * page_size
            query = query.order_by(Sandbox.created_at.desc()).offset(offset).limit(page_size)

            result = await self.session.execute(query)
            sandboxes = result.scalars().all()
            return list(sandboxes), total

    async def start_sandbox(self, sandbox_id: str) -> Optional[Sandbox]:
        with self.tracer.start_as_current_span("sandbox.start") as span:
            sandbox = await self.get_sandbox(sandbox_id)
            if not sandbox:
                return None
            if sandbox.status not in (SandboxStatus.CREATING, SandboxStatus.STOPPED, SandboxStatus.ERROR):
                raise ValueError(f"Cannot start sandbox in status {sandbox.status.value}")
            sandbox.status = SandboxStatus.RUNNING
            sandbox.started_at = datetime.now(timezone.utc)
            await self.session.flush()
            span.set_attribute("sandbox.id", sandbox.sandbox_id)
            return sandbox

    async def stop_sandbox(self, sandbox_id: str) -> Optional[Sandbox]:
        with self.tracer.start_as_current_span("sandbox.stop") as span:
            sandbox = await self.get_sandbox(sandbox_id)
            if not sandbox:
                return None
            if sandbox.status != SandboxStatus.RUNNING:
                raise ValueError(f"Cannot stop sandbox in status {sandbox.status.value}")
            sandbox.status = SandboxStatus.STOPPED
            sandbox.stopped_at = datetime.now(timezone.utc)
            await self.session.flush()
            span.set_attribute("sandbox.id", sandbox.sandbox_id)
            return sandbox

    async def terminate_sandbox(self, sandbox_id: str) -> Optional[Sandbox]:
        with self.tracer.start_as_current_span("sandbox.terminate") as span:
            sandbox = await self.get_sandbox(sandbox_id)
            if not sandbox:
                return None
            if sandbox.status == SandboxStatus.TERMINATED:
                return sandbox
            sandbox.status = SandboxStatus.TERMINATED
            await self.session.flush()
            span.set_attribute("sandbox.id", sandbox.sandbox_id)
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
            # Reload with policy relationship if policy_id changed
            if policy_id is not None:
                result = await self.session.execute(
                    select(Sandbox)
                    .where(Sandbox.id == sandbox.id)
                    .options(selectinload(Sandbox.policy))
                )
                sandbox = result.scalar_one()
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
                    completed_at=datetime.now(timezone.utc),
                )
                self.session.add(execution)
                await self.session.flush()
                span.set_attribute("execution.denied", True)
                return execution

            # Execute command using subprocess
            started_at = datetime.now(timezone.utc)
            try:
                # Build command list safely
                cmd_list = [command]
                if args:
                    cmd_list.extend(args)

                result = subprocess.run(
                    cmd_list,
                    capture_output=True,
                    text=True,
                    timeout=self.execution_timeout,
                    shell=False,
                )
                stdout = result.stdout
                stderr = result.stderr
                exit_code = result.returncode
            except subprocess.TimeoutExpired:
                stdout = ""
                stderr = f"Command timed out after {self.execution_timeout} seconds"
                exit_code = -2
            except FileNotFoundError:
                # Command not found - try with shell for builtins like echo
                try:
                    full_cmd = full_command
                    result = subprocess.run(
                        full_cmd,
                        capture_output=True,
                        text=True,
                        timeout=self.execution_timeout,
                        shell=True,
                    )
                    stdout = result.stdout
                    stderr = result.stderr
                    exit_code = result.returncode
                except Exception as e:
                    stdout = ""
                    stderr = f"Execution error: {str(e)}"
                    exit_code = -3
            except Exception as e:
                stdout = ""
                stderr = f"Execution error: {str(e)}"
                exit_code = -3

            completed_at = datetime.now(timezone.utc)

            execution = Execution(
                sandbox_id=sandbox.id,
                command=command,
                args=str(args) if args else None,
                stdout=stdout,
                stderr=stderr,
                exit_code=exit_code,
                trace_id=trace_id,
                span_id=span_id,
                completed_at=completed_at,
            )
            self.session.add(execution)
            await self.session.flush()
            span.set_attribute("execution.id", execution.id)
            span.set_attribute("execution.exit_code", exit_code)
            return execution

    async def get_executions(
        self, sandbox_id: str, page: int = 1, page_size: int = 20
    ) -> tuple[List[Execution], int]:
        sandbox = await self.get_sandbox(sandbox_id)
        if not sandbox:
            return [], 0

        query = select(Execution).where(Execution.sandbox_id == sandbox.id).order_by(Execution.started_at.desc())
        count_query = select(func.count(Execution.id)).where(Execution.sandbox_id == sandbox.id)

        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.session.execute(query)
        executions = result.scalars().all()
        return list(executions), total
