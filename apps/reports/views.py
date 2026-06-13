"""API views for content reports."""

from __future__ import annotations

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit_logs.models import AuditAction
from apps.audit_logs.services import write_audit_log
from apps.common.permissions import IsApprovedClassmate, IsModeratorOrAbove
from apps.moderation.services import apply_moderation_action

from .models import Report, ReportStatus
from .serializers import ReportCreateSerializer, ReportHandleSerializer, ReportSerializer


class ReportCreateView(APIView):
    permission_classes = [IsApprovedClassmate]
    serializer_class = ReportCreateSerializer

    @extend_schema(tags=["reports"], request=ReportCreateSerializer, responses=ReportSerializer)
    def post(self, request):
        serializer = ReportCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        report = serializer.save()
        write_audit_log(
            actor=request.user,
            action=AuditAction.REPORT_CREATED,
            target=report,
            reason=report.get_reason_display(),
            metadata={"object_id": report.object_id, "content_type": str(report.content_type)},
        )
        return Response(ReportSerializer(report, context={"request": request}).data, status=status.HTTP_201_CREATED)


class AdminReportListView(generics.ListAPIView):
    permission_classes = [IsModeratorOrAbove]
    serializer_class = ReportSerializer

    def get_queryset(self):
        qs = Report.objects.select_related("reporter", "handled_by", "content_type").all()
        status_value = self.request.query_params.get("status")
        if status_value:
            qs = qs.filter(status=status_value)
        return qs

    @extend_schema(tags=["admin-reports"], parameters=[OpenApiParameter("status", str)], responses=ReportSerializer)
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AdminReportDetailView(generics.RetrieveAPIView):
    permission_classes = [IsModeratorOrAbove]
    serializer_class = ReportSerializer
    queryset = Report.objects.select_related("reporter", "handled_by", "content_type").all()

    @extend_schema(tags=["admin-reports"], responses=ReportSerializer)
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AdminReportHandleView(APIView):
    permission_classes = [IsModeratorOrAbove]
    serializer_class = ReportHandleSerializer

    @extend_schema(tags=["admin-reports"], request=ReportHandleSerializer, responses=ReportSerializer)
    def post(self, request, pk: int):
        report = generics.get_object_or_404(Report, pk=pk)
        serializer = ReportHandleSerializer(data=request.data, context={"report": report})
        serializer.is_valid(raise_exception=True)
        apply_moderation_action(
            report=report,
            action_type=serializer.validated_data["action_type"],
            actor=request.user,
            reason=serializer.validated_data.get("reason", ""),
        )
        report.refresh_from_db()
        return Response(ReportSerializer(report, context={"request": request}).data)
