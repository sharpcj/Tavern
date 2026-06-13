"""URL routes for birthday wishes."""

from django.urls import path

from .views import BirthdayWishDeleteView, BirthdayWishHideView, BirthdayWishListCreateView, CurrentMonthBirthdayListView

urlpatterns = [
    path("birthdays/current-month/", CurrentMonthBirthdayListView.as_view(), name="birthday-current-month"),
    path("birthdays/wishes/", BirthdayWishListCreateView.as_view(), name="birthday-wish-list"),
    path("birthdays/wishes/<int:pk>/", BirthdayWishDeleteView.as_view(), name="birthday-wish-delete"),
    path("birthdays/wishes/<int:pk>/hide/", BirthdayWishHideView.as_view(), name="birthday-wish-hide"),
]
