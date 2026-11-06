"""Forums, threads, posts and moderation toggles."""
from __future__ import annotations

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy import func, or_, select

from .attachments import save_uploads
from .extensions import db
from datetime import datetime, timedelta, timezone

from .models import (
    Category,
    EmailLog,
    Forum,
    ForumRead,
    Poll,
    PollOption,
    PollVote,
    Post,
    PostReport,
    PrivateMessage,
    Thread,
    ThreadRating,
    ThreadSubscription,
    User,
    utcnow,
)
from .settings import get_setting
from .permissions import can, current_permissions
from .utils import censor_text, clamp_page, format_dt, page_args, render_body, time_ago

bp = Blueprint("forums", __name__)


def _naive(dt):
    """SQLite 读回来的是 naive，比较前统一成 naive UTC，避免 aware/naive 混比报错。"""
    if dt is None:
        return None
    return dt.astimezone(timezone.utc).replace(tzinfo=None) if dt.tzinfo else dt


def _mark_read(forum_id: int) -> None:
    """记录「已读到此」。登录用户写 forum_reads 表，游客写 session（对应 vB 的 cookie）。"""
    now = utcnow()
    if current_user.is_authenticated:
        row = db.session.scalar(
            select(ForumRead).where(
                ForumRead.user_id == current_user.id, ForumRead.forum_id == forum_id
            )
        )
        if row is None:
            row = ForumRead(user_id=current_user.id, forum_id=forum_id)
            db.session.add(row)
        row.marked_at = now
        db.session.commit()
    else:
        marks = dict(session.get("forum_marks", {}))
        marks[str(forum_id)] = now.isoformat()
        session["forum_marks"] = marks


def _read_cutoff(forum_id: int | None = None):
    """返回该用户「已读到此」的时间点；没有记录时退回 last_seen，游客没有则返回 None。"""
    candidates = []
    if current_user.is_authenticated:
        keys = [forum_id, -1] if forum_id is not None else [-1]
        for key in keys:
            row = db.session.scalar(
                select(ForumRead).where(
                    ForumRead.user_id == current_user.id, ForumRead.forum_id == key
                )
            )
            if row is not None:
                candidates.append(_naive(row.marked_at))
        if current_user.last_visit or current_user.joined_at:
            candidates.append(_naive(current_user.last_visit or current_user.joined_at))
    else:
        marks = session.get("forum_marks", {})
        keys = [str(forum_id), "-1"] if forum_id is not None else ["-1"]
        for key in keys:
            if marks.get(key):
                candidates.append(datetime.fromisoformat(marks[key]).replace(tzinfo=None))
    candidates = [c for c in candidates if c is not None]
    return max(candidates) if candidates else None


