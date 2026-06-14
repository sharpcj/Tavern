"""Notification and realtime event service helpers."""

from __future__ import annotations

from collections.abc import Iterable

from django.contrib.contenttypes.models import ContentType

from .models import Notification, NotificationType, RealtimeEvent, RealtimeEventType


def publish_event(
    *,
    event_type: str,
    target_type: str = "",
    target_id: int | str | None = None,
    payload: dict | None = None,
    recipient=None,
) -> RealtimeEvent:
    """Publish a minimal realtime event for SSE and reconnect backfill."""

    safe_payload = payload or {}
    return RealtimeEvent.objects.create(
        recipient=recipient,
        event_type=event_type,
        target_type=target_type,
        target_id="" if target_id is None else str(target_id),
        payload=safe_payload,
    )


def create_notification(*, recipient, notification_type: str, title: str, content: str = "", target=None) -> Notification:
    """Create a one-way system notification and publish a realtime refresh event."""

    content_type = None
    object_id = None
    if target is not None:
        content_type = ContentType.objects.get_for_model(target.__class__)
        object_id = target.pk
    notification = Notification.objects.create(
        recipient=recipient,
        notification_type=notification_type,
        title=title,
        content=content,
        target_content_type=content_type,
        target_object_id=object_id,
    )
    publish_event(
        recipient=recipient,
        event_type=RealtimeEventType.NOTIFICATION_CREATED,
        target_type="notification",
        target_id=notification.pk,
        payload={"notification_type": notification.notification_type},
    )
    return notification


def create_notifications(*, recipients: Iterable, notification_type: str, title: str, content: str = "", target=None) -> int:
    """Create notifications for multiple users and return created count."""

    count = 0
    for recipient in recipients:
        create_notification(
            recipient=recipient,
            notification_type=notification_type,
            title=title,
            content=content,
            target=target,
        )
        count += 1
    return count


__all__ = [
    "NotificationType",
    "RealtimeEventType",
    "create_notification",
    "create_notifications",
    "publish_event",
]
