"""
OCSF event conversion utilities for OpenShell observability.

This module provides functions to convert internal audit logs into OCSF
(Open Cybersecurity Schema Framework) events, enabling trace correlation
with OpenTelemetry traces.
"""

from typing import Dict, Any
from datetime import datetime, timezone
from app.models import AuditLog


# Mapping of internal event_type strings to OCSF event_type_uid values.
# These are example mappings; production deployments should reference
# the official OCSF taxonomy.
_EVENT_TYPE_UID_MAP = {
    "command_execution": 1001,
    "connection_request": 1002,
    # Add more mappings as needed.
}


def audit_log_to_ocsf(audit: AuditLog) -> Dict[str, Any]:
    """
    Convert an AuditLog model instance into an OCSF event dictionary.

    The resulting dictionary contains the required fields for an OCSF
    trace profile event, including the trace_uid derived from the audit's
    trace_id. All other fields are populated with sensible defaults.
    """
    # Determine OCSF event type UID; default to 0 if unknown.
    event_type_uid = _EVENT_TYPE_UID_MAP.get(
        audit.event_type, 0
    )

    # Build the OCSF event structure.
    ocsf_event: Dict[str, Any] = {
        "@timestamp": (
            audit.timestamp.isoformat()
            if audit.timestamp.tzinfo is None
            else audit.timestamp.isoformat()
        ),
        "event_id": str(audit.id),
        "event_uid": str(audit.id),
        "event_type_uid": event_type_uid,
        "category_uid": 0,  # Placeholder; use appropriate security category.
        "severity_id": "5",  # Medium severity; adjust based on decision.
        "product_uid": "openshell",
        "event_source": "openshell",
        "trace_uid": audit.trace_id or "",
        # Include original data for correlation.
        "original_event_type": audit.event_type,
        "original_decision": audit.decision,
        "original_details": audit.details,
        "original_sandbox_id": audit.sandbox_id,
    }

    return ocsf_event

