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
@pytest.mark.asyncio
async def test_evaluate_connection_endpoint_allow(client: AsyncClient, sample_sandbox_data, sample_policy_data):
    """Test the evaluate-connection API endpoint with allowed connection."""
    sample_policy_data["action"] = "allow"
    sample_policy_data["destination_host"] = "*.example.com"
    policy_resp = await client.post("/api/v1/policies", json=sample_policy_data)
    policy_id = policy_resp.json()["id"]

    sample_sandbox_data["policy_id"] = policy_id
    sandbox_resp = await client.post("/api/v1/sandboxes", json=sample_sandbox_data)
    sandbox_id = sandbox_resp.json()["sandbox_id"]

    # Test matching subdomain
    response = await client.post(
        f"/api/v1/sandboxes/{sandbox_id}/evaluate-connection",
        json={"destination_host": "api.example.com", "destination_port": 443, "protocol": "tcp"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "allow"
    assert data["matched"] is True
    assert data["policy_id"] == policy_id
    assert data["policy_name"] == sample_policy_data["name"]

    # Test non-matching domain
    response = await client.post(
        f"/api/v1/sandboxes/{sandbox_id}/evaluate-connection",
        json={"destination_host": "evil.com", "destination_port": 443, "protocol": "tcp"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "deny"
    assert data["matched"] is False
    assert data["policy_id"] is None


@pytest.mark.asyncio
async def test_evaluate_connection_endpoint_no_policy(client: AsyncClient, sample_sandbox_data):
    """Test the evaluate-connection API endpoint with no policy (default deny)."""
    sandbox_resp = await client.post("/api/v1/sandboxes", json=sample_sandbox_data)
    sandbox_id = sandbox_resp.json()["sandbox_id"]

    response = await client.post(
        f"/api/v1/sandboxes/{sandbox_id}/evaluate-connection",
        json={"destination_host": "api.example.com", "destination_port": 443, "protocol": "tcp"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "deny"
    assert data["matched"] is False
    assert data["policy_id"] is None


@pytest.mark.asyncio
async def test_evaluate_connection_endpoint_sandbox_not_found(client: AsyncClient):
    """Test the evaluate-connection API endpoint with non-existent sandbox."""
    response = await client.post(
        "/api/v1/sandboxes/non-existent/evaluate-connection",
        json={"destination_host": "api.example.com", "destination_port": 443, "protocol": "tcp"}
    )
    assert response.status_code == 400

