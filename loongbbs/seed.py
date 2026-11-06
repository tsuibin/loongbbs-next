"""Demo data for a fresh install: categories, forums, admin, sample threads."""
from __future__ import annotations

from datetime import timedelta

from .extensions import db
from .models import Category, Forum, Post, Setting, Thread, User, UserGroup, utcnow
from .settings import DEFAULTS
from .models import Attachment  # noqa: F401  (imported for table creation ordering)

# 参考站 usergroup 表的 (id, 组名, 头衔)
GROUPS = [
    (1, "Unregistered / Not Logged In", "Guest"),
    (2, "Registered", ""),
    (3, "Users Awaiting Email Confirmation", ""),
    (4, "(COPPA) Users Awaiting Moderation", ""),
    (5, "Super Moderators", "Super Moderator"),
    (6, "Administrators", "Administrator"),
    (7, "Moderators", "Moderator"),
]


def seed(admin_name: str = "admin", admin_password: str = "admin12345") -> None:
    db.create_all()

    # vB 2.3.11 的 usergroup 表：显示身份用的是 usertitle 这一列
    for gid, title, usertitle in GROUPS:
        if db.session.get(UserGroup, gid) is None:
            db.session.add(UserGroup(id=gid, title=title, usertitle=usertitle))
    db.session.flush()

    existing_settings = {row.key for row in db.session.execute(db.select(Setting)).scalars()}
    for key, value in DEFAULTS.items():
        if key not in existing_settings:
            db.session.add(Setting(key=key, value=value))

    admin = db.session.scalar(db.select(User).where(User.username == admin_name))
    if admin is None:
        admin = User(username=admin_name, email=f"{admin_name}@localhost", is_admin=True, usergroupid=6)
        admin.set_password(admin_password)
        db.session.add(admin)
        db.session.flush()

    demo = db.session.scalar(db.select(User).where(User.username == "loongfan"))
    if demo is None:
        demo = User(username="loongfan", email="loongfan@localhost", usergroupid=2)
        demo.set_password("loongfan123")
        db.session.add(demo)
        db.session.flush()

    if db.session.scalar(db.select(Category).limit(1)) is None:
        general = Category(name="社区大厅", position=1)
        tech = Category(name="龙芯技术", position=2)
        db.session.add_all([general, tech])
        db.session.flush()

        forums = [
            Forum(category_id=general.id, name="站务公告", description="站点规则、公告与反馈。", position=1),
            Forum(category_id=general.id, name="闲聊灌水", description="随便聊聊，别跑题太远。", position=2),
            Forum(category_id=tech.id, name="龙架构移植", description="LoongArch 上的软硬件移植经验。", position=1),
            Forum(category_id=tech.id, name="数据库与运维", description="PostgreSQL / MySQL、备份与迁移。", position=2),
        ]
        db.session.add_all(forums)
        db.session.flush()
    else:
        forums = db.session.execute(db.select(Forum)).scalars().all()

    if db.session.scalar(db.select(Thread).limit(1)) is None and forums:
        target = forums[0]
        now = utcnow()

        thread1 = Thread(
            forum_id=target.id,
            author_id=admin.id,
            title="欢迎来到 LoongBBS Next",
            created_at=now - timedelta(days=2),
            last_post_at=now - timedelta(hours=3),
        )
        db.session.add(thread1)
        db.session.flush()
        db.session.add(
            Post(
                thread_id=thread1.id,
                author_id=admin.id,
                title="欢迎来到 LoongBBS Next",
                body=(
                    "这是用 Flask + SQLAlchemy 重写的论坛，PostgreSQL 是一等公民。\n\n"
                    "已经能做的事情：发主题、回复、上传附件（图片带细边框，可在后台切换缩略图/原图）、"
                    "搜索、私信、后台管版块和用户。\n\n支持 [b]BBCode[/b]、[i]斜体[/i]、"
                    "[url=https://www.loongson.cn]链接[/url] 和 [code]代码块[/code]。"
                ),
                created_at=now - timedelta(days=2),
            )
        )

        thread2 = Thread(
            forum_id=target.id,
            author_id=demo.id,
            title="迁移到 PostgreSQL 之后，搜索该怎么优化？",
            created_at=now - timedelta(days=1),
            last_post_at=now - timedelta(hours=1),
        )
        db.session.add(thread2)
        db.session.flush()
        db.session.add_all(
            [
                Post(
                    thread_id=thread2.id,
                    author_id=demo.id,
                    title="迁移到 PostgreSQL 之后，搜索该怎么优化？",
                    body="现在搜索是 ILIKE 全表扫，数据量一上来就慢。考虑换成 tsvector + GIN 索引，有人踩过坑吗？",
                    created_at=now - timedelta(days=1),
                ),
                Post(
                    thread_id=thread2.id,
                    author_id=admin.id,
                    title="Re: 迁移到 PostgreSQL 之后，搜索该怎么优化？",
                    body=(
                        "可以先用 [code]to_tsvector('simple', coalesce(title,'') || ' ' || coalesce(body,''))[/code] "
                        "建表达式索引，中文分词再上 zhparser 或 pg_jieba。"
                    ),
                    created_at=now - timedelta(hours=1),
                ),
            ]
        )

        thread3 = Thread(
            forum_id=forums[-1].id,
            author_id=admin.id,
            title="附件图片的缩略图上限怎么定？",
            created_at=now - timedelta(hours=5),
            last_post_at=now - timedelta(hours=4),
        )
        db.session.add(thread3)
        db.session.flush()
        db.session.add(
            Post(
                thread_id=thread3.id,
                author_id=admin.id,
                title="附件图片的缩略图上限怎么定？",
                body="默认 480×360，后台「附件图片显示缩略图」可以关掉，改成原图显示。",
                created_at=now - timedelta(hours=5),
            )
        )

        thread1.is_sticky = True

    db.session.commit()
    print("演示数据已写入。")
    print(f"管理员：{admin_name} / {admin_password}")
    print("演示用户：loongfan / loongfan123")
