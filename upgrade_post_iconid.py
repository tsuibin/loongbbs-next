"""给 posts 加 iconid 列（vB 发帖页的消息图标，0 = 不使用；新装库 flask init-db 即可）。"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "loongbbs-next"))

from sqlalchemy import inspect, text

from loongbbs import create_app
from loongbbs.extensions import db


def main() -> None:
    app = create_app()
    with app.app_context():
        existing = {c["name"] for c in inspect(db.engine).get_columns("posts")}
        if "iconid" in existing:
            print("posts.iconid 已存在，跳过")
        else:
            db.session.execute(
                text("ALTER TABLE posts ADD COLUMN iconid INTEGER NOT NULL DEFAULT 0")
            )
            db.session.commit()
            print("已添加 posts.iconid")
        print("posts 现有列:", sorted(c["name"] for c in inspect(db.engine).get_columns("posts")))
        print("数据库:", app.config["SQLALCHEMY_DATABASE_URI"])


if __name__ == "__main__":
    main()
