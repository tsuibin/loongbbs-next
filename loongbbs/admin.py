"""Admin control panel: settings, forums, users, avatars, threads, stats."""
from __future__ import annotations

from pathlib import Path

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy import func, select

from .extensions import db
from .models import (
    Attachment,
    Avatar,
    Category,
    Forum,
    Post,
    PostReport,
    PrivateMessage,
    Thread,
    User,
)
from .settings import DEFAULTS, get_settings, set_setting
from .utils import format_dt, human_size

bp = Blueprint("admin", __name__, url_prefix="/admin")

# 左侧导航：分组与条目顺序照抄 vB 2.3.11 admin/index.php?action=nav
# endpoint 有值 = 已移植，链到真实页面；module 有值 = 原版模块，尚未移植
NAV_GROUPS = [
    {"title": "Options", "links": [
        {"label": "vBulletin Options", "endpoint": "admin.settings_page"},
    ]},
    {"title": "Announcements", "links": [
        {"label": "Add", "module": "Add Announcement"},
        {"label": "Modify", "module": "Modify Announcements"},
    ]},
    {"title": "Forums & Moderators", "links": [
        {"label": "Add", "module": "Add Forum"},
        {"label": "Modify", "endpoint": "admin.forums_page"},
        {"label": "Permissions", "module": "Forum Permissions"},
    ]},
    {"title": "Threads & Posts", "links": [
        {"label": "Mass Prune", "module": "Mass Prune"},
        {"label": "Mass Move", "endpoint": "admin.threads_page"},
        {"label": "Unsubscribe Thread", "module": "Unsubscribe Thread"},
        {"label": "Strip Poll", "module": "Strip Poll"},
        {"label": "Who Voted?", "module": "Who Voted?"},
    ]},
    {"title": "Moderation", "links": [
        {"label": "Reported Posts", "endpoint": "admin.reports_page"},
        {"label": "New Posts", "module": "Moderate New Posts"},
        {"label": "New Attachments", "module": "Moderate New Attachments"},
    ]},
    {"title": "Users", "links": [
        {"label": "Add", "module": "Add User"},
        {"label": "Find", "endpoint": "admin.users_page"},
        {"label": "Move/Prune", "module": "Move/Prune Users"},
        {"label": "PM Statistics", "module": "PM Statistics"},
        {"label": "IP Addresses", "module": "IP Addresses"},
        {"label": "Referrals", "module": "Referrals"},
        {"label": "Email Users", "module": "Email Users"},
        {"label": "Build Mailing List", "module": "Build Mailing List"},
    ]},
    {"title": "User Titles", "links": [
        {"label": "Add", "module": "Add User Title"},
        {"label": "Modify", "module": "Modify User Titles"},
    ]},
    {"title": "User Profile Fields", "links": [
        {"label": "Add", "module": "Add Profile Field"},
        {"label": "Modify", "module": "Modify Profile Fields"},
    ]},
    {"title": "User Groups", "links": [
        {"label": "Add", "module": "Add User Group"},
        {"label": "Modify", "module": "Modify User Groups"},
        {"label": "Forum Permissions", "module": "Forum Permissions"},
    ]},
    {"title": "Avatars", "links": [
        {"label": "Add", "endpoint": "admin.avatars_add"},
        {"label": "Modify", "endpoint": "admin.avatars_page"},
        {"label": "Upload", "endpoint": "admin.avatars_upload"},
    ]},
    {"title": "Post Icons", "links": [
        {"label": "Add", "module": "Add Post Icon"},
        {"label": "Modify", "module": "Modify Post Icons"},
        {"label": "Upload", "module": "Upload Post Icons"},
    ]},
    {"title": "Smilies", "links": [
        {"label": "Add", "module": "Add Smilie"},
        {"label": "Modify", "module": "Modify Smilies"},
        {"label": "Upload", "module": "Upload Smilies"},
    ]},
    {"title": "Custom vB Codes", "links": [
        {"label": "Add", "module": "Add vB Code"},
        {"label": "Modify", "module": "Modify vB Codes"},
    ]},
    {"title": "Import & Maintenance", "links": [
        {"label": "Back-up Database", "module": "Back-up Database"},
        {"label": "Database Settings", "module": "Database Settings"},
        {"label": "BB Import Systems", "module": "BB Import Systems"},
        {"label": "Update Counters", "module": "Update Counters"},
    ]},
    {"title": "Statistics & Logs", "links": [
        {"label": "Statistics", "endpoint": "admin.dashboard"},
        {"label": "Admin Log", "module": "Admin Log"},
    ]},
    {"title": "Styles", "links": [
        {"label": "Add Style", "module": "Add Style"},
        {"label": "Modify", "module": "Modify Styles"},
        {"label": "Download/Upload", "module": "Download/Upload Style"},
    ]},
    {"title": "Replacements", "links": [
        {"label": "Add", "module": "Add Replacement"},
        {"label": "Modify", "module": "Modify Replacements"},
        {"label": "Add Set", "module": "Add Replacement Set"},
    ]},
    {"title": "Templates", "links": [
        {"label": "Add", "module": "Add Template"},
        {"label": "Modify", "module": "Modify Templates"},
        {"label": "Search", "module": "Search Templates"},
        {"label": "Add Template Set", "module": "Add Template Set"},
    ]},
]

