"""Serializers for birthday classmates and wishes."""

from __future__ import annotations

from django.utils import timezone
from rest_framework import serializers

from apps.accounts.models import AccountStatus, ReviewStatus
from apps.common.enums import ContentStatus, DisplayMode
from apps.profiles.models import Profile
from apps.profiles.serializers import ProfileAvatarUrlMixin

from .models import BirthdayWish


class BirthdayClassmateSerializer(ProfileAvatarUrlMixin, serializers.Serializer):
    account_id = serializers.UUIDField(source="user.account_id")
    real_name = serializers.SerializerMethodField()
    nickname = serializers.CharField(source="user.nickname")
    display_name = serializers.SerializerMethodField()
    avatar_url = serializers.URLField()
    city = serializers.CharField()
    birthday_month = serializers.IntegerField()

    def get_real_name(self, obj: Profile) -> str:
        return obj.user.real_name if obj.real_name_visible else ""

    def get_display_name(self, obj: Profile) -> str:
        if obj.real_name_visible:
            return obj.user.real_name
        return obj.user.nickname or "同学"


class BirthdayWishSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(read_only=True)
    recipient_account_id = serializers.SerializerMethodField()
    recipient_name = serializers.SerializerMethodField()

    class Meta:
        model = BirthdayWish
        fields = [
            "id",
            "recipient_account_id",
            "recipient_name",
            "display_name",
            "content",
            "display_mode",
            "created_at",
        ]
        read_only_fields = ["id", "recipient_account_id", "recipient_name", "display_name", "created_at"]

    def get_recipient_account_id(self, obj: BirthdayWish) -> str | None:
        if not obj.recipient_id:
            return None
        return str(obj.recipient.account_id)

    def get_recipient_name(self, obj: BirthdayWish) -> str:
        if not obj.recipient_id:
            return "本月生日同学"
        profile = getattr(obj.recipient, "profile", None)
        if profile and profile.real_name_visible:
            return obj.recipient.real_name
        return obj.recipient.nickname or "同学"


class BirthdayWishCreateSerializer(serializers.Serializer):
    recipient_account_id = serializers.UUIDField(required=False, allow_null=True, write_only=True)
    recipient_account_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False, allow_empty=True, write_only=True
    )
    content = serializers.CharField()
    display_mode = serializers.ChoiceField(choices=DisplayMode.choices, default=DisplayMode.REAL_NAME)

    def validate_content(self, value: str) -> str:
        if not value.strip():
            raise serializers.ValidationError("祝福内容不能为空")
        return value.strip()

    def validate(self, attrs):
        account_ids = []
        if attrs.get("recipient_account_id"):
            account_ids.append(attrs["recipient_account_id"])
        account_ids.extend(attrs.get("recipient_account_ids", []))
        # Keep order while de-duplicating repeated selections.
        unique_account_ids = list(dict.fromkeys(account_ids))
        current_month = timezone.localdate().month
        profiles = list(
            Profile.objects.select_related("user").filter(
                user__account_id__in=unique_account_ids,
                user__review_status=ReviewStatus.APPROVED,
                user__account_status=AccountStatus.NORMAL,
                birthday_month=current_month,
                show_birthday=True,
            )
        )
        profiles_by_id = {p.user.account_id: p for p in profiles}
        if len(profiles_by_id) != len(unique_account_ids):
            raise serializers.ValidationError({"recipient_account_ids": "只能给本月且已开启生日展示的同学送祝福"})
        attrs["_recipient_profiles"] = [profiles_by_id[account_id] for account_id in unique_account_ids]
        return attrs

    def create(self, validated_data):
        profiles = validated_data.pop("_recipient_profiles", [])
        validated_data.pop("recipient_account_id", None)
        validated_data.pop("recipient_account_ids", None)
        recipients = [profile.user for profile in profiles] or [None]
        return [
            BirthdayWish.objects.create(
                recipient=recipient,
                author=self.context["request"].user,
                **validated_data,
            )
            for recipient in recipients
        ]
