"""Serializers for birthday classmates and wishes."""

from __future__ import annotations

from django.utils import timezone
from rest_framework import serializers

from apps.accounts.models import AccountStatus, ReviewStatus
from apps.common.enums import ContentStatus
from apps.profiles.models import Profile

from .models import BirthdayWish


class BirthdayClassmateSerializer(serializers.Serializer):
    account_id = serializers.UUIDField(source="user.account_id")
    real_name = serializers.CharField(source="user.real_name")
    nickname = serializers.CharField(source="user.nickname")
    avatar_url = serializers.URLField()
    city = serializers.CharField()
    birthday_month = serializers.IntegerField()


class BirthdayWishSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(read_only=True)
    recipient_account_id = serializers.UUIDField(source="recipient.account_id", read_only=True)
    recipient_name = serializers.CharField(source="recipient.real_name", read_only=True)

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


class BirthdayWishCreateSerializer(serializers.ModelSerializer):
    recipient_account_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = BirthdayWish
        fields = ["recipient_account_id", "content", "display_mode"]

    def validate_content(self, value: str) -> str:
        if not value.strip():
            raise serializers.ValidationError("祝福内容不能为空")
        return value.strip()

    def validate_recipient_account_id(self, value):
        current_month = timezone.localdate().month
        profile = (
            Profile.objects.select_related("user")
            .filter(
                user__account_id=value,
                user__review_status=ReviewStatus.APPROVED,
                user__account_status=AccountStatus.NORMAL,
                birthday_month=current_month,
                show_birthday=True,
            )
            .first()
        )
        if not profile:
            raise serializers.ValidationError("只能给本月且已开启生日展示的同学送祝福")
        return value

    def create(self, validated_data):
        account_id = validated_data.pop("recipient_account_id")
        profile = Profile.objects.select_related("user").get(user__account_id=account_id)
        return BirthdayWish.objects.create(
            recipient=profile.user,
            author=self.context["request"].user,
            **validated_data,
        )
