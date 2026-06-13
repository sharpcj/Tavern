"""API tests for account registration and identity review."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import ReviewStatus

User = get_user_model()


class AccountRegistrationTests(APITestCase):
    def test_register_requires_identity_fields(self):
        response = self.client.post(
            reverse("auth-register"),
            {
                "email": "student@example.com",
                "password": "StrongPass123!",
                "password_confirm": "StrongPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("real_name", response.data)
        self.assertIn("high_school", response.data)
        self.assertIn("high_school_class", response.data)

    def test_register_creates_pending_user(self):
        response = self.client.post(
            reverse("auth-register"),
            {
                "email": "student@example.com",
                "password": "StrongPass123!",
                "password_confirm": "StrongPass123!",
                "real_name": "张三",
                "high_school": "一中",
                "high_school_class": "高三一班",
                "nickname": "三三",
                "extra_info": "班主任是李老师",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email="student@example.com")
        self.assertEqual(user.review_status, ReviewStatus.PENDING)
        self.assertEqual(user.real_name, "张三")
        self.assertTrue(response.data["user"]["account_id"])

    def test_registered_user_can_login_and_view_review_status(self):
        User.objects.create_user(
            email="student@example.com",
            password="StrongPass123!",
            real_name="张三",
            high_school="一中",
            high_school_class="高三一班",
        )

        token_response = self.client.post(
            reverse("token-obtain-pair"),
            {"email": "student@example.com", "password": "StrongPass123!"},
            format="json",
        )
        self.assertEqual(token_response.status_code, status.HTTP_200_OK)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}")
        me_response = self.client.get(reverse("auth-me"))
        self.assertEqual(me_response.status_code, status.HTTP_200_OK)
        self.assertEqual(me_response.data["review_status"], ReviewStatus.PENDING)
        self.assertEqual(me_response.data["account_id"], str(User.objects.get(email="student@example.com").account_id))


class AdminReviewTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(email="admin@example.com", password="AdminPass123!")
        self.user = User.objects.create_user(
            email="student@example.com",
            password="StrongPass123!",
            real_name="张三",
            high_school="一中",
            high_school_class="高三一班",
        )

    def test_non_admin_cannot_review_user(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(
            reverse("admin-account-review", kwargs={"account_id": self.user.account_id}),
            {"action": "approve"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_approve_user(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            reverse("admin-account-review", kwargs={"account_id": self.user.account_id}),
            {"action": "approve", "review_message": "欢迎加入"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.review_status, ReviewStatus.APPROVED)
        self.assertEqual(self.user.reviewed_by, self.admin)
        self.assertEqual(self.user.review_message, "欢迎加入")
