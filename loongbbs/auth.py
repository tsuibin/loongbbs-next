"""Registration, login, logout, avatar editing and public profiles."""
from __future__ import annotations

import re
import secrets
from pathlib import Path

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import func, select

from .extensions import db
from .models import Avatar, Forum, Post, PrivateMessage, Thread, User, utcnow
from .settings import get_setting
from .utils import clamp_page, format_dt

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


# ---------------------------------------------------------------- avatar
# 对应 vB 2.3.11 member.php?action=editavatar（模板 modifyavatar / modifyavatarbit）

CUSTOM_AVATAR_DIR = "images/custom-avatars"
AVATAR_EXTS = {".gif", ".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def _custom_avatar_dir() -> Path:
    path = Path(current_app.static_folder) / "images" / "custom-avatars"
    path.mkdir(parents=True, exist_ok=True)
    return path


@bp.route("/avatar", methods=["GET", "POST"])
@login_required
def edit_avatar():
    if get_setting("avatarenabled") != "1":
        flash("本站已关闭头像功能。", "error")
        return redirect(url_for("forums.index"))

    perpage = 25
    page = clamp_page(request.args.get("page"))

    if request.method == "POST":
        choice = request.form.get("avatarid")
        try:
            choice_num = int(choice) if choice is not None else 0
        except ValueError:
            choice_num = 0

        selected_url = (request.form.get("avatarurl") or "").strip()
        storage = request.files.get("avatarfile")
        message, ok = _apply_avatar_choice(choice_num, storage, selected_url)
        flash(message, "success" if ok else "error")
        return redirect(url_for("auth.edit_avatar"))

    total = db.session.scalar(select(func.count(Avatar.id))) or 0
    pages = max(1, (total + perpage - 1) // perpage)
    page = min(page, pages)
    avatars = (
        db.session.execute(
            select(Avatar)
            .order_by(Avatar.minimumposts, Avatar.id)
            .offset((page - 1) * perpage)
            .limit(perpage)
        )
        .scalars()
        .all()
    )
    return render_template(
        "auth/avatar.html",
        avatars=avatars,
        page=page,
        pages=pages,
        perpage=perpage,
        total=total,
        lower=(page - 1) * perpage + 1 if total else 0,
        upper=min(page * perpage, total),
        custom_required=int(get_setting("avatarcustomposts") or 0),
        max_dimension=int(get_setting("avatarmaxdimension") or 65),
        max_size_kb=int(get_setting("avatarmaxsize") or 60),
    )


def _apply_avatar_choice(choice: int, storage, selected_url: str) -> tuple[str, bool]:
    """Apply the posted avatar choice. Returns (message, success)."""
    user = current_user

    # no avatar
    if choice == -1:
        user.avatar_id = 0
        user.custom_avatar = ""
        db.session.commit()
        return "已选择「不使用头像」，自定义头像也已清除。", True

    # custom avatar: uploaded file first, then remote URL
    if storage is not None and storage.filename:
        ext = Path(storage.filename).suffix.lower()
        if ext not in AVATAR_EXTS:
            return "自定义头像只支持 gif / jpg / png / bmp / webp 图片。", False
        required = int(get_setting("avatarcustomposts") or 0)
        if user.post_count < required:
            return f"至少需要 {required} 个帖子才能使用自定义头像。", False

        name = f"u{user.id}-{secrets.token_hex(8)}{ext}"
        target = _custom_avatar_dir() / name
        storage.save(target)
        if target.stat().st_size > int(get_setting("avatarmaxsize") or 60) * 1024:
            target.unlink(missing_ok=True)
            return "图片超过体积上限，已放弃上传。", False
        user.custom_avatar = f"{CUSTOM_AVATAR_DIR}/{name}"
        user.avatar_id = 0
        db.session.commit()
        return "自定义头像已上传。", True

    if selected_url:
        if not selected_url.lower().startswith(("http://", "https://")):
            return "自定义头像网址必须以 http:// 或 https:// 开头。", False
        required = int(get_setting("avatarcustomposts") or 0)
        if user.post_count < required:
            return f"至少需要 {required} 个帖子才能使用自定义头像。", False
        user.custom_avatar = selected_url
        user.avatar_id = 0
        db.session.commit()
        return "已把该网址设为你的自定义头像。", True

    if choice > 0:
        avatar = db.session.get(Avatar, choice)
        if avatar is None:
            return "找不到这个头像。", False
        if user.post_count < avatar.minimumposts:
            return f"这个头像需要至少 {avatar.minimumposts} 个帖子才能使用。", False
        user.avatar_id = avatar.id
        user.custom_avatar = ""
        db.session.commit()
        return f"头像已改为「{avatar.title or '未命名'}」。", True

    # choice == 0 with nothing new: keep the current custom avatar / selection
    return "头像设置未变化。", True


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


@bp.get("/usercp")
@login_required
def usercp():
    """User Control Panel home — mirrors vBulletin's usercp.php."""
    inbox = (
        db.session.execute(
            select(PrivateMessage)
            .where(PrivateMessage.recipient_id == current_user.id)
            .order_by(PrivateMessage.created_at.desc())
            .limit(50)
        )
        .scalars()
        .all()
    )
    unread = sum(1 for row in inbox if row.read_at is None)
    latest = inbox[0] if inbox else None
    forums = (
        db.session.execute(select(Forum).order_by(Forum.category_id, Forum.position))
        .scalars()
        .all()
    )
    return render_template(
        "auth/usercp.html",
        unread=unread,
        latest_pm=latest,
        forums=forums,
        joined=format_dt(current_user.joined_at, "%Y-%m-%d"),
    )


def _forum_jump_list():
    """版块跳转下拉用到的版块清单（vB 的 usercp 系列页面都有这个下拉）。"""
    return (
        db.session.execute(select(Forum).order_by(Forum.category_id, Forum.position))
        .scalars()
        .all()
    )


def _tz_minutes(raw: str | None) -> int:
    """把 vB 的时区值（"-3.5" / "+8"）换算成分钟数。"""
    try:
        hours = float(str(raw))
    except (TypeError, ValueError):
        return 0
    return int(round(hours * 60))


def _list_names(raw: str) -> list[str]:
    return [part.strip() for part in (raw or "").split(",") if part.strip()]


# ---- member.php?action=editoptions -----------------------------------------


@bp.get("/usercp/options")
@login_required
def edit_options():
    """对应 vB 的 member.php?action=editoptions。"""
    return render_template(
        "auth/options.html",
        cpnav_current="options",
        forums=_forum_jump_list(),
        now_gmt=format_dt(utcnow(), "%I:%M %p").lstrip("0"),
        style_sets=[("1", "默认风格")],
    )


@bp.post("/usercp/options")
@login_required
def edit_options_post():
    form = request.form
    user = current_user

    def flag(name: str, default: bool = False) -> bool:
        value = form.get(name)
        if value is None:
            return default
        return value == "yes"

    def as_int(name: str, fallback: int) -> int:
        try:
            return int(form.get(name, ""))
        except (TypeError, ValueError):
            return fallback

    user.invisible = flag("invisible")
    user.cookieuser = flag("cookieuser", True)
    # 表单问的是「Browse board with cookies?」，选 no 才表示不走 cookie（nosessionhash=1）
    user.nosessionhash = not flag("nosessionhash", True)
    user.allowmail = flag("allowmail", True)
    # 表单是「Hide Email Address?」，value=no 的按钮表示"是（隐藏）"
    user.showemail = form.get("showemail") != "no"
    user.emailnotification = flag("emailnotification")
    user.receivepm = flag("receivepm", True)
    user.emailonpm = flag("emailonpm", True)
    user.pmpopup = flag("pmpopup", True)
    user.showsignatures = flag("showsignatures", True)
    user.showavatars = flag("showavatars", True)
    user.showimages = flag("showimages", True)
    user.vbcode = flag("vbcode", True)
    user.prunedays = as_int("prunedays", -1)
    user.umaxposts = as_int("umaxposts", -1)
    user.startofweek = as_int("startofweek", 1)
    user.timezoneoffset = _tz_minutes(form.get("timezoneoffset"))
    user.newstyleset = as_int("newstyleset", 0)

    db.session.commit()
    flash("选项已保存。")
    return redirect(url_for("auth.usercp"))


# ---- member.php?action=editpassword ----------------------------------------


@bp.get("/usercp/password")
@login_required
def edit_password():
    """对应 vB 的 member.php?action=editpassword。"""
    return render_template(
        "auth/password.html",
        cpnav_current="password",
        forums=_forum_jump_list(),
    )


@bp.post("/usercp/password")
@login_required
def edit_password_post():
    current = request.form.get("currentpassword", "")
    new = request.form.get("newpassword", "")
    confirm = request.form.get("newpasswordconfirm", "")
    if not current_user.verify_password(current):
        flash("当前密码不正确。")
    elif len(new) < 6:
        flash("新密码至少需要 6 个字符。")
    elif new != confirm:
        flash("两次输入的新密码不一致。")
    else:
        current_user.set_password(new)
        db.session.commit()
        flash("密码已修改。")
        return redirect(url_for("auth.usercp"))
    return render_template(
        "auth/password.html",
        cpnav_current="password",
        forums=_forum_jump_list(),
    )


# ---- member2.php?action=viewlist&userlist=buddy|ignore ---------------------


def _render_list(kind: str):
    field = "buddylist" if kind == "buddy" else "ignorelist"
    names = _list_names(getattr(current_user, field))
    return render_template(
        "auth/lists.html",
        cpnav_current=kind,
        list_kind=kind,
        list_type="好友" if kind == "buddy" else "忽略",
        names=names,
        slots=max(0, 6 - len(names)),
        forums=_forum_jump_list(),
    )


@bp.get("/usercp/buddy")
@login_required
def buddy_list():
    return _render_list("buddy")


@bp.get("/usercp/ignore")
@login_required
def ignore_list():
    return _render_list("ignore")


def _update_list(kind: str):
    field = "buddylist" if kind == "buddy" else "ignorelist"
    submitted = [part.strip() for part in request.form.getlist("listbits[]")]
    keep: list[str] = []
    problems: list[str] = []
    for name in submitted:
        if not name:
            continue
        if name.lower() == (current_user.username or "").lower():
            problems.append(f"{name}：不能把自己加入列表。")
            continue
        user = db.session.scalar(select(User).where(func.lower(User.username) == name.lower()))
        if user is None:
            problems.append(f"{name}：没有这个用户。")
            continue
        if user.username not in keep:
            keep.append(user.username)
    if problems:
        for line in problems:
            flash(line)
    setattr(current_user, field, ",".join(keep))
    db.session.commit()
    if not problems:
        flash("列表已更新。")
    return redirect(url_for("auth.buddy_list" if kind == "buddy" else "auth.ignore_list"))


@bp.post("/usercp/buddy")
@login_required
def buddy_list_post():
    return _update_list("buddy")


@bp.post("/usercp/ignore")
@login_required
def ignore_list_post():
    return _update_list("ignore")

