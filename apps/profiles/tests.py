"""Tests for profile management and classmate directory."""

from __future__ import annotations

import tempfile
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from PIL import Image
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import AccountStatus, ReviewStatus
from apps.common.models import Media

from .models import ContactVisibility, Profile

User = get_user_model()


def make_image_file(name: str = "avatar.png", size: tuple[int, int] = (64, 64)) -> SimpleUploadedFile:
    buffer = BytesIO()
    image = Image.new("RGB", size, color="blue")
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type="image/png")


class ProfileTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="user@example.com", password="Pass1234!",
            real_name="张三", high_school="一中", high_school_class="一班",
        )
        cls.user.review_status = ReviewStatus.APPROVED
        cls.user.save()

        cls.other = User.objects.create_user(
            email="other@example.com", password="Pass1234!",
            real_name="李四", high_school="一中", high_school_class="二班",
        )
        cls.other.review_status = ReviewStatus.APPROVED
        cls.other.save()

        cls.pending_user = User.objects.create_user(
            email="pending@example.com", password="Pass1234!",
            real_name="待审核", high_school="一中", high_school_class="三班",
        )

    def test_profile_auto_created(self):
        self.assertTrue(Profile.objects.filter(user=self.user).exists())

    def test_get_own_profile(self):
        self.client.force_authenticate(self.user)
        resp = self.client.get(reverse("my-profile"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["real_name"], "张三")

    def test_patch_own_profile(self):
        self.client.force_authenticate(self.user)
        resp = self.client.patch(
            reverse("my-profile"),
            {"city": "北京", "occupation": "工程师", "birthday_month": 3, "avatar_visible": False},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["city"], "北京")
        self.assertEqual(resp.data["birthday_month"], 3)
        self.assertFalse(resp.data["avatar_visible"])

    def test_upload_avatar_updates_profile_avatar_url(self):
        self.client.force_authenticate(self.user)
        with tempfile.TemporaryDirectory() as tmpdir, override_settings(MEDIA_ROOT=tmpdir):
            resp = self.client.patch(
                reverse("my-profile"),
                {"avatar": make_image_file()},
                format="multipart",
            )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.user.profile.refresh_from_db()
        self.assertTrue(self.user.profile.avatar_url)
        self.assertTrue(Media.objects.filter(uploader=self.user, original_name="avatar.png").exists())

    def test_reject_oversized_avatar_dimensions(self):
        self.client.force_authenticate(self.user)
        with tempfile.TemporaryDirectory() as tmpdir, override_settings(MEDIA_ROOT=tmpdir):
            resp = self.client.patch(
                reverse("my-profile"),
                {"avatar": make_image_file(size=(1200, 1200))},
                format="multipart",
            )

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_birthday_month_validation(self):
        self.client.force_authenticate(self.user)
        resp = self.client.patch(
            reverse("my-profile"),
            {"birthday_month": 13},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_set_contact_visibility(self):
        self.client.force_authenticate(self.user)
        resp = self.client.patch(
            reverse("my-profile"),
            {
                "phone": "13800138000",
                "phone_visibility": ContactVisibility.EVERYONE,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["phone_visibility"], ContactVisibility.EVERYONE)


class ClassmateDirectoryTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="user@example.com", password="Pass1234!",
            real_name="张三", high_school="一中", high_school_class="一班",
        )
        cls.user.review_status = ReviewStatus.APPROVED
        cls.user.save()
        Profile.objects.filter(user=cls.user).update(city="北京", occupation="工程师")

        cls.other = User.objects.create_user(
            email="other@example.com", password="Pass1234!",
            real_name="李四", high_school="一中", high_school_class="二班",
        )
        cls.other.review_status = ReviewStatus.APPROVED
        cls.other.save()
        Profile.objects.filter(user=cls.other).update(
            city="上海", occupation="设计师",
            phone="13900139000", phone_visibility=ContactVisibility.EVERYONE,
        )

        cls.pending_user = User.objects.create_user(
            email="pending@example.com", password="Pass1234!",
            real_name="待审核", high_school="一中", high_school_class="三班",
        )

    def test_pending_user_cannot_access_classmates(self):
        self.client.force_authenticate(self.pending_user)
        resp = self.client.get(reverse("classmate-list"))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_classmate_list_excludes_pending(self):
        self.client.force_authenticate(self.user)
        resp = self.client.get(reverse("classmate-list"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        names = [item["real_name"] for item in resp.data["results"]]
        self.assertIn("李四", names)
        self.assertNotIn("待审核", names)
        # Contact fields should not appear in list
        self.assertNotIn("phone", resp.data["results"][0])

    def test_classmate_list_search(self):
        self.client.force_authenticate(self.user)
        resp = self.client.get(reverse("classmate-list"), {"search": "上海"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data["results"]), 1)
        self.assertEqual(resp.data["results"][0]["real_name"], "李四")

    def test_classmate_detail_shows_public_contact(self):
        self.client.force_authenticate(self.user)
        resp = self.client.get(
            reverse("classmate-detail", kwargs={"account_id": self.other.account_id})
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["phone"], "13900139000")

    def test_classmate_detail_hides_private_contact(self):
        # Set other's phone to only_me
        Profile.objects.filter(user=self.other).update(
            phone_visibility=ContactVisibility.ONLY_ME
        )
        self.client.force_authenticate(self.user)
        resp = self.client.get(
            reverse("classmate-detail", kwargs={"account_id": self.other.account_id})
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIsNone(resp.data["phone"])

    def test_classmate_list_hides_private_avatar(self):
        Profile.objects.filter(user=self.other).update(
            avatar_url="/media/avatars/private.png",
            avatar_visible=False,
        )
        self.client.force_authenticate(self.user)
        resp = self.client.get(reverse("classmate-list"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        other_item = next(item for item in resp.data["results"] if item["real_name"] == "李四")
        self.assertEqual(other_item["avatar_url"], "")

    def test_classmate_detail_hides_private_avatar_from_others(self):
        Profile.objects.filter(user=self.other).update(
            avatar_url="/media/avatars/private.png",
            avatar_visible=False,
        )
        self.client.force_authenticate(self.user)
        resp = self.client.get(
            reverse("classmate-detail", kwargs={"account_id": self.other.account_id})
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["avatar_url"], "")

    def test_classmate_detail_selected_visibility(self):
        Profile.objects.filter(user=self.other).update(
            phone_visibility=ContactVisibility.SELECTED,
        )
        profile = Profile.objects.get(user=self.other)
        profile.contact_visible_to.add(self.user)

        self.client.force_authenticate(self.user)
        resp = self.client.get(
            reverse("classmate-detail", kwargs={"account_id": self.other.account_id})
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["phone"], "13900139000")

    def test_own_detail_shows_all(self):
        self.client.force_authenticate(self.user)
        resp = self.client.get(
            reverse("classmate-detail", kwargs={"account_id": self.user.account_id})
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # Own detail should show email (from User model)
        self.assertEqual(resp.data["email"], "user@example.com")

    def test_own_detail_keeps_private_avatar_visible_to_self(self):
        Profile.objects.filter(user=self.user).update(
            avatar_url="/media/avatars/private.png",
            avatar_visible=False,
        )
        self.client.force_authenticate(self.user)
        resp = self.client.get(
            reverse("classmate-detail", kwargs={"account_id": self.user.account_id})
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["avatar_url"])
