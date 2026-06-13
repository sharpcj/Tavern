"""Shared database models for the common app.

Includes SoftDeletableModel mixin and Media metadata model.
"""

from __future__ import annotations

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone


class SoftDeletableModel(models.Model):
    """Abstract mixin that adds soft-delete fields and a helper method."""

    deleted_at = models.DateTimeField("删除时间", null=True, blank=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="删除操作人",
    )
    delete_reason = models.CharField("删除原因", max_length=256, blank=True)

    class Meta:
        abstract = True

    def soft_delete(self, user, reason: str = "") -> None:
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.delete_reason = reason
        save_fields = ["deleted_at", "deleted_by", "delete_reason"]
        if hasattr(self, "status"):
            from apps.common.enums import ContentStatus

            self.status = ContentStatus.DELETED
            save_fields.append("status")
        if hasattr(self, "updated_at"):
            save_fields.append("updated_at")
        self.save(update_fields=save_fields)


class Media(models.Model):
    """Metadata for an uploaded file, linked to any model via GenericForeignKey."""

    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="uploads",
        verbose_name="上传人",
    )
    file = models.FileField("文件", upload_to="media/%Y/%m/")
    original_name = models.CharField("原始文件名", max_length=256)
    content_type = models.CharField("MIME 类型", max_length=128)
    size = models.PositiveIntegerField("文件大小（字节）")
    width = models.PositiveIntegerField("宽度", null=True, blank=True)
    height = models.PositiveIntegerField("高度", null=True, blank=True)

    # Generic foreign key to associate with any content object.
    content_type_fk = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="关联对象类型",
    )
    object_id = models.PositiveIntegerField("关联对象 ID", null=True, blank=True)
    content_object = GenericForeignKey("content_type_fk", "object_id")

    created_at = models.DateTimeField("上传时间", auto_now_add=True)

    class Meta:
        verbose_name = "媒体文件"
        verbose_name_plural = "媒体文件"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.original_name
