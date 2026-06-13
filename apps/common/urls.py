"""Common API URL routes."""

from django.urls import path

from .views import HealthCheckView
from .admin_views import (
    AdminAlbumHideView,
    AdminAlbumListView,
    AdminCommentDeleteView,
    AdminCommentHideView,
    AdminCommentListView,
    AdminPhotoHideView,
    AdminPhotoListView,
    AdminPostDeleteView,
    AdminPostHideView,
    AdminPostListView,
)

urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="health-check"),
    path("admin/contents/posts/", AdminPostListView.as_view(), name="admin-post-list"),
    path("admin/contents/posts/<int:pk>/hide/", AdminPostHideView.as_view(), name="admin-post-hide"),
    path("admin/contents/posts/<int:pk>/delete/", AdminPostDeleteView.as_view(), name="admin-post-delete"),
    path("admin/contents/comments/", AdminCommentListView.as_view(), name="admin-comment-list"),
    path("admin/contents/comments/<int:pk>/hide/", AdminCommentHideView.as_view(), name="admin-comment-hide"),
    path("admin/contents/comments/<int:pk>/delete/", AdminCommentDeleteView.as_view(), name="admin-comment-delete"),
    path("admin/contents/photos/", AdminPhotoListView.as_view(), name="admin-photo-list"),
    path("admin/contents/photos/<int:pk>/hide/", AdminPhotoHideView.as_view(), name="admin-photo-hide"),
    path("admin/contents/albums/", AdminAlbumListView.as_view(), name="admin-album-list"),
    path("admin/contents/albums/<int:pk>/hide/", AdminAlbumHideView.as_view(), name="admin-album-hide"),
]
