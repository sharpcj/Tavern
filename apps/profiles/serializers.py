"""Serializers for profile and classmate directory."""

from __future__ import annotations

from PIL import Image
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.common.media_urls import sign_stored_media_url
from apps.common.models import Media
from apps.common.validators import validate_image_type

from .models import ContactVisibility, Profile

User = get_user_model()

MAX_AVATAR_SIZE = 512 * 1024
MAX_AVATAR_DIMENSION = 1024


def validate_avatar_image(uploaded_file):
    """Validate avatar upload type, file size and dimensions."""

    try:
        validate_image_type(uploaded_file)
    except DjangoValidationError as exc:
        raise serializers.ValidationError(exc.messages) from exc
    if uploaded_file.size > MAX_AVATAR_SIZE:
        raise serializers.ValidationError("头像图片不能超过 512 KB")
    try:
        pos = uploaded_file.tell()
        image = Image.open(uploaded_file)
        width, height = image.size
        image.verify()
        uploaded_file.seek(pos)
    except Exception as exc:
        raise serializers.ValidationError("头像图片校验失败") from exc
    if width > MAX_AVATAR_DIMENSION or height > MAX_AVATAR_DIMENSION:
        raise serializers.ValidationError(f"头像图片宽高不能超过 {MAX_AVATAR_DIMENSION} 像素")
    return width, height


class ProfileAvatarUrlMixin:
    """Return profile avatar URLs as browser-accessible signed media URLs."""

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        viewer = getattr(request, "user", None)
        if not instance.avatar_visible and viewer != instance.user:
            data["avatar_url"] = ""
        else:
            data["avatar_url"] = sign_stored_media_url(data.get("avatar_url", ""), request=request)
        return data


class ProfileSerializer(ProfileAvatarUrlMixin, serializers.ModelSerializer):
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
            "avatar_visible",
            "real_name_visible",
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
        instance = super().update(instance, validated_data)
        avatar = self.context.get("avatar")
        if avatar is not None:
            width, height = validate_avatar_image(avatar)
            media = Media.objects.create(
                uploader=instance.user,
                file=avatar,
                original_name=avatar.name,
                content_type=getattr(avatar, "content_type", ""),
                size=avatar.size,
                width=width,
                height=height,
                content_type_fk=ContentType.objects.get_for_model(Profile),
                object_id=instance.id,
            )
            instance.avatar_url = media.file.url
            instance.save(update_fields=["avatar_url", "updated_at"])
        return instance

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


class ClassmateListSerializer(ProfileAvatarUrlMixin, serializers.Serializer):
    """Public classmate directory list item — no contact info."""

    account_id = serializers.UUIDField(source="user.account_id")
    real_name = serializers.CharField(source="user.real_name")
    nickname = serializers.CharField(source="user.nickname")
    avatar_url = serializers.URLField()
    city = serializers.CharField()
    occupation = serializers.CharField()
    bio = serializers.CharField()
    birthday_month = serializers.IntegerField()


class ClassmateDetailSerializer(ProfileAvatarUrlMixin, serializers.Serializer):
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
