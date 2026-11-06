"""Forums, threads, posts and moderation toggles."""
from __future__ import annotations

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy import func, or_, select

from .attachments import save_uploads
from .extensions import db
from datetime import timedelta

from .models import Category, Forum, Post, Thread, User, utcnow
from .settings import get_setting
from .utils import clamp_page, format_dt, page_args, render_body, time_ago

bp = Blueprint("forums", __name__)


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
    return render_template("index.html", categories=categories, stats=stats)


@bp.get("/f/<int:forum_id>")
def forum(forum_id: int):
    forum_obj = db.session.get(Forum, forum_id)
    if forum_obj is None:
        abort(404)

    page = clamp_page(request.args.get("page"))
    per_page = _per_page("threads_per_page", 25)

    stmt = (
        select(Thread)
        .where(Thread.forum_id == forum_obj.id)
        .order_by(Thread.is_sticky.desc(), Thread.last_post_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    threads = db.session.execute(stmt).scalars().all()
    total = db.session.scalar(
        select(func.count(Thread.id)).where(Thread.forum_id == forum_obj.id)
    ) or 0
    pages = max(1, (total + per_page - 1) // per_page)

    forums_all = db.session.execute(select(Forum).order_by(Forum.position, Forum.id)).scalars().all()

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

    post = Post(thread_id=thread_obj.id, author_id=current_user.id, body=body)
    db.session.add(post)
    db.session.flush()

    save_uploads(post, request.files.getlist("files"))
    db.session.commit()

    flash("主题已发布。", "success")
    return redirect(url_for("forums.thread", thread_id=thread_obj.id))


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
    if not body:
        flash("回复内容不能为空。", "error")
        return redirect(url_for("forums.thread", thread_id=thread_id, page="last"))

    post = Post(thread_id=thread_obj.id, author_id=current_user.id, body=body)
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
    if not body:
        flash("内容不能为空。", "error")
        return redirect(url_for("forums.edit_post_form", post_id=post_id))

    post.body = body
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
