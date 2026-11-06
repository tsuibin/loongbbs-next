"""建 polls / poll_options / poll_votes 三张表（vB 发帖页的「发起投票」）。"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "loongbbs-next"))

from loongbbs import create_app
from loongbbs.extensions import db
from loongbbs.models import Poll, PollOption, PollVote


def main() -> None:
    app = create_app()
    with app.app_context():
        for model in (Poll, PollOption, PollVote):
            model.__table__.create(db.engine, checkfirst=True)
            print("表就绪:", model.__tablename__)
        print("数据库:", app.config["SQLALCHEMY_DATABASE_URI"])


if __name__ == "__main__":
    main()
