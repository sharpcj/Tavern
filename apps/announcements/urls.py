"""URL routes for announcements."""

from django.urls import path

from .views import AnnouncementDetailView, AnnouncementListCreateView, AnnouncementReadConfirmView, PinnedAnnouncementListView

urlpatterns = [
    path("announcements/", AnnouncementListCreateView.as_view(), name="announcement-list"),
    path("announcements/pinned/", PinnedAnnouncementListView.as_view(), name="announcement-pinned"),
    path("announcements/<int:pk>/", AnnouncementDetailView.as_view(), name="announcement-detail"),
    path("announcements/<int:pk>/read-confirm/", AnnouncementReadConfirmView.as_view(), name="announcement-read-confirm"),
]
