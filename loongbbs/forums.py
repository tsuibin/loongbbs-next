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
    Thread,
    ThreadRating,
    ThreadSubscription,
    User,
    utcnow,
)
from .settings import get_setting
from .utils import clamp_page, format_dt, page_args, render_body, time_ago

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


@bp.get("/post/<int:post_id>/report")
@login_required
def report_form(post_id: int):
    """对应 vB report.php：举报某一条帖子。"""
    post_obj = db.session.get(Post, post_id)
    if post_obj is None:
        abort(404)
    return render_template("report.html", post=post_obj, sent=False)


@bp.post("/post/<int:post_id>/report")
@login_required
def report_post(post_id: int):
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
    thread_obj = db.session.get(Thread, request.args.get("thread_id", type=int) or 0)
    if thread_obj is None:
        abort(404)
    return render_template(
        "sendtofriend.html",
        thread=thread_obj,
        sent=False,
        from_name=(current_user.username if current_user.is_authenticated else ""),
    )


@bp.post("/sendtofriend")
def sendtofriend_send():
    thread_obj = db.session.get(Thread, request.form.get("thread_id", type=int) or 0)
    if thread_obj is None:
        abort(404)
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


@bp.get("/")
def index():
    categories = db.session.execute(
        select(Category).order_by(Category.position, Category.id)
    ).scalars().all()

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
    return render_template("index.html", categories=categories, stats=stats)


@bp.get("/f/<int:forum_id>")
def forum(forum_id: int):
    forum_obj = db.session.get(Forum, forum_id)
    if forum_obj is None:
        abort(404)

    page = clamp_page(request.args.get("page"))
    per_page = _per_page("threads_per_page", 25)

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

    return render_template(
        "forum.html",
        forum=forum_obj,
        forums_all=forums_all,
        threads=threads,
        page=page,
        pages=pages,
        total=total,
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
    if len(title) > 200:
        title = title[:200]

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
    )
    db.session.add(post)
    db.session.flush()

    save_uploads(post, request.files.getlist("files"))

    # 发帖时勾了「发起投票」才建 poll（对应 vB newthread 的 $postpolloption）
    if request.form.get("postpoll") == "yes":
        question = (request.form.get("pollquestion") or "").strip()
        options = [
            (request.form.get(f"polloption{i}") or "").strip() for i in range(1, 6)
        ]
        options = [option for option in options if option][:5]
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
    db.session.commit()
    flash("投票成功，谢谢参与。", "success")
    return redirect(target)


@bp.get("/t/<int:thread_id>")
def thread(thread_id: int):
    thread_obj = db.session.get(Thread, thread_id)
    if thread_obj is None:
        abort(404)

    page = clamp_page(request.args.get("page"))
    per_page = _per_page("posts_per_page", 10)

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
            .order_by(Post.created_at)
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

    return render_template(
        "thread.html",
        thread=thread_obj,
        forum=thread_obj.forum,
        posts=posts,
        page=page,
        pages=pages,
        total=total,
        page_args=page_args,
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

    if len(title) > 200:
        title = title[:200]

    post = Post(
        thread_id=thread_obj.id,
        author_id=current_user.id,
        title=title,
        body=body,
        iconid=_icon_id(),
    )
    db.session.add(post)
    db.session.flush()
    save_uploads(post, request.files.getlist("files"))
    thread_obj.last_post_at = utcnow()
    db.session.commit()

    return redirect(url_for("forums.thread", thread_id=thread_id, page=_last_page(thread_obj)))


def _last_page(thread_obj: Thread) -> int:
    per_page = _per_page("posts_per_page", 10)
    count = db.session.scalar(
        select(func.count(Post.id)).where(
            Post.thread_id == thread_obj.id, Post.is_deleted.is_(False)
        )
    ) or 1
    return max(1, (count + per_page - 1) // per_page)


@bp.get("/post/<int:post_id>/edit")
@login_required
def edit_post_form(post_id: int):
    post = db.session.get(Post, post_id)
    if post is None:
        abort(404)
    if post.author_id != current_user.id and not current_user.is_admin:
        abort(403)
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

    post.body = body
    post.iconid = _icon_id()
    title = (request.form.get("title") or "").strip()
    if title:
        post.title = title[:200]
    post.updated_at = utcnow()
    save_uploads(post, request.files.getlist("files"))
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
