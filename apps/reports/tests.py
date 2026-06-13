"""Tests for reports, moderation actions and audit logs."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import AccountStatus, ReviewStatus, UserRole
from apps.activities.models import Activity, ActivityStatus, ActivityType
from apps.audit_logs.models import AuditAction, AuditLog
from apps.common.enums import ContentStatus
from apps.moderation.models import ModerationAction, ModerationActionType
from apps.posts.models import Post

from .models import Report, ReportReason, ReportStatus

User = get_user_model()


class ReportModerationTests(APITestCase):
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

        cls.author = User.objects.create_user(
            email="author@example.com",
            password="Pass1234!",
            real_name="李四",
            high_school="一中",
            high_school_class="一班",
        )
        cls.author.review_status = ReviewStatus.APPROVED
        cls.author.account_status = AccountStatus.NORMAL
        cls.author.save()

        cls.moderator = User.objects.create_user(
            email="mod@example.com",
            password="Pass1234!",
            real_name="管理员",
            high_school="一中",
            high_school_class="一班",
            role=UserRole.MODERATOR,
        )
        cls.moderator.review_status = ReviewStatus.APPROVED
        cls.moderator.account_status = AccountStatus.NORMAL
        cls.moderator.save()

    def create_post(self):
        return Post.objects.create(author=self.author, content="一条动态")

    def create_report(self, target=None):
        target = target or self.create_post()
        self.client.force_authenticate(self.user)
        return self.client.post(
            reverse("report-create"),
            {"target_type": "post", "object_id": target.pk, "reason": ReportReason.PRIVACY, "description": "涉及隐私"},
            format="json",
        )

    def test_approved_user_can_create_report(self):
        post = self.create_post()
        self.client.force_authenticate(self.user)
        resp = self.client.post(
            reverse("report-create"),
            {"target_type": "post", "object_id": post.pk, "reason": ReportReason.ABUSE, "description": "不合适"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Report.objects.count(), 1)
        self.assertEqual(AuditLog.objects.filter(action=AuditAction.REPORT_CREATED).count(), 1)

    def test_user_cannot_access_admin_report_list(self):
        self.create_report()
        self.client.force_authenticate(self.user)
        resp = self.client.get(reverse("admin-report-list"))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_moderator_can_list_reports(self):
        self.create_report()
        self.client.force_authenticate(self.moderator)
        resp = self.client.get(reverse("admin-report-list"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)

    def test_handle_report_hide_content(self):
        post = self.create_post()
        self.create_report(post)
        report = Report.objects.get()
        self.client.force_authenticate(self.moderator)
        resp = self.client.post(
            reverse("admin-report-handle", kwargs={"pk": report.pk}),
            {"action_type": ModerationActionType.HIDE_CONTENT, "reason": "隐藏处理"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        post.refresh_from_db()
        report.refresh_from_db()
        self.assertEqual(post.status, ContentStatus.HIDDEN)
        self.assertEqual(report.status, ReportStatus.RESOLVED)
        self.assertEqual(ModerationAction.objects.count(), 1)
        self.assertTrue(AuditLog.objects.filter(action=AuditAction.CONTENT_HIDDEN).exists())
        self.assertTrue(AuditLog.objects.filter(action=AuditAction.REPORT_HANDLED).exists())

    def test_handle_report_restrict_user(self):
        post = self.create_post()
        self.create_report(post)
        report = Report.objects.get()
        self.client.force_authenticate(self.moderator)
        resp = self.client.post(
            reverse("admin-report-handle", kwargs={"pk": report.pk}),
            {"action_type": ModerationActionType.RESTRICT_USER, "reason": "限制发言"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.author.refresh_from_db()
        self.assertEqual(self.author.account_status, AccountStatus.RESTRICTED)
        self.assertTrue(AuditLog.objects.filter(action=AuditAction.USER_RESTRICTED).exists())

    def test_ignore_report_sets_ignored(self):
        self.create_report()
        report = Report.objects.get()
        self.client.force_authenticate(self.moderator)
        resp = self.client.post(
            reverse("admin-report-handle", kwargs={"pk": report.pk}),
            {"action_type": ModerationActionType.IGNORE, "reason": "无需处理"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        report.refresh_from_db()
        self.assertEqual(report.status, ReportStatus.IGNORED)

    def test_cannot_handle_resolved_report_twice(self):
        self.create_report()
        report = Report.objects.get()
        self.client.force_authenticate(self.moderator)
        first = self.client.post(
            reverse("admin-report-handle", kwargs={"pk": report.pk}),
            {"action_type": ModerationActionType.IGNORE, "reason": "无需处理"},
            format="json",
        )
        second = self.client.post(
            reverse("admin-report-handle", kwargs={"pk": report.pk}),
            {"action_type": ModerationActionType.IGNORE, "reason": "重复处理"},
            format="json",
        )
        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertEqual(second.status_code, status.HTTP_400_BAD_REQUEST)

    def test_activity_report_delete_content_cancels_activity(self):
        activity = Activity.objects.create(
            title="活动",
            activity_type=ActivityType.GATHERING,
            initiator=self.author,
            initiator_name_snapshot=self.author.real_name,
            description="活动说明",
        )
        self.client.force_authenticate(self.user)
        report_resp = self.client.post(
            reverse("report-create"),
            {"target_type": "activity", "object_id": activity.pk, "reason": ReportReason.OTHER},
            format="json",
        )
        self.assertEqual(report_resp.status_code, status.HTTP_201_CREATED)
        report = Report.objects.get()
        self.client.force_authenticate(self.moderator)
        handle_resp = self.client.post(
            reverse("admin-report-handle", kwargs={"pk": report.pk}),
            {"action_type": ModerationActionType.DELETE_CONTENT, "reason": "取消活动"},
            format="json",
        )
        self.assertEqual(handle_resp.status_code, status.HTTP_200_OK)
        activity.refresh_from_db()
        self.assertEqual(activity.status, ActivityStatus.CANCELLED)

    def test_admin_audit_log_list(self):
        self.create_report()
        self.client.force_authenticate(self.moderator)
        resp = self.client.get(reverse("admin-audit-log-list"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(resp.data["count"], 1)
