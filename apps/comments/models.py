"""Comment model for the classmate community."""

from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.posts.models import DisplayMode


class CommentStatus(models.TextChoices):
    PUBLISHED = "published", "已发布"
    DELETED = "deleted", "已删除"


class Comment(models.Model):
    """A comment on a post, or a reply to a comment (two-level only)."""

    post = models.ForeignKey(
        "posts.Post",
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="所属动态",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="comments",
        verbose_name="作者",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies",
        verbose_name="父评论",
    )
    content = models.TextField("内容")
    display_mode = models.CharField(
        "展示身份",
        max_length=16,
        choices=DisplayMode.choices,
        default=DisplayMode.REAL_NAME,
    )
    status = models.CharField("状态", max_length=16, choices=CommentStatus.choices, default=CommentStatus.PUBLISHED, db_index=True)
    deleted_at = models.DateTimeField("删除时间", null=True, blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "评论"
        verbose_name_plural = "评论"
        ordering = ["created_at"]

    def __str__(self) -> str:
        preview = self.content[:40]
        return f"Comment({self.author.real_name}): {preview}"

    @property
    def display_name(self) -> str:
        if self.display_mode == DisplayMode.NICKNAME and self.author.nickname:
            return self.author.nickname
        return self.author.real_name
