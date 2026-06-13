"""Notification service helpers."""

from __future__ import annotations

from collections.abc import Iterable

from django.contrib.contenttypes.models import ContentType

from .models import Notification, NotificationType


def create_notification(*, recipient, notification_type: str, title: str, content: str = "", target=None) -> Notification:
    """Create a one-way system notification."""

    content_type = None
    object_id = None
    if target is not None:
        content_type = ContentType.objects.get_for_model(target.__class__)
        object_id = target.pk
    return Notification.objects.create(
        recipient=recipient,
        notification_type=notification_type,
        title=title,
        content=content,
        target_content_type=content_type,
        target_object_id=object_id,
    )


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


__all__ = ["NotificationType", "create_notification", "create_notifications"]
