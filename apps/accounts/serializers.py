"""Serializers for account registration, status and review."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers

from .models import ReviewStatus

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """Create a pending user registration."""

    password = serializers.CharField(write_only=True, trim_whitespace=False)
    password_confirm = serializers.CharField(write_only=True, trim_whitespace=False)

    class Meta:
        model = User
        fields = [
            "id",
            "account_id",
            "email",
            "password",
            "password_confirm",
            "real_name",
            "high_school",
            "high_school_class",
            "nickname",
            "extra_info",
            "review_status",
        ]
        read_only_fields = ["id", "account_id", "review_status"]

    def validate_email(self, value: str) -> str:
        email = User.objects.normalize_email(value)
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("该邮箱已注册")
        return email

    def validate(self, attrs: dict) -> dict:
        password = attrs.get("password")
        password_confirm = attrs.pop("password_confirm", None)
        if password != password_confirm:
            raise serializers.ValidationError({"password_confirm": "两次输入的密码不一致"})
        validate_password(password)
        return attrs

    def create(self, validated_data: dict):
        password = validated_data.pop("password")
        return User.objects.create_user(password=password, **validated_data)


class CurrentUserSerializer(serializers.ModelSerializer):
    """Current user's non-sensitive account and review status."""

    review_status_display = serializers.CharField(source="get_review_status_display", read_only=True)
    account_status_display = serializers.CharField(source="get_account_status_display", read_only=True)
    role_display = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "account_id",
            "email",
            "real_name",
            "high_school",
            "high_school_class",
            "nickname",
            "extra_info",
            "role",
            "role_display",
            "review_status",
            "review_status_display",
            "account_status",
            "account_status_display",
            "review_message",
            "date_joined",
        ]
        read_only_fields = fields


class AdminUserListSerializer(serializers.ModelSerializer):
    """Admin-facing user list for review."""

    review_status_display = serializers.CharField(source="get_review_status_display", read_only=True)
    account_status_display = serializers.CharField(source="get_account_status_display", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "account_id",
            "email",
            "real_name",
            "high_school",
            "high_school_class",
            "nickname",
            "extra_info",
            "review_status",
            "review_status_display",
            "account_status",
            "account_status_display",
            "review_note",
            "review_message",
            "reviewed_by",
            "reviewed_at",
            "date_joined",
        ]
        read_only_fields = fields


class ReviewActionSerializer(serializers.Serializer):
    """Validate an admin review action."""

    action = serializers.ChoiceField(
        choices=[
            ("approve", "审核通过"),
            ("reject", "审核拒绝"),
            ("need_more_info", "需补充资料"),
        ]
    )
    review_note = serializers.CharField(required=False, allow_blank=True)
    review_message = serializers.CharField(required=False, allow_blank=True)

    def update_user(self, user, reviewer):
        action = self.validated_data["action"]
        status_map = {
            "approve": ReviewStatus.APPROVED,
            "reject": ReviewStatus.REJECTED,
            "need_more_info": ReviewStatus.NEED_MORE_INFO,
        }
        user.review_status = status_map[action]
        user.review_note = self.validated_data.get("review_note", "")
        user.review_message = self.validated_data.get("review_message", "")
        user.reviewed_by = reviewer
        user.reviewed_at = timezone.now()
        user.save(update_fields=["review_status", "review_note", "review_message", "reviewed_by", "reviewed_at", "updated_at"])
        return user
