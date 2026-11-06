"""补上 usergroup 表、users.usergroupid/usertitle、posts.title，并回填参考站初值。

用法：在仓库根执行
    .venv\\Scripts\\python.exe upgrade_groups_posts.py

新装库用 ``flask init-db`` 即可，不需要本脚本。
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
DB = BASE / "loongbbs.db"

if not DB.exists():
    raise SystemExit(f"找不到数据库：{DB}")

# 列名, DDL（默认值与 models.py 的 server_default 一致）
COLUMNS = [
    ("users", "usergroupid", "INTEGER NOT NULL DEFAULT 2"),
    ("users", "usertitle", "VARCHAR(100) NOT NULL DEFAULT ''"),
    ("posts", "title", "VARCHAR(200) NOT NULL DEFAULT ''"),
]

con = sqlite3.connect(DB)
for table, name, ddl in COLUMNS:
    cols = [row[1] for row in con.execute(f"PRAGMA table_info({table})")]
    if name not in cols:
        con.execute(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}")
        print(f"{table}.{name} 已添加")
con.commit()
con.close()

sys.path.insert(0, str(BASE))
from loongbbs import create_app  # noqa: E402
from loongbbs.extensions import db  # noqa: E402
from loongbbs.models import Post, Thread, User, UserGroup  # noqa: E402

# 参考站 usergroup 表里的组名与头衔（title / usertitle）
GROUPS = [
    (1, "Unregistered / Not Logged In", "Guest"),
    (2, "Registered", ""),
    (3, "Users Awaiting Email Confirmation", ""),
    (4, "(COPPA) Users Awaiting Moderation", ""),
    (5, "Super Moderators", "Super Moderator"),
    (6, "Administrators", "Administrator"),
    (7, "Moderators", "Moderator"),
]

app = create_app()
with app.app_context():
    db.create_all()

    for gid, title, usertitle in GROUPS:
        if db.session.get(UserGroup, gid) is None:
            db.session.add(UserGroup(id=gid, title=title, usertitle=usertitle))
    db.session.flush()

    # 管理员进 Administrators 组，其余注册会员进 Registered 组
    for user in db.session.execute(db.select(User)).scalars():
        user.usergroupid = 6 if user.is_admin else 2
        user.usertitle = ""

    # 每条帖子补标题：主题首帖用主题标题，回复用 "Re: 主题标题"
    for thread in db.session.execute(db.select(Thread)).scalars():
        first = db.session.scalar(
            db.select(Post).where(Post.thread_id == thread.id).order_by(Post.created_at).limit(1)
        )
        for post in db.session.execute(
            db.select(Post).where(Post.thread_id == thread.id).order_by(Post.created_at)
        ).scalars():
            if not post.title:
                post.title = thread.title if (first is not None and post.id == first.id) else f"Re: {thread.title}"

    db.session.commit()

    print("用户组：", [(g.id, g.title, g.usertitle) for g in db.session.execute(db.select(UserGroup)).scalars()])
    print("用户：", [(u.username, u.usergroupid, u.usertitle_text) for u in db.session.execute(db.select(User)).scalars()])
    print("帖子标题：", [(p.id, p.title) for p in db.session.execute(db.select(Post)).scalars()])