EDITABLE_SETTINGS = {
    "site_name": ("站点名称", "text"),
    "site_tagline": ("站点副标题", "text"),
    "posts_per_page": ("每页帖子数", "number"),
    "threads_per_page": ("每页主题数", "number"),
    "allow_registration": ("开放注册", "bool"),
    "thumb_mode": ("附件图片显示缩略图", "bool"),
    "thumb_width": ("缩略图最大宽度 (px)", "number"),
    "thumb_height": ("缩略图最大高度 (px)", "number"),
    "avatarenabled": ("启用头像", "bool"),
    "avatarmaxdimension": ("头像最大尺寸 (px)", "number"),
    "avatarmaxsize": ("自定义头像最大体积 (KB)", "number"),
    "avatarcustomposts": ("使用自定义头像所需帖子数", "number"),
}


@bp.before_request
@login_required
def require_admin():
    if not current_user.is_admin:
        abort(403)


@bp.get("/")
def frameset():
    """后台入口：还原 vB 的三栏 frameset（左导航 180px / 顶条 20px / 主区）。"""
    return render_template("admin/frameset.html")


@bp.get("/nav")
def nav():
    return render_template("admin/nav.html", nav_groups=NAV_GROUPS)


@bp.get("/head")
def head():
    return render_template("admin/head.html")


@bp.get("/not-port")
def not_port():
    module = (request.args.get("module") or "该模块").strip()
    return render_template("admin/not_port.html", module=module)


@bp.get("/home")
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


