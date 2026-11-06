"""建 thread_ratings 表（vB 的 threadrate）。新装库 flask init-db 即可，不需要本脚本。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from loongbbs import create_app
from loongbbs.extensions import db
from loongbbs.models import ThreadRating


def main() -> None:
    app = create_app()
    with app.app_context():
        ThreadRating.__table__.create(db.engine, checkfirst=True)
        print("thread_ratings 表已就绪")
        print("数据库:", app.config["SQLALCHEMY_DATABASE_URI"])


if __name__ == "__main__":
    main()
