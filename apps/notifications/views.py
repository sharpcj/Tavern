"""API views for system notifications."""

from __future__ import annotations

from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import IsApprovedClassmate

from .models import Notification
from .serializers import NotificationSerializer


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
        return Response(NotificationSerializer(notification).data)


class NotificationMarkAllReadView(APIView):
    permission_classes = [IsApprovedClassmate]
    serializer_class = NotificationSerializer

    @extend_schema(tags=["notifications"])
    def post(self, request):
        now = timezone.now()
        updated = Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True, read_at=now)
        return Response({"updated": updated})
