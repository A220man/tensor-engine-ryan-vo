"""Tests for the OTel traces export endpoint."""
import pytest
from fastapi.testclient import TestClient
from app.main import create_app


def test_traces_export_endpoint_returns_dict():
    """Test that the traces export endpoint returns a dict with trace context."""
    app = create_app()
    client = TestClient(app)

    response = client.post("/traces/export")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "trace_id" in data
    assert "span_id" in data
    assert "trace_state" in data
    assert "export_status" in data


def test_traces_export_has_proper_trace_id_format():
    """Test that trace_id is 32 hex chars (W3C format)."""
    app = create_app()
    client = TestClient(app)

    response = client.post("/traces/export")
    data = response.json()
    # trace_id should be 32 hex characters
    assert len(data["trace_id"]) == 32
    # All characters should be hex
    assert all(c in "0123456789abcdef" for c in data["trace_id"])


def test_traces_export_has_proper_span_id_format():
    """Test that span_id is 16 hex chars (W3C format)."""
    app = create_app()
    client = TestClient(app)

    response = client.post("/traces/export")
    data = response.json()
    # span_id should be 16 hex characters
    assert len(data["span_id"]) == 16
    # All characters should be hex
    assert all(c in "0123456789abcdef" for c in data["span_id"])


def test_traces_export_export_status_is_success():
    """Test that export_status field is 'success'."""
    app = create_app()
    client = TestClient(app)

    response = client.post("/traces/export")
    data = response.json()
    assert data["export_status"] == "success"
