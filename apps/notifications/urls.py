"""URL routes for system notifications."""

from django.urls import path

from .views import (
    NotificationListView,
    NotificationMarkAllReadView,
    NotificationMarkReadView,
    NotificationUnreadCountView,
    RealtimeEventSinceView,
    realtime_event_stream_view,
)

urlpatterns = [
    path("events/stream/", realtime_event_stream_view, name="realtime-event-stream"),
    path("events/since/", RealtimeEventSinceView.as_view(), name="realtime-event-since"),
    path("notifications/", NotificationListView.as_view(), name="notification-list"),
    path("notifications/unread-count/", NotificationUnreadCountView.as_view(), name="notification-unread-count"),
    path("notifications/<int:pk>/read/", NotificationMarkReadView.as_view(), name="notification-read"),
    path("notifications/read-all/", NotificationMarkAllReadView.as_view(), name="notification-read-all"),
]
