import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_execute_command_allowed(client: AsyncClient, sample_sandbox_data, sample_policy_data):
    # Create allow policy for command pattern
    sample_policy_data["action"] = "allow"
    sample_policy_data["command_pattern"] = "echo *"
    policy_resp = await client.post("/api/v1/policies", json=sample_policy_data)
    policy_id = policy_resp.json()["id"]

    # Create sandbox with policy
    sample_sandbox_data["policy_id"] = policy_id
    sandbox_resp = await client.post("/api/v1/sandboxes", json=sample_sandbox_data)
    sandbox_id = sandbox_resp.json()["sandbox_id"]

    # Start sandbox
    await client.post(f"/api/v1/sandboxes/{sandbox_id}/start")

    # Execute allowed command
    response = await client.post(
        f"/api/v1/sandboxes/{sandbox_id}/execute",
        json={"command": "echo", "args": ["hello", "world"]}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["command"] == "echo"
    assert data["exit_code"] == 0
    assert "hello world" in data["stdout"]


@pytest.mark.asyncio
async def test_execute_command_denied(client: AsyncClient, sample_sandbox_data, sample_policy_data):
    # Create deny policy for command pattern
    sample_policy_data["action"] = "deny"
    sample_policy_data["command_pattern"] = "rm *"
    policy_resp = await client.post("/api/v1/policies", json=sample_policy_data)
    policy_id = policy_resp.json()["id"]

    # Create sandbox with policy
    sample_sandbox_data["policy_id"] = policy_id
    sandbox_resp = await client.post("/api/v1/sandboxes", json=sample_sandbox_data)
    sandbox_id = sandbox_resp.json()["sandbox_id"]

    # Start sandbox
    await client.post(f"/api/v1/sandboxes/{sandbox_id}/start")

    # Execute denied command
    response = await client.post(
        f"/api/v1/sandboxes/{sandbox_id}/execute",
        json={"command": "rm", "args": ["-rf", "/"]}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["command"] == "rm"
    assert data["exit_code"] == -1
    assert "denied" in data["stderr"].lower()


@pytest.mark.asyncio
async def test_execute_command_no_policy_default_deny(client: AsyncClient, sample_sandbox_data):
    # Create sandbox without policy (default deny)
    sandbox_resp = await client.post("/api/v1/sandboxes", json=sample_sandbox_data)
    sandbox_id = sandbox_resp.json()["sandbox_id"]
    await client.post(f"/api/v1/sandboxes/{sandbox_id}/start")

    response = await client.post(
        f"/api/v1/sandboxes/{sandbox_id}/execute",
        json={"command": "echo", "args": ["hello"]}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["exit_code"] == -1
    assert "denied" in data["stderr"].lower()


@pytest.mark.asyncio
async def test_execute_command_sandbox_not_running(client: AsyncClient, sample_sandbox_data):
    sandbox_resp = await client.post("/api/v1/sandboxes", json=sample_sandbox_data)
    sandbox_id = sandbox_resp.json()["sandbox_id"]
    # Don't start sandbox

    response = await client.post(
        f"/api/v1/sandboxes/{sandbox_id}/execute",
        json={"command": "echo", "args": ["hello"]}
    )
    assert response.status_code == 400
    assert "not running" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_execute_command_with_trace_context(client: AsyncClient, sample_sandbox_data):
    sandbox_resp = await client.post("/api/v1/sandboxes", json=sample_sandbox_data)
    sandbox_id = sandbox_resp.json()["sandbox_id"]
    await client.post(f"/api/v1/sandboxes/{sandbox_id}/start")

    trace_id = "0af7651916cd43dd8448eb211c80319c"
    span_id = "1234567890abcdef"
    response = await client.post(
        f"/api/v1/sandboxes/{sandbox_id}/execute?trace_id={trace_id}&span_id={span_id}",
        json={"command": "echo", "args": ["traced"]}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["trace_id"] == trace_id
    assert data["span_id"] == span_id


@pytest.mark.asyncio
async def test_list_executions(client: AsyncClient, sample_sandbox_data):
    sandbox_resp = await client.post("/api/v1/sandboxes", json=sample_sandbox_data)
    sandbox_id = sandbox_resp.json()["sandbox_id"]
    await client.post(f"/api/v1/sandboxes/{sandbox_id}/start")

    # Execute a few commands
    await client.post(f"/api/v1/sandboxes/{sandbox_id}/execute", json={"command": "echo", "args": ["1"]})
    await client.post(f"/api/v1/sandboxes/{sandbox_id}/execute", json={"command": "echo", "args": ["2"]})

    response = await client.get(f"/api/v1/sandboxes/{sandbox_id}/executions")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2
    assert len(data["items"]) >= 2
    # Should be ordered by started_at desc
    assert data["items"][0]["started_at"] >= data["items"][1]["started_at"]