"""给已有 loongbbs.db 补上「编辑选项」所需的 users 列（新装库用 flask init-db 就够，不需要本脚本）。

用法：在仓库根执行
    .venv\\Scripts\\python.exe upgrade_options.py
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

BASE = Path(__file__).resolve().parent
DB = BASE / "loongbbs.db"

if not DB.exists():
    raise SystemExit(f"找不到数据库：{DB}")

# 列名, DDL 片段（默认值与 loongbbs/models.py 里的 server_default 保持一致）
COLUMNS = [
    ("invisible", "INTEGER NOT NULL DEFAULT 0"),
    ("cookieuser", "INTEGER NOT NULL DEFAULT 1"),
    ("nosessionhash", "INTEGER NOT NULL DEFAULT 0"),
    ("allowmail", "INTEGER NOT NULL DEFAULT 1"),
    ("showemail", "INTEGER NOT NULL DEFAULT 1"),
    ("emailnotification", "INTEGER NOT NULL DEFAULT 0"),
    ("receivepm", "INTEGER NOT NULL DEFAULT 1"),
    ("emailonpm", "INTEGER NOT NULL DEFAULT 1"),
    ("pmpopup", "INTEGER NOT NULL DEFAULT 1"),
    ("showsignatures", "INTEGER NOT NULL DEFAULT 1"),
    ("showavatars", "INTEGER NOT NULL DEFAULT 1"),
    ("showimages", "INTEGER NOT NULL DEFAULT 1"),
    ("vbcode", "INTEGER NOT NULL DEFAULT 1"),
    ("prunedays", "INTEGER NOT NULL DEFAULT -1"),
    ("umaxposts", "INTEGER NOT NULL DEFAULT -1"),
    ("startofweek", "INTEGER NOT NULL DEFAULT 1"),
    ("timezoneoffset", "INTEGER NOT NULL DEFAULT 0"),
    ("newstyleset", "INTEGER NOT NULL DEFAULT 0"),
    ("buddylist", "VARCHAR(255) NOT NULL DEFAULT ''"),
    ("ignorelist", "VARCHAR(255) NOT NULL DEFAULT ''"),
]

con = sqlite3.connect(DB)
cols = [row[1] for row in con.execute("PRAGMA table_info(users)")]
for name, ddl in COLUMNS:
    if name not in cols:
        con.execute(f"ALTER TABLE users ADD COLUMN {name} {ddl}")
        print(f"users.{name} 已添加")
con.commit()
con.close()

# 表结构由 SQLAlchemy 兜底（新表/新索引）
import sys

sys.path.insert(0, str(BASE))
from loongbbs import create_app
from loongbbs.extensions import db

app = create_app()
with app.app_context():
    db.create_all()
    from sqlalchemy import inspect

    user_cols = [c["name"] for c in inspect(db.engine).get_columns("users")]
    missing = [n for n, _ in COLUMNS if n not in user_cols]
    print("缺失列：", missing or "无")
