import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.policy import PolicyService
from app.models import PolicyRule, PolicyAction, Sandbox, SandboxStatus


@pytest.mark.asyncio
async def test_policy_service_create(session: AsyncSession):
    service = PolicyService(session)
    policy = await service.create_policy({
        "name": "test-policy",
        "action": PolicyAction.ALLOW,
        "destination_host": "api.example.com",
        "priority": 10,
    })
    assert policy.id is not None
    assert policy.name == "test-policy"
    assert policy.action == PolicyAction.ALLOW


@pytest.mark.asyncio
async def test_policy_service_evaluate_connection_allow(session: AsyncSession):
    service = PolicyService(session)
    policy = await service.create_policy({
        "name": "allow-api",
        "action": PolicyAction.ALLOW,
        "destination_host": "api.example.com",
        "destination_port": 443,
        "enabled": True,
    })

    sandbox = Sandbox(
        name="test",
        sandbox_id="sb-test123",
        status=SandboxStatus.RUNNING,
        policy_id=policy.id,
    )
    session.add(sandbox)
    await session.flush()

    decision, matched_policy = await service.evaluate_connection(
        sandbox, "api.example.com", 443, "tcp"
    )
    assert decision == PolicyAction.ALLOW
    assert matched_policy is not None
    assert matched_policy.id == policy.id


@pytest.mark.asyncio
async def test_policy_service_evaluate_connection_deny_wrong_host(session: AsyncSession):
    service = PolicyService(session)
    policy = await service.create_policy({
        "name": "allow-api",
        "action": PolicyAction.ALLOW,
        "destination_host": "api.example.com",
        "enabled": True,
    })

    sandbox = Sandbox(
        name="test",
        sandbox_id="sb-test123",
        status=SandboxStatus.RUNNING,
        policy_id=policy.id,
    )
    session.add(sandbox)
    await session.flush()

    decision, matched_policy = await service.evaluate_connection(
        sandbox, "evil.com", 443, "tcp"
    )
    assert decision == PolicyAction.DENY
    assert matched_policy is None


@pytest.mark.asyncio
async def test_policy_service_evaluate_connection_deny_wrong_port(session: AsyncSession):
    service = PolicyService(session)
    policy = await service.create_policy({
        "name": "allow-api",
        "action": PolicyAction.ALLOW,
        "destination_host": "api.example.com",
        "destination_port": 443,
        "enabled": True,
    })

    sandbox = Sandbox(
        name="test",
        sandbox_id="sb-test123",
        status=SandboxStatus.RUNNING,
        policy_id=policy.id,
    )
    session.add(sandbox)
    await session.flush()

    decision, matched_policy = await service.evaluate_connection(
        sandbox, "api.example.com", 80, "tcp"
    )
    assert decision == PolicyAction.DENY
    assert matched_policy is None


@pytest.mark.asyncio
async def test_policy_service_evaluate_command_allow(session: AsyncSession):
    service = PolicyService(session)
    policy = await service.create_policy({
        "name": "allow-echo",
        "action": PolicyAction.ALLOW,
        "command_pattern": "echo *",
        "enabled": True,
    })

    sandbox = Sandbox(
        name="test",
        sandbox_id="sb-test123",
        status=SandboxStatus.RUNNING,
        policy_id=policy.id,
    )
    session.add(sandbox)
    await session.flush()

    decision, matched_policy = await service.evaluate_command(sandbox, "echo hello")
    assert decision == PolicyAction.ALLOW
    assert matched_policy is not None


@pytest.mark.asyncio
async def test_policy_service_evaluate_command_deny(session: AsyncSession):
    service = PolicyService(session)
    policy = await service.create_policy({
        "name": "deny-rm",
        "action": PolicyAction.DENY,
        "command_pattern": "rm *",
        "enabled": True,
    })

    sandbox = Sandbox(
        name="test",
        sandbox_id="sb-test123",
        status=SandboxStatus.RUNNING,
        policy_id=policy.id,
    )
    session.add(sandbox)
    await session.flush()

    decision, matched_policy = await service.evaluate_command(sandbox, "rm -rf /")
    assert decision == PolicyAction.DENY
    assert matched_policy is not None


@pytest.mark.asyncio
async def test_policy_service_no_policy_default_deny(session: AsyncSession):
    service = PolicyService(session)
    sandbox = Sandbox(
        name="test",
        sandbox_id="sb-test123",
        status=SandboxStatus.RUNNING,
        policy_id=None,
    )
    session.add(sandbox)
    await session.flush()

    decision, matched_policy = await service.evaluate_connection(sandbox, "api.example.com", 443)
    assert decision == PolicyAction.DENY
    assert matched_policy is None

    decision, matched_policy = await service.evaluate_command(sandbox, "echo hello")
    assert decision == PolicyAction.DENY
    assert matched_policy is None


@pytest.mark.asyncio
async def test_policy_service_audit_log(session: AsyncSession):
    service = PolicyService(session)
    audit = await service.log_audit(
        event_type="test_event",
        sandbox_id="sb-test123",
        policy_id=1,
        decision="allow",
        details='{"test": "data"}',
        trace_id="0af7651916cd43dd8448eb211c80319c",
    )
    assert audit.id is not None
    assert audit.event_type == "test_event"
    assert audit.sandbox_id == "sb-test123"
    assert audit.trace_id == "0af7651916cd43dd8448eb211c80319c"