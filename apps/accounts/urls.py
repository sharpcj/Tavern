"""URL routes for account registration and review."""

from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import AdminReviewAccountView, CurrentUserView, PendingAccountListView, RegisterView

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/token/", TokenObtainPairView.as_view(), name="token-obtain-pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("auth/me/", CurrentUserView.as_view(), name="auth-me"),
    path("admin/accounts/pending/", PendingAccountListView.as_view(), name="admin-accounts-pending"),
    path("admin/accounts/<uuid:account_id>/review/", AdminReviewAccountView.as_view(), name="admin-account-review"),
]
