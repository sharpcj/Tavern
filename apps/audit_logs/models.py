"""Audit log models for governance and administration actions."""

from __future__ import annotations

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class AuditAction(models.TextChoices):
    REPORT_CREATED = "report_created", "提交举报"
    REPORT_HANDLED = "report_handled", "处理举报"
    CONTENT_HIDDEN = "content_hidden", "隐藏内容"
    CONTENT_DELETED = "content_deleted", "删除内容"
    USER_WARNED = "user_warned", "警告用户"
    USER_RESTRICTED = "user_restricted", "限制用户"
    USER_BANNED = "user_banned", "封禁用户"


class AuditLog(models.Model):
    """A generic audit log entry for key administrative actions."""

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
        verbose_name="操作者",
    )
    action = models.CharField("操作类型", max_length=64, choices=AuditAction.choices, db_index=True)
    target_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_log_targets",
        verbose_name="对象类型",
    )
    target_object_id = models.PositiveIntegerField("对象 ID", null=True, blank=True)
    target_object = GenericForeignKey("target_content_type", "target_object_id")
    reason = models.CharField("原因", max_length=512, blank=True)
    metadata = models.JSONField("扩展信息", default=dict, blank=True)
    created_at = models.DateTimeField("操作时间", auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "操作日志"
        verbose_name_plural = "操作日志"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"AuditLog({self.action})"
