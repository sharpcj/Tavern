"""URL routes for account registration and review."""

from django.urls import path
from .views import AdminReviewAccountView, CurrentUserView, PendingAccountListView, RegisterView, TavernTokenObtainPairView, TavernTokenRefreshView
from .admin_views import AdminReviewActionView, AdminReviewListView, AdminUserListView, AdminUserUpdateView

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/token/", TavernTokenObtainPairView.as_view(), name="token-obtain-pair"),
    path("auth/token/refresh/", TavernTokenRefreshView.as_view(), name="token-refresh"),
    path("auth/me/", CurrentUserView.as_view(), name="auth-me"),
    path("admin/accounts/pending/", PendingAccountListView.as_view(), name="admin-accounts-pending"),
    path("admin/accounts/<uuid:account_id>/review/", AdminReviewAccountView.as_view(), name="admin-account-review"),
    path("admin/users/", AdminUserListView.as_view(), name="admin-user-list"),
    path("admin/users/<uuid:account_id>/", AdminUserUpdateView.as_view(), name="admin-user-update"),
    path("admin/users/review/", AdminReviewListView.as_view(), name="admin-review-list"),
    path("admin/users/<uuid:account_id>/review-action/", AdminReviewActionView.as_view(), name="admin-review-action"),
]
