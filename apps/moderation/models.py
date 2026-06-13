"""Moderation action models."""

from __future__ import annotations

from django.conf import settings
from django.db import models


class ModerationActionType(models.TextChoices):
    IGNORE = "ignore", "忽略举报"
    HIDE_CONTENT = "hide_content", "隐藏内容"
    DELETE_CONTENT = "delete_content", "删除内容"
    REQUEST_REVISION = "request_revision", "要求修改"
    WARN_USER = "warn_user", "警告用户"
    RESTRICT_USER = "restrict_user", "限制用户"
    BAN_USER = "ban_user", "封禁用户"


class ModerationAction(models.Model):
    """A concrete moderation action taken for a report."""

    report = models.ForeignKey(
        "reports.Report",
        on_delete=models.CASCADE,
        related_name="moderation_actions",
        verbose_name="关联举报",
    )
    action_type = models.CharField("处理动作", max_length=32, choices=ModerationActionType.choices, db_index=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="moderation_actions",
        verbose_name="处理人",
    )
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="received_moderation_actions",
        verbose_name="被处理用户",
    )
    reason = models.TextField("处理原因", blank=True)
    metadata = models.JSONField("扩展信息", default=dict, blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "治理动作"
        verbose_name_plural = "治理动作"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"ModerationAction({self.action_type})"
