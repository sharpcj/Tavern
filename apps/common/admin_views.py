"""Admin API views for content management."""

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.albums.models import Album, Photo
from apps.audit_logs.models import AuditAction
from apps.audit_logs.services import write_audit_log
from apps.comments.models import Comment
from apps.common.enums import ContentStatus
from apps.common.permissions import IsModeratorOrAbove
from apps.posts.models import Post


class AdminPostListView(generics.ListAPIView):
    permission_classes = [IsModeratorOrAbove]

    def get_queryset(self):
        qs = Post.objects.select_related("author").all().order_by("-created_at")
        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        return qs

    @extend_schema(tags=["admin-contents"])
    def get(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(qs)
        if page is not None:
            data = [{"id": p.id, "author_name": p.author.real_name, "content": p.content[:100], "status": p.status, "created_at": p.created_at} for p in page]
            return self.get_paginated_response(data)
        data = [{"id": p.id, "author_name": p.author.real_name, "content": p.content[:100], "status": p.status, "created_at": p.created_at} for p in qs]
        return Response(data)


class AdminPostHideView(APIView):
    permission_classes = [IsModeratorOrAbove]

    @extend_schema(tags=["admin-contents"])
    def post(self, request, pk: int):
        post = generics.get_object_or_404(Post, pk=pk)
        post.status = ContentStatus.HIDDEN
        post.save(update_fields=["status", "updated_at"])
        write_audit_log(actor=request.user, action=AuditAction.CONTENT_HIDDEN, target=post, reason="管理员隐藏动态")
        return Response({"detail": "已隐藏"})


class AdminPostDeleteView(APIView):
    permission_classes = [IsModeratorOrAbove]

    @extend_schema(tags=["admin-contents"])
    def post(self, request, pk: int):
        post = generics.get_object_or_404(Post, pk=pk)
        post.soft_delete(request.user, reason="管理员删除")
        write_audit_log(actor=request.user, action=AuditAction.CONTENT_DELETED, target=post, reason="管理员删除动态")
        return Response({"detail": "已删除"})


class AdminCommentListView(generics.ListAPIView):
    permission_classes = [IsModeratorOrAbove]

    def get_queryset(self):
        return Comment.objects.select_related("author").all().order_by("-created_at")

    @extend_schema(tags=["admin-contents"])
    def get(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(qs)
        if page is not None:
            data = [{"id": c.id, "author_name": c.author.real_name, "content": c.content[:100], "status": c.status, "created_at": c.created_at} for c in page]
            return self.get_paginated_response(data)
        data = [{"id": c.id, "author_name": c.author.real_name, "content": c.content[:100], "status": c.status, "created_at": c.created_at} for c in qs]
        return Response(data)


class AdminCommentHideView(APIView):
    permission_classes = [IsModeratorOrAbove]

    @extend_schema(tags=["admin-contents"])
    def post(self, request, pk: int):
        comment = generics.get_object_or_404(Comment, pk=pk)
        comment.status = ContentStatus.HIDDEN
        comment.save(update_fields=["status", "updated_at"])
        write_audit_log(actor=request.user, action=AuditAction.CONTENT_HIDDEN, target=comment, reason="管理员隐藏评论")
        return Response({"detail": "已隐藏"})


class AdminCommentDeleteView(APIView):
    permission_classes = [IsModeratorOrAbove]

    @extend_schema(tags=["admin-contents"])
    def post(self, request, pk: int):
        comment = generics.get_object_or_404(Comment, pk=pk)
        comment.soft_delete(request.user, reason="管理员删除")
        write_audit_log(actor=request.user, action=AuditAction.CONTENT_DELETED, target=comment, reason="管理员删除评论")
        return Response({"detail": "已删除"})


class AdminPhotoListView(generics.ListAPIView):
    permission_classes = [IsModeratorOrAbove]

    def get_queryset(self):
        return Photo.objects.select_related("uploader", "album").all().order_by("-created_at")

    @extend_schema(tags=["admin-contents"])
    def get(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(qs)
        if page is not None:
            data = [{"id": p.id, "uploader_name": p.uploader.real_name, "caption": p.caption or "", "album_title": p.album.title, "status": p.status, "created_at": p.created_at} for p in page]
            return self.get_paginated_response(data)
        data = [{"id": p.id, "uploader_name": p.uploader.real_name, "caption": p.caption or "", "album_title": p.album.title, "status": p.status, "created_at": p.created_at} for p in qs]
        return Response(data)


class AdminPhotoHideView(APIView):
    permission_classes = [IsModeratorOrAbove]

    @extend_schema(tags=["admin-contents"])
    def post(self, request, pk: int):
        photo = generics.get_object_or_404(Photo, pk=pk)
        photo.status = ContentStatus.HIDDEN
        photo.save(update_fields=["status", "updated_at"])
        write_audit_log(actor=request.user, action=AuditAction.CONTENT_HIDDEN, target=photo, reason="管理员隐藏照片")
        return Response({"detail": "已隐藏"})


class AdminAlbumListView(generics.ListAPIView):
    permission_classes = [IsModeratorOrAbove]

    def get_queryset(self):
        return Album.objects.select_related("creator").all().order_by("-created_at")

    @extend_schema(tags=["admin-contents"])
    def get(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(qs)
        if page is not None:
            data = [{"id": a.id, "title": a.title, "creator_name": a.creator.real_name, "status": a.status, "created_at": a.created_at} for a in page]
            return self.get_paginated_response(data)
        data = [{"id": a.id, "title": a.title, "creator_name": a.creator.real_name, "status": a.status, "created_at": a.created_at} for a in qs]
        return Response(data)


class AdminAlbumHideView(APIView):
    permission_classes = [IsModeratorOrAbove]

    @extend_schema(tags=["admin-contents"])
    def post(self, request, pk: int):
        album = generics.get_object_or_404(Album, pk=pk)
        album.status = ContentStatus.HIDDEN
        album.save(update_fields=["status", "updated_at"])
        write_audit_log(actor=request.user, action=AuditAction.CONTENT_HIDDEN, target=album, reason="管理员隐藏相册")
        return Response({"detail": "已隐藏"})
