"""API views for audit logs."""

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework import generics

from apps.common.permissions import IsModeratorOrAbove

from .models import AuditLog
from .serializers import AuditLogSerializer


class AdminAuditLogListView(generics.ListAPIView):
    permission_classes = [IsModeratorOrAbove]
    serializer_class = AuditLogSerializer
    queryset = AuditLog.objects.select_related("actor", "target_content_type").all()

    @extend_schema(tags=["admin-audit-logs"], responses=AuditLogSerializer)
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
