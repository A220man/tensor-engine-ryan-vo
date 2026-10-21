import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_audit_log_created_on_policy_evaluation(client: AsyncClient, sample_sandbox_data, sample_policy_data):
    sample_policy_data["action"] = "allow"
    sample_policy_data["command_pattern"] = "echo *"
    policy_resp = await client.post("/api/v1/policies", json=sample_policy_data)
    policy_id = policy_resp.json()["id"]

    sample_sandbox_data["policy_id"] = policy_id
    sandbox_resp = await client.post("/api/v1/sandboxes", json=sample_sandbox_data)
    sandbox_id = sandbox_resp.json()["sandbox_id"]
    await client.post(f"/api/v1/sandboxes/{sandbox_id}/start")

    await client.post(
        f"/api/v1/sandboxes/{sandbox_id}/execute",
        json={"command": "echo", "args": ["test"]}
    )

    response = await client.get("/api/v1/audit?event_type=command_execution")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    log = data["items"][0]
    assert log["event_type"] == "command_execution"
    assert log["sandbox_id"] == sandbox_id
    assert log["decision"] == "allow"
    assert log["policy_id"] == policy_id


@pytest.mark.asyncio
async def test_audit_log_filter_by_sandbox(client: AsyncClient, sample_sandbox_data):
    sandbox_resp = await client.post("/api/v1/sandboxes", json=sample_sandbox_data)
    sandbox_id = sandbox_resp.json()["sandbox_id"]
    await client.post(f"/api/v1/sandboxes/{sandbox_id}/start")

    await client.post(f"/api/v1/sandboxes/{sandbox_id}/execute", json={"command": "echo", "args": ["1"]})

    response = await client.get(f"/api/v1/audit?sandbox_id={sandbox_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    for log in data["items"]:
        assert log["sandbox_id"] == sandbox_id


@pytest.mark.asyncio
async def test_audit_log_filter_by_event_type(client: AsyncClient, sample_sandbox_data):
    sandbox_resp = await client.post("/api/v1/sandboxes", json=sample_sandbox_data)
    sandbox_id = sandbox_resp.json()["sandbox_id"]
    await client.post(f"/api/v1/sandboxes/{sandbox_id}/start")

    await client.post(f"/api/v1/sandboxes/{sandbox_id}/execute", json={"command": "echo", "args": ["1"]})

    response = await client.get("/api/v1/audit?event_type=command_execution")
    assert response.status_code == 200
    data = response.json()
    for log in data["items"]:
        assert log["event_type"] == "command_execution"


@pytest.mark.asyncio
async def test_audit_log_pagination(client: AsyncClient, sample_sandbox_data):
    sandbox_resp = await client.post("/api/v1/sandboxes", json=sample_sandbox_data)
    sandbox_id = sandbox_resp.json()["sandbox_id"]
    await client.post(f"/api/v1/sandboxes/{sandbox_id}/start")

    for i in range(5):
        await client.post(f"/api/v1/sandboxes/{sandbox_id}/execute", json={"command": "echo", "args": [str(i)]})

    response = await client.get("/api/v1/audit?page=1&page_size=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["total_pages"] >= 3