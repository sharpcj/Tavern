"""API views for activities."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import AccountStatus, ReviewStatus
from apps.common.permissions import IsApprovedClassmate, IsSuperAdmin
from apps.notifications.services import NotificationType, RealtimeEventType, create_notifications, publish_event

from .models import (
    Activity,
    ActivityStatus,
    ActivityType,
    ChainRecord,
    Signup,
    VoteOption,
    VoteRecord,
)
from .serializers import (
    ActivityCreateSerializer,
    ActivityDetailSerializer,
    ActivityListSerializer,
    ActivityStatusUpdateSerializer,
    ChainRecordSerializer,
    SignupSerializer,
    VoteSerializer,
)

User = get_user_model()


def publish_activity_updated(activity: Activity, action: str) -> None:
    publish_event(
        event_type=RealtimeEventType.ACTIVITY_UPDATED,
        target_type="activity",
        target_id=activity.pk,
        payload={"activity_id": activity.pk, "action": action},
    )


class ActivityListView(generics.ListCreateAPIView):
    permission_classes = [IsApprovedClassmate]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ActivityCreateSerializer
        return ActivityListSerializer

    def get_queryset(self):
        qs = Activity.objects.all()
        status_filter = self.request.query_params.get("status", "").strip()
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    def perform_create(self, serializer):
        activity = serializer.save()
        recipients = User.objects.filter(
            review_status=ReviewStatus.APPROVED,
            account_status=AccountStatus.NORMAL,
        ).exclude(pk=self.request.user.pk)
        create_notifications(
            recipients=recipients,
            notification_type=NotificationType.ACTIVITY_STATUS,
            title="有新活动发布",
            content=f"{self.request.user.real_name} 发起了活动「{activity.title}」，快去看看吧。",
            target=activity,
        )

    @extend_schema(
        tags=["activities"],
        parameters=[
            OpenApiParameter("status", str, description="按状态筛选"),
            OpenApiParameter("page", int),
            OpenApiParameter("page_size", int),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(request=ActivityCreateSerializer, responses=ActivityDetailSerializer, tags=["activities"])
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class ActivityDetailView(generics.RetrieveAPIView):
    permission_classes = [IsApprovedClassmate]
    queryset = Activity.objects.all()
    serializer_class = ActivityDetailSerializer

    @extend_schema(responses=ActivityDetailSerializer, tags=["activities"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ActivityEditView(APIView):
    permission_classes = [IsApprovedClassmate]

    @extend_schema(request=ActivityCreateSerializer, responses=ActivityDetailSerializer, tags=["activities"])
    def patch(self, request, pk: int):
        activity = generics.get_object_or_404(Activity, pk=pk)
        if activity.initiator != request.user:
            return Response({"detail": "只有发起人可以编辑活动"}, status=status.HTTP_403_FORBIDDEN)
        serializer = ActivityCreateSerializer(activity, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ActivityDetailSerializer(activity).data)


class ActivityStatusUpdateView(APIView):
    permission_classes = [IsApprovedClassmate]

    @extend_schema(request=ActivityStatusUpdateSerializer, responses=ActivityDetailSerializer, tags=["activities"])
    def post(self, request, pk: int):
        activity = generics.get_object_or_404(Activity, pk=pk)
        if activity.initiator != request.user:
            return Response({"detail": "只有发起人可以更新活动状态"}, status=status.HTTP_403_FORBIDDEN)
        serializer = ActivityStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        activity.status = serializer.validated_data["status"]
        activity.save(update_fields=["status", "updated_at"])
        return Response(ActivityDetailSerializer(activity).data)


class ActivityDeleteView(APIView):
    permission_classes = [IsSuperAdmin]
    serializer_class = ActivityDetailSerializer

    @extend_schema(tags=["activities"])
    def delete(self, request, pk: int):
        activity = generics.get_object_or_404(Activity, pk=pk)
        activity.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SignupView(APIView):
    permission_classes = [IsApprovedClassmate]
    serializer_class = SignupSerializer

    @extend_schema(request=SignupSerializer, tags=["activities"])
    def post(self, request, pk: int):
        activity = generics.get_object_or_404(Activity, pk=pk)
        if activity.activity_type != ActivityType.GATHERING:
            return Response({"detail": "该活动不是聚会报名"}, status=status.HTTP_400_BAD_REQUEST)
        if activity.status != ActivityStatus.OPEN:
            return Response({"detail": "活动不在报名中"}, status=status.HTTP_400_BAD_REQUEST)
        if Signup.objects.filter(activity=activity, user=request.user).exists():
            return Response({"detail": "已报名"}, status=status.HTTP_400_BAD_REQUEST)
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        Signup.objects.create(
            activity=activity, user=request.user,
            real_name_snapshot=request.user.real_name,
            **serializer.validated_data,
        )
        publish_activity_updated(activity, "signup.created")
        return Response({"detail": "报名成功"}, status=status.HTTP_201_CREATED)

    @extend_schema(tags=["activities"])
    def delete(self, request, pk: int):
        activity = generics.get_object_or_404(Activity, pk=pk)
        if activity.status not in (ActivityStatus.OPEN,):
            return Response({"detail": "活动已截止，不能取消报名"}, status=status.HTTP_400_BAD_REQUEST)
        signup = generics.get_object_or_404(Signup, activity=activity, user=request.user)
        signup.delete()
        publish_activity_updated(activity, "signup.deleted")
        return Response(status=status.HTTP_204_NO_CONTENT)


class VoteView(APIView):
    permission_classes = [IsApprovedClassmate]
    serializer_class = VoteSerializer

    @extend_schema(request=VoteSerializer, tags=["activities"])
    def post(self, request, pk: int):
        activity = generics.get_object_or_404(Activity, pk=pk)
        if activity.activity_type != ActivityType.VOTING:
            return Response({"detail": "该活动不是投票"}, status=status.HTTP_400_BAD_REQUEST)
        if activity.status != ActivityStatus.OPEN:
            return Response({"detail": "投票已截止"}, status=status.HTTP_400_BAD_REQUEST)
        serializer = VoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        option_ids = serializer.validated_data["option_ids"]

        if not activity.is_multi_choice and len(option_ids) > 1:
            return Response({"detail": "该投票为单选"}, status=status.HTTP_400_BAD_REQUEST)

        existing = VoteRecord.objects.filter(option__activity=activity, user=request.user)
        if existing.exists():
            if not activity.allow_vote_change:
                return Response({"detail": "不允许修改投票"}, status=status.HTTP_400_BAD_REQUEST)
            existing.delete()

        for oid in option_ids:
            option = generics.get_object_or_404(VoteOption, pk=oid, activity=activity)
            VoteRecord.objects.create(
                option=option, user=request.user,
                real_name_snapshot=request.user.real_name,
            )
        publish_activity_updated(activity, "vote.submitted")
        return Response({"detail": "投票成功"}, status=status.HTTP_201_CREATED)


class ChainView(APIView):
    permission_classes = [IsApprovedClassmate]
    serializer_class = ChainRecordSerializer

    @extend_schema(request=ChainRecordSerializer, tags=["activities"])
    def post(self, request, pk: int):
        activity = generics.get_object_or_404(Activity, pk=pk)
        if activity.activity_type != ActivityType.CHAIN:
            return Response({"detail": "该活动不是接龙"}, status=status.HTTP_400_BAD_REQUEST)
        if activity.status != ActivityStatus.OPEN:
            return Response({"detail": "接龙已截止"}, status=status.HTTP_400_BAD_REQUEST)
        if ChainRecord.objects.filter(activity=activity, user=request.user).exists():
            return Response({"detail": "已填写"}, status=status.HTTP_400_BAD_REQUEST)
        serializer = ChainRecordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ChainRecord.objects.create(
            activity=activity, user=request.user,
            real_name_snapshot=request.user.real_name,
            **serializer.validated_data,
        )
        publish_activity_updated(activity, "chain.created")
        return Response({"detail": "接龙填写成功"}, status=status.HTTP_201_CREATED)
