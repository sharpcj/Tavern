"""Tests for system notifications."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import AccountStatus, ReviewStatus, UserRole
from apps.activities.models import Activity, ActivityType
from apps.announcements.models import Announcement
from apps.comments.models import Comment
from apps.posts.models import Post

from .models import Notification, NotificationType, RealtimeEventType
from .services import create_notification, publish_event

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

    def test_notification_list_includes_target_url_for_common_targets(self):
        activity = Activity.objects.create(
            title="聚会",
            activity_type=ActivityType.GATHERING,
            initiator=self.other,
            initiator_name_snapshot=self.other.real_name,
            description="desc",
        )
        post = Post.objects.create(author=self.other, content="动态")
        comment = Comment.objects.create(post=post, author=self.other, content="评论")
        announcement = Announcement.objects.create(
            title="公告",
            content="内容",
            publisher=self.other,
            publisher_name_snapshot=self.other.real_name,
        )
        create_notification(
            recipient=self.user,
            notification_type=NotificationType.ACTIVITY_STATUS,
            title="活动",
            target=activity,
        )
        create_notification(
            recipient=self.user,
            notification_type=NotificationType.COMMENT_REPLY,
            title="评论",
            target=comment,
        )
        create_notification(
            recipient=self.user,
            notification_type=NotificationType.ANNOUNCEMENT,
            title="公告",
            target=announcement,
        )
        self.client.force_authenticate(self.user)

        resp = self.client.get(reverse("notification-list"))

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        urls_by_title = {item["title"]: item["target_url"] for item in resp.data["results"]}
        self.assertEqual(urls_by_title["活动"], f"/activities/{activity.pk}")
        self.assertEqual(urls_by_title["评论"], f"/posts/{post.pk}")
        self.assertEqual(urls_by_title["公告"], f"/announcements/{announcement.pk}")

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

    def test_realtime_since_returns_broadcast_and_own_events_only(self):
        broadcast = publish_event(event_type=RealtimeEventType.POST_CREATED, target_type="post", target_id=1)
        own = publish_event(
            recipient=self.user,
            event_type=RealtimeEventType.NOTIFICATION_CREATED,
            target_type="notification",
            target_id=2,
        )
        publish_event(
            recipient=self.other,
            event_type=RealtimeEventType.NOTIFICATION_CREATED,
            target_type="notification",
            target_id=3,
        )

        self.client.force_authenticate(self.user)
        resp = self.client.get(reverse("realtime-event-since"), {"cursor": 0})

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in resp.data["results"]], [broadcast.pk, own.pk])
        self.assertEqual(resp.data["latest_cursor"], own.pk)

    def test_pending_user_cannot_access_realtime_since(self):
        pending = User.objects.create_user(
            email="pending@example.com",
            password="Pass1234!",
            real_name="王五",
            high_school="一中",
            high_school_class="一班",
        )
        pending.review_status = ReviewStatus.PENDING
        pending.account_status = AccountStatus.NORMAL
        pending.save()

        self.client.force_authenticate(pending)
        resp = self.client.get(reverse("realtime-event-since"), {"cursor": 0})

        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