@bp.route("/threads", methods=["GET", "POST"])
def threads_page():
    """Threads & Posts → Mass Move / Mass Prune（原版 thread.php 的两个动作）。"""
    if request.method == "POST":
        ids = [int(x) for x in request.form.getlist("threadids") if x.strip().isdigit()]
        action = request.form.get("action")
        if not ids:
            flash("没有选择任何主题。", "error")
            return redirect(url_for("admin.threads_page"))
        if action == "move":
            target = request.form.get("forumid", type=int)
            forum_obj = db.session.get(Forum, target) if target else None
            if forum_obj is None:
                flash("请选择要移动到的目标版块。", "error")
            else:
                moved = 0
                for tid in ids:
                    thread_obj = db.session.get(Thread, tid)
                    if thread_obj is not None:
                        thread_obj.forum_id = forum_obj.id
                        moved += 1
                db.session.commit()
                flash(f"{moved} 个主题已移动到「{forum_obj.name}」。", "success")
        elif action == "delete":
            deleted = 0
            for tid in ids:
                thread_obj = db.session.get(Thread, tid)
                if thread_obj is None:
                    continue
                for post in thread_obj.posts:
                    db.session.delete(post)
                db.session.delete(thread_obj)
                deleted += 1
            db.session.commit()
            flash(f"{deleted} 个主题已删除（含其全部回复）。", "success")
        return redirect(url_for("admin.threads_page"))

    forum_id = request.args.get("forumid", type=int)
    page = max(1, request.args.get("page", type=int) or 1)
    per_page = 25
    stmt = select(Thread).order_by(Thread.last_post_at.desc())
    if forum_id:
        stmt = stmt.where(Thread.forum_id == forum_id)
    total = db.session.scalar(
        select(func.count(Thread.id)).where(Thread.forum_id == forum_id) if forum_id
        else select(func.count(Thread.id))
    ) or 0
    threads = (
        db.session.execute(stmt.offset((page - 1) * per_page).limit(per_page)).scalars().all()
    )
    forums = (
        db.session.execute(select(Forum).order_by(Forum.position, Forum.id)).scalars().all()
    )
    return render_template(
        "admin/threads.html",
        threads=threads,
        forums=forums,
        forum_id=forum_id,
        page=page,
        pages=max(1, (total + per_page - 1) // per_page),
        total=total,
    )


@bp.get("/users")
def users_page():
    page = max(1, request.args.get("page", type=int) or 1)
    q = (request.args.get("q") or "").strip()
    per_page = 20
    stmt = select(User).order_by(User.id)
    count_stmt = select(func.count(User.id))
    if q:
        stmt = stmt.where(User.username.ilike(f"%{q}%"))
        count_stmt = count_stmt.where(User.username.ilike(f"%{q}%"))
    total = db.session.scalar(count_stmt) or 0
    users = (
        db.session.execute(stmt.offset((page - 1) * per_page).limit(per_page)).scalars().all()
    )
    return render_template(
        "admin/users.html",
        users=users,
        q=q,
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


# ---------------------------------------------------------------- avatars
# 对应 vB 2.3.11 admin/avatar.php：action=modify / add / insert / insertmultiple
# / domultiple / upload / doupload / edit / doupdate / remove / kill

AVATAR_SUBDIR = "images/avatars"
AVATAR_EXTS = {".gif", ".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def _avatar_dir() -> Path:
    path = Path(current_app.static_folder) / "images" / "avatars"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _clean_avatarpath(raw: str) -> str:
    """把管理员填的路径归一化成「相对 static」或完整外链。"""
    raw = (raw or "").strip().replace("\\", "/")
    if not raw:
        return ""
    if raw.startswith(("http://", "https://")):
        return raw
    raw = raw.lstrip("/")
    for prefix in ("static/", "../"):
        if raw.startswith(prefix):
            raw = raw[len(prefix):]
    return raw


def _avatar_name_for(filename: str) -> str:
    """安全文件名：只保留字母数字、横线下划线点、中文。"""
    base = Path(filename).name
    stem = Path(base).stem
    ext = Path(base).suffix.lower()
    safe = "".join(ch for ch in stem if ch.isalnum() or ch in "-_")[:60] or "avatar"
    return f"{safe}{ext if ext in AVATAR_EXTS else '.gif'}"


def _scan_avatar_dir(subdir: str) -> list[str]:
    directory = Path(current_app.static_folder) / subdir
    if not directory.is_dir():
        return []
    found: list[str] = []
    for entry in sorted(directory.iterdir(), key=lambda p: p.name.lower()):
        if entry.is_file() and entry.suffix.lower() in AVATAR_EXTS:
            found.append(f"{subdir}/{entry.name}")
    return found


@bp.get("/reports")
def reports_page():
    """Moderation › Reported Posts —— 前台举报的队列。"""
    page = max(1, request.args.get("startpage", type=int) or 1)
    perpage = 25
    total = db.session.scalar(select(func.count(PostReport.id))) or 0
    pending = (
        db.session.scalar(
            select(func.count(PostReport.id)).where(PostReport.resolved.is_(False))
        )
        or 0
    )
    pages = max(1, (total + perpage - 1) // perpage)
    page = min(page, pages)
    rows = (
        db.session.execute(
            select(PostReport)
            .order_by(PostReport.resolved, PostReport.created_at.desc())
            .offset((page - 1) * perpage)
            .limit(perpage)
        )
        .scalars()
        .all()
    )
    return render_template(
        "admin/reports.html",
        rows=rows,
        total=total,
        pending=pending,
        page=page,
        pages=pages,
        format_dt=format_dt,
    )


@bp.post("/reports/<int:report_id>/resolve")
def reports_resolve(report_id: int):
    """标记举报为已处理（再按一次可重新打开）。"""
    row = db.session.get(PostReport, report_id)
    if row is None:
        abort(404)
    row.resolved = not bool(request.form.get("undo"))
    db.session.commit()
    flash("举报状态已更新。")
    return redirect(url_for("admin.reports_page"))


@bp.get("/avatars")
def avatars_page():
    """Avatars › Modify —— 原版按 minimumposts 分组的 5 列网格。"""
    page = max(1, request.args.get("startpage", type=int) or 1)
    perpage = request.args.get("perpage", type=int) or 25
    perpage = max(5, min(perpage, 100))

    total = db.session.scalar(select(func.count(Avatar.id))) or 0
    pages = max(1, (total + perpage - 1) // perpage)
    page = min(page, pages)
    rows = (
        db.session.execute(
            select(Avatar)
            .order_by(Avatar.minimumposts, Avatar.id)
            .offset((page - 1) * perpage)
            .limit(perpage)
        )
        .scalars()
        .all()
    )

    # 每行 5 个，按 minimumposts 分段，和原版一样在段首插一条 "-- N Posts --"
    display_rows: list[dict] = []
    bucket: list = []
    current_posts = None
    for avatar in rows:
        if current_posts is None or avatar.minimumposts != current_posts:
            if bucket:
                display_rows.append({"header": None, "items": bucket})
                bucket = []
            current_posts = avatar.minimumposts
            display_rows.append({"header": current_posts, "items": []})
        bucket.append(avatar)
        if len(bucket) == 5:
            display_rows.append({"header": None, "items": bucket})
            bucket = []
    if bucket:
        display_rows.append({"header": None, "items": bucket})

    return render_template(
        "admin/avatars.html",
        display_rows=display_rows,
        total=total,
        page=page,
        pages=pages,
        perpage=perpage,
        lower=(page - 1) * perpage + 1 if total else 0,
        upper=min(page * perpage, total),
    )


@bp.get("/avatars/add")
def avatars_add():
    return render_template("admin/avatars_add.html")


@bp.post("/avatars/add")
def avatars_insert():
    action = request.form.get("action")
    if action == "insertmultiple":
        subdir = _clean_avatarpath(request.form.get("avatarpath") or AVATAR_SUBDIR)
        perpage = request.form.get("iconsperpage", type=int) or 10
        return redirect(
            url_for("admin.avatars_multiple", avatarpath=subdir, iconsperpage=perpage)
        )

    title = (request.form.get("title") or "").strip()[:120]
    minimumposts = max(0, request.form.get("minimumposts", type=int) or 0)
    avatarpath = _clean_avatarpath(request.form.get("avatarpath") or "")
    if not avatarpath:
        flash("请填写头像文件路径。", "error")
        return redirect(url_for("admin.avatars_add"))

    db.session.add(Avatar(title=title, minimumposts=minimumposts, avatarpath=avatarpath))
    db.session.commit()
    flash("头像已添加。", "success")
    return redirect(url_for("admin.avatars_page"))


@bp.get("/avatars/multiple")
def avatars_multiple():
    subdir = _clean_avatarpath(request.args.get("avatarpath") or AVATAR_SUBDIR)
    perpage = max(1, min(request.args.get("iconsperpage", type=int) or 10, 100))
    page = max(1, request.args.get("startpage", type=int) or 1)

    known = set(
        db.session.execute(select(Avatar.avatarpath)).scalars().all()
    )
    files = [f for f in _scan_avatar_dir(subdir) if f not in known]
    total = len(files)
    pages = max(1, (total + perpage - 1) // perpage)
    page = min(page, pages)
    shown = files[(page - 1) * perpage: page * perpage]

    return render_template(
        "admin/avatars_multiple.html",
        files=shown,
        subdir=subdir,
        perpage=perpage,
        page=page,
        pages=pages,
        total=total,
        lower=(page - 1) * perpage + 1 if total else 0,
        upper=min(page * perpage, total),
        directory_exists=(Path(current_app.static_folder) / subdir).is_dir(),
    )


@bp.post("/avatars/multiple")
def avatars_insert_multiple():
    subdir = _clean_avatarpath(request.form.get("avatarpath") or AVATAR_SUBDIR)
    added = 0
    for key in request.form:
        if not key.startswith("use_"):
            continue
        index = key[4:]
        if request.form.get(key) != "yes":
            continue
        path = _clean_avatarpath(request.form.get(f"path_{index}", ""))
        if not path:
            continue
        posts_raw = (request.form.get(f"posts_{index}") or "0").strip()
        db.session.add(
            Avatar(
                title=(request.form.get(f"title_{index}") or "").strip()[:120],
                minimumposts=int(posts_raw) if posts_raw.isdigit() else 0,
                avatarpath=path,
            )
        )
        added += 1
    db.session.commit()
    if added:
        flash(f"已添加 {added} 个头像。", "success")
    else:
        flash("没有选中任何头像。", "error")
    return redirect(url_for("admin.avatars_multiple", avatarpath=subdir))


@bp.get("/avatars/upload")
def avatars_upload():
    return render_template("admin/avatars_upload.html")


@bp.post("/avatars/upload")
def avatars_do_upload():
    storage = request.files.get("avatarfile")
    if storage is None or not storage.filename:
        flash("请选择要上传的图片。", "error")
        return redirect(url_for("admin.avatars_upload"))

    ext = Path(storage.filename).suffix.lower()
    if ext not in AVATAR_EXTS:
        flash("只支持 gif / jpg / png / bmp / webp 图片。", "error")
        return redirect(url_for("admin.avatars_upload"))

    target_dir = _avatar_dir()
    name = _avatar_name_for(storage.filename)
    target = target_dir / name
    counter = 1
    while target.exists():
        target = target_dir / f"{Path(name).stem}-{counter}{Path(name).suffix}"
        counter += 1
    storage.save(target)

    size = target.stat().st_size
    limit_kb = int(get_settings().get("avatarmaxsize") or 60)
    if size > limit_kb * 1024:
        target.unlink(missing_ok=True)
        flash(f"图片超过 {limit_kb} KB 上限，已放弃。", "error")
        return redirect(url_for("admin.avatars_upload"))

    rel = f"{AVATAR_SUBDIR}/{target.name}"
    title = (request.form.get("title") or Path(storage.filename).stem).strip()[:120]
    minimumposts = max(0, request.form.get("minimumposts", type=int) or 0)
    db.session.add(Avatar(title=title, minimumposts=minimumposts, avatarpath=rel))
    db.session.commit()
    flash(f"头像已上传：{rel}", "success")
    return redirect(url_for("admin.avatars_page"))


@bp.route("/avatars/<int:avatar_id>/edit", methods=["GET", "POST"])
def avatars_edit(avatar_id: int):
    avatar = db.session.get(Avatar, avatar_id)
    if avatar is None:
        abort(404)
    if request.method == "POST":
        avatar.title = (request.form.get("title") or "").strip()[:120]
        avatar.minimumposts = max(0, request.form.get("minimumposts", type=int) or 0)
        avatar.avatarpath = _clean_avatarpath(request.form.get("avatarpath") or "") or avatar.avatarpath
        db.session.commit()
        flash("头像记录已更新。", "success")
        return redirect(url_for("admin.avatars_page"))
    return render_template("admin/avatars_edit.html", avatar=avatar)


@bp.route("/avatars/<int:avatar_id>/remove", methods=["GET", "POST"])
def avatars_remove(avatar_id: int):
    avatar = db.session.get(Avatar, avatar_id)
    if avatar is None:
        abort(404)
    if request.method == "POST":
        # 原版 kill：删记录后把所有用它的用户 avatarid 归零
        db.session.execute(
            db.update(User).where(User.avatar_id == avatar.id).values(avatar_id=0)
        )
        db.session.delete(avatar)
        db.session.commit()
        flash("头像已删除，使用它的会员已切回没有头像。", "success")
        return redirect(url_for("admin.avatars_page"))
    return render_template("admin/avatars_remove.html", avatar=avatar)
