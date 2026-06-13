"""Moderation service helpers."""

from __future__ import annotations

from django.utils import timezone

from apps.accounts.models import AccountStatus
from apps.activities.models import Activity, ActivityStatus
from apps.audit_logs.models import AuditAction
from apps.audit_logs.services import write_audit_log
from apps.common.enums import ContentStatus
from apps.moderation.models import ModerationAction, ModerationActionType
from apps.reports.models import ReportStatus


def get_content_owner(obj):
    """Return the owner/author user for a supported content object, if available."""

    for field in ("author", "uploader", "initiator"):
        if hasattr(obj, field):
            return getattr(obj, field)
    return None


def _save_status(obj, status_value: str) -> None:
    obj.status = status_value
    update_fields = ["status"]
    if hasattr(obj, "updated_at"):
        update_fields.append("updated_at")
    obj.save(update_fields=update_fields)


def apply_moderation_action(*, report, action_type: str, actor, reason: str = "") -> ModerationAction:
    """Apply a moderation action for a report and write audit logs."""

    content = report.content_object
    target_user = get_content_owner(content) if content is not None else None
    metadata = {"report_id": report.id, "content_type": str(report.content_type), "object_id": report.object_id}

    if action_type == ModerationActionType.HIDE_CONTENT and content is not None:
        if isinstance(content, Activity):
            content.status = ActivityStatus.CANCELLED
            content.save(update_fields=["status", "updated_at"])
        elif hasattr(content, "status"):
            _save_status(content, ContentStatus.HIDDEN)
        write_audit_log(actor=actor, action=AuditAction.CONTENT_HIDDEN, target=content, reason=reason, metadata=metadata)

    elif action_type == ModerationActionType.DELETE_CONTENT and content is not None:
        if hasattr(content, "soft_delete"):
            content.soft_delete(actor, reason=reason)
        elif isinstance(content, Activity):
            content.status = ActivityStatus.CANCELLED
            content.save(update_fields=["status", "updated_at"])
        write_audit_log(actor=actor, action=AuditAction.CONTENT_DELETED, target=content, reason=reason, metadata=metadata)

    elif action_type == ModerationActionType.WARN_USER:
        write_audit_log(actor=actor, action=AuditAction.USER_WARNED, target=target_user, reason=reason, metadata=metadata)

    elif action_type == ModerationActionType.RESTRICT_USER and target_user is not None:
        target_user.account_status = AccountStatus.RESTRICTED
        target_user.save(update_fields=["account_status", "updated_at"])
        write_audit_log(actor=actor, action=AuditAction.USER_RESTRICTED, target=target_user, reason=reason, metadata=metadata)

    elif action_type == ModerationActionType.BAN_USER and target_user is not None:
        target_user.account_status = AccountStatus.BANNED
        target_user.save(update_fields=["account_status", "updated_at"])
        write_audit_log(actor=actor, action=AuditAction.USER_BANNED, target=target_user, reason=reason, metadata=metadata)

    action = ModerationAction.objects.create(
        report=report,
        action_type=action_type,
        actor=actor,
        target_user=target_user,
        reason=reason,
        metadata=metadata,
    )
    report.status = ReportStatus.IGNORED if action_type == ModerationActionType.IGNORE else ReportStatus.RESOLVED
    report.handled_by = actor
    report.handled_at = timezone.now()
    report.handle_note = reason
    report.save(update_fields=["status", "handled_by", "handled_at", "handle_note", "updated_at"])
    write_audit_log(actor=actor, action=AuditAction.REPORT_HANDLED, target=report, reason=reason, metadata={"action_type": action_type})
    return action
