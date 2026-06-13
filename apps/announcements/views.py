"""API views for announcements."""

from __future__ import annotations

from django.db.models import Q
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.enums import ContentStatus
from apps.common.permissions import IsApprovedClassmate, IsModeratorOrAbove
from apps.audit_logs.models import AuditAction
from apps.audit_logs.services import write_audit_log

from .models import Announcement, AnnouncementReadReceipt
from .serializers import AnnouncementDetailSerializer, AnnouncementListSerializer, AnnouncementWriteSerializer


def active_announcements_queryset():
    now = timezone.now()
    return Announcement.objects.filter(status=ContentStatus.PUBLISHED).filter(Q(expires_at__isnull=True) | Q(expires_at__gt=now))


class AnnouncementListCreateView(generics.ListCreateAPIView):
    """List active announcements or create a new announcement."""

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsModeratorOrAbove()]
        return [IsApprovedClassmate()]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AnnouncementWriteSerializer
        return AnnouncementListSerializer

    def get_queryset(self):
        return active_announcements_queryset()

    @extend_schema(
        tags=["announcements"],
        parameters=[OpenApiParameter("page", int), OpenApiParameter("page_size", int)],
        responses=AnnouncementListSerializer,
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(tags=["announcements"], request=AnnouncementWriteSerializer, responses=AnnouncementDetailSerializer)
    def post(self, request, *args, **kwargs):
        write_serializer = self.get_serializer(data=request.data)
        write_serializer.is_valid(raise_exception=True)
        announcement = write_serializer.save()
        write_audit_log(actor=request.user, action=AuditAction.ANNOUNCEMENT_CREATED, target=announcement, reason=announcement.title)
        return Response(
            AnnouncementDetailSerializer(announcement, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class PinnedAnnouncementListView(generics.ListAPIView):
    """List active pinned announcements for the homepage banner."""

    permission_classes = [IsApprovedClassmate]
    serializer_class = AnnouncementListSerializer

    def get_queryset(self):
        return active_announcements_queryset().filter(is_pinned=True)

    @extend_schema(tags=["announcements"], responses=AnnouncementListSerializer)
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AnnouncementDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or soft-delete an announcement."""

    queryset = Announcement.objects.all()

    def get_permissions(self):
        if self.request.method in ("PATCH", "PUT", "DELETE"):
            return [IsModeratorOrAbove()]
        return [IsApprovedClassmate()]

    def get_serializer_class(self):
        if self.request.method in ("PATCH", "PUT"):
            return AnnouncementWriteSerializer
        return AnnouncementDetailSerializer

    @extend_schema(tags=["announcements"], responses=AnnouncementDetailSerializer)
    def get(self, request, *args, **kwargs):
        announcement = self.get_object()
        if not announcement.is_active:
            return Response({"detail": "公告不可用"}, status=status.HTTP_404_NOT_FOUND)
        return Response(AnnouncementDetailSerializer(announcement, context={"request": request}).data)

    @extend_schema(tags=["announcements"], request=AnnouncementWriteSerializer, responses=AnnouncementDetailSerializer)
    def patch(self, request, *args, **kwargs):
        announcement = self.get_object()
        serializer = AnnouncementWriteSerializer(announcement, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        announcement = serializer.save()
        write_audit_log(actor=request.user, action=AuditAction.ANNOUNCEMENT_UPDATED, target=announcement, reason=announcement.title)
        return Response(AnnouncementDetailSerializer(announcement, context={"request": request}).data)

    @extend_schema(tags=["announcements"])
    def delete(self, request, *args, **kwargs):
        announcement = self.get_object()
        announcement.soft_delete(request.user)
        write_audit_log(actor=request.user, action=AuditAction.ANNOUNCEMENT_DELETED, target=announcement, reason=announcement.title)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AnnouncementReadConfirmView(APIView):
    """Confirm that the current user has read an important announcement."""

    permission_classes = [IsApprovedClassmate]
    serializer_class = AnnouncementDetailSerializer

    @extend_schema(tags=["announcements"], responses=AnnouncementDetailSerializer)
    def post(self, request, pk: int):
        announcement = generics.get_object_or_404(active_announcements_queryset(), pk=pk)
        if not announcement.require_read_confirm:
            return Response({"detail": "该公告不需要确认已读"}, status=status.HTTP_400_BAD_REQUEST)
        AnnouncementReadReceipt.objects.get_or_create(announcement=announcement, user=request.user)
        return Response(AnnouncementDetailSerializer(announcement, context={"request": request}).data)
