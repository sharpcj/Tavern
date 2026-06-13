"""DRF permission classes for the Tavern classmate community."""

from __future__ import annotations

from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.request import Request
from rest_framework.views import View

from apps.accounts.models import AccountStatus, ReviewStatus, UserRole


def _is_authenticated_approved_normal(user) -> tuple[bool, str | None]:
    """Check the base conditions for internal API access.

    Returns (allowed, error_code).
    """
    if not user or not user.is_authenticated:
        return False, None  # DRF handles 401 itself
    if user.review_status == ReviewStatus.PENDING:
        return False, "ACCOUNT_PENDING_REVIEW"
    if user.review_status == ReviewStatus.REJECTED:
        return False, "ACCOUNT_REJECTED"
    if user.review_status == ReviewStatus.NEED_MORE_INFO:
        return False, "ACCOUNT_NEED_MORE_INFO"
    if user.account_status == AccountStatus.BANNED:
        return False, "ACCOUNT_BANNED"
    return True, None


class IsApprovedClassmate(BasePermission):
    """Only allow users who have passed identity review and have a normal account."""

    def has_permission(self, request: Request, view: View) -> bool:
        allowed, error_code = _is_authenticated_approved_normal(request.user)
        if not allowed:
            if error_code:
                # Attach error code so the exception handler can use it.
                request._tavern_permission_code = error_code
            return False
        if request.user.account_status == AccountStatus.RESTRICTED:
            request._tavern_permission_code = "ACCOUNT_RESTRICTED"
            return False
        return True


class IsApprovedClassmateOrReadOnly(BasePermission):
    """Allow restricted users to read, but not write."""

    def has_permission(self, request: Request, view: View) -> bool:
        allowed, error_code = _is_authenticated_approved_normal(request.user)
        if not allowed:
            if error_code:
                request._tavern_permission_code = error_code
            return False
        if request.user.account_status == AccountStatus.RESTRICTED:
            if request.method in SAFE_METHODS:
                return True
            request._tavern_permission_code = "ACCOUNT_RESTRICTED"
            return False
        return True


class IsModeratorOrAbove(BasePermission):
    """Allow moderators and super admins to access auxiliary admin endpoints."""

    def has_permission(self, request: Request, view: View) -> bool:
        allowed, error_code = _is_authenticated_approved_normal(request.user)
        if not allowed:
            if error_code:
                request._tavern_permission_code = error_code
            return False
        if request.user.role not in (UserRole.MODERATOR, UserRole.SUPER_ADMIN):
            request._tavern_permission_code = "PERMISSION_DENIED"
            return False
        return True


class IsSuperAdmin(BasePermission):
    """Only allow super admins."""

    def has_permission(self, request: Request, view: View) -> bool:
        allowed, error_code = _is_authenticated_approved_normal(request.user)
        if not allowed:
            if error_code:
                request._tavern_permission_code = error_code
            return False
        if request.user.role != UserRole.SUPER_ADMIN:
            request._tavern_permission_code = "PERMISSION_DENIED"
            return False
        return True
