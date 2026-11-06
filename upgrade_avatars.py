"""给已有 loongbbs.db 补上头像所需的列和表（新装库用 flask init-db 就够，不需要本脚本）。

用法：在仓库根执行
    .\.venv\Scripts\python.exe upgrade_avatars.py
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

BASE = Path(__file__).resolve().parent
DB = BASE / "loongbbs.db"

if not DB.exists():
    raise SystemExit(f"找不到数据库：{DB}")

con = sqlite3.connect(DB)
cols = [row[1] for row in con.execute("PRAGMA table_info(users)")]
if "avatar_id" not in cols:
    con.execute("ALTER TABLE users ADD COLUMN avatar_id INTEGER NOT NULL DEFAULT 0")
    print("users.avatar_id 已添加")
if "custom_avatar" not in cols:
    con.execute("ALTER TABLE users ADD COLUMN custom_avatar VARCHAR(255) NOT NULL DEFAULT ''")
    print("users.custom_avatar 已添加")
con.commit()
con.close()

# avatars 表由 SQLAlchemy 建，避免这里重复写 DDL
import sys

sys.path.insert(0, str(BASE))
from loongbbs import create_app
from loongbbs.extensions import db

app = create_app()
with app.app_context():
    db.create_all()
    from sqlalchemy import inspect

    tables = inspect(db.engine).get_table_names()
    print("avatars 表存在：", "avatars" in tables)
