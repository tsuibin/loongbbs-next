"""给已有 loongbbs.db 补上个人资料字段（新装库 flask init-db 即可，不需要本脚本）。

对应 vB 2.3.11 的 user 表：homepage / icq / aim / yahoo / location / interests / occupation / birthday。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "loongbbs-next"))

from sqlalchemy import inspect, text

from loongbbs import create_app
from loongbbs.extensions import db

COLUMNS = {
    "homepage": "VARCHAR(255) NOT NULL DEFAULT ''",
    "icq": "VARCHAR(30) NOT NULL DEFAULT ''",
    "aim": "VARCHAR(30) NOT NULL DEFAULT ''",
    "yahoo": "VARCHAR(30) NOT NULL DEFAULT ''",
    "location": "VARCHAR(100) NOT NULL DEFAULT ''",
    "interests": "VARCHAR(200) NOT NULL DEFAULT ''",
    "occupation": "VARCHAR(100) NOT NULL DEFAULT ''",
    "birthday": "VARCHAR(10) NOT NULL DEFAULT ''",
}


def main() -> None:
    app = create_app()
    with app.app_context():
        existing = {c["name"] for c in inspect(db.engine).get_columns("users")}
        added = []
        for name, ddl in COLUMNS.items():
            if name not in existing:
                db.session.execute(text(f"ALTER TABLE users ADD COLUMN {name} {ddl}"))
                added.append(name)
        db.session.commit()
        print("新增列:", added or "无（都已存在）")
        print("数据库:", app.config["SQLALCHEMY_DATABASE_URI"])


if __name__ == "__main__":
    main()
