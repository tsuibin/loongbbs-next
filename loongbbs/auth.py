"""Registration, login, logout and public profiles."""
from __future__ import annotations

import re

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import func, select

from .extensions import db
from .models import Post, Thread, User, utcnow
from .settings import get_setting
from .utils import format_dt

bp = Blueprint("auth", __name__)

USERNAME_RE = re.compile(r"^[A-Za-z0-9_\u4e00-\u9fa5]{3,20}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@bp.get("/register")
def register_form():
    if current_user.is_authenticated:
        return redirect(url_for("forums.index"))
    if get_setting("allow_registration") != "1":
        flash("本站暂未开放注册。", "error")
        return redirect(url_for("forums.index"))
    return render_template("auth/register.html")


@bp.post("/register")
def register():
    if get_setting("allow_registration") != "1":
        flash("本站暂未开放注册。", "error")
        return redirect(url_for("forums.index"))

    username = (request.form.get("username") or "").strip()
    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""
    password2 = request.form.get("password2") or ""

    errors: list[str] = []
    if not USERNAME_RE.match(username):
        errors.append("用户名需为 3–20 位，允许中文、字母、数字和下划线。")
    if not EMAIL_RE.match(email):
        errors.append("请填写有效的邮箱地址。")
    if len(password) < 8:
        errors.append("密码至少 8 位。")
    if password != password2:
        errors.append("两次输入的密码不一致。")

    if not errors:
        exists = db.session.scalar(
            select(User).where(
                (func.lower(User.username) == username.lower()) | (User.email == email)
            )
        )
        if exists:
            errors.append("用户名或邮箱已被注册。")

    if errors:
        for message in errors:
            flash(message, "error")
        return render_template("auth/register.html", username=username, email=email), 400

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    login_user(user)
    flash("注册成功，欢迎加入。", "success")
    return redirect(url_for("forums.index"))


@bp.get("/login")
def login_form():
    if current_user.is_authenticated:
        return redirect(url_for("forums.index"))
    return render_template("auth/login.html")


@bp.post("/login")
def login():
    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""
    remember = request.form.get("remember") == "1"

    user = db.session.scalar(
        select(User).where(func.lower(User.username) == username.lower())
    )
    if user is None or not user.verify_password(password):
        flash("用户名或密码不正确。", "error")
        return render_template("auth/login.html", username=username), 401
    if user.is_banned:
        flash("这个账号已被封禁，如有疑问请联系管理员。", "error")
        return render_template("auth/login.html", username=username), 403

    user.last_seen = utcnow()
    db.session.commit()
    login_user(user, remember=remember)
    flash(f"欢迎回来，{user.username}。", "success")
    return redirect(url_for("forums.index"))


@bp.post("/logout")
@login_required
def logout():
    logout_user()
    flash("已退出登录。", "success")
    return redirect(url_for("forums.index"))


@bp.get("/u/<username>")
def profile(username: str):
    user = db.session.scalar(select(User).where(User.username == username))
    if user is None:
        flash("找不到这个用户。", "error")
        return redirect(url_for("forums.index"))

    threads = (
        db.session.execute(
            select(Thread).where(Thread.author_id == user.id).order_by(Thread.created_at.desc()).limit(8)
        )
        .scalars()
        .all()
    )
    posts = (
        db.session.execute(
            select(Post)
            .where(Post.author_id == user.id, Post.is_deleted.is_(False))
            .order_by(Post.created_at.desc())
            .limit(8)
        )
        .scalars()
        .all()
    )
    return render_template(
        "auth/profile.html",
        profile_user=user,
        threads=threads,
        posts=posts,
        joined=format_dt(user.joined_at, "%Y-%m-%d"),
    )
