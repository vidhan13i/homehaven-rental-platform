"""
Domain Event Envelope
=====================
Standardized event schema for all Kafka events in the HomeHaven platform.

Every event published to Kafka MUST use this envelope to ensure:
  - Traceability via event_id and correlation_id
  - Idempotent processing by consumers (deduplicate on event_id)
  - Service attribution via source_service
  - Schema versioning for backward compatibility
  - Millisecond-precision timestamps for ordering

Example:
    {
        "event_id": "550e8400-e29b-41d4-a716-446655440000",
        "event_type": "ApplicationApproved",
        "timestamp": "2026-07-04T21:00:00.123456Z",
        "source_service": "application_service",
        "aggregate_id": "uuid-of-application",
        "correlation_id": "uuid-linking-request-chain",
        "version": "1.0",
        "payload": {
            "application_id": "...",
            "renter_id": "...",
            "agent_id": "...",
            ...
        }
    }
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional


def build_event(
    event_type: str,
    aggregate_id: str,
    source_service: str,
    payload: Dict[str, Any],
    correlation_id: Optional[str] = None,
    version: str = "1.0",
) -> Dict[str, Any]:
    """
    Build a standardized domain event envelope.

    Args:
        event_type:      Human-readable event name e.g. "ApplicationApproved"
        aggregate_id:    UUID of the primary entity this event is about
        source_service:  Name of the service publishing the event
        payload:         Domain-specific data for this event
        correlation_id:  Optional request-chain ID for distributed tracing
        version:         Schema version (default "1.0")

    Returns:
        Dict ready to be JSON-serialized and published to Kafka
    """
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_service": source_service,
        "aggregate_id": str(aggregate_id),
        "correlation_id": correlation_id or str(uuid.uuid4()),
        "version": version,
        "payload": payload,
    }


def validate_event(event: Dict[str, Any]) -> bool:
    """
    Validate that a consumed event has all required envelope fields.

    Returns True if valid, False if malformed (consumer should send to DLQ).
    """
    required_fields = {
        "event_id",
        "event_type",
        "timestamp",
        "source_service",
        "aggregate_id",
        "payload",
    }
    return required_fields.issubset(event.keys())
