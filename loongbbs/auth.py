"""Registration, login, logout, avatar editing and public profiles."""
from __future__ import annotations

import io
import re
import secrets
from datetime import timezone
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
from .models import (
    Avatar,
    Forum,
    Post,
    PrivateMessage,
    Thread,
    ThreadSubscription,
    User,
    utcnow,
)
from .settings import get_setting
from .utils import censor_text, clamp_page, format_dt, now_gmt

bp = Blueprint("auth", __name__)

USERNAME_CHARS = "A-Za-z0-9_\u4e00-\u9fa5"
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _username_limits() -> tuple[int, int]:
    """vB 组 6：minuserlength / maxuserlength（默认 3 / 15）。"""
    try:
        low = max(1, int(get_setting("minuserlength") or 3))
    except ValueError:
        low = 3
    try:
        high = int(get_setting("maxuserlength") or 15)
    except ValueError:
        high = 15
    return low, max(low, high)


def _username_allowed(name: str) -> bool:
    low, high = _username_limits()
    return bool(re.match(rf"^[{USERNAME_CHARS}]{{{low},{high}}}$", name))


def _username_forbidden(name: str) -> bool:
    """vB 组 6 的 illegalusernames：空格分隔的片段，命中小写子串即禁止。"""
    raw = (get_setting("illegalusernames") or "").strip().lower()
    if not raw:
        return False
    lowered = name.lower()
    return any(token and token in lowered for token in raw.split())


@bp.get("/register")
def register_form():
    if current_user.is_authenticated:
        return redirect(url_for("forums.index"))
    if get_setting("allowregistration") != "1":
        flash("本站暂未开放注册。", "error")
        return redirect(url_for("forums.index"))
    low, high = _username_limits()
    return render_template("auth/register.html", min_user=low, max_user=high)


def _banned_email(email: str) -> bool:
    """vB 组 17 的 banemail：列表按空格分隔，可填完整邮箱或整个域名。

    原版用 `stristr(" ".$banemail." ", " ".$email." ")`，即空格包裹后的精确片段匹配，
    域名匹配则拿 @ 后面的部分再比对一次。
    """
    if get_setting("enablebanning", "0") != "1":
        return False
    ban = " ".join((get_setting("banemail") or "").split()).lower()
    if not ban:
        return False
    email = (email or "").strip().lower()
    if not email:
        return False
    if f" {email} " in f" {ban} ":
        return True
    domain = email.rsplit("@", 1)[-1]
    return bool(domain) and f" {domain} " in f" {ban} "


@bp.post("/register")
def register():
    if get_setting("allowregistration") != "1":
        flash("本站暂未开放注册。", "error")
        return redirect(url_for("forums.index"))
    username = (request.form.get("username") or "").strip()
    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""
    password2 = request.form.get("password2") or ""

    low, high = _username_limits()
    errors: list[str] = []
    if not _username_allowed(username):
        errors.append(f"用户名需为 {low}–{high} 位，允许中文、字母、数字和下划线。")
    elif _username_forbidden(username):
        errors.append("这个用户名不被允许。")
    if not EMAIL_RE.match(email):
        errors.append("请填写有效的邮箱地址。")
    elif _banned_email(email):
        # 组 17 banemail：注册时命中封禁列表（整页错误，对应 error_banemail）
        return render_template("ban_email.html"), 403
    if len(password) < 8:
        errors.append("密码至少 8 位。")
    if password != password2:
        errors.append("两次输入的密码不一致。")

    if not errors:
        if db.session.scalar(select(User).where(func.lower(User.username) == username.lower())):
            errors.append("用户名已被注册。")
        elif db.session.scalar(select(User).where(func.lower(User.email) == email)):
            # 本项目的 users.email 带唯一索引，所以 requireuniqueemail=0 也不能真的重复；
            # 仍然给出可读提示，避免数据库抛出 IntegrityError 变 500。
            if get_setting("requireuniqueemail") == "0":
                errors.append("本站数据库要求邮箱唯一，这个邮箱已被注册。")
            else:
                errors.append("邮箱已被注册。")

    if errors:
        for message in errors:
            flash(message, "error")
        return (
            render_template("auth/register.html", username=username, email=email, min_user=low, max_user=high),
            400,
        )

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


