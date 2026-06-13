"""Serializers for posts and comments."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from apps.posts.models import Post, PostStatus
from apps.comments.models import Comment, CommentStatus

User = get_user_model()


class PostListSerializer(serializers.ModelSerializer):
    """Post item for the feed list."""

    display_name = serializers.CharField(read_only=True)
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
        return obj.comments.filter(status=CommentStatus.PUBLISHED).count()


class PostDetailSerializer(serializers.ModelSerializer):
    """Full post detail with author info for the author or admin."""

    display_name = serializers.CharField(read_only=True)
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
        read_only_fields = ["id", "author_id", "author_real_name", "display_name", "is_pinned", "created_at", "updated_at"]


class PostCreateSerializer(serializers.ModelSerializer):
    """Create or update a post."""

    class Meta:
        model = Post
        fields = ["content", "images", "category", "display_mode"]

    def validate_images(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("图片必须是 URL 列表")
        for url in value:
            if not isinstance(url, str) or not url.startswith(("http://", "https://")):
                raise serializers.ValidationError(f"无效的图片链接: {url}")
        return value


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
        replies_qs = obj.replies.filter(status=CommentStatus.PUBLISHED).select_related("author")
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
