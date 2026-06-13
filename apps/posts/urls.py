"""URL routes for posts and comments."""

from django.urls import path

from .views import (
    CommentDeleteView,
    CommentListView,
    CommentReplyView,
    PostDetailView,
    PostListView,
    PostPinView,
)

urlpatterns = [
    path("posts/", PostListView.as_view(), name="post-list"),
    path("posts/<int:pk>/", PostDetailView.as_view(), name="post-detail"),
    path("posts/<int:pk>/pin/", PostPinView.as_view(), name="post-pin"),
    path("posts/<int:post_pk>/comments/", CommentListView.as_view(), name="comment-list"),
    path("comments/<int:pk>/replies/", CommentReplyView.as_view(), name="comment-reply"),
    path("comments/<int:pk>/", CommentDeleteView.as_view(), name="comment-delete"),
]
