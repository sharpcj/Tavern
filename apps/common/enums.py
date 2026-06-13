"""Shared enumerations used across Tavern apps."""

from __future__ import annotations

from django.db import models


class ContentStatus(models.TextChoices):
    """Lifecycle states for user-generated content."""

    DRAFT = "draft", "草稿"
    PUBLISHED = "published", "已发布"
    HIDDEN = "hidden", "已隐藏"
    DELETED = "deleted", "已删除"
    PENDING_REVIEW = "pending_review", "待审核"


class DisplayMode(models.TextChoices):
    """How the author's identity is shown to classmates."""

    REAL_NAME = "real_name", "真实姓名"
    NICKNAME = "nickname", "昵称"
