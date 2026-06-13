"""Serializers for profile and classmate directory."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import ContactVisibility, Profile

User = get_user_model()


class ProfileSerializer(serializers.ModelSerializer):
    """Full profile for the owner to view and edit."""

    real_name = serializers.CharField(source="user.real_name", read_only=True)
    nickname = serializers.CharField(source="user.nickname")
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Profile
        fields = [
            "real_name",
            "nickname",
            "email",
            "avatar_url",
            "city",
            "occupation",
            "bio",
            "birthday_month",
            "show_birthday",
            "phone",
            "phone_visibility",
            "wechat",
            "wechat_visibility",
            "email_visibility",
            "contact_visible_to",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["real_name", "email", "created_at", "updated_at"]

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", {})
        if "nickname" in user_data:
            instance.user.nickname = user_data["nickname"]
            instance.user.save(update_fields=["nickname", "updated_at"])
        return super().update(instance, validated_data)

    def validate_birthday_month(self, value):
        if value is not None and (value < 1 or value > 12):
            raise serializers.ValidationError("生日月份必须在 1 到 12 之间")
        return value

    def validate_contact_visible_to(self, value):
        """Ensure only approved classmates can be selected."""
        from apps.accounts.models import ReviewStatus, AccountStatus

        for u in value:
            if u.review_status != ReviewStatus.APPROVED or u.account_status != AccountStatus.NORMAL:
                raise serializers.ValidationError(f"用户 {u.real_name} 不是有效的同学")
        return value


class ClassmateListSerializer(serializers.Serializer):
    """Public classmate directory list item — no contact info."""

    account_id = serializers.UUIDField(source="user.account_id")
    real_name = serializers.CharField(source="user.real_name")
    nickname = serializers.CharField(source="user.nickname")
    avatar_url = serializers.URLField()
    city = serializers.CharField()
    occupation = serializers.CharField()
    bio = serializers.CharField()
    birthday_month = serializers.IntegerField()


class ClassmateDetailSerializer(serializers.Serializer):
    """Single classmate detail — contact fields filtered by visibility."""

    account_id = serializers.UUIDField(source="user.account_id")
    real_name = serializers.CharField(source="user.real_name")
    nickname = serializers.CharField(source="user.nickname")
    avatar_url = serializers.URLField()
    city = serializers.CharField()
    occupation = serializers.CharField()
    bio = serializers.CharField()
    birthday_month = serializers.IntegerField()
    # Contact fields — included only when the viewer has permission.
    email = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()
    wechat = serializers.SerializerMethodField()

    def __init__(self, *args, viewer=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._viewer = viewer

    def get_email(self, obj: Profile) -> str | None:
        if obj.can_view_contact("email", self._viewer):
            return obj.user.email
        return None

    def get_phone(self, obj: Profile) -> str | None:
        if obj.can_view_contact("phone", self._viewer):
            return obj.phone or None
        return None

    def get_wechat(self, obj: Profile) -> str | None:
        if obj.can_view_contact("wechat", self._viewer):
            return obj.wechat or None
        return None
