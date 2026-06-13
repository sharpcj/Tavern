"""Audit log helpers."""

from __future__ import annotations

from django.contrib.contenttypes.models import ContentType

from .models import AuditLog


def write_audit_log(*, actor, action: str, target=None, reason: str = "", metadata: dict | None = None) -> AuditLog:
    """Create an audit log entry for a target object."""

    content_type = None
    object_id = None
    if target is not None:
        content_type = ContentType.objects.get_for_model(target.__class__)
        object_id = target.pk
    return AuditLog.objects.create(
        actor=actor,
        action=action,
        target_content_type=content_type,
        target_object_id=object_id,
        reason=reason,
        metadata=metadata or {},
    )
