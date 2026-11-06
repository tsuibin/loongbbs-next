"""建 post_reports 表（vB 的 reported post 队列）。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from loongbbs import create_app
from loongbbs.extensions import db
from loongbbs.models import PostReport


def main() -> None:
    app = create_app()
    with app.app_context():
        PostReport.__table__.create(db.engine, checkfirst=True)
        print("post_reports 表已就绪")


if __name__ == "__main__":
    main()
