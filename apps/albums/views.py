"""API views for albums, photos and photo comments."""

from __future__ import annotations

from django.http import Http404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import UserRole
from apps.common.enums import ContentStatus
from apps.common.permissions import IsApprovedClassmate

from .models import Album, Photo, PhotoComment
from .serializers import (
    AlbumCreateUpdateSerializer,
    AlbumDetailSerializer,
    AlbumListSerializer,
    PhotoCommentCreateSerializer,
    PhotoCommentSerializer,
    PhotoDetailSerializer,
    PhotoListSerializer,
    PhotoUploadSerializer,
)


def is_moderator_or_above(user) -> bool:
    return user.role in (UserRole.MODERATOR, UserRole.SUPER_ADMIN)


def active_albums():
    return Album.objects.filter(status=ContentStatus.PUBLISHED)


def active_photos():
    return Photo.objects.filter(status=ContentStatus.PUBLISHED, album__status=ContentStatus.PUBLISHED)


class AlbumListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsApprovedClassmate]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AlbumCreateUpdateSerializer
        return AlbumListSerializer

    def get_queryset(self):
        qs = active_albums()
        category = self.request.query_params.get("category")
        activity = self.request.query_params.get("activity")
        if category:
            qs = qs.filter(category=category)
        if activity:
            qs = qs.filter(activity_id=activity)
        return qs

    @extend_schema(
        tags=["albums"],
        parameters=[OpenApiParameter("category", str), OpenApiParameter("activity", int), OpenApiParameter("page", int)],
        responses=AlbumListSerializer,
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(tags=["albums"], request=AlbumCreateUpdateSerializer, responses=AlbumDetailSerializer)
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        album = serializer.save()
        return Response(AlbumDetailSerializer(album, context={"request": request}).data, status=status.HTTP_201_CREATED)


class AlbumDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsApprovedClassmate]
    queryset = Album.objects.all()

    def get_serializer_class(self):
        if self.request.method in ("PATCH", "PUT"):
            return AlbumCreateUpdateSerializer
        return AlbumDetailSerializer

    def get_object(self):
        obj = super().get_object()
        if self.request.method == "GET" and obj.status != ContentStatus.PUBLISHED:
            raise Http404
        return obj

    @extend_schema(tags=["albums"], responses=AlbumDetailSerializer)
    def get(self, request, *args, **kwargs):
        return Response(AlbumDetailSerializer(self.get_object(), context={"request": request}).data)

    @extend_schema(tags=["albums"], request=AlbumCreateUpdateSerializer, responses=AlbumDetailSerializer)
    def patch(self, request, *args, **kwargs):
        album = self.get_object()
        if album.creator != request.user and not is_moderator_or_above(request.user):
            return Response({"detail": "只有创建人或管理员可以编辑相册"}, status=status.HTTP_403_FORBIDDEN)
        serializer = AlbumCreateUpdateSerializer(album, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        album = serializer.save()
        return Response(AlbumDetailSerializer(album, context={"request": request}).data)

    @extend_schema(tags=["albums"])
    def delete(self, request, *args, **kwargs):
        album = self.get_object()
        if album.creator != request.user and not is_moderator_or_above(request.user):
            return Response({"detail": "只有创建人或管理员可以删除相册"}, status=status.HTTP_403_FORBIDDEN)
        album.soft_delete(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PhotoUploadView(APIView):
    permission_classes = [IsApprovedClassmate]
    serializer_class = PhotoUploadSerializer

    @extend_schema(tags=["albums"], request=PhotoUploadSerializer, responses=PhotoDetailSerializer)
    def post(self, request, pk: int):
        album = generics.get_object_or_404(active_albums(), pk=pk)
        serializer = PhotoUploadSerializer(data=request.data, context={"request": request, "album": album})
        serializer.is_valid(raise_exception=True)
        photo = serializer.save()
        return Response(PhotoDetailSerializer(photo, context={"request": request}).data, status=status.HTTP_201_CREATED)


class PhotoDetailView(generics.RetrieveAPIView):
    permission_classes = [IsApprovedClassmate]
    serializer_class = PhotoDetailSerializer

    def get_queryset(self):
        return active_photos()

    @extend_schema(tags=["albums"], responses=PhotoDetailSerializer)
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class PhotoDeleteView(APIView):
    permission_classes = [IsApprovedClassmate]
    serializer_class = PhotoDetailSerializer

    @extend_schema(tags=["albums"])
    def delete(self, request, pk: int):
        photo = generics.get_object_or_404(Photo, pk=pk)
        if photo.uploader != request.user and not is_moderator_or_above(request.user):
            return Response({"detail": "只有上传人或管理员可以删除照片"}, status=status.HTTP_403_FORBIDDEN)
        photo.soft_delete(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PhotoCommentCreateView(APIView):
    permission_classes = [IsApprovedClassmate]
    serializer_class = PhotoCommentCreateSerializer

    @extend_schema(tags=["albums"], request=PhotoCommentCreateSerializer, responses=PhotoCommentSerializer)
    def post(self, request, pk: int):
        photo = generics.get_object_or_404(active_photos(), pk=pk)
        serializer = PhotoCommentCreateSerializer(data=request.data, context={"request": request, "photo": photo})
        serializer.is_valid(raise_exception=True)
        comment = serializer.save()
        return Response(PhotoCommentSerializer(comment, context={"request": request}).data, status=status.HTTP_201_CREATED)


class PhotoCommentDeleteView(APIView):
    permission_classes = [IsApprovedClassmate]
    serializer_class = PhotoCommentSerializer

    @extend_schema(tags=["albums"])
    def delete(self, request, pk: int):
        comment = generics.get_object_or_404(PhotoComment, pk=pk)
        if comment.author != request.user and not is_moderator_or_above(request.user):
            return Response({"detail": "只有作者或管理员可以删除评论"}, status=status.HTTP_403_FORBIDDEN)
        comment.soft_delete(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)
