"""生成一套默认头像（不依赖第三方库，纯 Python 写 PNG）并加入头像库。

在仓库根执行：
    .\\venv\\Scripts\\python.exe seed_avatars.py

重复执行是安全的：已存在的同名记录会跳过。
"""
from __future__ import annotations

import struct
import sys
import zlib
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

from loongbbs import create_app
from loongbbs.extensions import db
from loongbbs.models import Avatar

OUT_SUBDIR = "images/avatars"
SIZE = 60

# (文件名, 显示名, 主色 RGB, 最少帖子数)
PALETTE = [
    ("avatar-01.png", "龙芯蓝", (52, 84, 160), 0),
    ("avatar-02.png", "社区青", (32, 132, 132), 0),
    ("avatar-03.png", "编码紫", (108, 72, 156), 0),
    ("avatar-04.png", "编译橙", (196, 112, 40), 5),
    ("avatar-05.png", "内核绿", (60, 140, 72), 5),
    ("avatar-06.png", "终端黑", (62, 62, 70), 10),
    ("avatar-07.png", "测试红", (176, 64, 64), 10),
    ("avatar-08.png", "社区灰", (110, 110, 122), 20),
]


def _blend(bg, fg, alpha):
    return tuple(int(round(b * (1 - alpha) + f * alpha)) for b, f in zip(bg, fg))


def _inside_disc(x, y, cx, cy, r):
    return (x - cx) ** 2 + (y - cy) ** 2 <= r * r


def _inside_ellipse(x, y, cx, cy, rx, ry):
    if rx <= 0 or ry <= 0:
        return False
    return ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0


def _pixel(x, y, base):
    """一个像素的颜色：主色底 + 白色圆 + 主色人形剪影。"""
    # 2×2 超采样，边缘不至于太生硬
    hits = 0
    white = 0
    for dx in (0.25, 0.75):
        for dy in (0.25, 0.75):
            sx, sy = x + dx, y + dy
            if not _inside_disc(sx, sy, SIZE / 2, SIZE / 2, SIZE / 2 - 2):
                continue
            hits += 1
            # 白色圆盘：去掉四角，形成圆形头像
            if _inside_disc(sx, sy, SIZE / 2, SIZE / 2, SIZE / 2 - 6):
                white += 1
    alpha_white = white / 4
    color = _blend(base, (255, 255, 255), alpha_white)

    # 人形：头 + 肩（只画在白色圆盘内）
    head = 0
    body = 0
    for dx in (0.25, 0.75):
        for dy in (0.25, 0.75):
            sx, sy = x + dx, y + dy
            if not _inside_disc(sx, sy, SIZE / 2, SIZE / 2, SIZE / 2 - 8):
                continue
            if _inside_disc(sx, sy, SIZE / 2, 24, 7):
                head += 1
            if _inside_ellipse(sx, sy, SIZE / 2, 48, 12, 12):
                body += 1
    alpha = max(head, body) / 4
    return _blend(color, base, alpha * 0.95)


def write_png(path: Path, base: tuple[int, int, int]) -> None:
    rows = []
    for y in range(SIZE):
        row = bytearray()
        for x in range(SIZE):
            row.extend(_pixel(x, y, base))
        rows.append(bytes(row))

    raw = b"".join(b"\x00" + row for row in rows)

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", SIZE, SIZE, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 9))
    png += chunk(b"IEND", b"")
    path.write_bytes(png)


def main() -> None:
    app = create_app()
    out_dir = Path(app.static_folder) / OUT_SUBDIR
    out_dir.mkdir(parents=True, exist_ok=True)

    created_files = 0
    with app.app_context():
        for filename, title, color, minposts in PALETTE:
            target = out_dir / filename
            if not target.exists():
                write_png(target, color)
                created_files += 1
            rel = f"{OUT_SUBDIR}/{filename}"
            exists = db.session.scalar(db.select(Avatar).where(Avatar.avatarpath == rel))
            if exists is None:
                db.session.add(
                    Avatar(title=title, minimumposts=minposts, avatarpath=rel)
                )
        db.session.commit()
        total = db.session.scalar(db.select(db.func.count(Avatar.id))) or 0

    print(f"生成图片 {created_files} 个，头像库现有 {total} 条，目录 {OUT_SUBDIR}")


if __name__ == "__main__":
    main()
