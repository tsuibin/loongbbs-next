"""会员列表（对应 vB 2.3.11 的 memberlist.php）。"""
from __future__ import annotations

from flask import Blueprint, render_template, request
from sqlalchemy import func, select

from .extensions import db
from .models import Post, User
from .utils import clamp_page, format_dt

bp = Blueprint("members", __name__)

# vB 的字母栏：A-Z + 数字开头 + 其他
LETTERS = [chr(c) for c in range(ord("A"), ord("Z") + 1)] + ["0-9", "OTHER"]
PERPAGE = {"all": 25, "datejoined": 25, "topposters": 10}


def _letter_filter(stmt, letter: str):
    if letter == "0-9":
        return stmt.where(User.username >= "0", User.username < ":")
    if letter == "OTHER":
        # 非 A-Z、非数字开头（含中文用户名）
        az = [chr(c) for c in range(ord("A"), ord("Z") + 1)]
        digits = [str(i) for i in range(10)]
        return stmt.where(
            func.upper(func.substr(User.username, 1, 1)).notin_(az),
            func.substr(User.username, 1, 1).notin_(digits),
        )
    return stmt.where(func.upper(func.substr(User.username, 1, 1)) == letter)


@bp.get("/members")
def memberlist():
    what = request.args.get("what") or "all"
    if what not in PERPAGE:
        what = "all"
    letter = (request.args.get("letter") or "").upper()
    if letter and letter not in LETTERS:
        letter = ""
    page = clamp_page(request.args.get("page"))
    perpage = PERPAGE[what]

    base = select(User)
    if letter:
        base = _letter_filter(base, letter)

    if what == "topposters":
        counts = (
            select(Post.author_id, func.count(Post.id).label("cnt"))
            .where(Post.is_deleted.is_(False))
            .group_by(Post.author_id)
            .subquery()
        )
        stmt = base.join(counts, counts.c.author_id == User.id)
        stmt = stmt.order_by(counts.c.cnt.desc(), User.id.asc())
        total = db.session.scalar(select(func.count()).select_from(base.subquery()))
    elif what == "datejoined":
        stmt = base.order_by(User.joined_at.desc(), User.id.desc())
        total = db.session.scalar(select(func.count()).select_from(base.subquery()))
    else:
        stmt = base.order_by(func.lower(User.username), User.id)
        total = db.session.scalar(select(func.count()).select_from(base.subquery()))

    total = total or 0
    pages = max(1, (total + perpage - 1) // perpage)
    if page > pages:
        page = pages
    users = db.session.execute(
        stmt.offset((page - 1) * perpage).limit(perpage)
    ).scalars().all()

    return render_template(
        "memberlist.html",
        users=users,
        letters=LETTERS,
        letter=letter,
        what=what,
        page=page,
        pages=pages,
        total=total,
        perpage=perpage,
        topcount=PERPAGE["topposters"],
        format_dt=format_dt,
    )
