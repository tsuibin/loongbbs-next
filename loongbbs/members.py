"""会员列表（对应 vB 2.3.11 的 memberlist.php）。"""
from __future__ import annotations

from flask import Blueprint, redirect, render_template, request, url_for
from sqlalchemy import func, select

from .extensions import db
from .models import Post, User
from .settings import get_setting
from .utils import clamp_page, format_dt

bp = Blueprint("members", __name__)

# vB 的字母栏：A-Z + 数字开头 + 其他
LETTERS = [chr(c) for c in range(ord("A"), ord("Z") + 1)] + ["0-9", "OTHER"]
VIEWS = ("all", "datejoined", "topposters")


def _setting_int(name: str, default: int) -> int:
    """组 7 的数值设置；原版 sanitize_pageresults 把每页上限卡在 200。"""
    try:
        value = int(get_setting(name) or default)
    except (TypeError, ValueError):
        value = default
    return max(1, min(200, value))


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


@bp.get("/members/search")
def member_search():
    """原版 memberlist.php?action=search：开关关掉时给 error_nomemberlistsearch。"""
    if get_setting("usememberlistadvsearch") != "1":
        return render_template("memberlist_nosearch.html")
    return redirect(url_for("search.search"))


@bp.get("/members")
def memberlist():
    # 组 7 enablememberlist：关掉后与原版 error_nomemberlist 一样整页拒绝
    if get_setting("enablememberlist") != "1":
        return render_template("memberlist_off.html")

    what = request.args.get("what") or "all"
    if what not in VIEWS:
        what = "all"
    letter = (request.args.get("letter") or "").upper()
    if letter and letter not in LETTERS:
        letter = ""
    page = clamp_page(request.args.get("page"))
    # 原版：普通列表用 memberlistperpage，Top Posters 用 memberlisttopposters
    perpage = (
        _setting_int("memberlisttopposters", 10)
        if what == "topposters"
        else _setting_int("memberlistperpage", 30)
    )

    base = select(User)
    # 原版 memberAllGood：把游客 / 等待验证 / COPPA 组排除在列表之外
    if get_setting("memberAllGood") == "1":
        base = base.where(User.usergroupid.notin_([1, 3, 4]))
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
        topcount=_setting_int("memberlisttopposters", 10),
        format_dt=format_dt,
    )
