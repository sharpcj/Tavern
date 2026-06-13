"""
Seed data management command.

Creates sample users, posts, comments, activities, announcements,
albums, photos, birthday wishes, and notifications for manual testing.

Usage:
    uv run python manage.py seed_data
    uv run python manage.py seed_data --clean   # delete existing data first
"""

from __future__ import annotations

import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import AccountStatus, ReviewStatus, UserRole
from apps.activities.models import Activity, ActivityStatus, ActivityType
from apps.announcements.models import Announcement
from apps.birthdays.models import BirthdayWish
from apps.comments.models import Comment
from apps.common.enums import ContentStatus, DisplayMode
from apps.posts.models import Post, PostCategory
from apps.profiles.models import Profile

User = get_user_model()

# ── sample data ──────────────────────────────────────────────────

SAMPLE_USERS = [
    {"email": "admin@tavern.local", "real_name": "陈老师", "nickname": "班主任陈老师", "role": UserRole.SUPER_ADMIN, "city": "北京", "occupation": "班主任", "bio": "大家好，我是当年的班主任，很高兴能在这里和大家保持联系。", "birthday_month": 3, "show_birthday": True},
    {"email": "zhangwei@tavern.local", "real_name": "张伟", "nickname": "大伟", "role": UserRole.MODERATOR, "city": "上海", "occupation": "软件工程师", "bio": "在上海做后端开发，平时喜欢跑步和摄影。", "birthday_month": 6, "show_birthday": True},
    {"email": "lina@tavern.local", "real_name": "李娜", "nickname": "娜娜", "role": UserRole.CLASSMATE, "city": "深圳", "occupation": "产品经理", "bio": "在深圳一家互联网公司做产品，周末喜欢爬山。", "birthday_month": 6, "show_birthday": True},
    {"email": "wangfang@tavern.local", "real_name": "王芳", "nickname": "小芳", "role": UserRole.CLASSMATE, "city": "广州", "occupation": "医生", "bio": "在广州一家三甲医院工作，欢迎大家来广州玩。", "birthday_month": 9, "show_birthday": True},
    {"email": "liuqiang@tavern.local", "real_name": "刘强", "nickname": "强哥", "role": UserRole.CLASSMATE, "city": "杭州", "occupation": "创业者", "bio": "在杭州创业，做电商相关的项目。", "birthday_month": 12, "show_birthday": False},
    {"email": "zhaomin@tavern.local", "real_name": "赵敏", "nickname": "敏敏", "role": UserRole.CLASSMATE, "city": "成都", "occupation": "教师", "bio": "在成都一所中学教英语，喜欢旅行和读书。", "birthday_month": 6, "show_birthday": True},
    {"email": "sunhao@tavern.local", "real_name": "孙浩", "nickname": "浩子", "role": UserRole.CLASSMATE, "city": "北京", "occupation": "金融分析师", "bio": "在北京做金融，平时比较忙，但聚会一定参加。", "birthday_month": 1, "show_birthday": True},
    {"email": "zhoujie@tavern.local", "real_name": "周洁", "nickname": "洁洁", "role": UserRole.CLASSMATE, "city": "南京", "occupation": "设计师", "bio": "在南京做 UI 设计，喜欢画画和摄影。", "birthday_month": 8, "show_birthday": True},
]

SAMPLE_POSTS = [
    {"content": "大家好！毕业这么多年了，很高兴能在咱们班的社区里和大家重逢。我在上海做软件开发，有来上海的同学可以联系我！", "category": PostCategory.LIFE, "display_mode": DisplayMode.REAL_NAME},
    {"content": "上周翻到了高中时候的老照片，那时候大家真年轻啊。改天扫描一下发到相册里。", "category": PostCategory.OLD_PHOTOS, "display_mode": DisplayMode.REAL_NAME},
    {"content": "最近深圳天气特别好，周末去爬了梧桐山。有在深圳的同学吗？下次可以一起。", "category": PostCategory.LIFE, "display_mode": DisplayMode.NICKNAME},
    {"content": "听说陈老师退休了，大家要不要组织一次探望？我可以负责联系。", "category": PostCategory.TEACHER, "display_mode": DisplayMode.REAL_NAME},
    {"content": "有没有做前端开发的同学？公司最近在招人，可以内推。", "category": PostCategory.HELP, "display_mode": DisplayMode.REAL_NAME},
    {"content": "刚参加完一个同学聚会，感慨万千。虽然大家各奔东西，但感情还在。", "category": PostCategory.REUNION, "display_mode": DisplayMode.REAL_NAME},
    {"content": "我家小朋友刚满三岁，时间过得真快。大家有娃的来交流一下育儿经验？", "category": PostCategory.FAMILY, "display_mode": DisplayMode.NICKNAME},
    {"content": "周末无聊，有人一起打游戏吗？王者荣耀或者吃鸡都行。", "category": PostCategory.CHAT, "display_mode": DisplayMode.NICKNAME},
]

