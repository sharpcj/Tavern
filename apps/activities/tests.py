"""Tests for activities."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import ReviewStatus
from .models import Activity, ActivityStatus, ActivityType, ChainRecord, Signup, VoteOption, VoteRecord

User = get_user_model()


class ActivityTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="user@example.com", password="Pass1234!",
            real_name="张三", high_school="一中", high_school_class="一班",
        )
        cls.user.review_status = ReviewStatus.APPROVED
        cls.user.save()
        cls.admin = User.objects.create_superuser(email="admin@example.com", password="AdminPass123!")

    def test_create_gathering(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post(reverse("activity-list"), {
            "title": "周末聚餐", "activity_type": "gathering",
            "description": "一起吃饭", "location": "北京",
            "start_time": "2026-07-01T18:00:00Z",
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Activity.objects.count(), 1)

    def test_create_voting(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post(reverse("activity-list"), {
            "title": "聚会时间投票", "activity_type": "voting",
            "description": "选个时间", "is_multi_choice": False,
            "vote_options": ["周六", "周日"],
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(VoteOption.objects.count(), 2)

    def test_create_chain(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post(reverse("activity-list"), {
            "title": "车辆安排", "activity_type": "chain",
            "description": "统计车辆",
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_activity_list_filter_by_status(self):
        Activity.objects.create(
            title="活动1", activity_type="gathering", initiator=self.user,
            initiator_name_snapshot=self.user.real_name, description="desc", status=ActivityStatus.OPEN,
        )
        Activity.objects.create(
            title="活动2", activity_type="gathering", initiator=self.user,
            initiator_name_snapshot=self.user.real_name, description="desc", status=ActivityStatus.FINISHED,
        )
        self.client.force_authenticate(self.user)
        resp = self.client.get(reverse("activity-list"), {"status": "open"})
        self.assertEqual(len(resp.data["results"]), 1)

    def test_initiator_can_update_status(self):
        activity = Activity.objects.create(
            title="活动", activity_type="gathering", initiator=self.user,
            initiator_name_snapshot=self.user.real_name, description="desc",
        )
        self.client.force_authenticate(self.user)
        resp = self.client.post(
            reverse("activity-update-status", kwargs={"pk": activity.pk}),
            {"status": "closed"}, format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        activity.refresh_from_db()
        self.assertEqual(activity.status, ActivityStatus.CLOSED)

    def test_non_initiator_cannot_update_status(self):
        other = User.objects.create_user(
            email="other@example.com", password="Pass1234!",
            real_name="李四", high_school="一中", high_school_class="二班",
        )
        other.review_status = ReviewStatus.APPROVED
        other.save()
        activity = Activity.objects.create(
            title="活动", activity_type="gathering", initiator=self.user,
            initiator_name_snapshot=self.user.real_name, description="desc",
        )
        self.client.force_authenticate(other)
        resp = self.client.post(
            reverse("activity-update-status", kwargs={"pk": activity.pk}),
            {"status": "closed"}, format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_delete_activity(self):
        activity = Activity.objects.create(
            title="活动", activity_type="gathering", initiator=self.user,
            initiator_name_snapshot=self.user.real_name, description="desc",
        )
        self.client.force_authenticate(self.admin)
        resp = self.client.delete(reverse("activity-delete", kwargs={"pk": activity.pk}))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_user_cannot_delete_activity(self):
        activity = Activity.objects.create(
            title="活动", activity_type="gathering", initiator=self.user,
            initiator_name_snapshot=self.user.real_name, description="desc",
        )
        self.client.force_authenticate(self.user)
        resp = self.client.delete(reverse("activity-delete", kwargs={"pk": activity.pk}))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


class SignupTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="user@example.com", password="Pass1234!",
            real_name="张三", high_school="一中", high_school_class="一班",
        )
        cls.user.review_status = ReviewStatus.APPROVED
        cls.user.save()
        cls.activity = Activity.objects.create(
            title="聚餐", activity_type="gathering", initiator=cls.user,
            initiator_name_snapshot=cls.user.real_name, description="desc",
        )

    def test_signup(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post(
            reverse("activity-signup", kwargs={"pk": self.activity.pk}),
            {"participant_count": 2, "bring_guests": False, "note": "准时到"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Signup.objects.count(), 1)

    def test_cancel_signup(self):
        Signup.objects.create(activity=self.activity, user=self.user, real_name_snapshot=self.user.real_name)
        self.client.force_authenticate(self.user)
        resp = self.client.delete(reverse("activity-signup", kwargs={"pk": self.activity.pk}))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Signup.objects.count(), 0)


class VoteTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="user@example.com", password="Pass1234!",
            real_name="张三", high_school="一中", high_school_class="一班",
        )
        cls.user.review_status = ReviewStatus.APPROVED
        cls.user.save()
        cls.activity = Activity.objects.create(
            title="投票", activity_type="voting", initiator=cls.user,
            initiator_name_snapshot=cls.user.real_name, description="desc",
        )
        cls.opt1 = VoteOption.objects.create(activity=cls.activity, text="选项A", order=0)
        cls.opt2 = VoteOption.objects.create(activity=cls.activity, text="选项B", order=1)

    def test_vote_single(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post(
            reverse("activity-vote", kwargs={"pk": self.activity.pk}),
            {"option_ids": [self.opt1.id]}, format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(VoteRecord.objects.count(), 1)

    def test_vote_multi_not_allowed(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post(
            reverse("activity-vote", kwargs={"pk": self.activity.pk}),
            {"option_ids": [self.opt1.id, self.opt2.id]}, format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class ChainTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="user@example.com", password="Pass1234!",
            real_name="张三", high_school="一中", high_school_class="一班",
        )
        cls.user.review_status = ReviewStatus.APPROVED
        cls.user.save()
        cls.activity = Activity.objects.create(
            title="接龙", activity_type="chain", initiator=cls.user,
            initiator_name_snapshot=cls.user.real_name, description="desc",
        )

    def test_fill_chain(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post(
            reverse("activity-chain", kwargs={"pk": self.activity.pk}),
            {"will_attend": True, "participant_count": 1, "note": "参加"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ChainRecord.objects.count(), 1)
