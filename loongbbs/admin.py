"""Admin control panel: settings, forums, users, stats."""
from __future__ import annotations

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func, select

from .extensions import db
from .models import Attachment, Category, Forum, Post, PrivateMessage, Thread, User
from .settings import DEFAULTS, get_settings, set_setting
from .utils import format_dt, human_size

bp = Blueprint("admin", __name__, url_prefix="/admin")

EDITABLE_SETTINGS = {
    "site_name": ("站点名称", "text"),
    "site_tagline": ("站点副标题", "text"),
    "posts_per_page": ("每页帖子数", "number"),
    "threads_per_page": ("每页主题数", "number"),
    "allow_registration": ("开放注册", "bool"),
    "thumb_mode": ("附件图片显示缩略图", "bool"),
    "thumb_width": ("缩略图最大宽度 (px)", "number"),
    "thumb_height": ("缩略图最大高度 (px)", "number"),
}


@bp.before_request
@login_required
def require_admin():
    if not current_user.is_admin:
        abort(403)


@bp.get("/")
def dashboard():
    stats = {
        "users": db.session.scalar(select(func.count(User.id))) or 0,
        "threads": db.session.scalar(select(func.count(Thread.id))) or 0,
        "posts": db.session.scalar(
            select(func.count(Post.id)).where(Post.is_deleted.is_(False))
        ) or 0,
        "attachments": db.session.scalar(select(func.count(Attachment.id))) or 0,
        "messages": db.session.scalar(select(func.count(PrivateMessage.id))) or 0,
        "attachment_bytes": db.session.scalar(select(func.coalesce(func.sum(Attachment.size), 0))) or 0,
    }
    recent_users = (
        db.session.execute(select(User).order_by(User.joined_at.desc()).limit(6)).scalars().all()
    )
    recent_posts = (
        db.session.execute(select(Post).order_by(Post.created_at.desc()).limit(6)).scalars().all()
    )
    return render_template(
        "admin/dashboard.html",
        stats=stats,
        recent_users=recent_users,
        recent_posts=recent_posts,
        human_size=human_size,
        format_dt=format_dt,
    )


@bp.route("/settings", methods=["GET", "POST"])
def settings_page():
    if request.method == "POST":
        for key, (_, kind) in EDITABLE_SETTINGS.items():
            if kind == "bool":
                value = "1" if request.form.get(key) == "1" else "0"
            else:
                value = (request.form.get(key) or "").strip()
                if kind == "number":
                    try:
                        value = str(int(value))
                    except ValueError:
                        continue
                    if key in ("posts_per_page", "threads_per_page") and int(value) < 1:
                        value = "1"
                    if key in ("thumb_width", "thumb_height") and int(value) < 0:
                        value = "0"
            set_setting(key, value)
        db.session.commit()
        flash("设置已保存。", "success")
        return redirect(url_for("admin.settings_page"))

    return render_template(
        "admin/settings.html", values=get_settings(), editable=EDITABLE_SETTINGS, defaults=DEFAULTS
    )


@bp.route("/forums", methods=["GET", "POST"])
def forums_page():
    if request.method == "POST":
        action = request.form.get("action")
        if action == "add_category":
            name = (request.form.get("name") or "").strip()
            if name:
                max_pos = db.session.scalar(select(func.max(Category.position))) or 0
                db.session.add(Category(name=name[:120], position=max_pos + 1))
                db.session.commit()
                flash("分类已添加。", "success")
        elif action == "add_forum":
            name = (request.form.get("name") or "").strip()
            category_id = request.form.get("category_id", type=int)
            if name and category_id:
                max_pos = db.session.scalar(
                    select(func.max(Forum.position)).where(Forum.category_id == category_id)
                ) or 0
                db.session.add(
                    Forum(
                        name=name[:120],
                        description=(request.form.get("description") or "").strip(),
                        category_id=category_id,
                        position=max_pos + 1,
                    )
                )
                db.session.commit()
                flash("版块已添加。", "success")
        return redirect(url_for("admin.forums_page"))

    categories = (
        db.session.execute(select(Category).order_by(Category.position, Category.id)).scalars().all()
    )
    return render_template("admin/forums.html", categories=categories)


@bp.post("/forums/<int:forum_id>/delete")
def delete_forum(forum_id: int):
    forum_obj = db.session.get(Forum, forum_id)
    if forum_obj is None:
        abort(404)
    if forum_obj.threads.count() > 0:
        flash("这个版块下还有主题，先移走或删除再删版块。", "error")
        return redirect(url_for("admin.forums_page"))
    db.session.delete(forum_obj)
    db.session.commit()
    flash("版块已删除。", "success")
    return redirect(url_for("admin.forums_page"))


@bp.post("/forums/<int:forum_id>/toggle")
def toggle_forum(forum_id: int):
    forum_obj = db.session.get(Forum, forum_id)
    if forum_obj is None:
        abort(404)
    forum_obj.is_closed = not forum_obj.is_closed
    db.session.commit()
    flash("版块状态已切换。", "success")
    return redirect(url_for("admin.forums_page"))


@bp.get("/users")
def users_page():
    page = max(1, request.args.get("page", type=int) or 1)
    per_page = 20
    total = db.session.scalar(select(func.count(User.id))) or 0
    users = (
        db.session.execute(
            select(User).order_by(User.id).offset((page - 1) * per_page).limit(per_page)
        )
        .scalars()
        .all()
    )
    return render_template(
        "admin/users.html",
        users=users,
        page=page,
        pages=max(1, (total + per_page - 1) // per_page),
        total=total,
        format_dt=format_dt,
    )


@bp.post("/users/<int:user_id>/ban")
def ban_user(user_id: int):
    user = db.session.get(User, user_id)
    if user is None:
        abort(404)
    if user.id == current_user.id:
        flash("不能封禁自己。", "error")
        return redirect(url_for("admin.users_page"))
    user.is_banned = not user.is_banned
    db.session.commit()
    flash(f"{user.username} 已{'解封' if not user.is_banned else '封禁'}。", "success")
    return redirect(url_for("admin.users_page"))


@bp.post("/users/<int:user_id>/promote")
def promote_user(user_id: int):
    user = db.session.get(User, user_id)
    if user is None:
        abort(404)
    if user.id == current_user.id:
        flash("不能修改自己的管理员状态。", "error")
        return redirect(url_for("admin.users_page"))
    user.is_admin = not user.is_admin
    db.session.commit()
    flash(f"{user.username} 管理员权限已切换。", "success")
    return redirect(url_for("admin.users_page"))