SAMPLE_COMMENTS = [
    "欢迎欢迎！",
    "好怀念啊，期待看到老照片。",
    "我在深圳！下次爬山叫上我。",
    "支持！算我一个。",
    "帮顶，希望能找到合适的人。",
    "是啊，时间过得太快了。",
    "小朋友好可爱！",
    "来来来，我带你。",
]

SAMPLE_ANNOUNCEMENTS = [
    {"title": "欢迎来到班级社区", "content": "各位同学好！这是咱们班的专属社区网站。在这里可以分享近况、发布动态、组织活动、上传照片。请大家先完善个人资料，方便同学之间联系。\n\n注意：\n1. 请使用真实姓名\n2. 联系方式默认不公开，需要自行设置\n3. 发布内容请遵守社区规则\n4. 有问题请联系管理员", "is_pinned": True, "require_read_confirm": True},
    {"title": "关于下个月同学聚会的初步想法", "content": "有同学提议下个月在母校附近聚一次，具体时间和地点待定。请大家关注活动板块，届时会发布正式报名。\n\n初步计划：\n- 时间：下月中旬周末\n- 地点：母校附近餐厅\n- 形式：午餐 + 校园重游\n\n有建议的同学可以在活动板块留言。", "is_pinned": True, "require_read_confirm": False},
]

SAMPLE_ACTIVITIES = [
    {"title": "2026年夏季同学聚会", "activity_type": ActivityType.GATHERING, "description": "一年一度的夏季聚会，欢迎大家参加！地点定在母校附近的老地方餐厅。", "location": "母校附近老地方餐厅", "status": ActivityStatus.OPEN},
    {"title": "聚会时间投票", "activity_type": ActivityType.VOTING, "description": "请大家投票选择最方便的聚会时间。", "status": ActivityStatus.OPEN},
    {"title": "聚会报名接龙", "activity_type": ActivityType.CHAIN, "description": "请确认参加聚会的同学在此接龙，方便统计人数。", "status": ActivityStatus.OPEN},
]

# ── helpers ───────────────────────────────────────────────────────

def create_users():
    """Create sample users and return them keyed by email."""
    users = {}
    for data in SAMPLE_USERS:
        user, created = User.objects.get_or_create(
            email=data["email"],
            defaults={
                "real_name": data["real_name"],
                "nickname": data.get("nickname", data["real_name"]),
                "high_school": "第一中学",
                "high_school_class": "高三（1）班",
                "role": data["role"],
                "review_status": ReviewStatus.APPROVED,
                "account_status": AccountStatus.NORMAL,
                "is_staff": data["role"] == UserRole.SUPER_ADMIN,
                "is_superuser": data["role"] == UserRole.SUPER_ADMIN,
            },
        )
        if created:
            user.set_password("Pass1234!")
            user.save()
        # Update profile
        profile = user.profile
        profile.city = data.get("city", "")
        profile.occupation = data.get("occupation", "")
        profile.bio = data.get("bio", "")
        profile.birthday_month = data.get("birthday_month")
        profile.show_birthday = data.get("show_birthday", False)
        profile.save(update_fields=["city", "occupation", "bio", "birthday_month", "show_birthday"])
        users[data["email"]] = user
    return users


def create_posts(users: dict):
    """Create sample posts with random authors."""
    user_list = [u for e, u in users.items() if u.role != UserRole.SUPER_ADMIN]
    admin = users["admin@tavern.local"]
    posts = []
    for i, data in enumerate(SAMPLE_POSTS):
        author = user_list[i % len(user_list)]
        post = Post.objects.create(
            author=author,
            content=data["content"],
            category=data["category"],
            display_mode=data["display_mode"],
            status=ContentStatus.PUBLISHED,
            created_at=timezone.now() - timedelta(days=len(SAMPLE_POSTS) - i),
        )
        posts.append(post)

    # Pin one post
    posts[0].is_pinned = True
    posts[0].pinned_at = timezone.now()
    posts[0].pinned_by = admin
    posts[0].save(update_fields=["is_pinned", "pinned_at", "pinned_by"])
    return posts


