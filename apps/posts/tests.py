"""Tests for posts and comments."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import ReviewStatus
from apps.posts.models import Post
from apps.comments.models import Comment
from apps.common.enums import ContentStatus

User = get_user_model()


class PostTests(APITestCase):
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

        cls.admin = User.objects.create_superuser(
            email="admin@example.com", password="AdminPass123!",
        )

    def test_create_post(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post(
            reverse("post-list"),
            {"content": "大家好", "category": "chat", "display_mode": "real_name"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 1)

    def test_post_list_shows_published(self):
        Post.objects.create(author=self.user, content="测试动态", category="chat")
        self.client.force_authenticate(self.user)
        resp = self.client.get(reverse("post-list"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data["results"]), 1)

    def test_post_list_excludes_deleted(self):
        post = Post.objects.create(author=self.user, content="已删除", category="chat")
        post.status = ContentStatus.DELETED
        post.save()
        self.client.force_authenticate(self.user)
        resp = self.client.get(reverse("post-list"))
        self.assertEqual(len(resp.data["results"]), 0)

    def test_edit_own_post(self):
        post = Post.objects.create(author=self.user, content="原文", category="chat")
        self.client.force_authenticate(self.user)
        resp = self.client.patch(
            reverse("post-detail", kwargs={"pk": post.pk}),
            {"content": "修改后"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        post.refresh_from_db()
        self.assertEqual(post.content, "修改后")

    def test_cannot_edit_others_post(self):
        post = Post.objects.create(author=self.other, content="别人的动态", category="chat")
        self.client.force_authenticate(self.user)
        resp = self.client.patch(
            reverse("post-detail", kwargs={"pk": post.pk}),
            {"content": "hack"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_own_post_soft(self):
        post = Post.objects.create(author=self.user, content="要删除", category="chat")
        self.client.force_authenticate(self.user)
        resp = self.client.delete(reverse("post-detail", kwargs={"pk": post.pk}))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        post.refresh_from_db()
        self.assertEqual(post.status, ContentStatus.DELETED)

    def test_admin_can_pin_post(self):
        post = Post.objects.create(author=self.user, content="重要通知", category="chat")
        self.client.force_authenticate(self.admin)
        resp = self.client.post(
            reverse("post-pin", kwargs={"pk": post.pk}),
            {"pin": True},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        post.refresh_from_db()
        self.assertTrue(post.is_pinned)

    def test_non_admin_cannot_pin(self):
        post = Post.objects.create(author=self.user, content="通知", category="chat")
        self.client.force_authenticate(self.user)
        resp = self.client.post(
            reverse("post-pin", kwargs={"pk": post.pk}),
            {"pin": True},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


class CommentTests(APITestCase):
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

        cls.post = Post.objects.create(author=cls.user, content="动态", category="chat")

    def test_create_comment(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post(
            reverse("comment-list", kwargs={"post_pk": self.post.pk}),
            {"content": "好文章", "display_mode": "real_name"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.count(), 1)

    def test_reply_to_comment(self):
        comment = Comment.objects.create(
            post=self.post, author=self.user, content="评论", display_mode="real_name",
        )
        self.client.force_authenticate(self.other)
        resp = self.client.post(
            reverse("comment-reply", kwargs={"pk": comment.pk}),
            {"content": "回复", "display_mode": "nickname"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.filter(parent=comment).count(), 1)

    def test_reply_to_reply_is_flattened_under_root_comment(self):
        comment = Comment.objects.create(
            post=self.post, author=self.user, content="评论", display_mode="real_name",
        )
        reply = Comment.objects.create(
            post=self.post, author=self.other, content="回复", display_mode="real_name",
            parent=comment,
        )
        self.client.force_authenticate(self.user)
        resp = self.client.post(
            reverse("comment-reply", kwargs={"pk": reply.pk}),
            {"content": "再回复", "display_mode": "real_name"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        nested_reply = Comment.objects.get(content="再回复")
        self.assertEqual(nested_reply.parent, comment)
        self.assertEqual(nested_reply.reply_to, reply)

        list_resp = self.client.get(reverse("comment-list", kwargs={"post_pk": self.post.pk}))
        replies = list_resp.data["results"][0]["replies"]
        self.assertEqual(len(replies), 2)
        self.assertEqual(replies[1]["reply_to"], reply.pk)
        self.assertEqual(replies[1]["reply_to_display_name"], reply.display_name)

    def test_delete_own_comment(self):
        comment = Comment.objects.create(
            post=self.post, author=self.user, content="评论", display_mode="real_name",
        )
        self.client.force_authenticate(self.user)
        resp = self.client.delete(reverse("comment-delete", kwargs={"pk": comment.pk}))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        comment.refresh_from_db()
        self.assertEqual(comment.status, ContentStatus.DELETED)

    def test_cannot_delete_others_comment(self):
        comment = Comment.objects.create(
            post=self.post, author=self.other, content="评论", display_mode="real_name",
        )
        self.client.force_authenticate(self.user)
        resp = self.client.delete(reverse("comment-delete", kwargs={"pk": comment.pk}))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
