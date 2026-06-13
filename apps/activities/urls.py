"""URL routes for activities."""

from django.urls import path

from .admin_views import AdminActivityDeleteView, AdminActivityListView, AdminActivityStatusUpdateView
from .views import (
    ActivityDeleteView,
    ActivityDetailView,
    ActivityEditView,
    ActivityListView,
    ActivityStatusUpdateView,
    ChainView,
    SignupView,
    VoteView,
)

urlpatterns = [
    path("activities/", ActivityListView.as_view(), name="activity-list"),
    path("activities/<int:pk>/", ActivityDetailView.as_view(), name="activity-detail"),
    path("activities/<int:pk>/edit/", ActivityEditView.as_view(), name="activity-edit"),
    path("activities/<int:pk>/update-status/", ActivityStatusUpdateView.as_view(), name="activity-update-status"),
    path("activities/<int:pk>/delete/", ActivityDeleteView.as_view(), name="activity-delete"),
    path("activities/<int:pk>/signup/", SignupView.as_view(), name="activity-signup"),
    path("activities/<int:pk>/vote/", VoteView.as_view(), name="activity-vote"),
    path("activities/<int:pk>/chain/", ChainView.as_view(), name="activity-chain"),
    path("admin/activities/", AdminActivityListView.as_view(), name="admin-activity-list"),
    path("admin/activities/<int:pk>/update-status/", AdminActivityStatusUpdateView.as_view(), name="admin-activity-status-update"),
    path("admin/activities/<int:pk>/delete/", AdminActivityDeleteView.as_view(), name="admin-activity-delete"),
]