def create_comments(users: dict, posts: list):
    """Create sample comments and replies."""
    user_list = list(users.values())
    for post in posts[:4]:
        for j in range(random.randint(1, 3)):
            author = random.choice(user_list)
            comment = Comment.objects.create(
                post=post,
                author=author,
                content=random.choice(SAMPLE_COMMENTS),
                display_mode=random.choice([DisplayMode.REAL_NAME, DisplayMode.NICKNAME]),
                status=ContentStatus.PUBLISHED,
            )
            # Maybe add a reply
            if random.random() > 0.5:
                reply_author = random.choice([u for u in user_list if u != author])
                Comment.objects.create(
                    post=post,
                    author=reply_author,
                    parent=comment,
                    content=random.choice(SAMPLE_COMMENTS),
                    display_mode=DisplayMode.REAL_NAME,
                    status=ContentStatus.PUBLISHED,
                )


def create_announcements(users: dict):
    """Create sample announcements."""
    admin = users["admin@tavern.local"]
    for data in SAMPLE_ANNOUNCEMENTS:
        Announcement.objects.create(
            title=data["title"],
            content=data["content"],
            publisher=admin,
            publisher_name_snapshot=admin.real_name,
            is_pinned=data["is_pinned"],
            require_read_confirm=data["require_read_confirm"],
            expires_at=timezone.now() + timedelta(days=90),
            status=ContentStatus.PUBLISHED,
        )


def create_activities(users: dict):
    """Create sample activities."""
    user_list = [u for e, u in users.items() if u.role != UserRole.SUPER_ADMIN]
    for i, data in enumerate(SAMPLE_ACTIVITIES):
        initiator = user_list[i % len(user_list)]
        Activity.objects.create(
            title=data["title"],
            activity_type=data["activity_type"],
            initiator=initiator,
            initiator_name_snapshot=initiator.real_name,
            description=data["description"],
            location=data.get("location", ""),
            start_time=timezone.now() + timedelta(days=30),
            deadline=timezone.now() + timedelta(days=20),
            status=data["status"],
        )


def create_birthday_wishes(users: dict):
    """Create sample birthday wishes for users whose birthday is this month."""
    current_month = timezone.now().month
    birthday_users = [
        u for u in users.values()
        if u.profile.birthday_month == current_month and u.profile.show_birthday
    ]
    if not birthday_users:
        return
    other_users = [u for u in users.values() if u not in birthday_users]
    for recipient in birthday_users:
        for _ in range(random.randint(1, 3)):
            if not other_users:
                break
            author = random.choice(other_users)
            BirthdayWish.objects.create(
                recipient=recipient,
                author=author,
                content=f"{recipient.real_name}，生日快乐！祝你身体健康，工作顺利，天天开心！",
                display_mode=random.choice([DisplayMode.REAL_NAME, DisplayMode.NICKNAME]),
                status=ContentStatus.PUBLISHED,
            )


# ── command ───────────────────────────────────────────────────────

class Command(BaseCommand):
    help = "Populate the database with sample data for manual testing."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clean",
            action="store_true",
            help="Delete all existing data before seeding.",
        )

    def handle(self, *args, **options):
        if options["clean"]:
            self.stdout.write("Cleaning existing data...")
            BirthdayWish.objects.all().delete()
            Comment.objects.all().delete()
            Post.objects.all().delete()
            Announcement.objects.all().delete()
            Activity.objects.all().delete()
            Profile.objects.all().delete()
            User.objects.all().delete()
            self.stdout.write("Cleaned.")

        self.stdout.write("Creating users...")
        users = create_users()
        self.stdout.write(f"  Created {len(users)} users (password: Pass1234!)")

        self.stdout.write("Creating posts and comments...")
        posts = create_posts(users)
        create_comments(users, posts)
        self.stdout.write(f"  Created {len(posts)} posts with comments")

        self.stdout.write("Creating announcements...")
        create_announcements(users)
        self.stdout.write(f"  Created {len(SAMPLE_ANNOUNCEMENTS)} announcements")

        self.stdout.write("Creating activities...")
        create_activities(users)
        self.stdout.write(f"  Created {len(SAMPLE_ACTIVITIES)} activities")

        self.stdout.write("Creating birthday wishes...")
        create_birthday_wishes(users)
        self.stdout.write("  Done")

        self.stdout.write(self.style.SUCCESS("\nSeed data created successfully!"))
        self.stdout.write("")
        self.stdout.write("Test accounts (all passwords: Pass1234!):")
        self.stdout.write(f"  Super Admin:  admin@tavern.local")
        self.stdout.write(f"  Moderator:    zhangwei@tavern.local")
        self.stdout.write(f"  Classmates:   lina@tavern.local / wangfang@tavern.local / ...")
        self.stdout.write("")
        self.stdout.write("Start the server and open http://localhost:5173 to explore.")
