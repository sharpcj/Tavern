"""Serializers for audit logs."""

from __future__ import annotations

from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source="actor.real_name", read_only=True)
    target_type = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = ["id", "actor_name", "action", "target_type", "target_object_id", "reason", "metadata", "created_at"]
        read_only_fields = fields

    def get_target_type(self, obj: AuditLog) -> str | None:
        if not obj.target_content_type:
            return None
        return f"{obj.target_content_type.app_label}.{obj.target_content_type.model}"
