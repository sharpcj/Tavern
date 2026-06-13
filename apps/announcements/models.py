"""Announcement models for the classmate community."""

from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.common.enums import ContentStatus
from apps.common.models import SoftDeletableModel


class Announcement(SoftDeletableModel):
    """A class-level announcement published by moderators or super admins."""

    title = models.CharField("标题", max_length=256)
    content = models.TextField("内容")
    publisher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="published_announcements",
        verbose_name="发布人",
    )
    publisher_name_snapshot = models.CharField("发布人姓名快照", max_length=64)
    is_pinned = models.BooleanField("置顶", default=False, db_index=True)
    pinned_at = models.DateTimeField("置顶时间", null=True, blank=True)
    require_read_confirm = models.BooleanField("需要已读确认", default=False)
    expires_at = models.DateTimeField("过期时间", null=True, blank=True, db_index=True)
    status = models.CharField(
        "状态",
        max_length=16,
        choices=ContentStatus.choices,
        default=ContentStatus.PUBLISHED,
        db_index=True,
    )
    created_at = models.DateTimeField("创建时间", auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "公告"
        verbose_name_plural = "公告"
        ordering = ["-is_pinned", "-pinned_at", "-created_at"]

    def __str__(self) -> str:
        return self.title

    @property
    def is_active(self) -> bool:
        if self.status != ContentStatus.PUBLISHED:
            return False
        return self.expires_at is None or self.expires_at > timezone.now()


class AnnouncementReadReceipt(models.Model):
    """Read-confirmation record for important announcements."""

    announcement = models.ForeignKey(
        Announcement,
        on_delete=models.CASCADE,
        related_name="read_receipts",
        verbose_name="公告",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="announcement_read_receipts",
        verbose_name="用户",
    )
    read_at = models.DateTimeField("确认时间", auto_now_add=True)

    class Meta:
        verbose_name = "公告已读记录"
        verbose_name_plural = "公告已读记录"
        unique_together = [("announcement", "user")]
        ordering = ["-read_at"]

    def __str__(self) -> str:
        return f"{self.user.real_name} read {self.announcement.title}"
