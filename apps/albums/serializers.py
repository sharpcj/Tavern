"""Serializers for albums, photos and photo comments."""

from __future__ import annotations

from PIL import Image
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.common.enums import ContentStatus, DisplayMode
from apps.common.models import Media
from apps.common.validators import validate_file_size, validate_image_type

from .models import Album, AlbumCategory, Photo, PhotoComment


class PhotoCommentSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(read_only=True)

    class Meta:
        model = PhotoComment
        fields = ["id", "display_name", "content", "display_mode", "created_at"]
        read_only_fields = ["id", "display_name", "created_at"]


class PhotoListSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(read_only=True)
    album = serializers.IntegerField(source="album_id", read_only=True)
    image_url = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()

    class Meta:
        model = Photo
        fields = ["id", "album", "display_name", "caption", "display_mode", "image_url", "comment_count", "created_at"]
        read_only_fields = fields

    def get_image_url(self, obj: Photo) -> str:
        request = self.context.get("request")
        url = obj.media.file.url
        if request:
            return request.build_absolute_uri(url)
        return url

    def get_comment_count(self, obj: Photo) -> int:
        return obj.comments.filter(status=ContentStatus.PUBLISHED).count()


class PhotoDetailSerializer(PhotoListSerializer):
    comments = serializers.SerializerMethodField()

    class Meta(PhotoListSerializer.Meta):
        fields = PhotoListSerializer.Meta.fields + ["comments"]

    def get_comments(self, obj: Photo) -> list:
        comments = obj.comments.filter(status=ContentStatus.PUBLISHED)
        return PhotoCommentSerializer(comments, many=True, context=self.context).data


class AlbumListSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source="get_category_display", read_only=True)
    creator_name = serializers.CharField(source="creator_name_snapshot", read_only=True)
    cover_url = serializers.SerializerMethodField()
    photo_count = serializers.SerializerMethodField()

    class Meta:
        model = Album
        fields = [
            "id", "title", "description", "category", "category_display",
            "creator_name", "activity", "cover_url", "photo_count", "created_at",
        ]
        read_only_fields = fields

    def get_cover_url(self, obj: Album) -> str | None:
        if not obj.cover_photo:
            return None
        return PhotoListSerializer(obj.cover_photo, context=self.context).data["image_url"]

    def get_photo_count(self, obj: Album) -> int:
        return obj.photos.filter(status=ContentStatus.PUBLISHED).count()


class AlbumDetailSerializer(AlbumListSerializer):
    photos = serializers.SerializerMethodField()

    class Meta(AlbumListSerializer.Meta):
        fields = AlbumListSerializer.Meta.fields + ["photos", "updated_at"]

    def get_photos(self, obj: Album) -> list:
        photos = obj.photos.filter(status=ContentStatus.PUBLISHED)
        return PhotoListSerializer(photos, many=True, context=self.context).data


class AlbumCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Album
        fields = ["title", "description", "category", "activity"]

    def validate_category(self, value: str) -> str:
        if value not in AlbumCategory.values:
            raise serializers.ValidationError("无效的相册分类")
        return value

    def create(self, validated_data):
        request = self.context["request"]
        return Album.objects.create(
            creator=request.user,
            creator_name_snapshot=request.user.real_name,
            **validated_data,
        )


class PhotoUploadSerializer(serializers.Serializer):
    image = serializers.ImageField()
    caption = serializers.CharField(required=False, allow_blank=True)
    display_mode = serializers.ChoiceField(choices=DisplayMode.choices, default=DisplayMode.REAL_NAME)

    def validate_image(self, image):
        try:
            validate_file_size(image)
            validate_image_type(image)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
        try:
            pos = image.tell()
            pil_image = Image.open(image)
            pil_image.verify()
            image.seek(pos)
        except Exception as exc:
            raise serializers.ValidationError("图片文件校验失败") from exc
        return image

    def create(self, validated_data):
        request = self.context["request"]
        album: Album = self.context["album"]
        image = validated_data["image"]
        width = height = None
        try:
            pil_image = Image.open(image)
            width, height = pil_image.size
            image.seek(0)
        except Exception:
            width = height = None
        media = Media.objects.create(
            uploader=request.user,
            file=image,
            original_name=image.name,
            content_type=getattr(image, "content_type", ""),
            size=image.size,
            width=width,
            height=height,
        )
        photo = Photo.objects.create(
            album=album,
            uploader=request.user,
            uploader_name_snapshot=request.user.real_name,
            media=media,
            caption=validated_data.get("caption", ""),
            display_mode=validated_data.get("display_mode", DisplayMode.REAL_NAME),
        )
        media.content_type_fk = ContentType.objects.get_for_model(Photo)
        media.object_id = photo.id
        media.save(update_fields=["content_type_fk", "object_id"])
        if album.cover_photo_id is None:
            album.cover_photo = photo
            album.save(update_fields=["cover_photo", "updated_at"])
        return photo


class PhotoCommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhotoComment
        fields = ["content", "display_mode"]

    def create(self, validated_data):
        request = self.context["request"]
        photo: Photo = self.context["photo"]
        return PhotoComment.objects.create(photo=photo, author=request.user, **validated_data)
