"""建 online_sessions 表（vB session 表的对应物，供 /online 在线用户页使用）。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from loongbbs import create_app
from loongbbs.extensions import db
from loongbbs.models import OnlineSession


def main() -> None:
    app = create_app()
    with app.app_context():
        OnlineSession.__table__.create(db.engine, checkfirst=True)
        print("表就绪:", OnlineSession.__tablename__)
        print("数据库:", app.config["SQLALCHEMY_DATABASE_URI"])


if __name__ == "__main__":
    main()
