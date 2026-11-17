import pytest
from app.models import AuditLog
from app.services.ocsevent import audit_log_to_ocsf
import json
import os


def test_ocsf_schema_exists():
    """Verify that the OCSF trace profile schema file exists."""
    schema_path = "./otel/trace-profile-schema.json"
    assert os.path.exists(schema_path), f"Schema file not found at {schema_path}"
    # Ensure it's valid JSON
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    assert "title" in schema, "Schema missing title field"
    assert schema["title"] == "OCSF Trace Profile", "Unexpected schema title"


def test_audit_log_to_ocsf_basic():
    """Test conversion of a basic audit log to OCSF event."""
    # Create a minimal AuditLog instance (no DB interaction needed)
    audit = AuditLog(
        id=42,
        event_type="command_execution",
        sandbox_id="sb-abc123",
        policy_id=7,
        decision="allow",
        details="executed echo hello",
        trace_id="0af7651916cd43dd8448eb211c80319c",
        timestamp="2025-01-01T12:00:00+00:00",
    )
    ocsf_event = audit_log_to_ocsf(audit)

    # Required OCSF fields
    assert ocsf_event["event_id"] == "42"
    assert ocsf_event["event_uid"] == "42"
    assert ocsf_event["event_type_uid"] == 1001  # from mapping
    assert ocsf_event["product_uid"] == "openshell"
    assert ocsf_event["event_source"] == "openshell"
    assert ocsf_event["trace_uid"] == "0af7651916cd43dd8448eb211c80319c"
    # Ensure original fields are preserved
    assert ocsf_event["original_event_type"] == "command_execution"
    assert ocsf_event["original_decision"] == "allow"
    assert ocsf_event["original_sandbox_id"] == "sb-abc123"


def test_audit_log_to_ocsf_missing_trace_id():
    """Test conversion when trace_id is None."""
    audit = AuditLog(
        id=99,
        event_type="connection_request",
        sandbox_id=None,
        policy_id=None,
        decision="deny",
        details="blocked inbound",
        trace_id=None,
        timestamp="2025-01-01T12:00:00+00:00",
    )
    ocsf_event = audit_log_to_ocsf(audit)

    assert ocsf_event["event_type_uid"] == 1002
    assert ocsf_event["trace_uid"] == ""


def test_audit_log_to_ocsf_unknown_event_type():
    """Test conversion for an unknown event_type."""
    audit = AuditLog(
        id=100,
        event_type="unknown_event",
        sandbox_id="sb-x",
        policy_id=None,
        decision="unknown",
        details="",
        trace_id="trace123",
        timestamp="2025-01-01T12:00:00+00:00",
    )
    ocsf_event = audit_log_to_ocsf(audit)

    assert ocsf_event["event_type_uid"] == 0  # default for unknown


