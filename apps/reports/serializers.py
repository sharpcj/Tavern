"""Serializers for reports and moderation handling."""

from __future__ import annotations

from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from apps.activities.models import Activity
from apps.albums.models import Photo
from apps.birthdays.models import BirthdayWish
from apps.comments.models import Comment
from apps.moderation.models import ModerationActionType
from apps.posts.models import Post

from .models import Report, ReportReason, ReportStatus

REPORT_TARGET_MODELS = {
    "post": Post,
    "comment": Comment,
    "photo": Photo,
    "activity": Activity,
    "birthday_wish": BirthdayWish,
}


class ReportCreateSerializer(serializers.Serializer):
    target_type = serializers.ChoiceField(choices=[(k, k) for k in REPORT_TARGET_MODELS.keys()])
    object_id = serializers.IntegerField(min_value=1)
    reason = serializers.ChoiceField(choices=ReportReason.choices)
    description = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        model = REPORT_TARGET_MODELS[attrs["target_type"]]
        obj = model.objects.filter(pk=attrs["object_id"]).first()
        if obj is None:
            raise serializers.ValidationError("举报对象不存在")
        attrs["content_object"] = obj
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        target_type = validated_data.pop("target_type")
        object_id = validated_data.pop("object_id")
        obj = validated_data.pop("content_object")
        content_type = ContentType.objects.get_for_model(obj.__class__)
        return Report.objects.create(
            reporter=request.user,
            content_type=content_type,
            object_id=object_id,
            **validated_data,
        )


class ReportSerializer(serializers.ModelSerializer):
    reporter_name = serializers.CharField(source="reporter.real_name", read_only=True)
    handled_by_name = serializers.CharField(source="handled_by.real_name", read_only=True)
    target_type = serializers.SerializerMethodField()
    target_label = serializers.SerializerMethodField()
    reason_display = serializers.CharField(source="get_reason_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Report
        fields = [
            "id", "reporter_name", "target_type", "object_id", "target_label",
            "reason", "reason_display", "description", "status", "status_display",
            "handled_by_name", "handled_at", "handle_note", "created_at",
        ]
        read_only_fields = fields

    def get_target_type(self, obj: Report) -> str:
        return f"{obj.content_type.app_label}.{obj.content_type.model}"

    def get_target_label(self, obj: Report) -> str:
        content = obj.content_object
        if content is None:
            return "对象不存在"
        if hasattr(content, "title"):
            return str(content.title)
        if hasattr(content, "content"):
            return str(content.content)[:60]
        if hasattr(content, "caption"):
            return str(content.caption or "照片")[:60]
        return str(content)


class ReportHandleSerializer(serializers.Serializer):
    action_type = serializers.ChoiceField(choices=ModerationActionType.choices)
    reason = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        report: Report = self.context["report"]
        if report.status in (ReportStatus.RESOLVED, ReportStatus.IGNORED):
            raise serializers.ValidationError("举报已经处理，不能重复处理")
        return attrs
