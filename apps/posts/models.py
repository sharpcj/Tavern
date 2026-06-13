"""Post model for the classmate community feed."""

from __future__ import annotations

from django.conf import settings
from django.db import models


class PostCategory(models.TextChoices):
    LIFE = "life", "生活近况"
    OLD_PHOTOS = "old_photos", "老照片"
    REUNION = "reunion", "同学聚会"
    TEACHER = "teacher", "老师相关"
    WORK_CITY = "work_city", "工作与城市"
    FAMILY = "family", "家庭与成长"
    HELP = "help", "求助与互助"
    CHAT = "chat", "闲聊"


class DisplayMode(models.TextChoices):
    REAL_NAME = "real_name", "真实姓名"
    NICKNAME = "nickname", "昵称"


class PostStatus(models.TextChoices):
    PUBLISHED = "published", "已发布"
    DELETED = "deleted", "已删除"


class Post(models.Model):
    """A feed post in the classmate community."""

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="posts",
        verbose_name="作者",
    )
    content = models.TextField("内容")
    images = models.JSONField("图片列表", default=list, blank=True)
    category = models.CharField("分类", max_length=32, choices=PostCategory.choices, default=PostCategory.CHAT)
    display_mode = models.CharField(
        "展示身份",
        max_length=16,
        choices=DisplayMode.choices,
        default=DisplayMode.REAL_NAME,
    )
    status = models.CharField("状态", max_length=16, choices=PostStatus.choices, default=PostStatus.PUBLISHED, db_index=True)
    is_pinned = models.BooleanField("置顶", default=False, db_index=True)
    pinned_at = models.DateTimeField("置顶时间", null=True, blank=True)
    pinned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pinned_posts",
        verbose_name="置顶操作人",
    )
    deleted_at = models.DateTimeField("删除时间", null=True, blank=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deleted_posts",
        verbose_name="删除操作人",
    )
    created_at = models.DateTimeField("创建时间", auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "动态"
        verbose_name_plural = "动态"
        ordering = ["-is_pinned", "-pinned_at", "-created_at"]

    def __str__(self) -> str:
        preview = self.content[:60]
        return f"Post({self.author.real_name}): {preview}"

    @property
    def display_name(self) -> str:
        if self.display_mode == DisplayMode.NICKNAME and self.author.nickname:
            return self.author.nickname
        return self.author.real_name
