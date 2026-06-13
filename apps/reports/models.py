"""Report models for user-submitted content reports."""

from __future__ import annotations

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class ReportReason(models.TextChoices):
    PRIVACY = "privacy", "涉及隐私"
    FALSE_INFO = "false_info", "内容不实"
    ABUSE = "abuse", "攻击辱骂"
    AD = "ad", "广告推广"
    FRAUD = "fraud", "诈骗或诱导转账"
    ILLEGAL = "illegal", "违法违规"
    COPYRIGHT = "copyright", "侵犯肖像权或著作权"
    OTHER = "other", "其他原因"


class ReportStatus(models.TextChoices):
    PENDING = "pending", "待处理"
    PROCESSING = "processing", "处理中"
    RESOLVED = "resolved", "已处理"
    IGNORED = "ignored", "已忽略"


class Report(models.Model):
    """A report submitted by a classmate against a content object."""

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="submitted_reports",
        verbose_name="举报人",
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT, verbose_name="对象类型")
    object_id = models.PositiveIntegerField("对象 ID")
    content_object = GenericForeignKey("content_type", "object_id")
    reason = models.CharField("举报原因", max_length=32, choices=ReportReason.choices)
    description = models.TextField("补充说明", blank=True)
    status = models.CharField("状态", max_length=16, choices=ReportStatus.choices, default=ReportStatus.PENDING, db_index=True)
    handled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="handled_reports",
        verbose_name="处理人",
    )
    handled_at = models.DateTimeField("处理时间", null=True, blank=True)
    handle_note = models.TextField("处理说明", blank=True)
    created_at = models.DateTimeField("举报时间", auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "举报"
        verbose_name_plural = "举报"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Report({self.reason})"
