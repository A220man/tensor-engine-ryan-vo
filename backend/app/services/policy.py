from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import PolicyRule, PolicyAction, Sandbox, AuditLog
from app.core.telemetry import get_tracer


class PolicyService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.tracer = get_tracer(__name__)

    async def create_policy(self, policy_data: dict) -> PolicyRule:
        with self.tracer.start_as_current_span("policy.create") as span:
            policy = PolicyRule(**policy_data)
            self.session.add(policy)
            await self.session.flush()
            span.set_attribute("policy.id", policy.id)
            span.set_attribute("policy.name", policy.name)
            return policy

    async def get_policy(self, policy_id: int) -> Optional[PolicyRule]:
        with self.tracer.start_as_current_span("policy.get") as span:
            span.set_attribute("policy.id", policy_id)
            result = await self.session.execute(
                select(PolicyRule).where(PolicyRule.id == policy_id)
            )
            return result.scalar_one_or_none()

    async def get_policy_by_name(self, name: str) -> Optional[PolicyRule]:
        result = await self.session.execute(
            select(PolicyRule).where(PolicyRule.name == name)
        )
        return result.scalar_one_or_none()

    async def list_policies(
        self, enabled_only: bool = False, page: int = 1, page_size: int = 20
    ) -> tuple[List[PolicyRule], int]:
        with self.tracer.start_as_current_span("policy.list") as span:
            query = select(PolicyRule)
            if enabled_only:
                query = query.where(PolicyRule.enabled == True)
            query = query.order_by(PolicyRule.priority.desc(), PolicyRule.id)

            # Count total
            count_result = await self.session.execute(
                select(PolicyRule.id).where(
                    PolicyRule.enabled == True if enabled_only else True
                )
            )
            total = len(count_result.scalars().all())

            # Paginate
            query = query.offset((page - 1) * page_size).limit(page_size)
            result = await self.session.execute(query)
            policies = result.scalars().all()

            span.set_attribute("policy.count", len(policies))
            span.set_attribute("policy.total", total)
            return list(policies), total

    async def update_policy(self, policy_id: int, updates: dict) -> Optional[PolicyRule]:
        with self.tracer.start_as_current_span("policy.update") as span:
            span.set_attribute("policy.id", policy_id)
            policy = await self.get_policy(policy_id)
            if not policy:
                return None
            for key, value in updates.items():
                if hasattr(policy, key) and value is not None:
                    setattr(policy, key, value)
            await self.session.flush()
            return policy

    async def delete_policy(self, policy_id: int) -> bool:
        with self.tracer.start_as_current_span("policy.delete") as span:
            span.set_attribute("policy.id", policy_id)
            policy = await self.get_policy(policy_id)
            if not policy:
                return False
            await self.session.delete(policy)
            await self.session.flush()
            return True

    async def evaluate_connection(
        self,
        sandbox: Sandbox,
        destination_host: str,
        destination_port: int,
        protocol: str = "tcp",
    ) -> tuple[PolicyAction, Optional[PolicyRule]]:
        """Evaluate a connection request against sandbox's policy."""
        with self.tracer.start_as_current_span("policy.evaluate_connection") as span:
            span.set_attribute("sandbox.id", sandbox.sandbox_id)
            span.set_attribute("destination.host", destination_host)
            span.set_attribute("destination.port", destination_port)
            span.set_attribute("protocol", protocol)

            if not sandbox.policy_id:
                # No policy assigned, default deny
                span.set_attribute("policy.decision", "deny_default")
                return PolicyAction.DENY, None

            policy = await self.get_policy(sandbox.policy_id)
            if not policy or not policy.enabled:
                span.set_attribute("policy.decision", "deny_no_policy")
                return PolicyAction.DENY, None

            # Check if policy matches
            matches = True
            if policy.destination_host and policy.destination_host != destination_host:
                matches = False
            if policy.destination_port and policy.destination_port != destination_port:
                matches = False
            if policy.protocol and policy.protocol != protocol:
                matches = False

            decision = policy.action if matches else PolicyAction.DENY
            span.set_attribute("policy.decision", decision.value)
            span.set_attribute("policy.matched", matches)
            if policy.id:
                span.set_attribute("policy.matched_id", policy.id)

            return decision, policy if matches else None

    async def evaluate_command(
        self, sandbox: Sandbox, command: str
    ) -> tuple[PolicyAction, Optional[PolicyRule]]:
        """Evaluate a command execution against sandbox's policy."""
        with self.tracer.start_as_current_span("policy.evaluate_command") as span:
            span.set_attribute("sandbox.id", sandbox.sandbox_id)
            span.set_attribute("command", command[:100])

            if not sandbox.policy_id:
                span.set_attribute("policy.decision", "deny_default")
                return PolicyAction.DENY, None

            policy = await self.get_policy(sandbox.policy_id)
            if not policy or not policy.enabled:
                span.set_attribute("policy.decision", "deny_no_policy")
                return PolicyAction.DENY, None

            matches = True
            if policy.command_pattern:
                import fnmatch
                matches = fnmatch.fnmatch(command, policy.command_pattern)

            decision = policy.action if matches else PolicyAction.DENY
            span.set_attribute("policy.decision", decision.value)
            span.set_attribute("policy.matched", matches)
            if policy.id:
                span.set_attribute("policy.matched_id", policy.id)

            return decision, policy if matches else None

    async def log_audit(
        self,
        event_type: str,
        sandbox_id: Optional[str] = None,
        policy_id: Optional[int] = None,
        decision: Optional[str] = None,
        details: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> AuditLog:
        with self.tracer.start_as_current_span("policy.audit_log") as span:
            audit = AuditLog(
                event_type=event_type,
                sandbox_id=sandbox_id,
                policy_id=policy_id,
                decision=decision,
                details=details,
                trace_id=trace_id,
            )
            self.session.add(audit)
            await self.session.flush()
            span.set_attribute("audit.id", audit.id)
            span.set_attribute("audit.event_type", event_type)
            return audit