@bp.route("/logout", methods=["GET", "POST"])
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


def _store_uploaded_avatar(storage, user_id: int, max_dim: int, max_bytes: int) -> tuple[str, str]:
    """把上传的图片等比缩到上限再落盘。返回 (相对 static 的路径, 错误信息)。

    vB 2.x 只认 50×50 / 20000 字节这种小图，现代照片直接拒绝；这里先缩放再存，
    保证用户上传任何常见格式都能得到一个可用的小头像。max_bytes 就是后台
    「头像」组 avatarmaxsize 的字节数。
    """
    from PIL import Image, ImageOps, UnidentifiedImageError

    try:
        image = Image.open(storage.stream)
        image.load()
    except (UnidentifiedImageError, OSError):
        return "", "上传的文件不是可识别的图片。"

    image = ImageOps.exif_transpose(image)
    if max(image.size) > max_dim:
        image.thumbnail((max_dim, max_dim), Image.LANCZOS)

    limit = max(1, max_bytes)
    payload = b""
    suffix = ".png"
    for scale in (1.0, 0.8, 0.65, 0.5, 0.35):
        frame = image
        if scale != 1.0:
            frame = image.resize(
                (max(1, int(image.width * scale)), max(1, int(image.height * scale))),
                Image.LANCZOS,
            )
        buffer = io.BytesIO()
        if frame.mode in ("RGBA", "LA", "P"):
            frame.convert("RGBA").save(buffer, "PNG", optimize=True)
            suffix = ".png"
        else:
            frame.convert("RGB").save(buffer, "JPEG", quality=85, optimize=True)
            suffix = ".jpg"
        if buffer.tell() <= limit:
            payload = buffer.getvalue()
            break
    if not payload:
        return "", f"图片缩到 {max_dim} 像素后仍超过 {max_kb} KB，请换一张内容更简单的图片。"

    name = f"u{user_id}-{secrets.token_hex(8)}{suffix}"
    (_custom_avatar_dir() / name).write_bytes(payload)
    return f"{CUSTOM_AVATAR_DIR}/{name}", ""


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
        max_dimension=int(get_setting("avatarmaxdimension") or 50),
        max_size_kb=max(1, int(get_setting("avatarmaxsize") or 20000) // 1024),
        allow_upload=get_setting("avatarallowupload") != "0",
        allow_website=get_setting("avatarallowwebsite") != "0",
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
        if get_setting("avatarallowupload") == "0":
            return "后台已关闭上传自定义头像，只能选择头像库里现成的头像。", False
        ext = Path(storage.filename).suffix.lower()
        if ext not in AVATAR_EXTS:
            return "自定义头像只支持 gif / jpg / png / bmp / webp 图片。", False
        required = int(get_setting("avatarcustomposts") or 0)
        if user.post_count < required:
            return f"至少需要 {required} 个帖子才能使用自定义头像。", False

        rel_path, error = _store_uploaded_avatar(
            storage,
            user.id,
            int(get_setting("avatarmaxdimension") or 50),
            int(get_setting("avatarmaxsize") or 20000),
        )
        if error:
            return error, False
        user.custom_avatar = rel_path
        user.avatar_id = 0
        db.session.commit()
        return "自定义头像已上传。", True

    if selected_url:
        if get_setting("avatarallowwebsite") == "0":
            return "后台已关闭「使用网址作为头像」。", False
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
        subscriptions=_my_subscriptions(limit=10),
    )


def _my_subscriptions(limit: int | None = None):
    """当前用户订阅的主题（vB 的 subscribethread），按最后发表倒序。"""
    stmt = (
        select(ThreadSubscription)
        .join(Thread, ThreadSubscription.thread_id == Thread.id)
        .where(ThreadSubscription.user_id == current_user.id)
        .order_by(Thread.last_post_at.desc())
    )
    if limit:
        stmt = stmt.limit(limit)
    return db.session.execute(stmt).scalars().all()


