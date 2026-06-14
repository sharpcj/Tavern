"""System notification models.

Notifications are one-way system messages. They are not private messages,
conversations, or chat groups.
"""

from __future__ import annotations

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class NotificationType(models.TextChoices):
    REVIEW_RESULT = "review_result", "审核结果"
    ANNOUNCEMENT = "announcement", "公告通知"
    COMMENT_REPLY = "comment_reply", "评论回复"
    ACTIVITY_STATUS = "activity_status", "活动状态"
    SYSTEM = "system", "系统通知"


class RealtimeEventType(models.TextChoices):
    POST_CREATED = "post.created", "动态发布"
    POST_UPDATED = "post.updated", "动态更新"
    COMMENT_CREATED = "comment.created", "动态评论"
    ALBUM_PHOTO_CREATED = "album.photo.created", "相册照片上传"
    PHOTO_COMMENT_CREATED = "photo.comment.created", "照片评论"
    ANNOUNCEMENT_CREATED = "announcement.created", "公告发布"
    ACTIVITY_UPDATED = "activity.updated", "活动更新"
    NOTIFICATION_CREATED = "notification.created", "系统通知创建"
    NOTIFICATION_READ = "notification.read", "系统通知已读"


class RealtimeEvent(models.Model):
    """Short-lived realtime event used by SSE and reconnect backfill."""

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="realtime_events",
        verbose_name="接收人",
    )
    event_type = models.CharField("事件类型", max_length=64, choices=RealtimeEventType.choices, db_index=True)
    target_type = models.CharField("目标类型", max_length=64, blank=True)
    target_id = models.CharField("目标 ID", max_length=64, blank=True)
    payload = models.JSONField("事件载荷", default=dict, blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "实时事件"
        verbose_name_plural = "实时事件"
        ordering = ["id"]
        indexes = [
            models.Index(fields=["recipient", "id"]),
            models.Index(fields=["event_type", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"RealtimeEvent({self.event_type}, {self.target_type}:{self.target_id})"


class Notification(models.Model):
    """One-way system notification for a user."""

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="接收人",
    )
    notification_type = models.CharField("通知类型", max_length=32, choices=NotificationType.choices, db_index=True)
    title = models.CharField("标题", max_length=120)
    content = models.TextField("内容", blank=True)
    target_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notification_targets",
        verbose_name="关联对象类型",
    )
    target_object_id = models.PositiveIntegerField("关联对象 ID", null=True, blank=True)
    target_object = GenericForeignKey("target_content_type", "target_object_id")
    is_read = models.BooleanField("是否已读", default=False, db_index=True)
    read_at = models.DateTimeField("已读时间", null=True, blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "系统通知"
        verbose_name_plural = "系统通知"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["recipient", "is_read", "-created_at"])]

    def __str__(self) -> str:
        return f"Notification({self.notification_type}, {self.title})"
