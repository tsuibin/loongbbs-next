"""建 email_log 表（sendtofriend 的待发队列）。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from loongbbs import create_app
from loongbbs.extensions import db
from loongbbs.models import EmailLog


def main() -> None:
    app = create_app()
    with app.app_context():
        EmailLog.__table__.create(db.engine, checkfirst=True)
        print("email_log 表已就绪")


if __name__ == "__main__":
    main()
