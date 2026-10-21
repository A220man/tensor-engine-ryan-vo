import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_policy(client: AsyncClient, sample_policy_data):
    response = await client.post("/api/v1/policies", json=sample_policy_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == sample_policy_data["name"]
    assert data["action"] == sample_policy_data["action"]
    assert data["destination_host"] == sample_policy_data["destination_host"]
    assert data["id"] > 0


@pytest.mark.asyncio
async def test_create_duplicate_policy(client: AsyncClient, sample_policy_data):
    await client.post("/api/v1/policies", json=sample_policy_data)
    response = await client.post("/api/v1/policies", json=sample_policy_data)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_list_policies(client: AsyncClient, sample_policy_data):
    await client.post("/api/v1/policies", json=sample_policy_data)
    response = await client.get("/api/v1/policies")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1
    assert data["page"] == 1
    assert "total_pages" in data


@pytest.mark.asyncio
async def test_list_policies_enabled_only(client: AsyncClient, sample_policy_data):
    sample_policy_data["enabled"] = False
    await client.post("/api/v1/policies", json=sample_policy_data)
    response = await client.get("/api/v1/policies?enabled_only=true")
    assert response.status_code == 200
    data = response.json()
    # Disabled policy should not appear in enabled_only
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_get_policy(client: AsyncClient, sample_policy_data):
    create_resp = await client.post("/api/v1/policies", json=sample_policy_data)
    policy_id = create_resp.json()["id"]

    response = await client.get(f"/api/v1/policies/{policy_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == policy_id
    assert data["name"] == sample_policy_data["name"]


@pytest.mark.asyncio
async def test_get_nonexistent_policy(client: AsyncClient):
    response = await client.get("/api/v1/policies/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_policy(client: AsyncClient, sample_policy_data):
    create_resp = await client.post("/api/v1/policies", json=sample_policy_data)
    policy_id = create_resp.json()["id"]

    response = await client.patch(f"/api/v1/policies/{policy_id}", json={"description": "Updated description"})
    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "Updated description"
    assert data["name"] == sample_policy_data["name"]


@pytest.mark.asyncio
async def test_delete_policy(client: AsyncClient, sample_policy_data):
    create_resp = await client.post("/api/v1/policies", json=sample_policy_data)
    policy_id = create_resp.json()["id"]

    response = await client.delete(f"/api/v1/policies/{policy_id}")
    assert response.status_code == 204

    get_resp = await client.get(f"/api/v1/policies/{policy_id}")
    assert get_resp.status_code == 404