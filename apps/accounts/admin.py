"""Django admin integration for account review."""

from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils import timezone

from .models import ReviewStatus, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin pages for custom users and identity review."""

    ordering = ["-date_joined"]
    list_display = ["email", "account_id", "real_name", "high_school", "high_school_class", "review_status", "account_status", "is_staff"]
    list_filter = ["review_status", "account_status", "role", "is_staff", "is_superuser"]
    search_fields = ["email", "real_name", "high_school", "high_school_class", "nickname"]
    actions = ["approve_users", "reject_users", "mark_need_more_info"]

    fieldsets = [
        ("登录信息", {"fields": ["account_id", "email", "password"]}),
        ("身份资料", {"fields": ["real_name", "high_school", "high_school_class", "nickname", "extra_info"]}),
        ("审核状态", {"fields": ["review_status", "review_note", "review_message", "reviewed_by", "reviewed_at"]}),
        ("权限", {"fields": ["role", "account_status", "is_active", "is_staff", "is_superuser", "groups", "user_permissions"]}),
        ("重要时间", {"fields": ["last_login", "date_joined", "created_at", "updated_at"]}),
    ]
    readonly_fields = ["account_id", "last_login", "date_joined", "created_at", "updated_at", "reviewed_by", "reviewed_at"]
    add_fieldsets = [
        (
            "创建用户",
            {
                "classes": ["wide"],
                "fields": [
                    "email",
                    "real_name",
                    "high_school",
                    "high_school_class",
                    "password1",
                    "password2",
                    "review_status",
                    "account_status",
                    "role",
                    "is_staff",
                    "is_superuser",
                ],
            },
        ),
    ]

    @admin.action(description="审核通过选中用户")
    def approve_users(self, request, queryset):
        queryset.update(review_status=ReviewStatus.APPROVED, reviewed_by=request.user, reviewed_at=timezone.now())

    @admin.action(description="审核拒绝选中用户")
    def reject_users(self, request, queryset):
        queryset.update(review_status=ReviewStatus.REJECTED, reviewed_by=request.user, reviewed_at=timezone.now())

    @admin.action(description="标记为需补充资料")
    def mark_need_more_info(self, request, queryset):
        queryset.update(review_status=ReviewStatus.NEED_MORE_INFO, reviewed_by=request.user, reviewed_at=timezone.now())
