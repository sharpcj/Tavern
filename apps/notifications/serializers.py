"""Serializers for system notifications."""

from __future__ import annotations

from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    notification_type_display = serializers.CharField(source="get_notification_type_display", read_only=True)
    target_type = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "notification_type",
            "notification_type_display",
            "title",
            "content",
            "target_type",
            "target_object_id",
            "is_read",
            "read_at",
            "created_at",
        ]
        read_only_fields = fields

    def get_target_type(self, obj: Notification) -> str | None:
        if not obj.target_content_type:
            return None
        return f"{obj.target_content_type.app_label}.{obj.target_content_type.model}"
