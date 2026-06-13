"""Account and identity-review models."""

from __future__ import annotations

import uuid

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone


class UserRole(models.TextChoices):
    """Role values reserved for the classmate community."""

    CLASSMATE = "classmate", "普通同学"
    MODERATOR = "moderator", "管理会员"
    SUPER_ADMIN = "super_admin", "超级管理员"


class ReviewStatus(models.TextChoices):
    """Identity review lifecycle."""

    PENDING = "pending", "待审核"
    APPROVED = "approved", "审核通过"
    REJECTED = "rejected", "审核拒绝"
    NEED_MORE_INFO = "need_more_info", "需补充资料"


class AccountStatus(models.TextChoices):
    """Account availability status."""

    NORMAL = "normal", "正常"
    RESTRICTED = "restricted", "已限制"
    BANNED = "banned", "已封禁"


class UserManager(BaseUserManager):
    """Manager for the email-based custom user model."""

    use_in_migrations = True

    def _create_user(self, email: str, password: str | None, **extra_fields: object) -> "User":
        if not email:
            raise ValueError("邮箱不能为空")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra_fields: object) -> "User":
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email: str, password: str | None = None, **extra_fields: object) -> "User":
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", UserRole.SUPER_ADMIN)
        extra_fields.setdefault("review_status", ReviewStatus.APPROVED)
        extra_fields.setdefault("account_status", AccountStatus.NORMAL)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("超级管理员必须设置 is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("超级管理员必须设置 is_superuser=True")

        extra_fields.setdefault("real_name", "系统管理员")
        extra_fields.setdefault("high_school", "系统")
        extra_fields.setdefault("high_school_class", "系统")
        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Email-login user with identity review fields."""

    account_id = models.UUIDField("账号唯一标识", default=uuid.uuid4, unique=True, editable=False)
    email = models.EmailField("邮箱", unique=True)
    real_name = models.CharField("真实姓名", max_length=64)
    high_school = models.CharField("高三所在学校", max_length=128)
    high_school_class = models.CharField("高三所在班级", max_length=128)
    nickname = models.CharField("外号", max_length=64, blank=True)
    extra_info = models.TextField("其它信息", blank=True)

    role = models.CharField("角色", max_length=32, choices=UserRole.choices, default=UserRole.CLASSMATE)
    review_status = models.CharField(
        "审核状态",
        max_length=32,
        choices=ReviewStatus.choices,
        default=ReviewStatus.PENDING,
        db_index=True,
    )
    account_status = models.CharField(
        "账号状态",
        max_length=32,
        choices=AccountStatus.choices,
        default=AccountStatus.NORMAL,
        db_index=True,
    )
    review_note = models.TextField("内部审核备注", blank=True)
    review_message = models.TextField("给用户的审核说明", blank=True)
    reviewed_by = models.ForeignKey(
        "self",
        verbose_name="审核人",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_users",
    )
    reviewed_at = models.DateTimeField("审核时间", null=True, blank=True)

    is_staff = models.BooleanField("员工状态", default=False)
    is_active = models.BooleanField("可登录", default=True)
    date_joined = models.DateTimeField("注册时间", default=timezone.now)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["real_name", "high_school", "high_school_class"]

    class Meta:
        verbose_name = "用户"
        verbose_name_plural = "用户"
        ordering = ["-date_joined"]

    def __str__(self) -> str:
        return f"{self.real_name} <{self.email}>"

    @property
    def is_review_approved(self) -> bool:
        return self.review_status == ReviewStatus.APPROVED
