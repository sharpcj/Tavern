"""Activity models for the classmate community."""

from __future__ import annotations

from django.conf import settings
from django.db import models


class ActivityType(models.TextChoices):
    GATHERING = "gathering", "聚会报名"
    VOTING = "voting", "投票"
    CHAIN = "chain", "接龙"


class ActivityStatus(models.TextChoices):
    PREPARING = "preparing", "筹备中"
    OPEN = "open", "报名中"
    CLOSED = "closed", "已截止"
    FINISHED = "finished", "已结束"
    CANCELLED = "cancelled", "已取消"


class Activity(models.Model):
    """An activity (gathering, voting, or chain) in the classmate community."""

    title = models.CharField("标题", max_length=256)
    activity_type = models.CharField("活动类型", max_length=16, choices=ActivityType.choices)
    initiator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="initiated_activities",
        verbose_name="发起人",
    )
    initiator_name_snapshot = models.CharField("发起人姓名快照", max_length=64)
    description = models.TextField("活动说明")
    location = models.CharField("活动地点", max_length=256, blank=True)
    start_time = models.DateTimeField("开始时间", null=True, blank=True)
    deadline = models.DateTimeField("截止时间", null=True, blank=True)
    max_participants = models.PositiveIntegerField("人数上限", null=True, blank=True)
    allow_guests = models.BooleanField("可带家属", default=False)
    contact_info = models.CharField("联系人信息", max_length=256, blank=True)
    status = models.CharField(
        "状态", max_length=16, choices=ActivityStatus.choices, default=ActivityStatus.OPEN, db_index=True
    )
    # Voting-specific fields
    is_multi_choice = models.BooleanField("允许多选", default=False)
    show_voter_names = models.BooleanField("展示投票参与人", default=False)
    allow_vote_change = models.BooleanField("允许修改投票", default=True)

    created_at = models.DateTimeField("创建时间", auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "活动"
        verbose_name_plural = "活动"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title


class Signup(models.Model):
    """A signup record for a gathering activity."""

    activity = models.ForeignKey(
        Activity, on_delete=models.CASCADE, related_name="signups", verbose_name="活动"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="signups", verbose_name="报名人"
    )
    real_name_snapshot = models.CharField("姓名快照", max_length=64)
    participant_count = models.PositiveSmallIntegerField("参加人数", default=1)
    bring_guests = models.BooleanField("带家属", default=False)
    note = models.CharField("备注", max_length=256, blank=True)
    created_at = models.DateTimeField("报名时间", auto_now_add=True)

    class Meta:
        verbose_name = "报名记录"
        verbose_name_plural = "报名记录"
        unique_together = [("activity", "user")]
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"{self.real_name_snapshot} 报名 {self.activity.title}"


class VoteOption(models.Model):
    """An option in a voting activity."""

    activity = models.ForeignKey(
        Activity, on_delete=models.CASCADE, related_name="vote_options", verbose_name="活动"
    )
    text = models.CharField("选项", max_length=256)
    order = models.PositiveSmallIntegerField("排序", default=0)

    class Meta:
        verbose_name = "投票选项"
        verbose_name_plural = "投票选项"
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return self.text


class VoteRecord(models.Model):
    """A vote cast by a user for a voting option."""

    option = models.ForeignKey(
        VoteOption, on_delete=models.CASCADE, related_name="votes", verbose_name="选项"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="vote_records", verbose_name="投票人"
    )
    real_name_snapshot = models.CharField("姓名快照", max_length=64)
    created_at = models.DateTimeField("投票时间", auto_now_add=True)

    class Meta:
        verbose_name = "投票记录"
        verbose_name_plural = "投票记录"
        unique_together = [("option", "user")]
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"{self.real_name_snapshot} 投票 {self.option.text}"


class ChainRecord(models.Model):
    """A chain entry filled by a user."""

    activity = models.ForeignKey(
        Activity, on_delete=models.CASCADE, related_name="chain_records", verbose_name="活动"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="chain_records", verbose_name="填写人"
    )
    real_name_snapshot = models.CharField("姓名快照", max_length=64)
    will_attend = models.BooleanField("是否参加", default=True)
    participant_count = models.PositiveSmallIntegerField("人数", default=1)
    note = models.CharField("备注", max_length=256, blank=True)
    created_at = models.DateTimeField("填写时间", auto_now_add=True)

    class Meta:
        verbose_name = "接龙记录"
        verbose_name_plural = "接龙记录"
        unique_together = [("activity", "user")]
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"{self.real_name_snapshot} 接龙 {self.activity.title}"
