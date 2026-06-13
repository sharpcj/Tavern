"""Admin API views for activity management."""

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit_logs.models import AuditAction
from apps.audit_logs.services import write_audit_log
from apps.common.permissions import IsModeratorOrAbove, IsSuperAdmin

from .models import Activity, ActivityStatus


class AdminActivityListView(generics.ListAPIView):
    permission_classes = [IsModeratorOrAbove]

    def get_queryset(self):
        qs = Activity.objects.select_related("initiator").all().order_by("-created_at")
        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        return qs

    @extend_schema(tags=["admin-activities"])
    def get(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(qs)
        if page is not None:
            data = [{"id": a.id, "title": a.title, "activity_type": a.activity_type, "initiator_name": a.initiator_name_snapshot, "status": a.status, "created_at": a.created_at} for a in page]
            return self.get_paginated_response(data)
        data = [{"id": a.id, "title": a.title, "activity_type": a.activity_type, "initiator_name": a.initiator_name_snapshot, "status": a.status, "created_at": a.created_at} for a in qs]
        return Response(data)


class AdminActivityStatusUpdateView(APIView):
    permission_classes = [IsModeratorOrAbove]

    @extend_schema(tags=["admin-activities"])
    def post(self, request, pk: int):
        activity = generics.get_object_or_404(Activity, pk=pk)
        new_status = request.data.get("status")
        if new_status not in dict(ActivityStatus.choices):
            return Response({"detail": "无效状态"}, status=status.HTTP_400_BAD_REQUEST)
        old_status = activity.status
        activity.status = new_status
        activity.save(update_fields=["status", "updated_at"])
        write_audit_log(
            actor=request.user,
            action=AuditAction.ACTIVITY_STATUS_CHANGED,
            target=activity,
            reason=f"活动状态变更: {old_status} → {new_status}",
            metadata={"old_status": old_status, "new_status": new_status},
        )
        return Response({"detail": "状态已更新"})


class AdminActivityDeleteView(APIView):
    permission_classes = [IsSuperAdmin]

    @extend_schema(tags=["admin-activities"])
    def post(self, request, pk: int):
        activity = generics.get_object_or_404(Activity, pk=pk)
        reason = request.data.get("reason", "管理员删除")
        activity.status = ActivityStatus.CANCELLED
        activity.save(update_fields=["status", "updated_at"])
        write_audit_log(actor=request.user, action=AuditAction.ACTIVITY_DELETED, target=activity, reason=f"管理员删除活动: {reason}")
        return Response({"detail": "活动已取消"})
