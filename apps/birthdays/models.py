"""Birthday wish models."""

from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.common.enums import ContentStatus, DisplayMode
from apps.common.models import SoftDeletableModel


class BirthdayWish(SoftDeletableModel):
    """A public-in-community birthday wish for a specific classmate."""

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="received_birthday_wishes",
        verbose_name="被祝福人",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="sent_birthday_wishes",
        verbose_name="祝福发布者",
    )
    content = models.TextField("祝福内容")
    display_mode = models.CharField(
        "展示身份",
        max_length=16,
        choices=DisplayMode.choices,
        default=DisplayMode.REAL_NAME,
    )
    status = models.CharField("状态", max_length=16, choices=ContentStatus.choices, default=ContentStatus.PUBLISHED, db_index=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "生日祝福"
        verbose_name_plural = "生日祝福"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"BirthdayWish({self.author.real_name} -> {self.recipient.real_name})"

    @property
    def display_name(self) -> str:
        if self.display_mode == DisplayMode.NICKNAME and self.author.nickname:
            return self.author.nickname
        return self.author.real_name
