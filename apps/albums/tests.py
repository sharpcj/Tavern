"""Tests for albums, photos and photo comments."""

from __future__ import annotations

import shutil
import tempfile
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from PIL import Image
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import ReviewStatus, UserRole
from apps.activities.models import Activity, ActivityType
from apps.common.enums import ContentStatus, DisplayMode
from apps.common.models import Media

from .models import Album, AlbumCategory, Photo, PhotoComment

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp()


def make_image_file(name: str = "photo.png") -> SimpleUploadedFile:
    buffer = BytesIO()
    image = Image.new("RGB", (16, 16), color="red")
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type="image/png")


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class AlbumTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="user@example.com",
            password="Pass1234!",
            real_name="张三",
            high_school="一中",
            high_school_class="一班",
            nickname="三三",
        )
        cls.user.review_status = ReviewStatus.APPROVED
        cls.user.save()

        cls.other = User.objects.create_user(
            email="other@example.com",
            password="Pass1234!",
            real_name="李四",
            high_school="一中",
            high_school_class="一班",
        )
        cls.other.review_status = ReviewStatus.APPROVED
        cls.other.save()

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

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_album(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post(
            reverse("album-list"),
            {"title": "毕业照", "description": "毕业那天", "category": AlbumCategory.GRADUATION},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        album = Album.objects.get()
        self.assertEqual(album.creator, self.user)
        self.assertEqual(album.creator_name_snapshot, self.user.real_name)

    def test_album_can_link_activity(self):
        activity = Activity.objects.create(
            title="聚会",
            activity_type=ActivityType.GATHERING,
            initiator=self.user,
            initiator_name_snapshot=self.user.real_name,
            description="desc",
        )
        self.client.force_authenticate(self.user)
        resp = self.client.post(
            reverse("album-list"),
            {"title": "聚会照片", "category": AlbumCategory.GATHERING, "activity": activity.id},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Album.objects.get().activity, activity)

    def test_list_filter_by_category(self):
        Album.objects.create(
            title="校园", category=AlbumCategory.CAMPUS, creator=self.user, creator_name_snapshot=self.user.real_name
        )
        Album.objects.create(
            title="毕业", category=AlbumCategory.GRADUATION, creator=self.user, creator_name_snapshot=self.user.real_name
        )
        self.client.force_authenticate(self.user)
        resp = self.client.get(reverse("album-list"), {"category": AlbumCategory.CAMPUS})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data["results"]), 1)
        self.assertEqual(resp.data["results"][0]["title"], "校园")

    def test_upload_photo_creates_media(self):
        album = Album.objects.create(title="相册", creator=self.user, creator_name_snapshot=self.user.real_name)
        self.client.force_authenticate(self.user)
        resp = self.client.post(
            reverse("album-photo-upload", kwargs={"pk": album.pk}),
            {"image": make_image_file(), "caption": "照片说明", "display_mode": DisplayMode.NICKNAME},
            format="multipart",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Photo.objects.count(), 1)
        self.assertEqual(Media.objects.count(), 1)
        album.refresh_from_db()
        self.assertIsNotNone(album.cover_photo)
        self.assertEqual(resp.data["display_name"], self.user.nickname)

    def test_upload_non_image_rejected(self):
        album = Album.objects.create(title="相册", creator=self.user, creator_name_snapshot=self.user.real_name)
        self.client.force_authenticate(self.user)
        bad_file = SimpleUploadedFile("bad.txt", b"not image", content_type="text/plain")
        resp = self.client.post(
            reverse("album-photo-upload", kwargs={"pk": album.pk}),
            {"image": bad_file},
            format="multipart",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_photo_detail_and_comment(self):
        album = Album.objects.create(title="相册", creator=self.user, creator_name_snapshot=self.user.real_name)
        self.client.force_authenticate(self.user)
        upload_resp = self.client.post(
            reverse("album-photo-upload", kwargs={"pk": album.pk}),
            {"image": make_image_file(), "caption": "说明"},
            format="multipart",
        )
        photo_id = upload_resp.data["id"]
        comment_resp = self.client.post(
            reverse("photo-comment-create", kwargs={"pk": photo_id}),
            {"content": "好照片", "display_mode": DisplayMode.REAL_NAME},
            format="json",
        )
        self.assertEqual(comment_resp.status_code, status.HTTP_201_CREATED)
        detail_resp = self.client.get(reverse("photo-detail", kwargs={"pk": photo_id}))
        self.assertEqual(detail_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(detail_resp.data["comments"]), 1)

    def test_owner_can_delete_album(self):
        album = Album.objects.create(title="相册", creator=self.user, creator_name_snapshot=self.user.real_name)
        self.client.force_authenticate(self.user)
        resp = self.client.delete(reverse("album-detail", kwargs={"pk": album.pk}))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        album.refresh_from_db()
        self.assertEqual(album.status, ContentStatus.DELETED)

    def test_other_user_cannot_delete_album(self):
        album = Album.objects.create(title="相册", creator=self.user, creator_name_snapshot=self.user.real_name)
        self.client.force_authenticate(self.other)
        resp = self.client.delete(reverse("album-detail", kwargs={"pk": album.pk}))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_moderator_can_delete_photo_comment(self):
        album = Album.objects.create(title="相册", creator=self.user, creator_name_snapshot=self.user.real_name)
        self.client.force_authenticate(self.user)
        upload_resp = self.client.post(
            reverse("album-photo-upload", kwargs={"pk": album.pk}),
            {"image": make_image_file()},
            format="multipart",
        )
        photo = Photo.objects.get(pk=upload_resp.data["id"])
        comment = PhotoComment.objects.create(photo=photo, author=self.user, content="评论")
        self.client.force_authenticate(self.moderator)
        resp = self.client.delete(reverse("photo-comment-delete", kwargs={"pk": comment.pk}))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        comment.refresh_from_db()
        self.assertEqual(comment.status, ContentStatus.DELETED)
