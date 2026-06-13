"""URL routes for albums and photos."""

from django.urls import path

from .views import (
    AlbumDetailView,
    AlbumListCreateView,
    PhotoCommentCreateView,
    PhotoCommentDeleteView,
    PhotoDeleteView,
    PhotoDetailView,
    PhotoUploadView,
)

urlpatterns = [
    path("albums/", AlbumListCreateView.as_view(), name="album-list"),
    path("albums/<int:pk>/", AlbumDetailView.as_view(), name="album-detail"),
    path("albums/<int:pk>/photos/", PhotoUploadView.as_view(), name="album-photo-upload"),
    path("photos/<int:pk>/", PhotoDetailView.as_view(), name="photo-detail"),
    path("photos/<int:pk>/delete/", PhotoDeleteView.as_view(), name="photo-delete"),
    path("photos/<int:pk>/comments/", PhotoCommentCreateView.as_view(), name="photo-comment-create"),
    path("photo-comments/<int:pk>/", PhotoCommentDeleteView.as_view(), name="photo-comment-delete"),
]
