"""把本站早期的头像/缩略图设置迁到 vB 后台 Options 的变量名与单位。

- thumb_mode / thumb_width / thumb_height  → attachthumbmode / attachthumbwidth / attachthumbheight
- avatarmaxsize 的值原来是 KB，改为 vB 的字节（<=1024 视为旧值，乘以 1024）
- avatarmaxdimension / avatarcustomposts / avatarenabled 语义一致，原地保留
"""
from loongbbs import create_app
from loongbbs.extensions import db
from loongbbs.models import Setting

app = create_app()

RENAMES = {
    "thumb_mode": "attachthumbmode",
    "thumb_width": "attachthumbwidth",
    "thumb_height": "attachthumbheight",
}

with app.app_context():
    rows = {row.key: row for row in db.session.query(Setting).all()}

    for old, new in RENAMES.items():
        if old not in rows:
            continue
        if new in rows:
            db.session.delete(rows[old])
            print(f"{old}: 目标键已存在，删除旧键")
        else:
            rows[old].key = new
            print(f"{old} -> {new} = {rows[old].value}")

    if "avatarmaxsize" in rows:
        raw = (rows["avatarmaxsize"].value or "").strip()
        try:
            size = int(raw)
        except ValueError:
            size = 0
        if 0 < size <= 1024:
            rows["avatarmaxsize"].value = str(size * 1024)
            print(f"avatarmaxsize: {raw} KB -> {size * 1024} 字节")
        else:
            print(f"avatarmaxsize: 已是字节值 {raw}，未改动")

    db.session.commit()

    final = {row.key: row.value for row in db.session.query(Setting).all()}
    for key in ("attachthumbmode", "attachthumbwidth", "attachthumbheight", "avatarmaxsize"):
        print(f"  {key} = {final.get(key, '(未设置，用默认值)')}")
