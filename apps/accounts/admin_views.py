"""Admin API views for user management."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit_logs.models import AuditAction
from apps.audit_logs.services import write_audit_log
from apps.common.permissions import IsModeratorOrAbove, IsSuperAdmin
from apps.notifications.services import NotificationType, create_notification

from .models import AccountStatus, ReviewStatus, UserRole
from .serializers import AdminUserDetailSerializer, AdminUserListSerializer, AdminUserUpdateSerializer, ReviewActionSerializer

User = get_user_model()


class AdminUserListView(generics.ListAPIView):
    permission_classes = [IsSuperAdmin]
    serializer_class = AdminUserListSerializer

    def get_queryset(self):
        qs = User.objects.all().order_by("-date_joined")
        status_param = self.request.query_params.get("status")
        role_param = self.request.query_params.get("role")
        if status_param:
            qs = qs.filter(account_status=status_param)
        if role_param:
            qs = qs.filter(role=role_param)
        return qs

    @extend_schema(tags=["admin-users"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AdminUserUpdateView(APIView):
    permission_classes = [IsSuperAdmin]

    @extend_schema(request=AdminUserUpdateSerializer, responses=AdminUserDetailSerializer, tags=["admin-users"])
    def patch(self, request, account_id: str):
        user = generics.get_object_or_404(User, account_id=account_id)
        serializer = AdminUserUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if "role" in data:
            old_role = user.role
            user.role = data["role"]
            user.save(update_fields=["role", "updated_at"])
            write_audit_log(
                actor=request.user,
                action=AuditAction.ROLE_CHANGED,
                target=user,
                reason=f"角色变更: {old_role} → {data['role']}",
                metadata={"old_role": old_role, "new_role": data["role"]},
            )

        if "account_status" in data:
            old_status = user.account_status
            user.account_status = data["account_status"]
            user.save(update_fields=["account_status", "updated_at"])
            action_map = {
                AccountStatus.NORMAL: AuditAction.ACCOUNT_STATUS_CHANGED,
                AccountStatus.RESTRICTED: AuditAction.USER_RESTRICTED,
                AccountStatus.BANNED: AuditAction.USER_BANNED,
            }
            action = action_map.get(data["account_status"], AuditAction.ACCOUNT_STATUS_CHANGED)
            write_audit_log(
                actor=request.user,
                action=action,
                target=user,
                reason=f"状态变更: {old_status} → {data['account_status']}",
                metadata={"old_status": old_status, "new_status": data["account_status"]},
            )

        user.refresh_from_db()
        return Response(AdminUserDetailSerializer(user).data)


class AdminReviewListView(generics.ListAPIView):
    permission_classes = [IsSuperAdmin]
    serializer_class = AdminUserListSerializer

    def get_queryset(self):
        return User.objects.filter(
            review_status__in=[ReviewStatus.PENDING, ReviewStatus.NEED_MORE_INFO]
        ).order_by("date_joined")

    @extend_schema(tags=["admin-users"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AdminReviewActionView(APIView):
    permission_classes = [IsSuperAdmin]

    @extend_schema(request=ReviewActionSerializer, responses=AdminUserListSerializer, tags=["admin-users"])
    def post(self, request, account_id: str):
        user = generics.get_object_or_404(User, account_id=account_id)
        serializer = ReviewActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action = serializer.validated_data["action"]
        reason = serializer.validated_data.get("reason", "")

        if action == "approve":
            user.review_status = ReviewStatus.APPROVED
            user.account_status = AccountStatus.NORMAL
        elif action == "reject":
            user.review_status = ReviewStatus.REJECTED
        elif action == "need_more_info":
            user.review_status = ReviewStatus.NEED_MORE_INFO

        user.reviewed_by = request.user
        user.reviewed_at = __import__("django").utils.timezone.now()
        user.review_note = reason
        user.save(update_fields=["review_status", "account_status", "reviewed_by", "reviewed_at", "review_note", "updated_at"])

        write_audit_log(
            actor=request.user,
            action=AuditAction.USER_REVIEWED,
            target=user,
            reason=f"审核操作: {action} - {reason}",
            metadata={"action": action},
        )
        create_notification(
            recipient=user,
            notification_type=NotificationType.REVIEW_RESULT,
            title="账号审核结果已更新",
            content=f"你的账号审核状态已更新为：{user.get_review_status_display()}。{reason}".strip(),
            target=user,
        )

        return Response(AdminUserListSerializer(user).data)
