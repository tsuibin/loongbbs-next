"""misc.php 的对应页：vB 代码帮助、表情列表、常见问题（FAQ）与版块管理人员。"""
from __future__ import annotations

from datetime import timedelta

from flask import Blueprint, abort, render_template, request
from sqlalchemy import func, select

from .extensions import db
from .faq_zh import translate_faq_html
from .i18n import current_language
from .models import (
    Category,
    OnlineSession,
    Post,
    Thread,
    User,
    UserGroup,
    utcnow,
)
from .settings import get_setting
from .utils import SMILIES

bp = Blueprint("misc", __name__, url_prefix="/misc")

# vB misc.php 的 faq 分支：page 为空渲染 faq.html（三节目录），1/2/3 渲染 faq1/2/3.html
FAQ_PAGES = {
    1: "misc/faq1.html",
    2: "misc/faq2.html",
    3: "misc/faq3.html",
}

# showgroups.php 只列 usergroup.showgroup=1 的组；vB 默认数据里就是超级版主与管理员两组
SHOWGROUP_IDS = (6, 5)
GROUP_DEFAULT_TITLES = {6: "Administrators", 5: "Super Moderators"}


@bp.get("/bbcode")
def bbcode():
    """对应 vB misc.php?action=bbcode，发帖页「[帮助]」指向这里（#buttons 锚点）。"""
    return render_template("misc/bbcode.html")


@bp.get("/smilies")
def smilies():
    """对应 vB misc.php?action=smilies：可用的表情清单。"""
    return render_template("misc/smilies.html", smilies=SMILIES)


@bp.get("/faq")
def faq():
    """对应 vB misc.php?action=faq[&page=N]。

    与参考站一致：不带 page 时是 FAQ 目录页（三节 + 27 条锚点链接），
    page=1/2/3 分别是「用户自助 / 版面使用 / 阅读与发帖」分节页。
    FAQ 正文沿用参考站模板里的英文原文（原版在中文语言包下同样是英文）。
    """
    page = request.args.get("page", type=int) or 0
    template = FAQ_PAGES.get(page, "misc/faq.html")
    html_text = render_template(
        template,
        inbox_name=get_setting("inboxname") or "Inbox",
        sentitems_name=get_setting("sentitemsname") or "Sent Items",
        attachextensions=(get_setting("attachextensions") or "").replace(",", ", "),
        censor_char=((get_setting("censorchar") or "*").strip()[:1] or "*"),
    )
    if current_language() == "zh":
        # 参考站在中文语言下会把这些 phrase 替换进 FAQ 模板，结果是中英混排
        html_text = translate_faq_html(html_text)
    return html_text


def _naive(value):
    if value is not None and value.tzinfo is not None:
        return value.replace(tzinfo=None)
    return value


@bp.get("/whoposted/<int:thread_id>")
def whoposted(thread_id: int):
    """对应 vB misc.php?action=whoposted（版块页回复数 javascript:who() 的弹窗）。

    原版按 userid 分组统计该主题的可见帖子数、按帖子数倒序，弹窗里一张表：
    顶部 Total Posts，表头 User / Posts，底部 [show thread & close window]。
    """
    thread_obj = db.session.get(Thread, thread_id)
    if thread_obj is None:
        abort(404)

    rows = db.session.execute(
        select(
            Post.author_id,
            func.count(Post.id).label("posts"),
        )
        .where(Post.thread_id == thread_id, Post.is_deleted.is_(False))
        .group_by(Post.author_id)
        .order_by(func.count(Post.id).desc(), Post.author_id)
    ).all()

    if not rows:
        abort(404)

    posters = []
    total_posts = 0
    for author_id, count in rows:
        total_posts += int(count)
        user_obj = db.session.get(User, author_id) if author_id else None
        posters.append(
            {
                "username": user_obj.username if user_obj else "",
                "user_id": author_id,
                "posts": int(count),
            }
        )

    return render_template(
        "misc/whoposted.html",
        thread=thread_obj,
        posters=posters,
        total_posts=total_posts,
        ui_lang=current_language(),
    )


@bp.get("/showgroups")
def showgroups():
    """对应 vB showgroups.php（Forum Leaders / 版块管理人员）。

    原版按 usergroup.showgroup=1 的组列出成员（管理员先、超级版主次、再其他组），
    每组一张表：在线状态 / 用户名 / 位置 / 联系（发送悄悄话）；页底是版块跳转下拉。
    版主（moderator 表）那一段本站没有这张关联表（后台也没有设置入口），
    参考站当前同样没有版主数据、不渲染该段，所以两边一致。
    """
    try:
        timeout = int(get_setting("cookietimeout") or 900)
    except (TypeError, ValueError):
        timeout = 900
    cutoff = _naive(utcnow()) - timedelta(seconds=max(60, timeout))

    last_active = {
        user_id: stamp
        for user_id, stamp in db.session.execute(
            select(OnlineSession.user_id, func.max(OnlineSession.last_activity)).where(
                OnlineSession.user_id.isnot(None)
            )
        ).all()
    }

    groups = []
    for index, group_id in enumerate(SHOWGROUP_IDS):
        group = db.session.get(UserGroup, group_id)
        members_users = [
            user
            for user in db.session.scalars(
                select(User).where(User.usergroupid == group_id).order_by(User.username)
            ).all()
            if user.username
        ]
        if not members_users:
            continue  # 原版：组里没成员就不出这张表
        name = (group.title if group is not None and group.title else "") or GROUP_DEFAULT_TITLES[group_id]
        if not name.endswith("s"):
            name += "s"  # 原版直接给组名补个复数 s
        members = []
        for row, user in enumerate(members_users):
            stamp = last_active.get(user.id)
            online = bool(stamp) and _naive(stamp) > cutoff and not user.invisible
            members.append(
                {
                    "username": user.username,
                    "location": (user.location or "").strip(),
                    "receivepm": bool(user.receivepm),
                    "online": online,
                    "bg": "#DFDFDF" if row % 2 == 0 else "#F1F1F1",
                }
            )
        groups.append({"name": name, "members": members})

    categories = (
        db.session.execute(select(Category).order_by(Category.position))
        .scalars()
        .all()
    )
    return render_template("misc/showgroups.html", groups=groups, categories=categories)
