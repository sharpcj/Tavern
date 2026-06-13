"""Serializers for posts and comments."""

from __future__ import annotations

from PIL import Image
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.comments.models import Comment
from apps.common.enums import ContentStatus, DisplayMode
from apps.common.models import Media
from apps.common.validators import validate_file_size, validate_image_type
from apps.posts.models import Post

User = get_user_model()


class PostImageUrlMixin:
    """Return post image URLs as browser-accessible absolute URLs."""

    def get_images(self, obj: Post) -> list[str]:
        request = self.context.get("request")
        result = []
        for url in obj.images or []:
            if isinstance(url, str) and url.startswith("/") and request:
                result.append(request.build_absolute_uri(url))
            else:
                result.append(url)
        return result


class PostListSerializer(PostImageUrlMixin, serializers.ModelSerializer):
    """Post item for the feed list."""

    display_name = serializers.CharField(read_only=True)
    images = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    category_display = serializers.CharField(source="get_category_display", read_only=True)

    class Meta:
        model = Post
        fields = [
            "id",
            "display_name",
            "content",
            "images",
            "category",
            "category_display",
            "is_pinned",
            "comment_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_comment_count(self, obj: Post) -> int:
        return obj.comments.filter(status=ContentStatus.PUBLISHED).count()


class PostDetailSerializer(PostImageUrlMixin, serializers.ModelSerializer):
    """Full post detail with author info for the author or admin."""

    display_name = serializers.CharField(read_only=True)
    images = serializers.SerializerMethodField()
    category_display = serializers.CharField(source="get_category_display", read_only=True)
    author_id = serializers.UUIDField(source="author.account_id", read_only=True)
    author_real_name = serializers.CharField(source="author.real_name", read_only=True)

    class Meta:
        model = Post
        fields = [
            "id",
            "author_id",
            "author_real_name",
            "display_name",
            "content",
            "images",
            "category",
            "category_display",
            "display_mode",
            "is_pinned",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "author_id", "author_real_name", "display_name", "images", "is_pinned", "created_at", "updated_at"]


class PostCreateSerializer(serializers.ModelSerializer):
    """Create or update a post with optional local image uploads."""

    class Meta:
        model = Post
        fields = ["content", "category", "display_mode"]

    def validate_uploaded_images(self, value):
        for image in value:
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
        return value

    def create(self, validated_data):
        uploaded_images = self.context.get("uploaded_images", [])
        post = Post.objects.create(images=[], **validated_data)
        image_urls = self._save_uploaded_images(post, uploaded_images)
        if image_urls:
            post.images = image_urls
            post.save(update_fields=["images", "updated_at"])
        return post

    def update(self, instance, validated_data):
        uploaded_images = self.context.get("uploaded_images")
        instance = super().update(instance, validated_data)
        if uploaded_images is not None:
            instance.images = self._save_uploaded_images(instance, uploaded_images)
            instance.save(update_fields=["images", "updated_at"])
        return instance

    def _save_uploaded_images(self, post: Post, uploaded_images) -> list[str]:
        image_urls: list[str] = []
        for image in uploaded_images:
            width = height = None
            try:
                pil_image = Image.open(image)
                width, height = pil_image.size
                image.seek(0)
            except Exception:
                width = height = None
            media = Media.objects.create(
                uploader=post.author,
                file=image,
                original_name=image.name,
                content_type=getattr(image, "content_type", ""),
                size=image.size,
                width=width,
                height=height,
                content_type_fk=ContentType.objects.get_for_model(Post),
                object_id=post.id,
            )
            image_urls.append(media.file.url)
        return image_urls


class CommentSerializer(serializers.ModelSerializer):
    """Comment with replies nested."""

    display_name = serializers.CharField(read_only=True)
    author_id = serializers.UUIDField(source="author.account_id", read_only=True)
    author_real_name = serializers.CharField(source="author.real_name", read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            "id",
            "author_id",
            "author_real_name",
            "display_name",
            "content",
            "display_mode",
            "parent",
            "replies",
            "created_at",
        ]
        read_only_fields = ["id", "author_id", "author_real_name", "display_name", "parent", "created_at"]

    def get_replies(self, obj: Comment) -> list:
        if obj.parent is not None:
            return []
        replies_qs = obj.replies.filter(status=ContentStatus.PUBLISHED).select_related("author")
        return CommentReplySerializer(replies_qs, many=True).data


class CommentReplySerializer(serializers.ModelSerializer):
    """A reply to a comment (no further nesting)."""

    display_name = serializers.CharField(read_only=True)
    author_id = serializers.UUIDField(source="author.account_id", read_only=True)
    author_real_name = serializers.CharField(source="author.real_name", read_only=True)

    class Meta:
        model = Comment
        fields = [
            "id",
            "author_id",
            "author_real_name",
            "display_name",
            "content",
            "display_mode",
            "created_at",
        ]
        read_only_fields = ["id", "author_id", "author_real_name", "display_name", "created_at"]


class CommentCreateSerializer(serializers.ModelSerializer):
    """Create a comment or reply."""

    class Meta:
        model = Comment
        fields = ["content", "display_mode"]


class PinToggleSerializer(serializers.Serializer):
    """Toggle pin status."""

    pin = serializers.BooleanField()