@bp.get("/usercp/subscriptions")
@login_required
def subscriptions():
    """对应 vB 的 subscription.php?do=viewsubscription。"""
    return render_template(
        "auth/subscriptions.html",
        cpnav_current="home",
        forums=_forum_jump_list(),
        rows=_my_subscriptions(),
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
        now_gmt=now_gmt(),
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


# ---- member.php?action=editprofile -----------------------------------------


def _post_count(user) -> int:
    return (
        db.session.scalar(
            select(func.count()).select_from(Post).where(Post.author_id == user.id)
        )
        or 0
    )


def _custom_title_allowed(user) -> bool:
    """vB 组 28：当前用户是否有资格自设头衔（member.php:277-296 / 497-519）。

    ctEnable=0 一律不可；管理员且 ctAdmin=1 无条件可；否则按 ctPosts（发帖数）
    与 ctDays（注册天数）判断，ctEitherOr=0 表示「任一满足」，=1 表示「两者都要」。
    """
    if get_setting("ctEnable", "1") != "1":
        return False
    if getattr(user, "is_admin", False) and get_setting("ctAdmin", "1") == "1":
        return True

    try:
        min_posts = int(get_setting("ctPosts") or 10)
    except (TypeError, ValueError):
        min_posts = 10
    try:
        min_days = int(get_setting("ctDays") or 10)
    except (TypeError, ValueError):
        min_days = 10

    posts_ok = _post_count(user) >= min_posts
    joined = user.joined_at
    if joined is not None and joined.tzinfo is None:
        joined = joined.replace(tzinfo=timezone.utc)
    days = (utcnow() - joined).days if joined else 0
    days_ok = min_days == 0 or days >= min_days

    if get_setting("ctEitherOr", "1") == "0":
        return posts_ok or days_ok
    return posts_ok and days_ok


def _ct_censor(text: str) -> str:
    """vB 的 customcensortext()：按 ctCensorWords 把命中词替换成 censorchar。"""
    words = (get_setting("ctCensorWords") or "").strip()
    char = (get_setting("censorchar") or "*").strip()[:1] or "*"
    for raw in words.split():
        token = raw.strip()
        if not token:
            continue
        if token.startswith("{") and token.endswith("}") and len(token) > 2:
            core = token[1:-1]
            pattern = r"(?<![A-Za-z])" + re.escape(core) + r"(?![A-Za-z])"
            length = len(core)
        else:
            pattern = re.escape(token)
            length = len(token)
        text = re.sub(pattern, char * length, text, flags=re.I)
    return text


def _custom_title_limits() -> tuple[bool, int]:
    try:
        max_chars = int(get_setting("ctMaxChars") or 25)
    except (TypeError, ValueError):
        max_chars = 25
    return _custom_title_allowed(current_user), max(1, max_chars)


@bp.get("/usercp/profile")
@login_required
def edit_profile():
    """对应 vB 的 member.php?action=editprofile。"""
    ct_allowed, ct_max_chars = _custom_title_limits()
    return render_template(
        "auth/editprofile.html",
        cpnav_current="profile",
        forums=_forum_jump_list(),
        ct_allowed=ct_allowed,
        ct_max_chars=ct_max_chars,
    )


@bp.post("/usercp/profile")
@login_required
def edit_profile_post():
    form = request.form
    user = current_user

    email = (form.get("email") or "").strip()
    email_confirm = (form.get("emailconfirm") or "").strip()
    ok = True
    if not email or "@" not in email:
        flash("邮箱地址格式不正确。")
        ok = False
    elif email != email_confirm:
        flash("两次输入的邮箱地址不一致。")
        ok = False
    else:
        taken = db.session.scalar(
            select(User).where(User.email == email, User.id != user.id)
        )
        if taken is not None:
            flash("这个邮箱地址已经被其他会员使用。")
            ok = False
        elif _banned_email(email) and not (
            get_setting("allowkeepbannedemail", "1") == "1" and email == user.email
        ):
            # 组 17：allowkeepbannedemail=1 且邮箱没变时放行（原版 member.php:388）
            flash("这个邮箱地址已被管理员封禁。")
            ok = False

    if not ok:
        ct_allowed, ct_max_chars = _custom_title_limits()
        return render_template(
            "auth/editprofile.html",
            cpnav_current="profile",
            forums=_forum_jump_list(),
            ct_allowed=ct_allowed,
            ct_max_chars=ct_max_chars,
        )

    user.email = email
    user.homepage = (form.get("homepage") or "").strip()[:255]
    user.icq = (form.get("icq") or "").strip()[:30]
    user.aim = (form.get("aim") or "").strip()[:30]
    user.yahoo = (form.get("yahoo") or "").strip()[:30]
    user.signature = censor_text((form.get("signature") or "").strip())
    user.location = (form.get("location") or "").strip()[:100]
    user.interests = (form.get("interests") or "").strip()[:200]
    user.occupation = (form.get("occupation") or "").strip()[:100]
    user.birthday = (form.get("birthday") or "").strip()[:10]

    # 组 28 自定义用户头衔：资格够了才处理 customtext / resettitle
    if _custom_title_allowed(user):
        try:
            max_chars = int(get_setting("ctMaxChars") or 25)
        except (TypeError, ValueError):
            max_chars = 25
        max_chars = max(1, max_chars)
        if form.get("resettitle") == "yes":
            # 原版勾 Reset 时把 customtitle 归 0，头衔回落到用户组/发帖数头衔
            user.usertitle = ""
            user.customtitle = 0
        else:
            customtext = (form.get("customtext") or "").strip()
            if customtext:
                customtext = customtext[:max_chars]
                customtext = censor_text(customtext)
                if (not getattr(user, "is_admin", False)) or get_setting("ctCensorMod", "1") == "1":
                    customtext = _ct_censor(customtext)
                user.usertitle = customtext
                user.customtitle = 1

    db.session.commit()
    flash("个人资料已更新。")
    return redirect(url_for("auth.profile", username=user.username))


# ---- member.php?action=lostpw ----------------------------------------------

RESET_MAX_AGE = 3600  # 令牌有效期（秒）


def _reset_serializer():
    from itsdangerous import URLSafeTimedSerializer

    return URLSafeTimedSerializer(current_app.secret_key, salt="loongbbs-lostpw")


def _read_reset_token(token: str):
    try:
        data = _reset_serializer().loads(token, max_age=RESET_MAX_AGE)
    except Exception:  # 过期、被篡改、格式不对
        return None
    return data.get("uid") if isinstance(data, dict) else None


def _render_lostpw(step: str, **kwargs):
    return render_template("auth/lostpw.html", step=step, **kwargs)


@bp.get("/lostpw")
def lostpw():
    """对应 vB 的 member.php?action=lostpw（忘记密码）。"""
    return _render_lostpw("form", reset_link=None)


@bp.post("/lostpw")
def lostpw_post():
    email = (request.form.get("email") or "").strip()
    user = None
    if email:
        user = db.session.scalar(
            select(User).where(func.lower(User.email) == email.lower())
        )
    if user is None:
        flash("没有找到使用这个邮箱地址的会员，请检查后重试。")
        return _render_lostpw("form", reset_link=None, email=email)
    token = _reset_serializer().dumps({"uid": user.id})
    reset_link = url_for("auth.lostpw_reset", token=token, _external=True)
    return _render_lostpw("sent", reset_link=reset_link, email=email, username=user.username)


@bp.get("/lostpw/reset/<token>")
def lostpw_reset(token: str):
    if _read_reset_token(token) is None:
        return _render_lostpw("invalid", reset_link=None)
    return _render_lostpw("reset", reset_link=None, token=token)


@bp.post("/lostpw/reset/<token>")
def lostpw_reset_post(token: str):
    uid = _read_reset_token(token)
    if uid is None:
        return _render_lostpw("invalid", reset_link=None)
    user = db.session.get(User, uid)
    if user is None:
        return _render_lostpw("invalid", reset_link=None)

    new = request.form.get("newpassword") or ""
    confirm = request.form.get("newpasswordconfirm") or ""
    if len(new) < 6:
        flash("新密码至少需要 6 个字符。")
        return _render_lostpw("reset", reset_link=None, token=token)
    if new != confirm:
        flash("两次输入的新密码不一致。")
        return _render_lostpw("reset", reset_link=None, token=token)

    user.set_password(new)
    db.session.commit()
    flash("密码已重设，请用新密码登录。")
    return redirect(url_for("auth.login"))


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

