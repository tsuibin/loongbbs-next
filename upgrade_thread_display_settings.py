"""组 8「主题显示选项」落地后的数据迁移：删掉本地旧键 posts_per_page。

每页帖数改由 vB 的 maxposts / usermaxposts 决定，旧键只会在后台「本站设置」
里制造第二个开关。
"""
from loongbbs import create_app
from loongbbs.models import Setting
from loongbbs.extensions import db

app = create_app()

with app.app_context():
    rows = db.session.query(Setting).all()
    removed = False
    for row in rows:
        if row.key == "posts_per_page":
            db.session.delete(row)
            removed = True
    db.session.commit()
    print("删除 posts_per_page:", removed)

    values = {row.key: row.value for row in db.session.query(Setting).all()}
    for key in ("maxposts", "usermaxposts", "postorder", "pagenavpages", "wordwrap",
                "postmaxchars", "showdeficon", "stopshouting"):
        print(f"  {key} = {values.get(key, '(未设置，用 vB 默认值)')}")
