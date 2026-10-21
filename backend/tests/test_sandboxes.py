import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_sandbox(client: AsyncClient, sample_sandbox_data):
    response = await client.post("/api/v1/sandboxes", json=sample_sandbox_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == sample_sandbox_data["name"]
    assert data["sandbox_id"].startswith("sb-")
    assert data["status"] == "creating"
    assert data["id"] > 0


@pytest.mark.asyncio
async def test_create_sandbox_with_policy(client: AsyncClient, sample_policy_data, sample_sandbox_data):
    policy_resp = await client.post("/api/v1/policies", json=sample_policy_data)
    policy_id = policy_resp.json()["id"]

    sample_sandbox_data["policy_id"] = policy_id
    response = await client.post("/api/v1/sandboxes", json=sample_sandbox_data)
    assert response.status_code == 201
    data = response.json()
    assert data["policy"] is not None
    assert data["policy"]["id"] == policy_id


@pytest.mark.asyncio
async def test_create_sandbox_invalid_policy(client: AsyncClient, sample_sandbox_data):
    sample_sandbox_data["policy_id"] = 99999
    response = await client.post("/api/v1/sandboxes", json=sample_sandbox_data)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_sandboxes(client: AsyncClient, sample_sandbox_data):
    await client.post("/api/v1/sandboxes", json=sample_sandbox_data)
    response = await client.get("/api/v1/sandboxes")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1


@pytest.mark.asyncio
async def test_list_sandboxes_filter_status(client: AsyncClient, sample_sandbox_data):
    await client.post("/api/v1/sandboxes", json=sample_sandbox_data)
    response = await client.get("/api/v1/sandboxes?status=creating")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    for item in data["items"]:
        assert item["status"] == "creating"


@pytest.mark.asyncio
async def test_get_sandbox(client: AsyncClient, sample_sandbox_data):
    create_resp = await client.post("/api/v1/sandboxes", json=sample_sandbox_data)
    sandbox_id = create_resp.json()["sandbox_id"]

    response = await client.get(f"/api/v1/sandboxes/{sandbox_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["sandbox_id"] == sandbox_id


@pytest.mark.asyncio
async def test_get_nonexistent_sandbox(client: AsyncClient):
    response = await client.get("/api/v1/sandboxes/sb-nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_start_sandbox(client: AsyncClient, sample_sandbox_data):
    create_resp = await client.post("/api/v1/sandboxes", json=sample_sandbox_data)
    sandbox_id = create_resp.json()["sandbox_id"]

    response = await client.post(f"/api/v1/sandboxes/{sandbox_id}/start")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert data["started_at"] is not None


@pytest.mark.asyncio
async def test_stop_sandbox(client: AsyncClient, sample_sandbox_data):
    create_resp = await client.post("/api/v1/sandboxes", json=sample_sandbox_data)
    sandbox_id = create_resp.json()["sandbox_id"]
    await client.post(f"/api/v1/sandboxes/{sandbox_id}/start")

    response = await client.post(f"/api/v1/sandboxes/{sandbox_id}/stop")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "stopped"
    assert data["stopped_at"] is not None


@pytest.mark.asyncio
async def test_terminate_sandbox(client: AsyncClient, sample_sandbox_data):
    create_resp = await client.post("/api/v1/sandboxes", json=sample_sandbox_data)
    sandbox_id = create_resp.json()["sandbox_id"]

    response = await client.post(f"/api/v1/sandboxes/{sandbox_id}/terminate")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "terminated"


@pytest.mark.asyncio
async def test_update_sandbox(client: AsyncClient, sample_sandbox_data):
    create_resp = await client.post("/api/v1/sandboxes", json=sample_sandbox_data)
    sandbox_id = create_resp.json()["sandbox_id"]

    response = await client.patch(f"/api/v1/sandboxes/{sandbox_id}", json={"name": "updated-name"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "updated-name"