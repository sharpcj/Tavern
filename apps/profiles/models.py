"""Profile and contact-visibility models for the profiles app."""

from __future__ import annotations

from django.conf import settings
from django.db import models


class ContactVisibility(models.TextChoices):
    """Per-contact-field visibility levels."""

    EVERYONE = "everyone", "所有人可见"
    SELECTED = "selected", "指定同学可见"
    ONLY_ME = "only_me", "仅自己可见"


class Profile(models.Model):
    """Public profile and privacy settings for an approved classmate."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="用户",
    )

    # --- public profile fields ---
    avatar_url = models.URLField("头像链接", blank=True, max_length=512)
    city = models.CharField("当前城市", max_length=64, blank=True)
    occupation = models.CharField("职业或行业", max_length=128, blank=True)
    bio = models.TextField("个人简介", blank=True)
    birthday_month = models.PositiveSmallIntegerField("生日月份", null=True, blank=True)
    show_birthday = models.BooleanField("在生日板块展示生日月份", default=False)

    # --- contact fields ---
    phone = models.CharField("手机号", max_length=32, blank=True)
    phone_visibility = models.CharField(
        "手机号可见范围",
        max_length=16,
        choices=ContactVisibility.choices,
        default=ContactVisibility.ONLY_ME,
    )
    wechat = models.CharField("微信号", max_length=64, blank=True)
    wechat_visibility = models.CharField(
        "微信号可见范围",
        max_length=16,
        choices=ContactVisibility.choices,
        default=ContactVisibility.ONLY_ME,
    )
    email_visibility = models.CharField(
        "邮箱可见范围",
        max_length=16,
        choices=ContactVisibility.choices,
        default=ContactVisibility.ONLY_ME,
    )

    contact_visible_to = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="visible_to_profiles",
        verbose_name="指定可见的同学",
    )

    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "个人资料"
        verbose_name_plural = "个人资料"
        ordering = ["user__real_name"]

    def __str__(self) -> str:
        return f"Profile({self.user.real_name})"

    def can_view_contact(self, field_name: str, viewer) -> bool:
        """Check whether *viewer* can see *field_name* on this profile."""
        if viewer == self.user:
            return True
        visibility = getattr(self, f"{field_name}_visibility", ContactVisibility.ONLY_ME)
        if visibility == ContactVisibility.EVERYONE:
            return True
        if visibility == ContactVisibility.SELECTED:
            return self.contact_visible_to.filter(pk=viewer.pk).exists()
        return False
