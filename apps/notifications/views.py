"""API views for system notifications and realtime events."""

from __future__ import annotations

import asyncio
import json

from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.http import JsonResponse, StreamingHttpResponse
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.accounts.models import AccountStatus, ReviewStatus
from apps.common.permissions import IsApprovedClassmate

from .models import Notification, RealtimeEvent
from .serializers import NotificationSerializer, RealtimeEventSerializer
from .services import RealtimeEventType, publish_event

User = get_user_model()


class NotificationListView(generics.ListAPIView):
    permission_classes = [IsApprovedClassmate]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Notification.objects.none()
        qs = Notification.objects.filter(recipient=self.request.user).select_related("target_content_type")
        unread = self.request.query_params.get("unread")
        if unread == "true":
            qs = qs.filter(is_read=False)
        return qs

    @extend_schema(tags=["notifications"], responses=NotificationSerializer)
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class NotificationUnreadCountView(APIView):
    permission_classes = [IsApprovedClassmate]
    serializer_class = NotificationSerializer

    @extend_schema(tags=["notifications"])
    def get(self, request):
        count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        return Response({"unread_count": count})


class NotificationMarkReadView(APIView):
    permission_classes = [IsApprovedClassmate]
    serializer_class = NotificationSerializer

    @extend_schema(tags=["notifications"], responses=NotificationSerializer)
    def post(self, request, pk: int):
        notification = generics.get_object_or_404(Notification, pk=pk, recipient=request.user)
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save(update_fields=["is_read", "read_at"])
            publish_event(
                recipient=request.user,
                event_type=RealtimeEventType.NOTIFICATION_READ,
                target_type="notification",
                target_id=notification.pk,
            )
        return Response(NotificationSerializer(notification).data)


class NotificationMarkAllReadView(APIView):
    permission_classes = [IsApprovedClassmate]
    serializer_class = NotificationSerializer

    @extend_schema(tags=["notifications"])
    def post(self, request):
        now = timezone.now()
        updated = Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True, read_at=now)
        if updated:
            publish_event(
                recipient=request.user,
                event_type=RealtimeEventType.NOTIFICATION_READ,
                target_type="notification",
                payload={"updated": updated},
            )
        return Response({"updated": updated})


def _visible_events_for_user(user):
    return RealtimeEvent.objects.filter(Q(recipient__isnull=True) | Q(recipient=user)).order_by("id")


def _serialize_sse_event_dict(event: dict) -> str:
    payload = {
        "id": event["id"],
        "type": event["event_type"],
        "target_type": event["target_type"],
        "target_id": event["target_id"],
        "payload": event["payload"],
        "created_at": event["created_at"].isoformat(),
    }
    data = json.dumps(payload, ensure_ascii=False, default=str)
    return f"id: {event['id']}\nevent: {event['event_type']}\ndata: {data}\n\n"


@sync_to_async
def _authenticate_realtime_user(request):
    user = None
    try:
        auth_result = JWTAuthentication().authenticate(request)
        if auth_result is not None:
            user = auth_result[0]
    except Exception:
        user = None

    if user is None and getattr(request, "user", None) and request.user.is_authenticated:
        user = request.user

    if user is None or not user.is_authenticated:
        return None, 401

    # Reload a concrete user instance so status checks do not rely on lazy auth objects.
    user = User.objects.get(pk=user.pk)
    if user.review_status in {ReviewStatus.PENDING, ReviewStatus.REJECTED, ReviewStatus.NEED_MORE_INFO}:
        return None, 403
    if user.account_status in {AccountStatus.RESTRICTED, AccountStatus.BANNED}:
        return None, 403
    return user.pk, None


@sync_to_async
def _fetch_realtime_event_dicts(user_id: int, last_id: int) -> list[dict]:
    return list(
        RealtimeEvent.objects.filter(Q(recipient__isnull=True) | Q(recipient_id=user_id), id__gt=last_id)
        .order_by("id")
        .values("id", "event_type", "target_type", "target_id", "payload", "created_at")[:50]
    )


class RealtimeEventSinceView(APIView):
    permission_classes = [IsApprovedClassmate]
    serializer_class = RealtimeEventSerializer

    @extend_schema(
        tags=["realtime-events"],
        parameters=[OpenApiParameter("cursor", int, description="只返回该事件 ID 之后的事件")],
        responses=RealtimeEventSerializer(many=True),
    )
    def get(self, request):
        raw_cursor = request.query_params.get("cursor") or "0"
        try:
            cursor = max(int(raw_cursor), 0)
        except ValueError:
            cursor = 0
        events = list(_visible_events_for_user(request.user).filter(id__gt=cursor)[:100])
        latest_cursor = events[-1].id if events else cursor
        return Response({"results": RealtimeEventSerializer(events, many=True).data, "latest_cursor": latest_cursor})


@extend_schema(tags=["realtime-events"], responses=RealtimeEventSerializer)
async def realtime_event_stream_view(request):
    user_id, error_status = await _authenticate_realtime_user(request)
    if error_status is not None:
        return JsonResponse({"detail": "Authentication credentials were not provided."}, status=error_status)

    raw_cursor = request.headers.get("Last-Event-ID") or request.GET.get("cursor") or "0"
    try:
        cursor = max(int(raw_cursor), 0)
    except ValueError:
        cursor = 0

    async def event_stream():
        last_id = cursor
        heartbeat_counter = 0
        yield ": connected\n\n"
        while True:
            events = await _fetch_realtime_event_dicts(user_id, last_id)
            if events:
                for event in events:
                    last_id = event["id"]
                    yield _serialize_sse_event_dict(event)
                heartbeat_counter = 0
            else:
                heartbeat_counter += 1
                if heartbeat_counter >= 8:
                    yield ": heartbeat\n\n"
                    heartbeat_counter = 0
            await asyncio.sleep(2)

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response
