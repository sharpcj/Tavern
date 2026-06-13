"""Tests for DRF permission classes and unified error responses."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import AccountStatus, ReviewStatus

User = get_user_model()

# A simple view protected by IsApprovedClassmate for testing.
# We reuse the existing auth/me/ endpoint but override its permission_classes
# in the test via @override_settings or by testing the admin endpoints directly.


class IsApprovedClassmateTests(APITestCase):
    """Test that IsApprovedClassmate blocks users based on review/account status."""

    @classmethod
    def setUpTestData(cls):
        cls.pending_user = User.objects.create_user(
            email="pending@example.com", password="Pass1234!",
            real_name="待审核", high_school="一中", high_school_class="一班",
        )
        cls.approved_user = User.objects.create_user(
            email="approved@example.com", password="Pass1234!",
            real_name="已通过", high_school="一中", high_school_class="一班",
        )
        cls.approved_user.review_status = ReviewStatus.APPROVED
        cls.approved_user.save()

        cls.rejected_user = User.objects.create_user(
            email="rejected@example.com", password="Pass1234!",
            real_name="已拒绝", high_school="一中", high_school_class="一班",
        )
        cls.rejected_user.review_status = ReviewStatus.REJECTED
        cls.rejected_user.save()

        cls.need_info_user = User.objects.create_user(
            email="needinfo@example.com", password="Pass1234!",
            real_name="需补充", high_school="一中", high_school_class="一班",
        )
        cls.need_info_user.review_status = ReviewStatus.NEED_MORE_INFO
        cls.need_info_user.save()

        cls.banned_user = User.objects.create_user(
            email="banned@example.com", password="Pass1234!",
            real_name="已封禁", high_school="一中", high_school_class="一班",
        )
        cls.banned_user.review_status = ReviewStatus.APPROVED
        cls.banned_user.account_status = AccountStatus.BANNED
        cls.banned_user.save()

        cls.restricted_user = User.objects.create_user(
            email="restricted@example.com", password="Pass1234!",
            real_name="已限制", high_school="一中", high_school_class="一班",
        )
        cls.restricted_user.review_status = ReviewStatus.APPROVED
        cls.restricted_user.account_status = AccountStatus.RESTRICTED
        cls.restricted_user.save()

        cls.super_admin = User.objects.create_superuser(
            email="admin@example.com", password="AdminPass123!",
        )

    # --- Admin endpoint tests (protected by IsSuperAdmin) ---

    def test_pending_user_blocked_from_admin(self):
        self.client.force_authenticate(self.pending_user)
        resp = self.client.get(reverse("admin-accounts-pending"))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(resp.data["code"], "ACCOUNT_PENDING_REVIEW")

    def test_rejected_user_blocked_from_admin(self):
        self.client.force_authenticate(self.rejected_user)
        resp = self.client.get(reverse("admin-accounts-pending"))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(resp.data["code"], "ACCOUNT_REJECTED")

    def test_need_more_info_user_blocked_from_admin(self):
        self.client.force_authenticate(self.need_info_user)
        resp = self.client.get(reverse("admin-accounts-pending"))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(resp.data["code"], "ACCOUNT_NEED_MORE_INFO")

    def test_banned_user_blocked_from_admin(self):
        self.client.force_authenticate(self.banned_user)
        resp = self.client.get(reverse("admin-accounts-pending"))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(resp.data["code"], "ACCOUNT_BANNED")

    def test_restricted_user_blocked_from_admin(self):
        self.client.force_authenticate(self.restricted_user)
        resp = self.client.get(reverse("admin-accounts-pending"))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        # Restricted user hits IsSuperAdmin role check first → PERMISSION_DENIED
        self.assertEqual(resp.data["code"], "PERMISSION_DENIED")

    def test_approved_user_blocked_from_admin(self):
        """Normal approved user should not access admin endpoints."""
        self.client.force_authenticate(self.approved_user)
        resp = self.client.get(reverse("admin-accounts-pending"))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(resp.data["code"], "PERMISSION_DENIED")

    def test_super_admin_can_access_admin(self):
        self.client.force_authenticate(self.super_admin)
        resp = self.client.get(reverse("admin-accounts-pending"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    # --- Me endpoint tests (IsAuthenticated, should work for all logged-in users) ---

    def test_pending_user_can_access_me(self):
        self.client.force_authenticate(self.pending_user)
        resp = self.client.get(reverse("auth-me"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_rejected_user_can_access_me(self):
        self.client.force_authenticate(self.rejected_user)
        resp = self.client.get(reverse("auth-me"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_banned_user_can_access_me(self):
        self.client.force_authenticate(self.banned_user)
        resp = self.client.get(reverse("auth-me"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_unauthenticated_cannot_access_me(self):
        resp = self.client.get(reverse("auth-me"))
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(resp.data["code"], "NOT_AUTHENTICATED")
