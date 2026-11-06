"""组 9「版块显示选项」落地后的数据迁移：删掉本地旧键 threads_per_page。

版块页每页主题数改由 vB 的 maxthreads 决定，旧键只会制造第二个开关。
"""
from loongbbs import create_app
from loongbbs.models import Setting
from loongbbs.extensions import db

app = create_app()

with app.app_context():
    removed = False
    for row in db.session.query(Setting).all():
        if row.key == "threads_per_page":
            db.session.delete(row)
            removed = True
    db.session.commit()
    print("删除 threads_per_page:", removed)

    # 原版前缀值末尾带一个空格；导入时尾随空格被写成了替换字符 U+FFFD，这里复原
    fixed = []
    for key, value in (
        ("movedthreadprefix", "Moved: "),
        ("stickythreadprefix", "Sticky: "),
        ("pollthreadprefix", "Poll: "),
    ):
        row = db.session.get(Setting, key)
        if row is not None and "\ufffd" in (row.value or ""):
            row.value = value
            fixed.append(key)
    db.session.commit()
    print("修正前缀值:", fixed or "无")

    values = {row.key: row.value for row in db.session.query(Setting).all()}
    for key in ("maxthreads", "usehotthreads", "hotnumberviews", "hotnumberposts", "showdots",
                "linktopages", "maxmultipage", "showvotes", "votechange", "movedthreadprefix",
                "stickythreadprefix", "pollthreadprefix", "useforumjump"):
        print(f"  {key} = {values.get(key, '(未设置，用 vB 默认值)')!r}")
