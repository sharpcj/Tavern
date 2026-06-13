"""Serializers for announcements."""

from __future__ import annotations

from django.utils import timezone
from rest_framework import serializers

from apps.common.enums import ContentStatus

from .models import Announcement, AnnouncementReadReceipt


class AnnouncementListSerializer(serializers.ModelSerializer):
    publisher_name = serializers.CharField(source="publisher_name_snapshot", read_only=True)
    is_read = serializers.SerializerMethodField()

    class Meta:
        model = Announcement
        fields = [
            "id",
            "title",
            "publisher_name",
            "is_pinned",
            "require_read_confirm",
            "expires_at",
            "created_at",
            "is_read",
        ]
        read_only_fields = fields

    def get_is_read(self, obj: Announcement) -> bool:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated or not obj.require_read_confirm:
            return False
        return AnnouncementReadReceipt.objects.filter(announcement=obj, user=request.user).exists()


class AnnouncementDetailSerializer(serializers.ModelSerializer):
    publisher_name = serializers.CharField(source="publisher_name_snapshot", read_only=True)
    is_read = serializers.SerializerMethodField()

    class Meta:
        model = Announcement
        fields = [
            "id",
            "title",
            "content",
            "publisher_name",
            "is_pinned",
            "pinned_at",
            "require_read_confirm",
            "expires_at",
            "status",
            "created_at",
            "updated_at",
            "is_read",
        ]
        read_only_fields = ["id", "publisher_name", "created_at", "updated_at", "is_read"]

    def get_is_read(self, obj: Announcement) -> bool:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated or not obj.require_read_confirm:
            return False
        return AnnouncementReadReceipt.objects.filter(announcement=obj, user=request.user).exists()


class AnnouncementWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = ["title", "content", "is_pinned", "require_read_confirm", "expires_at", "status"]

    def validate_status(self, value: str) -> str:
        allowed = {ContentStatus.PUBLISHED, ContentStatus.HIDDEN}
        if value not in allowed:
            raise serializers.ValidationError("公告状态只能是已发布或已隐藏")
        return value

    def validate(self, attrs):
        expires_at = attrs.get("expires_at")
        if expires_at is not None and expires_at <= timezone.now():
            raise serializers.ValidationError({"expires_at": "过期时间必须晚于当前时间"})
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        if validated_data.get("is_pinned"):
            validated_data["pinned_at"] = timezone.now()
        return Announcement.objects.create(
            publisher=request.user,
            publisher_name_snapshot=request.user.real_name,
            **validated_data,
        )

    def update(self, instance: Announcement, validated_data):
        old_is_pinned = instance.is_pinned
        new_is_pinned = validated_data.get("is_pinned", old_is_pinned)
        if new_is_pinned and not old_is_pinned:
            validated_data["pinned_at"] = timezone.now()
        if not new_is_pinned:
            validated_data["pinned_at"] = None
        return super().update(instance, validated_data)
