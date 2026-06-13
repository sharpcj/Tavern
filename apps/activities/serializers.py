"""Serializers for activities."""

from __future__ import annotations

from rest_framework import serializers

from .models import (
    Activity,
    ActivityStatus,
    ActivityType,
    ChainRecord,
    Signup,
    VoteOption,
    VoteRecord,
)


class VoteOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = VoteOption
        fields = ["id", "text", "order"]


class ActivityListSerializer(serializers.ModelSerializer):
    activity_type_display = serializers.CharField(source="get_activity_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    initiator_name = serializers.CharField(source="initiator_name_snapshot", read_only=True)
    signup_count = serializers.SerializerMethodField()

    class Meta:
        model = Activity
        fields = [
            "id", "title", "activity_type", "activity_type_display",
            "initiator_name", "status", "status_display",
            "location", "start_time", "deadline", "signup_count",
            "created_at",
        ]
        read_only_fields = fields

    def get_signup_count(self, obj: Activity) -> int:
        if obj.activity_type == ActivityType.GATHERING:
            return obj.signups.count()
        return 0


class ActivityDetailSerializer(serializers.ModelSerializer):
    activity_type_display = serializers.CharField(source="get_activity_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    initiator_name = serializers.CharField(source="initiator_name_snapshot", read_only=True)
    initiator_id = serializers.UUIDField(source="initiator.account_id", read_only=True)
    vote_options = VoteOptionSerializer(many=True, read_only=True)
    signups = serializers.SerializerMethodField()
    vote_results = serializers.SerializerMethodField()
    chain_records = serializers.SerializerMethodField()

    class Meta:
        model = Activity
        fields = [
            "id", "title", "activity_type", "activity_type_display",
            "initiator_id", "initiator_name", "description",
            "location", "start_time", "deadline",
            "max_participants", "allow_guests", "contact_info",
            "status", "status_display",
            "is_multi_choice", "show_voter_names", "allow_vote_change",
            "vote_options", "signups", "vote_results", "chain_records",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "initiator_id", "initiator_name", "created_at", "updated_at"]

    def get_signups(self, obj: Activity) -> list:
        if obj.activity_type != ActivityType.GATHERING:
            return []
        return [
            {"real_name": s.real_name_snapshot, "participant_count": s.participant_count,
             "bring_guests": s.bring_guests, "note": s.note, "created_at": s.created_at}
            for s in obj.signups.all()
        ]

    def get_vote_results(self, obj: Activity) -> list:
        if obj.activity_type != ActivityType.VOTING:
            return []
        results = []
        for opt in obj.vote_options.all():
            votes = opt.votes.all()
            item = {"option_id": opt.id, "text": opt.text, "count": votes.count()}
            if obj.show_voter_names:
                item["voters"] = [v.real_name_snapshot for v in votes]
            results.append(item)
        return results

    def get_chain_records(self, obj: Activity) -> list:
        if obj.activity_type != ActivityType.CHAIN:
            return []
        return [
            {"real_name": r.real_name_snapshot, "will_attend": r.will_attend,
             "participant_count": r.participant_count, "note": r.note, "created_at": r.created_at}
            for r in obj.chain_records.all()
        ]


class ActivityCreateSerializer(serializers.ModelSerializer):
    vote_options = serializers.ListField(
        child=serializers.CharField(), required=False, write_only=True,
        help_text="投票选项文本列表（仅投票活动）"
    )

    class Meta:
        model = Activity
        fields = [
            "title", "activity_type", "description", "location", "start_time",
            "deadline", "max_participants", "allow_guests", "contact_info",
            "is_multi_choice", "show_voter_names", "allow_vote_change",
            "vote_options",
        ]

    def validate(self, attrs):
        activity_type = attrs.get("activity_type")
        if activity_type == ActivityType.VOTING:
            options = attrs.pop("vote_options", [])
            if not options or len(options) < 2:
                raise serializers.ValidationError({"vote_options": "投票至少需要两个选项"})
            attrs["_vote_options"] = options
        return attrs

    def create(self, validated_data):
        vote_options = validated_data.pop("_vote_options", [])
        validated_data["initiator_name_snapshot"] = self.context["request"].user.real_name
        activity = Activity.objects.create(initiator=self.context["request"].user, **validated_data)
        for i, text in enumerate(vote_options):
            VoteOption.objects.create(activity=activity, text=text, order=i)
        return activity


class ActivityStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[
        ("open", "报名中"),
        ("closed", "已截止"),
        ("finished", "已结束"),
        ("cancelled", "已取消"),
    ])


class SignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Signup
        fields = ["participant_count", "bring_guests", "note"]


class VoteSerializer(serializers.Serializer):
    option_ids = serializers.ListField(child=serializers.IntegerField(), min_length=1)


class ChainRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChainRecord
        fields = ["will_attend", "participant_count", "note"]