@bp.get("/t/<int:thread_id>/print")
def print_thread(thread_id: int):
    """vB 的 printthread.php：不带样式的一页纯文本版，供打印/存档。"""
    thread_obj = db.session.get(Thread, thread_id)
    if thread_obj is None:
        abort(404)

    total = db.session.scalar(
        select(func.count(Post.id)).where(
            Post.thread_id == thread_obj.id, Post.is_deleted.is_(False)
        )
    ) or 0
    perpage = max(1, min(request.args.get("perpage", type=int) or 40, 200))
    page = max(1, request.args.get("pagenumber", type=int) or 1)
    pages = max(1, (total + perpage - 1) // perpage)
    posts = db.session.execute(
        select(Post)
        .where(Post.thread_id == thread_obj.id, Post.is_deleted.is_(False))
        .order_by(Post.created_at)
        .offset((page - 1) * perpage)
        .limit(perpage)
    ).scalars().all()

    return render_template(
        "printthread.html",
        thread=thread_obj,
        posts=posts,
        total=total,
        perpage=perpage,
        page=page,
        pages=pages,
        posts_count=total,
    )


@bp.post("/t/<int:thread_id>/rate")
@login_required
def rate_thread(thread_id: int):
    """对应 vB 的 threadrate.php：一人一票，改投覆盖旧票。"""
    thread_obj = db.session.get(Thread, thread_id)
    if thread_obj is None:
        abort(404)
    try:
        vote = int(request.form.get("vote", "-1"))
    except (TypeError, ValueError):
        vote = -1
    if vote < 1 or vote > 5:
        flash("请选择 1 到 5 之间的评分。")
        return redirect(url_for("forums.thread", thread_id=thread_obj.id))

    existing = db.session.scalar(
        select(ThreadRating).where(
            ThreadRating.thread_id == thread_obj.id,
            ThreadRating.user_id == current_user.id,
        )
    )
    if existing is None:
        db.session.add(
            ThreadRating(thread_id=thread_obj.id, user_id=current_user.id, vote=vote)
        )
        flash("感谢评分。")
    elif get_setting("votechange") != "1":
        # 组 9 votechange=0：原版 threadrate.php 直接拒绝改票
        flash("管理员没有开放修改评分。")
        return redirect(url_for("forums.thread", thread_id=thread_obj.id))
    else:
        existing.vote = vote
        flash("你的评分已更新。")
    db.session.commit()
    return redirect(url_for("forums.thread", thread_id=thread_obj.id))


@bp.post("/t/<int:thread_id>/subscribe")
@login_required
def subscribe_thread(thread_id: int):
    """对应 vB subscription.php?do=addsubscription。"""
    thread_obj = db.session.get(Thread, thread_id)
    if thread_obj is None:
        abort(404)
    exists = db.session.scalar(
        select(ThreadSubscription).where(
            ThreadSubscription.thread_id == thread_obj.id,
            ThreadSubscription.user_id == current_user.id,
        )
    )
    if exists is None:
        db.session.add(
            ThreadSubscription(thread_id=thread_obj.id, user_id=current_user.id)
        )
        db.session.commit()
        flash("已订阅这个主题，可以在用户控制面板里查看。")
    return redirect(url_for("forums.thread", thread_id=thread_obj.id))


@bp.post("/t/<int:thread_id>/unsubscribe")
@login_required
def unsubscribe_thread(thread_id: int):
    """对应 vB subscription.php?do=removesubscription。"""
    thread_obj = db.session.get(Thread, thread_id)
    if thread_obj is None:
        abort(404)
    row = db.session.scalar(
        select(ThreadSubscription).where(
            ThreadSubscription.thread_id == thread_obj.id,
            ThreadSubscription.user_id == current_user.id,
        )
    )
    if row is not None:
        db.session.delete(row)
        db.session.commit()
        flash("已取消订阅这个主题。")
    return redirect(url_for("forums.thread", thread_id=thread_obj.id))


def _email_disabled():
    """组 11 enableemail=0：原版 sendtofriend.php / report.php 都会先给这个错误页。"""
    return render_template("email_disabled.html")


@bp.get("/post/<int:post_id>/report")
@login_required
def report_form(post_id: int):
    """对应 vB report.php：举报某一条帖子。"""
    if get_setting("enableemail") != "1":
        return _email_disabled()
    post_obj = db.session.get(Post, post_id)
    if post_obj is None:
        abort(404)
    return render_template("report.html", post=post_obj, sent=False)


@bp.post("/post/<int:post_id>/report")
@login_required
def report_post(post_id: int):
    if get_setting("enableemail") != "1":
        return _email_disabled()
    post_obj = db.session.get(Post, post_id)
    if post_obj is None:
        abort(404)
    reason = (request.form.get("reason") or "").strip()[:50]
    note = (request.form.get("note") or "").strip()
    if not reason:
        flash("请选择举报原因。")
        return render_template("report.html", post=post_obj, sent=False)
    db.session.add(
        PostReport(
            post_id=post_obj.id,
            reporter_id=current_user.id,
            reason=reason,
            note=note,
        )
    )
    db.session.commit()
    return render_template("report.html", post=post_obj, sent=True, reason=reason)


@bp.get("/sendtofriend")
def sendtofriend_form():
    """对应 vB sendtofriend.php：把这个主题推荐给朋友。"""
    if get_setting("enableemail") != "1":
        return _email_disabled()
    thread_obj = db.session.get(Thread, request.args.get("thread_id", type=int) or 0)
    if thread_obj is None:
        abort(404)
    if not can("canemail", thread_obj.forum_id):
        abort(403)
    return render_template(
        "sendtofriend.html",
        thread=thread_obj,
        sent=False,
        from_name=(current_user.username if current_user.is_authenticated else ""),
    )


@bp.post("/sendtofriend")
def sendtofriend_send():
    if get_setting("enableemail") != "1":
        return _email_disabled()
    thread_obj = db.session.get(Thread, request.form.get("thread_id", type=int) or 0)
    if thread_obj is None:
        abort(404)
    if not can("canemail", thread_obj.forum_id):
        abort(403)
    to_email = (request.form.get("email") or "").strip()
    from_name = (request.form.get("fromname") or "").strip()
    note = (request.form.get("message") or "").strip()

    if not to_email or "@" not in to_email:
        flash("请填写有效的收件人邮箱地址。")
        return render_template(
            "sendtofriend.html", thread=thread_obj, sent=False, from_name=from_name, note=note
        )

    body = (
        f"{from_name or '一位访客'} 认为你可能对这个主题感兴趣：\n\n"
        f"  主题：{thread_obj.title}\n"
        f"  版块：{thread_obj.forum.name}\n"
        f"  链接：{url_for('forums.thread', thread_id=thread_obj.id, _external=True)}\n\n"
        + (f"附言：{note}\n" if note else "")
    )
    db.session.add(
        EmailLog(
            to_email=to_email,
            from_name=from_name,
            subject=f"推荐主题：{thread_obj.title}",
            body=body,
            thread_id=thread_obj.id,
        )
    )
    db.session.commit()
    return render_template(
        "sendtofriend.html", thread=thread_obj, sent=True, to_email=to_email, from_name=from_name
    )


@bp.get("/f/<int:forum_id>/markread")
def mark_forum_read(forum_id: int):
    forum_obj = db.session.get(Forum, forum_id)
    if forum_obj is None:
        abort(404)
    _mark_read(forum_obj.id)
    flash(f"「{forum_obj.name}」已标记为已读。", "success")
    return redirect(url_for("forums.forum", forum_id=forum_obj.id))


@bp.get("/markread/all")
def mark_all_read():
    _mark_read(-1)
    flash("所有版块已标记为已读。", "success")
    return redirect(request.referrer or url_for("forums.index"))


def _per_page(key: str, fallback: int) -> int:
    try:
        return max(1, min(int(get_setting(key, str(fallback))), 100))
    except (TypeError, ValueError):
        return fallback


def _setting_int(name: str, default: int, low: int = 0, high: int = 200) -> int:
    """读一个整数设置，夹在 [low, high] 之间。"""
    try:
        value = int(get_setting(name, str(default)) or default)
    except (TypeError, ValueError):
        value = default
    return max(low, min(value, high))


def _minutes_since(value: datetime | None) -> float:
    """距某个 UTC 时间点过了多少分钟（库里取回的是 naive 时间）。"""
    if value is None:
        return 0.0
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return (utcnow() - value).total_seconds() / 60


def _log_ip() -> str | None:
    """组 15 logip：1/2 才记录发帖 IP（原版 newthread.php / newreply.php 的写法）。"""
    if get_setting("logip", "0") not in ("1", "2"):
        return None
    return (request.remote_addr or "")[:45] or None


def _flood_wait() -> int:
    """组 16 enablefloodcheck / floodchecktime：返回还需等待的秒数（0 = 放行）。

    原版：`time()-$bbuserinfo[lastpost] <= $floodchecktime and !ismoderator(...)`。
    本站用该用户最后一条帖子的发表时间代替 user.lastpost，管理员豁免。
    """
    if get_setting("enablefloodcheck", "0") != "1":
        return 0
    if current_user.is_admin:
        return 0
    seconds = _setting_int("floodchecktime", 30, low=0, high=86400)
    if not seconds:
        return 0
    last = db.session.scalar(
        select(func.max(Post.created_at)).where(Post.author_id == current_user.id)
    )
    if last is None:
        return 0
    elapsed = _minutes_since(last) * 60
    if elapsed <= seconds:
        return max(1, int(seconds - elapsed) + 1)
    return 0


def _thread_per_page() -> int:
    """组 8 maxposts / usermaxposts：每页帖数。

    原版 showthread.php 先把 usermaxposts 与 maxposts 一起取最大值作为硬上限，
    用户 UCP 选的每页帖数不超过这个上限时就用用户的选择。
    """
    try:
        maxposts = int(get_setting("maxposts", "15") or 15)
    except (TypeError, ValueError):
        maxposts = 15
    maxposts = max(1, min(maxposts, 200))

    options: list[int] = []
    for part in (get_setting("usermaxposts") or "").split(","):
        part = part.strip()
        if part.isdigit():
            options.append(int(part))
    hard_max = max(options + [maxposts])

    chosen = 0
    if current_user.is_authenticated:
        chosen = getattr(current_user, "umaxposts", 0) or 0
    if 0 < chosen <= hard_max:
        return chosen
    return maxposts


def _post_order() -> str:
    """组 8 postorder：0 表示旧帖在前，非 0 表示新帖在前（原版 DESC）。"""
    return "desc" if (get_setting("postorder") or "0").strip() not in ("", "0") else "asc"


def _page_links(page: int, pages: int) -> list:
    """组 8 pagenavpages：页码导航里当前页左右各显示几个页码，中间用省略号。"""
    if pages <= 1:
        return []
    try:
        window = int(get_setting("pagenavpages", "3") or 3)
    except (TypeError, ValueError):
        window = 3
    window = max(1, window)
    keep = {1, pages}
    keep.update(p for p in range(page - window, page + window + 1) if 1 <= p <= pages)
    links: list = []
    previous = 0
    for number in sorted(keep):
        if previous and number - previous > 1:
            links.append(None)
        links.append(number)
        previous = number
    return links


def _stop_shouting(title: str) -> str:
    """组 8 stopshouting：整条标题全大写时改成词首大写（原版 ucwords(strtolower())）。"""
    if get_setting("stopshouting") != "1" or not title:
        return title
    if any(ch.isalpha() for ch in title) and title == title.upper():
        return title.title()
    return title


def _post_too_long(body: str) -> bool:
    """组 8 postmaxchars：0 表示不限；原版用 strlen（字节）比较。"""
    try:
        limit = int(get_setting("postmaxchars") or 0)
    except (TypeError, ValueError):
        limit = 0
    return limit > 0 and len(body.encode("utf-8")) > limit


def _postmaxchars() -> int:
    try:
        return max(0, int(get_setting("postmaxchars") or 0))
    except (TypeError, ValueError):
        return 0


@bp.get("/")
def index():
    categories = db.session.execute(
        select(Category).order_by(Category.position, Category.id)
    ).scalars().all()

    # vB forumhome 只显示 canview 为真的版块；权限全关的分类整块不出现
    visible_categories = []
    for category in categories:
        visible_forums = [
            forum_obj for forum_obj in category.forums
            if can("canview", forum_obj.id)
        ]
        if visible_forums:
            category.visible_forums = visible_forums
            visible_categories.append(category)
    categories = visible_categories

    # 后台「首页版块选项」组（vB 组 5），对应 index.php 的
    # $showforumdescription / $displayloggedin / $highlightadmin / $showlocks / $forumhomedepth
    show_description = get_setting("showforumdescription") != "0"
    display_loggedin = get_setting("displayloggedin") != "0"
    highlight_admin = get_setting("highlightadmin") != "0"
    show_locks = get_setting("showlocks") == "1"
    try:
        home_depth = int(get_setting("forumhomedepth") or 2)
    except ValueError:
        home_depth = 2

    stats = {
        "threads": db.session.scalar(select(func.count(Thread.id))) or 0,
        "posts": db.session.scalar(
            select(func.count(Post.id)).where(Post.is_deleted.is_(False))
        ) or 0,
        "users": db.session.scalar(select(func.count(User.id))) or 0,
        "last_thread": db.session.scalar(
            select(Thread).order_by(Thread.last_post_at.desc()).limit(1)
        ),
        "newest_user": db.session.scalar(select(User).order_by(User.id.desc()).limit(1)),
        "online": db.session.scalar(
            select(func.count(User.id)).where(
                User.last_seen >= utcnow() - timedelta(minutes=15)
            )
        ) or 0,
    }
    cutoff = _read_cutoff()
    for category in categories:
        for forum_obj in category.forums:
            last_post = forum_obj.last_post
            forum_obj.has_new = bool(
                cutoff and last_post and _naive(last_post.created_at)
                and _naive(last_post.created_at) > cutoff
            )
            # 原版：canpostnew 为假 / allowposting=0 且 showlocks 打开时才换成锁图标
            forum_obj.lock_icon = bool(show_locks and forum_obj.is_closed)

    online_users = []
    if display_loggedin:
        online_users = db.session.execute(
            select(User)
            .where(User.last_seen >= utcnow() - timedelta(minutes=15))
            .order_by(User.username)
        ).scalars().all()

    # 组 19 checknewpm：登录后首页提示「你有 N 条未读悄悄话」（原版 forumhome_pmloggedin）
    unread_pm = 0
    if current_user.is_authenticated and get_setting("checknewpm", "1") != "0":
        unread_pm = db.session.scalar(
            select(func.count())
            .select_from(PrivateMessage)
            .where(
                PrivateMessage.recipient_id == current_user.id,
                PrivateMessage.read_at.is_(None),
            )
        ) or 0

    return render_template(
        "index.html",
        categories=categories,
        stats=stats,
        show_description=show_description,
        display_loggedin=display_loggedin,
        highlight_admin=highlight_admin,
        home_depth=home_depth,
        online_users=online_users,
        unread_pm=unread_pm,
    )


@bp.get("/f/<int:forum_id>")
def forum(forum_id: int):
    forum_obj = db.session.get(Forum, forum_id)
    if forum_obj is None:
        abort(404)
    if not can("canview", forum_obj.id):
        abort(403)

    page = clamp_page(request.args.get("page"))
    # 组 9 maxthreads：版块页每页主题数（原版 sanitize_pageresults 上限 200）
    per_page = _setting_int("maxthreads", 25, low=1)

    # 排序/时间范围：对应 vB forumdisplay.php 的 sortfield / sortorder / daysprune
    sortfield = (request.args.get("sortfield") or "lastpost").lower()
    sortorder = (request.args.get("sortorder") or "desc").lower()
    if sortfield not in {"title", "lastpost", "replycount", "views", "postusername"}:
        sortfield = "lastpost"
    if sortorder not in {"asc", "desc"}:
        sortorder = "desc"
    try:
        daysprune = int(request.args.get("daysprune") or 1000)
    except (TypeError, ValueError):
        daysprune = 1000
    daysprune = max(1, min(daysprune, 1000))

    reply_subq = (
        select(func.count(Post.id))
        .where(Post.thread_id == Thread.id, Post.is_deleted.is_(False))
        .scalar_subquery()
    )
    sort_columns = {
        "title": Thread.title,
        "lastpost": Thread.last_post_at,
        "replycount": reply_subq,
        "views": Thread.views,
        "postusername": User.username,
    }

    stmt = select(Thread)
    if sortfield == "postusername":
        stmt = stmt.join(User, Thread.author_id == User.id)
    stmt = stmt.where(Thread.forum_id == forum_obj.id)
    # vB 的 canviewothers=0（vote 前的「只看自己的主题」）时只显示本人的主题
    if not can("canviewothers", forum_obj.id):
        stmt = stmt.where(Thread.author_id == (current_user.id if current_user.is_authenticated else -1))
    if daysprune < 1000:
        stmt = stmt.where(Thread.last_post_at >= utcnow() - timedelta(days=daysprune))
    column = sort_columns[sortfield]
    stmt = stmt.order_by(
        Thread.is_sticky.desc(),
        column.asc() if sortorder == "asc" else column.desc(),
    )
    stmt = stmt.offset((page - 1) * per_page).limit(per_page)
    threads = db.session.execute(stmt).scalars().all()

    total_stmt = select(func.count(Thread.id)).where(Thread.forum_id == forum_obj.id)
    if not can("canviewothers", forum_obj.id):
        total_stmt = total_stmt.where(
            Thread.author_id == (current_user.id if current_user.is_authenticated else -1)
        )
    if daysprune < 1000:
        total_stmt = total_stmt.where(
            Thread.last_post_at >= utcnow() - timedelta(days=daysprune)
        )
    total = db.session.scalar(total_stmt) or 0
    pages = max(1, (total + per_page - 1) // per_page)

    forums_all = db.session.execute(select(Forum).order_by(Forum.position, Forum.id)).scalars().all()

    cutoff = _read_cutoff(forum_obj.id)
    for thread_obj in threads:
        last_at = _naive(thread_obj.last_post_at)
        thread_obj.has_new = bool(cutoff and last_at and last_at > cutoff)

    # 评分一次聚合，避免模板里每行查一次
    rating_rows = db.session.execute(
        select(
            ThreadRating.thread_id,
            func.avg(ThreadRating.vote),
            func.count(ThreadRating.id),
        )
        .where(ThreadRating.thread_id.in_([t.id for t in threads] or [-1]))
        .group_by(ThreadRating.thread_id)
    ).all()
    ratings = {row[0]: (float(row[1] or 0), int(row[2] or 0)) for row in rating_rows}
    for thread_obj in threads:
        thread_obj._rating_cache = ratings.get(thread_obj.id, (0.0, 0))

    # 主题图标：取该主题首帖的 iconid（对应 vB forumdisplay.php 的 thread.iconid）
    icon_rows = db.session.execute(
        select(Post.thread_id, Post.iconid)
        .where(Post.thread_id.in_([t.id for t in threads] or [-1]))
        .order_by(Post.thread_id, Post.id)
    ).all()
    first_icons: dict[int, int] = {}
    for thread_id, icon_id_value in icon_rows:
        first_icons.setdefault(thread_id, icon_id_value or 0)
    for thread_obj in threads:
        thread_obj._icon_cache = first_icons.get(thread_obj.id, 0)

    # ---- 组 9「版块显示选项」：热门图标 / 参与点 / 多页导航 / 投票前缀 ----
    hot_on = get_setting("usehotthreads") == "1"
    hot_posts = _setting_int("hotnumberposts", 15)
    hot_views = _setting_int("hotnumberviews", 150)
    show_dots = get_setting("showdots") == "1"
    link_to_pages = get_setting("linktopages") == "1"
    max_multi = _setting_int("maxmultipage", 5, low=1, high=50)
    post_per_page = _thread_per_page()

    dot_threads: set[int] = set()
    if show_dots and current_user.is_authenticated:
        dot_threads = set(
            db.session.scalars(
                select(Post.thread_id)
                .where(
                    Post.author_id == current_user.id,
                    Post.is_deleted.is_(False),
                    Post.thread_id.in_([t.id for t in threads] or [-1]),
                )
                .distinct()
            )
        )

    poll_threads = set(
        db.session.scalars(
            select(Poll.thread_id).where(Poll.thread_id.in_([t.id for t in threads] or [-1]))
        )
    )

    for thread_obj in threads:
        replies = max(0, (thread_obj.reply_count or 0) - 1)
        thread_obj._hot = bool(
            hot_on
            and (
                (hot_posts > 0 and replies >= hot_posts)
                or (hot_views > 0 and (thread_obj.views or 0) >= hot_views)
            )
        )
        thread_obj._dot = thread_obj.id in dot_threads
        thread_obj._has_poll = thread_obj.id in poll_threads
        thread_obj._page_nav = []
        if link_to_pages and post_per_page > 0 and replies + 1 > post_per_page:
            page_count = (replies + 1 + post_per_page - 1) // post_per_page
            if page_count > 1:
                # 原版：到 maxmultipage 就只留「more...」，不再往下排
                nav = list(range(1, min(page_count, max_multi - 1) + 1))
                if page_count >= max_multi:
                    nav.append(None)
                thread_obj._page_nav = nav
                thread_obj._page_last = page_count

    return render_template(
        "forum.html",
        forum=forum_obj,
        forums_all=forums_all,
        threads=threads,
        page=page,
        pages=pages,
        total=total,
        per_page=per_page,
        page_args=page_args,
        time_ago=time_ago,
        sortfield=sortfield,
        sortorder=sortorder,
        daysprune=daysprune,
        inverse_order=("asc" if sortorder == "desc" else "desc"),
    )


@bp.get("/f/<int:forum_id>/new")
@login_required
def new_thread_form(forum_id: int):
    forum_obj = db.session.get(Forum, forum_id)
    if forum_obj is None:
        abort(404)
    if forum_obj.is_closed:
        flash("这个版块已关闭，不能发新主题。", "error")
        return redirect(url_for("forums.forum", forum_id=forum_id))
    if not can("canpostnew", forum_obj.id):
        abort(403)
    return render_template("post_form.html", forum=forum_obj, mode="new", thread=None, post=None)


def _icon_id() -> int:
    """发帖时选的帖子图标（vB 的 iconid，0 = 不使用）。"""
    raw = request.form.get("iconid")
    try:
        value = int(raw or 0)
    except (TypeError, ValueError):
        return 0
    return value if 1 <= value <= 14 else 0


@bp.post("/f/<int:forum_id>/new")
@login_required
def new_thread(forum_id: int):
    forum_obj = db.session.get(Forum, forum_id)
    if forum_obj is None:
        abort(404)
    if forum_obj.is_closed:
        abort(403)

    if not can("canpostnew", forum_obj.id):
        abort(403)

    title = (request.form.get("title") or "").strip()
    body = request.form.get("body") or ""
    if request.form.get("preview"):
        # 对应 vB newthread.php 的 preview 分支：只渲染 newpost_postpreview，不落库
        return render_template(
            "post_form.html",
            forum=forum_obj,
            mode="new",
            thread=None,
            post=None,
            preview={"title": title, "body": render_body(body)},
        )
    if not title:
        flash("标题不能为空。", "error")
        return render_template("post_form.html", forum=forum_obj, mode="new", thread=None, post=None), 400
    if _post_too_long(body):
        flash(f"帖子正文超过 {_postmaxchars()} 字节的上限，请精简后再发。", "error")
        return render_template("post_form.html", forum=forum_obj, mode="new", thread=None, post=None), 400
    wait = _flood_wait()
    if wait:
        return render_template("floodcheck.html", wait=wait), 429
    if len(title) > 200:
        title = title[:200]

    title = _stop_shouting(censor_text(title))
    body = censor_text(body)

    thread_obj = Thread(
        forum_id=forum_obj.id,
        author_id=current_user.id,
        title=title,
        created_at=utcnow(),
        last_post_at=utcnow(),
    )
    db.session.add(thread_obj)
    db.session.flush()

    post = Post(
        thread_id=thread_obj.id,
        author_id=current_user.id,
        title=title,
        body=body,
        iconid=_icon_id(),
        ipaddress=_log_ip(),
    )
    db.session.add(post)
    db.session.flush()

    _save_uploads_for(post, forum_obj.id)

    # 发帖时勾了「发起投票」才建 poll（对应 vB newthread 的 $postpolloption）
    if request.form.get("postpoll") == "yes":
        question = (request.form.get("pollquestion") or "").strip()
        # 组 25 maxpolloptions：投票选项个数的上限（原版 newthread.php 的 $maxpolloptions）
        max_options = _setting_int("maxpolloptions", 10, low=1)
        options = [
            (request.form.get(f"polloption{i}") or "").strip()
            for i in range(1, max_options + 1)
        ]
        options = [option for option in options if option][:max_options]
        if question and len(options) >= 2:
            poll_obj = Poll(thread_id=thread_obj.id, question=question[:200])
            db.session.add(poll_obj)
            db.session.flush()
            for index, text in enumerate(options):
                db.session.add(
                    PollOption(poll_id=poll_obj.id, position=index, text=text[:200])
                )

    db.session.commit()

    flash("主题已发布。", "success")
    return redirect(url_for("forums.thread", thread_id=thread_obj.id))


@bp.post("/t/<int:thread_id>/vote")
@login_required
def vote_thread(thread_id: int):
    """对应 vB poll.php?action=pollvote：一个用户对一个投票只投一票。"""
    thread_obj = db.session.get(Thread, thread_id)
    if thread_obj is None:
        abort(404)
    if not can("canvote", thread_obj.forum_id):
        abort(403)
    poll_obj = db.session.scalar(select(Poll).where(Poll.thread_id == thread_obj.id))
    if poll_obj is None:
        abort(404)

    target = url_for("forums.thread", thread_id=thread_obj.id)
    if poll_obj.is_closed:
        flash("这个投票已关闭。", "error")
        return redirect(target)

    already = db.session.scalar(
        select(PollVote.id).where(
            PollVote.poll_id == poll_obj.id, PollVote.user_id == current_user.id
        )
    )
    if already:
        flash("你已经投过票了。", "error")
        return redirect(target)

    try:
        option_id = int(request.form.get("optionid") or 0)
    except ValueError:
        option_id = 0
    option = db.session.get(PollOption, option_id)
    if option is None or option.poll_id != poll_obj.id:
        flash("请选择一个选项。", "error")
        return redirect(target)

    db.session.add(PollVote(poll_id=poll_obj.id, option_id=option.id, user_id=current_user.id))
    # 组 25 updatelastpost：投票后是否把主题的 lastpost 顶到当前时间（原版 poll.php）
    if get_setting("updatelastpost") == "1":
        thread_obj.last_post_at = utcnow()
    db.session.commit()
    flash("投票成功，谢谢参与。", "success")
    return redirect(target)


@bp.get("/t/<int:thread_id>")
def thread(thread_id: int):
    thread_obj = db.session.get(Thread, thread_id)
    if thread_obj is None:
        abort(404)
    if not can("canview", thread_obj.forum_id):
        abort(403)

    page = clamp_page(request.args.get("page"))
    per_page = _thread_per_page()
    post_order = _post_order()

    total = db.session.scalar(
        select(func.count(Post.id)).where(
            Post.thread_id == thread_obj.id, Post.is_deleted.is_(False)
        )
    ) or 0
    pages = max(1, (total + per_page - 1) // per_page)
    page = min(page, pages)

    posts = (
        db.session.execute(
            select(Post)
            .where(Post.thread_id == thread_obj.id, Post.is_deleted.is_(False))
            .order_by(Post.created_at.desc() if post_order == "desc" else Post.created_at)
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        .scalars()
        .all()
    )

    thread_obj.views = (thread_obj.views or 0) + 1
    db.session.commit()

    # vB 2.x 的 Last Thread / Next Thread 按 threadid 顺序取相邻主题
    prev_thread = db.session.scalar(
        select(Thread)
        .where(Thread.forum_id == thread_obj.forum_id, Thread.id < thread_obj.id)
        .order_by(Thread.id.desc())
        .limit(1)
    )
    next_thread = db.session.scalar(
        select(Thread)
        .where(Thread.forum_id == thread_obj.forum_id, Thread.id > thread_obj.id)
        .order_by(Thread.id)
        .limit(1)
    )

    # 投票：取本主题的 poll 与选项票数（对应 vB showthread 的 $pollinfo / $pollbits）
    poll_obj = db.session.scalar(select(Poll).where(Poll.thread_id == thread_obj.id))
    poll_rows = []
    poll_total = 0
    poll_my_vote = None
    if poll_obj is not None:
        counts = dict(
            db.session.execute(
                select(PollVote.option_id, func.count(PollVote.id))
                .where(PollVote.poll_id == poll_obj.id)
                .group_by(PollVote.option_id)
            ).all()
        )
        poll_total = sum(counts.values())
        for index, option in enumerate(poll_obj.options):
            votes = int(counts.get(option.id, 0))
            percent = int(round(votes * 100 / poll_total)) if poll_total else 0
            poll_rows.append(
                {
                    "id": option.id,
                    "text": option.text,
                    "votes": votes,
                    "percent": percent,
                    "graphic": (index % 6) + 1,
                    "width": max(1, int(round(votes * 100 / poll_total))) if poll_total else 1,
                }
            )
        if current_user.is_authenticated:
            poll_my_vote = db.session.scalar(
                select(PollVote.option_id).where(
                    PollVote.poll_id == poll_obj.id, PollVote.user_id == current_user.id
                )
            )

    # 组 9 votechange：0 时已投过的用户不再看到评分表单
    my_rating = None
    if current_user.is_authenticated:
        my_rating = db.session.scalar(
            select(ThreadRating.vote).where(
                ThreadRating.thread_id == thread_obj.id,
                ThreadRating.user_id == current_user.id,
            )
        )

    return render_template(
        "thread.html",
        thread=thread_obj,
        forum=thread_obj.forum,
        posts=posts,
        page=page,
        pages=pages,
        total=total,
        my_rating=my_rating,
        page_args=page_args,
        page_links=_page_links(page, pages),
        post_order=post_order,
        render_body=render_body,
        format_dt=format_dt,
        time_ago=time_ago,
        prev_thread=prev_thread,
        next_thread=next_thread,
        poll=poll_obj,
        poll_rows=poll_rows,
        poll_total=poll_total,
        poll_my_vote=poll_my_vote,
        subscribed=bool(
            current_user.is_authenticated
            and db.session.scalar(
                select(ThreadSubscription.id).where(
                    ThreadSubscription.thread_id == thread_obj.id,
                    ThreadSubscription.user_id == current_user.id,
                )
            )
        ),
    )


@bp.get("/t/<int:thread_id>/reply")
@login_required
def reply_form(thread_id: int):
    thread_obj = db.session.get(Thread, thread_id)
    if thread_obj is None:
        abort(404)
    if thread_obj.is_closed:
        flash("这个主题已关闭，不能回复。", "error")
        return redirect(url_for("forums.thread", thread_id=thread_id))
    if not _can_reply(thread_obj):
        abort(403)
    return render_template(
        "post_form.html", forum=thread_obj.forum, mode="reply", thread=thread_obj, post=None
    )


@bp.post("/t/<int:thread_id>/reply")
@login_required
def reply(thread_id: int):
    thread_obj = db.session.get(Thread, thread_id)
    if thread_obj is None:
        abort(404)
    if thread_obj.is_closed:
        flash("这个主题已关闭，不能回复。", "error")
        return redirect(url_for("forums.thread", thread_id=thread_id))
    if not _can_reply(thread_obj):
        abort(403)

    body = (request.form.get("body") or "").strip()
    title = (request.form.get("title") or "").strip() or f"Re: {thread_obj.title}"
    if request.form.get("preview"):
        return render_template(
            "post_form.html",
            forum=thread_obj.forum,
            mode="reply",
            thread=thread_obj,
            post=None,
            preview={"title": title, "body": render_body(body)},
        )
    if not body:
        flash("回复内容不能为空。", "error")
        return redirect(url_for("forums.thread", thread_id=thread_id, page="last"))
    if _post_too_long(body):
        flash(f"回复正文超过 {_postmaxchars()} 字节的上限，请精简后再发。", "error")
        return redirect(url_for("forums.thread", thread_id=thread_id, page="last"))
    wait = _flood_wait()
    if wait:
        return render_template("floodcheck.html", wait=wait), 429

    if len(title) > 200:
        title = title[:200]

    title = _stop_shouting(censor_text(title))
    body = censor_text(body)

    post = Post(
        thread_id=thread_obj.id,
        author_id=current_user.id,
        title=title,
        body=body,
        iconid=_icon_id(),
        ipaddress=_log_ip(),
    )
    db.session.add(post)
    db.session.flush()
    _save_uploads_for(post, thread_obj.forum_id)
    thread_obj.last_post_at = utcnow()
    db.session.commit()

    return redirect(url_for("forums.thread", thread_id=thread_id, page=_last_page(thread_obj)))


def _save_uploads_for(post: Post, forum_id: int):
    """vB 的 canpostattachment=0 的组发帖时不收附件。"""
    if not can("canpostattachment", forum_id):
        return []
    return save_uploads(post, request.files.getlist("files"))


def _can_reply(thread_obj: Thread) -> bool:
    """vB 的 canreplyown / canreplyothers：自己发的主题和别人发的主题分开判。"""
    is_owner = current_user.is_authenticated and thread_obj.author_id == current_user.id
    return can("canreplyown" if is_owner else "canreplyothers", thread_obj.forum_id)


def _last_page(thread_obj: Thread) -> int:
    per_page = _thread_per_page()
    count = db.session.scalar(
        select(func.count(Post.id)).where(
            Post.thread_id == thread_obj.id, Post.is_deleted.is_(False)
        )
    ) or 1
    return max(1, (count + per_page - 1) // per_page)


@bp.get("/post/<int:post_id>/ip")
@login_required
def post_ip(post_id: int):
    """对应 vB postings.php?action=getip：只有管理员/版主能看真实 IP。"""
    post = db.session.get(Post, post_id)
    if post is None:
        abort(404)
    if not (current_user.is_admin or _can_moderate(post.thread)):
        abort(403)
    return render_template("post_ip.html", post=post)


@bp.get("/post/<int:post_id>/edit")
@login_required
def edit_post_form(post_id: int):
    post = db.session.get(Post, post_id)
    if post is None:
        abort(404)
    if post.author_id != current_user.id and not current_user.is_admin:
        abort(403)
    if post.author_id == current_user.id and not can("caneditpost", post.thread.forum_id):
        abort(403)
    limit = _setting_int("edittimelimit", 0, high=100000)
    if (
        limit
        and not current_user.is_admin
        and _minutes_since(post.created_at) > limit
    ):
        flash(f"发帖 {limit} 分钟后就不能再自行编辑了，请联系版主。", "error")
        return redirect(url_for("forums.thread", thread_id=post.thread_id))
    return render_template(
        "post_form.html", forum=post.thread.forum, mode="edit", thread=post.thread, post=post
    )


@bp.post("/post/<int:post_id>/edit")
@login_required
def edit_post(post_id: int):
    post = db.session.get(Post, post_id)
    if post is None:
        abort(404)
    if post.author_id != current_user.id and not current_user.is_admin:
        abort(403)
    if post.author_id == current_user.id and not can("caneditpost", post.thread.forum_id):
        abort(403)

    # 组 14 edittimelimit：超过 N 分钟作者就不能再自己改（管理员不受限）
    limit = _setting_int("edittimelimit", 0, high=100000)
    if limit and not current_user.is_admin and _minutes_since(post.created_at) > limit:
        flash(f"发帖 {limit} 分钟后就不能再自行编辑了，请联系版主。", "error")
        return redirect(url_for("forums.thread", thread_id=post.thread_id))

    body = (request.form.get("body") or "").strip()
    if request.form.get("preview"):
        return render_template(
            "post_form.html",
            forum=post.thread.forum,
            mode="edit",
            thread=post.thread,
            post=post,
            preview={
                "title": (request.form.get("title") or "").strip() or post.title,
                "body": render_body(body),
            },
        )
    if not body:
        flash("内容不能为空。", "error")
        return redirect(url_for("forums.edit_post_form", post_id=post_id))
    if _post_too_long(body):
        flash(f"帖子正文超过 {_postmaxchars()} 字节的上限，请精简后再提交。", "error")
        return redirect(url_for("forums.edit_post_form", post_id=post_id))

    post.body = censor_text(body)
    post.iconid = _icon_id()
    title = (request.form.get("title") or "").strip()
    if title:
        post.title = _stop_shouting(censor_text(title))[:200]
        # 组 14 editthreadtitlelimit：首帖在发帖后 N 分钟内编辑才同步主题标题
        first_post_id = db.session.scalar(
            select(Post.id)
            .where(Post.thread_id == post.thread_id, Post.is_deleted.is_(False))
            .order_by(Post.created_at)
            .limit(1)
        )
        title_limit = _setting_int("editthreadtitlelimit", 5, high=100000)
        if post.id == first_post_id and _minutes_since(post.created_at) <= title_limit:
            post.thread.title = post.title

    # 组 14 showeditedby / showeditedbyadmin / noeditedbytime：
    # 原版只有在「距发帖超过 noeditedbytime 分钟」时才记 edituserid/editdate；
    # 管理员编辑且 showeditedbyadmin=0 时也不记。
    if get_setting("showeditedby", "1") == "1":
        if current_user.is_admin and get_setting("showeditedbyadmin", "0") != "1":
            pass
        elif _minutes_since(post.created_at) > _setting_int("noeditedbytime", 0, high=100000):
            post.updated_at = utcnow()
            post.edit_user_id = current_user.id
    _save_uploads_for(post, post.thread.forum_id)
    db.session.commit()

    flash("帖子已更新。", "success")
    return redirect(url_for("forums.thread", thread_id=post.thread_id))


# ------------------------------------------------------------- moderation


def _can_moderate(thread_obj: Thread) -> bool:
    return current_user.is_authenticated and current_user.is_admin


@bp.post("/t/<int:thread_id>/sticky")
@login_required
def toggle_sticky(thread_id: int):
    thread_obj = db.session.get(Thread, thread_id)
    if thread_obj is None:
        abort(404)
    if not _can_moderate(thread_obj):
        abort(403)
    thread_obj.is_sticky = not thread_obj.is_sticky
    db.session.commit()
    flash("已切换置顶状态。", "success")
    return redirect(url_for("forums.thread", thread_id=thread_id))


@bp.post("/t/<int:thread_id>/close")
@login_required
def toggle_closed(thread_id: int):
    thread_obj = db.session.get(Thread, thread_id)
    if thread_obj is None:
        abort(404)
    if not _can_moderate(thread_obj):
        abort(403)
    thread_obj.is_closed = not thread_obj.is_closed
    db.session.commit()
    flash("已切换关闭状态。", "success")
    return redirect(url_for("forums.thread", thread_id=thread_id))


@bp.post("/post/<int:post_id>/delete")
@login_required
def delete_post(post_id: int):
    post = db.session.get(Post, post_id)
    if post is None:
        abort(404)
    if not current_user.is_admin:
        abort(403)
    post.is_deleted = True
    db.session.commit()
    flash("帖子已删除。", "success")
    return redirect(url_for("forums.thread", thread_id=post.thread_id))
