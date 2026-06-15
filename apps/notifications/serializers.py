"""Serializers for system notifications."""

from __future__ import annotations

from rest_framework import serializers

from .models import Notification, RealtimeEvent


class NotificationSerializer(serializers.ModelSerializer):
    notification_type_display = serializers.CharField(source="get_notification_type_display", read_only=True)
    target_type = serializers.SerializerMethodField()
    target_url = serializers.SerializerMethodField()

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
            "target_url",
            "is_read",
            "read_at",
            "created_at",
        ]
        read_only_fields = fields

    def get_target_type(self, obj: Notification) -> str | None:
        if not obj.target_content_type:
            return None
        return f"{obj.target_content_type.app_label}.{obj.target_content_type.model}"

    def get_target_url(self, obj: Notification) -> str | None:
        target_type = self.get_target_type(obj)
        target = obj.target_object
        if not target_type or target is None:
            return None
        if target_type == "comments.comment":
            return f"/posts/{target.post_id}"
        if target_type == "albums.photocomment":
            return f"/photos/{target.photo_id}"
        if target_type == "activities.activity":
            return f"/activities/{target.pk}"
        if target_type == "announcements.announcement":
            return f"/announcements/{target.pk}"
        if target_type == "birthdays.birthdaywish":
            return "/birthdays"
        if target_type == "accounts.user":
            return "/review-status"
        return None


class RealtimeEventSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source="event_type", read_only=True)

    class Meta:
        model = RealtimeEvent
        fields = ["id", "type", "target_type", "target_id", "payload", "created_at"]
        read_only_fields = fields
