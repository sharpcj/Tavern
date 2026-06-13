"""API views for posts and comments."""

from __future__ import annotations

from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import IsApprovedClassmate, IsSuperAdmin
from apps.comments.models import Comment
from apps.common.enums import ContentStatus
from apps.notifications.services import NotificationType, create_notification

from .models import Post
from .serializers import (
    CommentCreateSerializer,
    CommentSerializer,
    PinToggleSerializer,
    PostCreateSerializer,
    PostDetailSerializer,
    PostListSerializer,
)


class PostListView(generics.ListCreateAPIView):
    """List or create feed posts."""

    permission_classes = [IsApprovedClassmate]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return PostCreateSerializer
        return PostListSerializer

    def get_queryset(self):
        qs = Post.objects.filter(status=ContentStatus.PUBLISHED).select_related("author")
        category = self.request.query_params.get("category", "").strip()
        if category:
            qs = qs.filter(category=category)
        return qs

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.request.method == "POST":
            context["uploaded_images"] = self.request.FILES.getlist("uploaded_images")
        return context

    @extend_schema(
        tags=["posts"],
        parameters=[
            OpenApiParameter("category", str, description="按分类筛选"),
            OpenApiParameter("page", int, description="页码"),
            OpenApiParameter("page_size", int, description="每页条数"),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(request=PostCreateSerializer, responses=PostDetailSerializer, tags=["posts"])
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        uploaded_images = request.FILES.getlist("uploaded_images")
        serializer.validate_uploaded_images(uploaded_images)
        post = serializer.save(author=request.user)
        return Response(PostDetailSerializer(post, context={"request": request}).data, status=status.HTTP_201_CREATED)


class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or soft-delete a post."""

    permission_classes = [IsApprovedClassmate]

    def get_queryset(self):
        return Post.objects.filter(status=ContentStatus.PUBLISHED).select_related("author")

    def get_serializer_class(self):
        if self.request.method in ("PATCH", "PUT"):
            return PostCreateSerializer
        return PostDetailSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.request.method in ("PATCH", "PUT") and "uploaded_images" in self.request.FILES:
            context["uploaded_images"] = self.request.FILES.getlist("uploaded_images")
        return context

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        if request.method in ("PATCH", "PUT", "DELETE"):
            if obj.author != request.user:
                self.permission_denied(request, message="只能编辑或删除自己的动态")

    def perform_destroy(self, instance):
        instance.soft_delete(self.request.user)

    @extend_schema(responses=PostDetailSerializer, tags=["posts"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(request=PostCreateSerializer, responses=PostDetailSerializer, tags=["posts"])
    def patch(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        uploaded_images = request.FILES.getlist("uploaded_images")
        if uploaded_images:
            serializer.validate_uploaded_images(uploaded_images)
        post = serializer.save()
        return Response(PostDetailSerializer(post, context={"request": request}).data)

    @extend_schema(tags=["posts"])
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class PostPinView(APIView):
    """Toggle pin status for a post (super admin only)."""

    permission_classes = [IsSuperAdmin]

    @extend_schema(request=PinToggleSerializer, responses=PostDetailSerializer, tags=["posts"])
    def post(self, request, pk: int):
        post = generics.get_object_or_404(Post.objects.filter(status=ContentStatus.PUBLISHED), pk=pk)
        serializer = PinToggleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if serializer.validated_data["pin"]:
            post.is_pinned = True
            post.pinned_at = timezone.now()
            post.pinned_by = request.user
        else:
            post.is_pinned = False
            post.pinned_at = None
            post.pinned_by = None
        post.save(update_fields=["is_pinned", "pinned_at", "pinned_by", "updated_at"])
        return Response(PostDetailSerializer(post).data)


class CommentListView(generics.ListCreateAPIView):
    """List comments for a post, or create a top-level comment."""

    permission_classes = [IsApprovedClassmate]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CommentCreateSerializer
        return CommentSerializer

    def get_queryset(self):
        post_id = self.kwargs.get("post_pk")
        if post_id is None:
            return Comment.objects.none()
        return (
            Comment.objects.filter(post_id=post_id, parent__isnull=True, status=ContentStatus.PUBLISHED)
            .select_related("author")
            .prefetch_related("replies__author", "replies__reply_to", "replies__reply_to__author")
        )

    def perform_create(self, serializer):
        post = generics.get_object_or_404(Post.objects.filter(status=ContentStatus.PUBLISHED), pk=self.kwargs["post_pk"])
        serializer.save(author=self.request.user, post=post)

    @extend_schema(tags=["comments"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(request=CommentCreateSerializer, responses=CommentSerializer, tags=["comments"])
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class CommentReplyView(APIView):
    """Create a reply to any existing comment while keeping two-level display."""

    permission_classes = [IsApprovedClassmate]

    @extend_schema(request=CommentCreateSerializer, responses=CommentSerializer, tags=["comments"])
    def post(self, request, pk: int):
        target = generics.get_object_or_404(
            Comment.objects.filter(status=ContentStatus.PUBLISHED).select_related("parent", "author"),
            pk=pk,
        )
        serializer = CommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if target.parent_id is None:
            root_parent = target
            reply_to = None
        else:
            root_parent = target.parent
            reply_to = target
        reply = serializer.save(author=request.user, post=target.post, parent=root_parent, reply_to=reply_to)
        if target.author != request.user:
            create_notification(
                recipient=target.author,
                notification_type=NotificationType.COMMENT_REPLY,
                title="你的评论收到了回复",
                content=reply.content[:200],
                target=reply,
            )
        return Response(CommentSerializer(reply, context={"request": request}).data, status=status.HTTP_201_CREATED)


class CommentDeleteView(APIView):
    """Soft-delete own comment."""

    permission_classes = [IsApprovedClassmate]
    serializer_class = CommentSerializer

    @extend_schema(tags=["comments"])
    def delete(self, request, pk: int):
        comment = generics.get_object_or_404(Comment.objects.filter(status=ContentStatus.PUBLISHED), pk=pk)
        if comment.author != request.user:
            self.permission_denied(request, message="只能删除自己的评论")
        comment.soft_delete(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)
