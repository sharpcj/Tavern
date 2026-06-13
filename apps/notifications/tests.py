"""Tests for system notifications."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import AccountStatus, ReviewStatus, UserRole

from .models import Notification, NotificationType
from .services import create_notification

User = get_user_model()


class NotificationApiTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="user@example.com",
            password="Pass1234!",
            real_name="张三",
            high_school="一中",
            high_school_class="一班",
        )
        cls.user.review_status = ReviewStatus.APPROVED
        cls.user.account_status = AccountStatus.NORMAL
        cls.user.save()

        cls.other = User.objects.create_user(
            email="other@example.com",
            password="Pass1234!",
            real_name="李四",
            high_school="一中",
            high_school_class="一班",
        )
        cls.other.review_status = ReviewStatus.APPROVED
        cls.other.account_status = AccountStatus.NORMAL
        cls.other.save()

    def test_user_can_list_own_notifications(self):
        create_notification(
            recipient=self.user,
            notification_type=NotificationType.SYSTEM,
            title="系统通知",
            content="测试",
        )
        create_notification(
            recipient=self.other,
            notification_type=NotificationType.SYSTEM,
            title="别人通知",
            content="测试",
        )
        self.client.force_authenticate(self.user)
        resp = self.client.get(reverse("notification-list"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)
        self.assertEqual(resp.data["results"][0]["title"], "系统通知")

    def test_unread_count_and_mark_read(self):
        notification = create_notification(
            recipient=self.user,
            notification_type=NotificationType.SYSTEM,
            title="未读",
        )
        self.client.force_authenticate(self.user)
        count_resp = self.client.get(reverse("notification-unread-count"))
        self.assertEqual(count_resp.data["unread_count"], 1)

        read_resp = self.client.post(reverse("notification-read", kwargs={"pk": notification.pk}))
        self.assertEqual(read_resp.status_code, status.HTTP_200_OK)
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)
        self.assertIsNotNone(notification.read_at)

    def test_user_cannot_mark_others_notification_read(self):
        notification = create_notification(
            recipient=self.other,
            notification_type=NotificationType.SYSTEM,
            title="别人通知",
        )
        self.client.force_authenticate(self.user)
        resp = self.client.post(reverse("notification-read", kwargs={"pk": notification.pk}))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_mark_all_read(self):
        create_notification(recipient=self.user, notification_type=NotificationType.SYSTEM, title="1")
        create_notification(recipient=self.user, notification_type=NotificationType.SYSTEM, title="2")
        self.client.force_authenticate(self.user)
        resp = self.client.post(reverse("notification-read-all"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["updated"], 2)
        self.assertEqual(Notification.objects.filter(recipient=self.user, is_read=False).count(), 0)
