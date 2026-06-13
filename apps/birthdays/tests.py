"""Tests for birthday classmates and wishes."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import AccountStatus, ReviewStatus, UserRole
from apps.common.enums import ContentStatus, DisplayMode
from apps.profiles.models import Profile

from .models import BirthdayWish

User = get_user_model()


class BirthdayTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        current_month = timezone.localdate().month
        cls.user = User.objects.create_user(
            email="user@example.com",
            password="Pass1234!",
            real_name="张三",
            high_school="一中",
            high_school_class="一班",
            nickname="三三",
        )
        cls.user.review_status = ReviewStatus.APPROVED
        cls.user.account_status = AccountStatus.NORMAL
        cls.user.save()
        cls.user.profile.birthday_month = current_month
        cls.user.profile.show_birthday = True
        cls.user.profile.save()

        cls.recipient = User.objects.create_user(
            email="recipient@example.com",
            password="Pass1234!",
            real_name="李四",
            high_school="一中",
            high_school_class="一班",
            nickname="四四",
        )
        cls.recipient.review_status = ReviewStatus.APPROVED
        cls.recipient.account_status = AccountStatus.NORMAL
        cls.recipient.save()
        cls.recipient.profile.birthday_month = current_month
        cls.recipient.profile.show_birthday = True
        cls.recipient.profile.city = "上海"
        cls.recipient.profile.save()

        cls.hidden_birthday_user = User.objects.create_user(
            email="hidden@example.com",
            password="Pass1234!",
            real_name="王五",
            high_school="一中",
            high_school_class="一班",
        )
        cls.hidden_birthday_user.review_status = ReviewStatus.APPROVED
        cls.hidden_birthday_user.save()
        cls.hidden_birthday_user.profile.birthday_month = current_month
        cls.hidden_birthday_user.profile.show_birthday = False
        cls.hidden_birthday_user.profile.save()

        cls.moderator = User.objects.create_user(
            email="mod@example.com",
            password="Pass1234!",
            real_name="管理员",
            high_school="一中",
            high_school_class="一班",
            role=UserRole.MODERATOR,
        )
        cls.moderator.review_status = ReviewStatus.APPROVED
        cls.moderator.save()

    def test_current_month_only_returns_visible_birthdays(self):
        self.client.force_authenticate(self.user)
        resp = self.client.get(reverse("birthday-current-month"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        names = {item["real_name"] for item in resp.data["results"]}
        self.assertIn("张三", names)
        self.assertIn("李四", names)
        self.assertNotIn("王五", names)
        first = resp.data["results"][0]
        self.assertIn("birthday_month", first)
        self.assertNotIn("birthday", first)
        self.assertNotIn("birth_day", first)
        self.assertNotIn("birth_year", first)

    def test_create_birthday_wish(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post(
            reverse("birthday-wish-list"),
            {
                "recipient_account_id": str(self.recipient.account_id),
                "content": "生日快乐！",
                "display_mode": DisplayMode.NICKNAME,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        wish = BirthdayWish.objects.get()
        self.assertEqual(wish.recipient, self.recipient)
        self.assertEqual(wish.author, self.user)
        self.assertEqual(resp.data["display_name"], self.user.nickname)

    def test_cannot_wish_to_user_without_birthday_display(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post(
            reverse("birthday-wish-list"),
            {
                "recipient_account_id": str(self.hidden_birthday_user.account_id),
                "content": "生日快乐！",
                "display_mode": DisplayMode.REAL_NAME,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_wishes_can_filter_by_recipient(self):
        BirthdayWish.objects.create(recipient=self.recipient, author=self.user, content="生日快乐")
        BirthdayWish.objects.create(recipient=self.user, author=self.recipient, content="也祝你快乐")
        self.client.force_authenticate(self.user)
        resp = self.client.get(reverse("birthday-wish-list"), {"recipient": str(self.recipient.account_id)})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data["results"]), 1)
        self.assertEqual(resp.data["results"][0]["recipient_name"], "李四")

    def test_author_can_delete_wish(self):
        wish = BirthdayWish.objects.create(recipient=self.recipient, author=self.user, content="生日快乐")
        self.client.force_authenticate(self.user)
        resp = self.client.delete(reverse("birthday-wish-delete", kwargs={"pk": wish.pk}))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        wish.refresh_from_db()
        self.assertEqual(wish.status, ContentStatus.DELETED)

    def test_other_user_cannot_delete_wish(self):
        wish = BirthdayWish.objects.create(recipient=self.recipient, author=self.user, content="生日快乐")
        self.client.force_authenticate(self.recipient)
        resp = self.client.delete(reverse("birthday-wish-delete", kwargs={"pk": wish.pk}))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_moderator_can_hide_wish(self):
        wish = BirthdayWish.objects.create(recipient=self.recipient, author=self.user, content="不合适内容")
        self.client.force_authenticate(self.moderator)
        resp = self.client.post(reverse("birthday-wish-hide", kwargs={"pk": wish.pk}))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        wish.refresh_from_db()
        self.assertEqual(wish.status, ContentStatus.HIDDEN)

    def test_profile_show_birthday_default_false(self):
        user = User.objects.create_user(
            email="new@example.com",
            password="Pass1234!",
            real_name="新同学",
            high_school="一中",
            high_school_class="一班",
        )
        profile = Profile.objects.get(user=user)
        self.assertFalse(profile.show_birthday)
