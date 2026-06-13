"""URL routes for profile and classmate directory."""

from django.urls import path

from .views import ClassmateDetailView, ClassmateListView, MyProfileView

urlpatterns = [
    path("me/profile/", MyProfileView.as_view(), name="my-profile"),
    path("classmates/", ClassmateListView.as_view(), name="classmate-list"),
    path("classmates/<uuid:account_id>/", ClassmateDetailView.as_view(), name="classmate-detail"),
]
