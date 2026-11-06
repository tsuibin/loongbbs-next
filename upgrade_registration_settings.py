"""把本站早期的 allow_registration 迁到 vB 后台 Options 的 allowregistration。

组 6「用户与注册」里的 allowregistration 才是权威开关，旧的 allow_registration
只是本地别名；迁移后只保留 vB 变量名。
"""
from loongbbs import create_app
from loongbbs.extensions import db
from loongbbs.models import Setting

app = create_app()

with app.app_context():
    rows = {row.key: row for row in db.session.query(Setting).all()}

    if "allow_registration" in rows:
        old = rows["allow_registration"]
        if "allowregistration" in rows:
            db.session.delete(old)
            print(f"allow_registration={old.value}: 目标键已存在，删除旧键")
        else:
            old.key = "allowregistration"
            print(f"allow_registration -> allowregistration = {old.value}")
    else:
        print("没有旧键 allow_registration")

    db.session.commit()
    final = {row.key: row.value for row in db.session.query(Setting).all()}
    for key in ("allowregistration", "minuserlength", "maxuserlength", "illegalusernames",
                "requireuniqueemail", "allowsignatures", "displayemails", "cookietimeout"):
        print(f"  {key} = {final.get(key, '(未设置，用 vB 默认值)')}")
