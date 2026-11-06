"""建 thread_subscriptions 表（vB 的 subscribethread）。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from loongbbs import create_app
from loongbbs.extensions import db
from loongbbs.models import ThreadSubscription


def main() -> None:
    app = create_app()
    with app.app_context():
        ThreadSubscription.__table__.create(db.engine, checkfirst=True)
        print("thread_subscriptions 表已就绪")
        print("数据库:", app.config["SQLALCHEMY_DATABASE_URI"])


if __name__ == "__main__":
    main()
