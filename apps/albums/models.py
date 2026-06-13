"""Album, photo and photo-comment models."""

from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.common.enums import ContentStatus, DisplayMode
from apps.common.models import Media, SoftDeletableModel


class AlbumCategory(models.TextChoices):
    CAMPUS = "campus", "高中校园"
    GRADUATION = "graduation", "毕业照"
    TEACHER = "teacher", "老师合影"
    GATHERING = "gathering", "聚会照片"
    CLASSMATE_LIFE = "classmate_life", "同学近况"
    MEMORY = "memory", "班级纪念"


class Album(SoftDeletableModel):
    """A photo album in the internal classmate community."""

    title = models.CharField("标题", max_length=256)
    description = models.TextField("说明", blank=True)
    category = models.CharField("分类", max_length=32, choices=AlbumCategory.choices, default=AlbumCategory.MEMORY)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_albums",
        verbose_name="创建人",
    )
    creator_name_snapshot = models.CharField("创建人姓名快照", max_length=64)
    activity = models.ForeignKey(
        "activities.Activity",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="albums",
        verbose_name="关联活动",
    )
    cover_photo = models.ForeignKey(
        "Photo",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cover_for_albums",
        verbose_name="封面照片",
    )
    status = models.CharField("状态", max_length=16, choices=ContentStatus.choices, default=ContentStatus.PUBLISHED, db_index=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "相册"
        verbose_name_plural = "相册"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title


class Photo(SoftDeletableModel):
    """A photo uploaded into an album."""

    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name="photos", verbose_name="相册")
    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="uploaded_photos",
        verbose_name="上传人",
    )
    uploader_name_snapshot = models.CharField("上传人姓名快照", max_length=64)
    media = models.OneToOneField(Media, on_delete=models.PROTECT, related_name="photo", verbose_name="媒体文件")
    caption = models.TextField("图片说明", blank=True)
    display_mode = models.CharField(
        "展示身份",
        max_length=16,
        choices=DisplayMode.choices,
        default=DisplayMode.REAL_NAME,
    )
    status = models.CharField("状态", max_length=16, choices=ContentStatus.choices, default=ContentStatus.PUBLISHED, db_index=True)
    created_at = models.DateTimeField("上传时间", auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "照片"
        verbose_name_plural = "照片"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Photo({self.album.title})"

    @property
    def display_name(self) -> str:
        if self.display_mode == DisplayMode.NICKNAME and self.uploader.nickname:
            return self.uploader.nickname
        return self.uploader.real_name


class PhotoComment(SoftDeletableModel):
    """A comment on a photo."""

    photo = models.ForeignKey(Photo, on_delete=models.CASCADE, related_name="comments", verbose_name="照片")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="photo_comments",
        verbose_name="作者",
    )
    content = models.TextField("内容")
    display_mode = models.CharField(
        "展示身份",
        max_length=16,
        choices=DisplayMode.choices,
        default=DisplayMode.REAL_NAME,
    )
    status = models.CharField("状态", max_length=16, choices=ContentStatus.choices, default=ContentStatus.PUBLISHED, db_index=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "照片评论"
        verbose_name_plural = "照片评论"
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"PhotoComment({self.author.real_name})"

    @property
    def display_name(self) -> str:
        if self.display_mode == DisplayMode.NICKNAME and self.author.nickname:
            return self.author.nickname
        return self.author.real_name
