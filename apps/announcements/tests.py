"""Tests for announcements."""

from __future__ import annotations

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import ReviewStatus, UserRole
from apps.common.enums import ContentStatus

from .models import Announcement, AnnouncementReadReceipt

User = get_user_model()


class AnnouncementTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.classmate = User.objects.create_user(
            email="student@example.com",
            password="Pass1234!",
            real_name="张三",
            high_school="一中",
            high_school_class="一班",
        )
        cls.classmate.review_status = ReviewStatus.APPROVED
        cls.classmate.save()

        cls.moderator = User.objects.create_user(
            email="moderator@example.com",
            password="Pass1234!",
            real_name="管理员甲",
            high_school="一中",
            high_school_class="一班",
        )
        cls.moderator.review_status = ReviewStatus.APPROVED
        cls.moderator.role = UserRole.MODERATOR
        cls.moderator.save()

        cls.super_admin = User.objects.create_superuser(email="admin@example.com", password="AdminPass123!")

    def test_moderator_can_create_announcement(self):
        self.client.force_authenticate(self.moderator)
        resp = self.client.post(
            reverse("announcement-list"),
            {
                "title": "聚会通知",
                "content": "周末聚会",
                "is_pinned": True,
                "require_read_confirm": True,
                "expires_at": (timezone.now() + timedelta(days=7)).isoformat(),
                "status": ContentStatus.PUBLISHED,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        announcement = Announcement.objects.get()
        self.assertEqual(announcement.publisher, self.moderator)
        self.assertEqual(announcement.publisher_name_snapshot, self.moderator.real_name)
        self.assertTrue(announcement.is_pinned)
        self.assertIsNotNone(announcement.pinned_at)

    def test_classmate_cannot_create_announcement(self):
        self.client.force_authenticate(self.classmate)
        resp = self.client.post(
            reverse("announcement-list"),
            {"title": "普通用户公告", "content": "不能发布", "status": ContentStatus.PUBLISHED},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_excludes_expired_and_hidden(self):
        Announcement.objects.create(
            title="有效公告",
            content="content",
            publisher=self.moderator,
            publisher_name_snapshot=self.moderator.real_name,
        )
        Announcement.objects.create(
            title="过期公告",
            content="content",
            publisher=self.moderator,
            publisher_name_snapshot=self.moderator.real_name,
            expires_at=timezone.now() - timedelta(days=1),
        )
        Announcement.objects.create(
            title="隐藏公告",
            content="content",
            publisher=self.moderator,
            publisher_name_snapshot=self.moderator.real_name,
            status=ContentStatus.HIDDEN,
        )
        self.client.force_authenticate(self.classmate)
        resp = self.client.get(reverse("announcement-list"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data["results"]), 1)
        self.assertEqual(resp.data["results"][0]["title"], "有效公告")

    def test_pinned_list_only_returns_active_pinned(self):
        Announcement.objects.create(
            title="置顶公告",
            content="content",
            publisher=self.moderator,
            publisher_name_snapshot=self.moderator.real_name,
            is_pinned=True,
            pinned_at=timezone.now(),
        )
        Announcement.objects.create(
            title="非置顶公告",
            content="content",
            publisher=self.moderator,
            publisher_name_snapshot=self.moderator.real_name,
        )
        self.client.force_authenticate(self.classmate)
        resp = self.client.get(reverse("announcement-pinned"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data["results"]), 1)
        self.assertEqual(resp.data["results"][0]["title"], "置顶公告")

    def test_read_confirm(self):
        announcement = Announcement.objects.create(
            title="重要公告",
            content="content",
            publisher=self.moderator,
            publisher_name_snapshot=self.moderator.real_name,
            require_read_confirm=True,
        )
        self.client.force_authenticate(self.classmate)
        resp = self.client.post(reverse("announcement-read-confirm", kwargs={"pk": announcement.pk}))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(AnnouncementReadReceipt.objects.filter(announcement=announcement, user=self.classmate).exists())

    def test_soft_delete_announcement(self):
        announcement = Announcement.objects.create(
            title="待删除公告",
            content="content",
            publisher=self.moderator,
            publisher_name_snapshot=self.moderator.real_name,
        )
        self.client.force_authenticate(self.moderator)
        resp = self.client.delete(reverse("announcement-detail", kwargs={"pk": announcement.pk}))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        announcement.refresh_from_db()
        self.assertEqual(announcement.status, ContentStatus.DELETED)
        self.assertEqual(announcement.deleted_by, self.moderator)
