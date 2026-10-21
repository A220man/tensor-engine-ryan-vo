import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.sandbox import SandboxService
from app.models import Sandbox, SandboxStatus, Execution, PolicyRule, PolicyAction


@pytest.mark.asyncio
async def test_sandbox_service_create(session: AsyncSession):
    service = SandboxService(session)
    sandbox = await service.create_sandbox("test-sandbox", policy_id=None, config='{"mem": "512m"}')
    assert sandbox.id is not None
    assert sandbox.name == "test-sandbox"
    assert sandbox.sandbox_id.startswith("sb-")
    assert sandbox.status == SandboxStatus.CREATING


@pytest.mark.asyncio
async def test_sandbox_service_get(session: AsyncSession):
    service = SandboxService(session)
    created = await service.create_sandbox("test-sandbox")
    found = await service.get_sandbox(created.sandbox_id)
    assert found is not None
    assert found.id == created.id
    assert found.sandbox_id == created.sandbox_id


@pytest.mark.asyncio
async def test_sandbox_service_list(session: AsyncSession):
    service = SandboxService(session)
    await service.create_sandbox("sandbox-1")
    await service.create_sandbox("sandbox-2")

    sandboxes, total = await service.list_sandboxes(page=1, page_size=10)
    assert total == 2
    assert len(sandboxes) == 2


@pytest.mark.asyncio
async def test_sandbox_service_list_filter_status(session: AsyncSession):
    service = SandboxService(session)
    s1 = await service.create_sandbox("sandbox-1")
    await service.create_sandbox("sandbox-2")
    await service.start_sandbox(s1.sandbox_id)

    sandboxes, total = await service.list_sandboxes(status=SandboxStatus.RUNNING)
    assert total == 1
    assert len(sandboxes) == 1
    assert sandboxes[0].status == SandboxStatus.RUNNING


@pytest.mark.asyncio
async def test_sandbox_service_start_stop_terminate(session: AsyncSession):
    service = SandboxService(session)
    sandbox = await service.create_sandbox("test-sandbox")

    started = await service.start_sandbox(sandbox.sandbox_id)
    assert started.status == SandboxStatus.RUNNING
    assert started.started_at is not None

    stopped = await service.stop_sandbox(sandbox.sandbox_id)
    assert stopped.status == SandboxStatus.STOPPED
    assert stopped.stopped_at is not None

    terminated = await service.terminate_sandbox(sandbox.sandbox_id)
    assert terminated.status == SandboxStatus.TERMINATED


@pytest.mark.asyncio
async def test_sandbox_service_update(session: AsyncSession):
    service = SandboxService(session)
    sandbox = await service.create_sandbox("original-name")

    updated = await service.update_sandbox(sandbox.sandbox_id, name="new-name", config='{"cpu": "1"}')
    assert updated.name == "new-name"
    assert updated.config == '{"cpu": "1"}'


@pytest.mark.asyncio
async def test_sandbox_service_execute_allowed(session: AsyncSession):
    from app.services.policy import PolicyService

    policy_service = PolicyService(session)
    policy = await policy_service.create_policy({
        "name": "allow-echo",
        "action": PolicyAction.ALLOW,
        "command_pattern": "echo *",
        "enabled": True,
    })

    service = SandboxService(session)
    sandbox = await service.create_sandbox("test-sandbox", policy_id=policy.id)
    await service.start_sandbox(sandbox.sandbox_id)

    execution = await service.execute_command(sandbox.sandbox_id, "echo hello world")
    assert execution.exit_code == 0
    assert "hello world" in execution.stdout


@pytest.mark.asyncio
async def test_sandbox_service_execute_denied(session: AsyncSession):
    from app.services.policy import PolicyService

    policy_service = PolicyService(session)
    policy = await policy_service.create_policy({
        "name": "deny-rm",
        "action": PolicyAction.DENY,
        "command_pattern": "rm *",
        "enabled": True,
    })

    service = SandboxService(session)
    sandbox = await service.create_sandbox("test-sandbox", policy_id=policy.id)
    await service.start_sandbox(sandbox.sandbox_id)

    execution = await service.execute_command(sandbox.sandbox_id, "rm -rf /")
    assert execution.exit_code == -1
    assert "denied" in execution.stderr.lower()


@pytest.mark.asyncio
async def test_sandbox_service_execute_not_running(session: AsyncSession):
    service = SandboxService(session)
    sandbox = await service.create_sandbox("test-sandbox")
    # Don't start

    with pytest.raises(ValueError, match="not running"):
        await service.execute_command(sandbox.sandbox_id, "echo hello")


@pytest.mark.asyncio
async def test_sandbox_service_execute_with_trace(session: AsyncSession):
    service = SandboxService(session)
    sandbox = await service.create_sandbox("test-sandbox")
    await service.start_sandbox(sandbox.sandbox_id)

    execution = await service.execute_command(
        sandbox.sandbox_id,
        "echo traced",
        trace_id="0af7651916cd43dd8448eb211c80319c",
        span_id="1234567890abcdef",
    )
    assert execution.trace_id == "0af7651916cd43dd8448eb211c80319c"
    assert execution.span_id == "1234567890abcdef"


@pytest.mark.asyncio
async def test_sandbox_service_get_executions(session: AsyncSession):
    from app.services.policy import PolicyService

    policy_service = PolicyService(session)
    policy = await policy_service.create_policy({
        "name": "allow-echo",
        "action": PolicyAction.ALLOW,
        "command_pattern": "echo *",
        "enabled": True,
    })

    service = SandboxService(session)
    sandbox = await service.create_sandbox("test-sandbox", policy_id=policy.id)
    await service.start_sandbox(sandbox.sandbox_id)

    await service.execute_command(sandbox.sandbox_id, "echo 1")
    await service.execute_command(sandbox.sandbox_id, "echo 2")

    executions, total = await service.get_executions(sandbox.sandbox_id, page=1, page_size=10)
    assert total == 2
    assert len(executions) == 2
    # Should be ordered by started_at desc
    assert executions[0].started_at >= executions[1].started_at