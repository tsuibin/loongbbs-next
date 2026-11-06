"""给已有 loongbbs.db 补上「标记已读」所需的 users.last_visit 列和 forum_reads 表。

新装库用 ``flask init-db`` + ``flask seed`` 即可，不需要本脚本。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "loongbbs-next"))

from sqlalchemy import inspect, text

from loongbbs import create_app
from loongbbs.extensions import db
from loongbbs.models import ForumRead


def main() -> None:
    app = create_app()
    with app.app_context():
        ForumRead.__table__.create(bind=db.engine, checkfirst=True)

        cols = {c["name"] for c in inspect(db.engine).get_columns("users")}
        if "last_visit" not in cols:
            db.session.execute(text("ALTER TABLE users ADD COLUMN last_visit DATETIME"))
            # 老数据没有 last_visit：用 joined_at 兜底，避免首次进入时整站都算“有新帖”
            db.session.execute(text("UPDATE users SET last_visit = joined_at"))
            db.session.commit()
            print("已补 users.last_visit 列")
        else:
            print("users.last_visit 已存在")

        print("forum_reads 表已就绪：", app.config["SQLALCHEMY_DATABASE_URI"])


if __name__ == "__main__":
    main()
