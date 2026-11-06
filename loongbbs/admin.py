"""Admin control panel: settings, forums, users, avatars, threads, stats."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
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
from sqlalchemy import delete, func, select

from .extensions import db
from .models import (
    Announcement,
    Attachment,
    Avatar,
    Category,
    Forum,
    ForumPermission,
    PERMISSION_FIELDS,
    PERMISSION_LABELS,
    Poll,
    PollVote,
    Post,
    PostReport,
    PrivateMessage,
    Thread,
    ThreadRating,
    ThreadSubscription,
    User,
    UserGroup,
)
from .permissions import ensure_seed, permissions_for_group
from .settings import DEFAULTS, get_settings, set_setting
from .admin_settings import SETTING_DEFAULTS, SETTING_GROUPS
from .utils import format_dt, human_size

bp = Blueprint("admin", __name__, url_prefix="/admin")

# 左侧导航：分组与条目顺序照抄 vB 2.3.11 admin/index.php?action=nav
# endpoint 有值 = 已移植，链到真实页面；module 有值 = 原版模块，尚未移植
NAV_GROUPS = [
    {"title": "Options", "links": [
        {"label": "vBulletin Options", "endpoint": "admin.settings_page"},
    ]},
    {"title": "Announcements", "links": [
        {"label": "Add", "endpoint": "admin.announcement_add"},
        {"label": "Modify", "endpoint": "admin.announcements_page"},
    ]},
    {"title": "Forums & Moderators", "links": [
        {"label": "Add", "module": "Add Forum"},
        {"label": "Modify", "endpoint": "admin.forums_page"},
        {"label": "Permissions", "endpoint": "admin.permissions_page"},
    ]},
    {"title": "Threads & Posts", "links": [
        {"label": "Mass Prune", "endpoint": "admin.threads_prune"},
        {"label": "Mass Move", "endpoint": "admin.threads_move"},
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
        {"label": "Forum Permissions", "endpoint": "admin.permissions_page"},
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
    groupid_raw = request.values.get("groupid") or ""
    current_group_id = int(groupid_raw) if groupid_raw.isdigit() else None

    if request.method == "POST":
        # 本项目自有设置（网站名称等）只在「全部组」页面上出现，
        # 提交单个分组（groupid）时不能拿空表单把它们清空。
        saving_group = (request.form.get("groupid") or request.args.get("groupid") or "").strip()
        for key, (_, kind) in (EDITABLE_SETTINGS.items() if not saving_group else ()):
            if kind == "bool":
                value = "1" if request.form.get(key) == "1" else "0"
            else:
                value = (request.form.get(key) or "").strip()
                if kind == "number":
                    try:
                        value = str(int(value))
                    except ValueError:
                        continue
            set_setting(key, value)

        # vB 后台 Options 的字段：只认表里定义过的变量名
        allowed = set(SETTING_DEFAULTS)
        for varname, value in request.form.items():
            if varname not in allowed:
                continue
            text = (value or "").strip()
            limit = 2000 if len(SETTING_DEFAULTS.get(varname, "")) > 200 else 200
            set_setting(varname, text[:limit])
        db.session.commit()
        flash("设置已保存。", "success")
        target = url_for("admin.settings_page")
        if current_group_id:
            target += f"?groupid={current_group_id}"
        return redirect(target)

    values = dict(SETTING_DEFAULTS)
    values.update(get_settings())

    shown_groups = []
    for group in SETTING_GROUPS:
        if current_group_id and group["id"] != current_group_id:
            continue
        rows = [dict(setting, value=values.get(setting["varname"], setting["default"])) for setting in group["settings"]]
        shown_groups.append({"id": group["id"], "title": group["title"], "settings": rows})

    return render_template(
        "admin/settings.html",
        values=values,
        editable=EDITABLE_SETTINGS,
        defaults=DEFAULTS,
        groups=SETTING_GROUPS,
        shown_groups=shown_groups,
        current_group_id=current_group_id,
    )


def _parse_announcement_date(raw: str, fallback: datetime) -> datetime:
    """照原版 yyyy-mm-dd hh:mm:ss 的日期输入；解析不了就用 fallback。"""
    text = (raw or "").strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return fallback


def _announcement_forums() -> list[dict]:
    """后台「Visible In」下拉和列表页共用的分类 → 版块结构。"""
    categories = db.session.execute(
        select(Category).order_by(Category.position, Category.id)
    ).scalars().all()
    return [
        {
            "category": category,
            "forums": sorted(category.forums, key=lambda f: (f.position, f.id)),
        }
        for category in categories
    ]


@bp.get("/announcements")
def announcements_page():
    """照 vB admin/announcement.php?action=modify：全站公告表 + 版块树。"""
    global_rows = db.session.execute(
        select(Announcement)
        .where(Announcement.forum_id == -1)
        .order_by(Announcement.start_date.desc())
    ).scalars().all()

    blocks = []
    for block in _announcement_forums():
        forums = []
        for forum_obj in block["forums"]:
            rows = db.session.execute(
                select(Announcement)
                .where(Announcement.forum_id == forum_obj.id)
                .order_by(Announcement.start_date.desc())
            ).scalars().all()
            forums.append({"forum": forum_obj, "rows": rows})
        blocks.append({"category": block["category"], "forums": forums})

    return render_template("admin/announcements.html", global_rows=global_rows, blocks=blocks)


@bp.route("/announcements/add", methods=["GET", "POST"])
def announcement_add():
    forum_id_raw = request.values.get("forum_id")
    forum_id = int(forum_id_raw) if (forum_id_raw or "").lstrip("-").isdigit() else -1

    if request.method == "POST":
        title = (request.form.get("title") or "").strip() or "Announcement"
        start = _parse_announcement_date(request.form.get("startdate"), datetime.now(timezone.utc))
        end = _parse_announcement_date(
            request.form.get("enddate"), datetime.now(timezone.utc) + timedelta(days=31)
        )
        posted_forum = request.form.get("forum_id")
        target_forum = int(posted_forum) if (posted_forum or "").lstrip("-").isdigit() else -1
        db.session.add(
            Announcement(
                title=title[:200],
                user_id=current_user.id,
                forum_id=target_forum,
                start_date=start,
                end_date=end,
                pagetext=request.form.get("pagetext") or "",
            )
        )
        db.session.commit()
        flash("Record added", "success")
        return redirect(url_for("admin.announcements_page"))

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    later = (datetime.now(timezone.utc) + timedelta(days=31)).strftime("%Y-%m-%d")
    return render_template(
        "admin/announcement_form.html",
        mode="add",
        announcement=None,
        blocks=_announcement_forums(),
        selected_forum=forum_id,
        startdate=today,
        enddate=later,
    )


@bp.route("/announcements/edit/<int:announcement_id>", methods=["GET", "POST"])
def announcement_edit(announcement_id: int):
    instance = db.session.get(Announcement, announcement_id)
    if instance is None:
        abort(404)

    if request.method == "POST":
        instance.title = ((request.form.get("title") or "").strip() or "Announcement")[:200]
        instance.pagetext = request.form.get("pagetext") or ""
        instance.start_date = _parse_announcement_date(
            request.form.get("startdate"), instance.start_date
        )
        instance.end_date = _parse_announcement_date(request.form.get("enddate"), instance.end_date)
        posted_forum = request.form.get("forum_id")
        if (posted_forum or "").lstrip("-").isdigit():
            instance.forum_id = int(posted_forum)
        db.session.commit()
        flash("Record updated!", "success")
        return redirect(url_for("admin.announcements_page"))

    return render_template(
        "admin/announcement_form.html",
        mode="edit",
        announcement=instance,
        blocks=_announcement_forums(),
        selected_forum=instance.forum_id,
        startdate=instance.start_date.strftime("%Y-%m-%d %H:%M:%S"),
        enddate=instance.end_date.strftime("%Y-%m-%d %H:%M:%S"),
    )


@bp.route("/announcements/remove/<int:announcement_id>", methods=["GET", "POST"])
def announcement_remove(announcement_id: int):
    instance = db.session.get(Announcement, announcement_id)
    if instance is None:
        abort(404)

    if request.method == "POST":
        db.session.delete(instance)
        db.session.commit()
        flash("Deleted!", "success")
        return redirect(url_for("admin.announcements_page"))

    return render_template("admin/announcement_remove.html", announcement=instance)


@bp.get("/permissions")
def permissions_page():
    """照 vB admin/forumpermission.php?action=modify：按版块列出各个用户组。
    参考站里「分类」本身也是 forum 表里 parentid=-1 的一条记录，所以分类层也能
    单设权限并由子版块继承（列表里的蓝字行）。本站分类是独立表、没有继承链，
    因此分类层没有可设置对象，只列到版块层。
    """
    ensure_seed()
    groups = db.session.execute(
        select(UserGroup).order_by(UserGroup.title)
    ).scalars().all()
    categories = db.session.execute(
        select(Category).order_by(Category.position, Category.id)
    ).scalars().all()
    overrides = {
        (row.forum_id, row.usergroup_id): row
        for row in db.session.execute(select(ForumPermission)).scalars().all()
    }

    blocks = []
    for category in categories:
        forums = []
        for forum_obj in sorted(category.forums, key=lambda f: (f.position, f.id)):
            rows = []
            for group in groups:
                override = overrides.get((forum_obj.id, group.id))
                rows.append({"group": group, "custom": override is not None})
            forums.append({"forum": forum_obj, "rows": rows})
        blocks.append({"category": category, "forums": forums})

    return render_template("admin/permissions.html", blocks=blocks)


@bp.get("/permissions/edit")
def permission_edit():
    """照 vB admin/forumpermission.php?action=edit 的 16 项 Yes/No 表单。"""
    forumpermissionid = (request.args.get("forumpermissionid") or "").strip()
    override = None
    if forumpermissionid.isdigit():
        override = db.session.get(ForumPermission, int(forumpermissionid))
        if override is None:
            abort(404)
        forum_obj = db.session.get(Forum, override.forum_id)
        group = db.session.get(UserGroup, override.usergroup_id)
        values = {field: bool(getattr(override, field)) for field in PERMISSION_FIELDS}
        custom = True
    else:
        forum_id = (request.args.get("forumid") or "").strip()
        usergroup_id = (request.args.get("usergroupid") or "").strip()
        if not (forum_id.isdigit() and usergroup_id.isdigit()):
            abort(404)
        forum_obj = db.session.get(Forum, int(forum_id))
        group = db.session.get(UserGroup, int(usergroup_id))
        if forum_obj is None or group is None:
            abort(404)
        # 参考站 getpermissions(forumid, 1, usergroupid)：没有自定义记录时取用户组默认
        values = permissions_for_group(forum_obj.id, group.id)
        custom = False

    return render_template(
        "admin/permission_edit.html",
        forum=forum_obj,
        group=group,
        values=values,
        custom=custom,
        fields=PERMISSION_FIELDS,
        labels=PERMISSION_LABELS,
    )


@bp.post("/permissions/edit")
def permission_save():
    """照 vB forumpermission.php 的 doupdate 分支：Use usergroup default 会删掉自定义记录。"""
    useusergroup = request.form.get("useusergroup") == "1"
    forumpermissionid = (request.form.get("forumpermissionid") or "").strip()
    override = None
    if forumpermissionid.isdigit():
        override = db.session.get(ForumPermission, int(forumpermissionid))

    if useusergroup:
        if override is not None:
            db.session.delete(override)
            db.session.commit()
    else:
        if override is None:
            forum_id = (request.form.get("forumid") or "").strip()
            usergroup_id = (request.form.get("usergroupid") or "").strip()
            if not (forum_id.isdigit() and usergroup_id.isdigit()):
                abort(404)
            override = ForumPermission(
                forum_id=int(forum_id), usergroup_id=int(usergroup_id)
            )
            db.session.add(override)
        for field in PERMISSION_FIELDS:
            setattr(override, field, request.form.get(field) == "1")
        db.session.commit()

    flash("Record updated!", "success")
    return redirect(url_for("admin.permissions_page"))


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


def _purge_threads(thread_ids: list[int]) -> int:
    """彻底删主题：帖子、投票、订阅、评分、举报记录一起清掉（对应原版 deletethread）。"""
    removed = 0
    for tid in thread_ids:
        thread_obj = db.session.get(Thread, tid)
        if thread_obj is None:
            continue
        poll_obj = db.session.scalar(select(Poll).where(Poll.thread_id == tid))
        if poll_obj is not None:
            db.session.execute(delete(PollVote).where(PollVote.poll_id == poll_obj.id))
            db.session.delete(poll_obj)
        db.session.execute(delete(ThreadSubscription).where(ThreadSubscription.thread_id == tid))
        db.session.execute(delete(ThreadRating).where(ThreadRating.thread_id == tid))
        post_ids = db.session.scalars(select(Post.id).where(Post.thread_id == tid)).all()
        if post_ids:
            db.session.execute(delete(PostReport).where(PostReport.post_id.in_(post_ids)))
            db.session.execute(delete(Post).where(Post.thread_id == tid))
        db.session.delete(thread_obj)
        removed += 1
    db.session.commit()
    return removed


def _checked_ids(form, prefix: str) -> list[int]:
    """原版用 delete[threadid]=1/0 的成对单选按钮；这里取勾起 Yes 的那批 id。"""
    ids: list[int] = []
    for key, value in form.items():
        if key.startswith(prefix) and value == "1":
            tail = key[len(prefix):]
            if tail.isdigit():
                ids.append(int(tail))
    return ids


def _forum_label(forum_id: int) -> str:
    """原版确认页里的论坛说法：all forums / the "xxx" forum。"""
    if not forum_id or forum_id < 0:
        return "all forums"
    forum_obj = db.session.get(Forum, forum_id)
    return f'the "{forum_obj.name}" forum' if forum_obj else "all forums"


@bp.route("/threads/move", methods=["GET", "POST"])
def threads_move():
    """Threads & Posts → Mass Move（原版 thread.php 的 move / movedate / moveuser 系列）。"""
    forums = db.session.execute(
        select(Forum).order_by(Forum.position, Forum.id)
    ).scalars().all()
    categories = (
        db.session.execute(select(Category).order_by(Category.position, Category.id))
        .scalars()
        .all()
    )
    step = (request.form.get("step") or "").strip()

    if request.method == "GET" or not step:
        return render_template(
            "admin/thread_move.html", mode="form", forums=forums, categories=categories
        )

    days = request.form.get("daysmove", type=int) or 0
    forum_id = request.form.get("forumid", type=int) or -1
    dest_id = request.form.get("destforumid", type=int) or -1
    username = (request.form.get("username") or "").strip()

    def _scope(stmt):
        return stmt.where(Thread.forum_id == forum_id) if forum_id > 0 else stmt

    def _dest_forum():
        return db.session.get(Forum, dest_id) if dest_id > 0 else None

    def _form_page():
        return render_template(
            "admin/thread_move.html", mode="form", forums=forums, categories=categories
        )

    def _do_move(ids, forum_obj, message):
        moved = 0
        for tid in ids:
            thread_obj = db.session.get(Thread, tid)
            if thread_obj is not None:
                thread_obj.forum_id = forum_obj.id
                moved += 1
        db.session.commit()
        flash(
            f"{message} {moved} thread(s) moved. It is recommended that you update counters now.",
            "success",
        )

    if step == "by_date":
        if days <= 0:
            flash("Please enter an age of post to move", "error")
            return _form_page()
        if _dest_forum() is None:
            flash("Please choose a destination forum.", "error")
            return _form_page()
        return render_template(
            "admin/thread_move.html",
            mode="confirm_date",
            forums=forums,
            categories=categories,
            days=days,
            forum_id=forum_id,
            dest_id=dest_id,
            forum_label=_forum_label(forum_id),
        )

    if step == "date_select":
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        rows = db.session.execute(
            _scope(select(Thread).where(Thread.last_post_at <= cutoff)).order_by(
                Thread.last_post_at.desc()
            )
        ).scalars().all()
        return render_template(
            "admin/thread_move.html",
            mode="select_date",
            forums=forums,
            categories=categories,
            rows=rows,
            days=days,
            forum_id=forum_id,
            dest_id=dest_id,
        )

    if step == "date_all":
        forum_obj = _dest_forum()
        if forum_obj is None:
            flash("Please choose a destination forum.", "error")
            return redirect(url_for("admin.threads_move"))
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        ids = db.session.scalars(
            _scope(select(Thread.id).where(Thread.last_post_at <= cutoff))
        ).all()
        _do_move(list(ids), forum_obj, "Posts moved successfully!")
        return redirect(url_for("admin.threads_move"))

    if step == "date_do":
        forum_obj = _dest_forum()
        if forum_obj is None:
            flash("Please choose a destination forum.", "error")
            return redirect(url_for("admin.threads_move"))
        _do_move(_checked_ids(request.form, "move_"), forum_obj, "Posts moved successfully!")
        return redirect(url_for("admin.threads_move"))

    if step == "by_user":
        if not username:
            flash("Please enter a username to search for", "error")
            return _form_page()
        if _dest_forum() is None:
            flash("Please choose a destination forum.", "error")
            return _form_page()
        users = db.session.execute(
            select(User).where(User.username.ilike(f"%{username}%")).order_by(User.username)
        ).scalars().all()
        return render_template(
            "admin/thread_move.html",
            mode="confirm_user",
            forums=forums,
            categories=categories,
            users=users,
            username=username,
            forum_id=forum_id,
            dest_id=dest_id,
            forum_label=_forum_label(forum_id),
        )

    if step == "user_all":
        forum_obj = _dest_forum()
        if forum_obj is None:
            flash("Please choose a destination forum.", "error")
            return redirect(url_for("admin.threads_move"))
        user_obj = db.session.get(User, request.form.get("userid", type=int))
        if user_obj is None:
            flash("No such user found.", "error")
            return redirect(url_for("admin.threads_move"))
        ids = db.session.scalars(_scope(select(Thread.id).where(Thread.author_id == user_obj.id))).all()
        _do_move(list(ids), forum_obj, "Threads moved successfully!")
        return redirect(url_for("admin.threads_move"))

    if step == "user_select":
        user_obj = db.session.get(User, request.form.get("userid", type=int))
        if user_obj is None:
            flash("No such user found.", "error")
            return redirect(url_for("admin.threads_move"))
        rows = db.session.execute(
            _scope(select(Thread).where(Thread.author_id == user_obj.id)).order_by(
                Thread.last_post_at.desc()
            )
        ).scalars().all()
        return render_template(
            "admin/thread_move.html",
            mode="select_user",
            forums=forums,
            categories=categories,
            user_obj=user_obj,
            rows=rows,
            forum_id=forum_id,
            dest_id=dest_id,
        )

    if step == "user_do":
        forum_obj = _dest_forum()
        if forum_obj is None:
            flash("Please choose a destination forum.", "error")
            return redirect(url_for("admin.threads_move"))
        _do_move(_checked_ids(request.form, "movethread_"), forum_obj, "Threads moved successfully!")
        return redirect(url_for("admin.threads_move"))

    return redirect(url_for("admin.threads_move"))


@bp.route("/threads/prune", methods=["GET", "POST"])
def threads_prune():
    """Threads & Posts → Mass Prune（原版 thread.php 的 prune / prunedate / pruneuser 系列）。"""
    forums = db.session.execute(
        select(Forum).order_by(Forum.position, Forum.id)
    ).scalars().all()
    categories = (
        db.session.execute(select(Category).order_by(Category.position, Category.id))
        .scalars()
        .all()
    )
    step = (request.form.get("step") or "").strip()

    if request.method == "GET" or not step:
        return render_template("admin/thread_prune.html", mode="form", forums=forums, categories=categories)

    days = request.form.get("daysdelete", type=int) or 0
    forum_id = request.form.get("forumid", type=int) or -1
    username = (request.form.get("username") or "").strip()

    def _scope(stmt):
        return stmt.where(Thread.forum_id == forum_id) if forum_id > 0 else stmt

    if step == "by_date":
        if days <= 0:
            flash("Please enter an age of post to delete", "error")
            return render_template("admin/thread_prune.html", mode="form", forums=forums, categories=categories)
        return render_template(
            "admin/thread_prune.html",
            mode="confirm_date",
            forums=forums,
            categories=categories,
            days=days,
            forum_id=forum_id,
            forum_label=_forum_label(forum_id),
        )

    if step == "date_select":
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        rows = db.session.execute(
            _scope(select(Thread).where(Thread.last_post_at <= cutoff))
            .order_by(Thread.last_post_at.desc())
        ).scalars().all()
        return render_template(
            "admin/thread_prune.html",
            mode="select_date",
            forums=forums,
            categories=categories,
            rows=rows,
            days=days,
            forum_id=forum_id,
        )

    if step == "date_all":
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        ids = db.session.scalars(
            _scope(
                select(Thread.id).where(
                    Thread.last_post_at <= cutoff, Thread.is_sticky.is_(False)
                )
            )
        ).all()
        removed = _purge_threads(list(ids))
        flash(f"Posts deleted successfully! {removed} thread(s) deleted. It is recommended that you update counters now.", "success")
        return redirect(url_for("admin.threads_prune"))

    if step == "date_do":
        ids = _checked_ids(request.form, "delete_")
        removed = _purge_threads(ids)
        flash(f"Threads deleted successfully! {removed} thread(s) deleted. It is recommended that you update counters now.", "success")
        return redirect(url_for("admin.threads_prune"))

    if step == "by_user":
        if not username:
            flash("Please enter a username to search for", "error")
            return render_template("admin/thread_prune.html", mode="form", forums=forums, categories=categories)
        users = db.session.execute(
            select(User).where(User.username.ilike(f"%{username}%")).order_by(User.username)
        ).scalars().all()
        return render_template(
            "admin/thread_prune.html",
            mode="confirm_user",
            forums=forums,
            categories=categories,
            users=users,
            username=username,
            forum_id=forum_id,
            forum_label=_forum_label(forum_id),
        )

    if step == "user_all":
        user_obj = db.session.get(User, request.form.get("userid", type=int))
        if user_obj is None:
            flash("No such user found.", "error")
            return redirect(url_for("admin.threads_prune"))
        posts_stmt = select(Post).where(Post.author_id == user_obj.id)
        threads_stmt = select(Thread.id).where(Thread.author_id == user_obj.id)
        if forum_id > 0:
            posts_stmt = posts_stmt.join(Thread, Thread.id == Post.thread_id).where(
                Thread.forum_id == forum_id
            )
            threads_stmt = threads_stmt.where(Thread.forum_id == forum_id)
        posts = db.session.execute(posts_stmt).scalars().all()
        post_ids = [p.id for p in posts]
        if post_ids:
            db.session.execute(delete(PostReport).where(PostReport.post_id.in_(post_ids)))
            db.session.execute(delete(Post).where(Post.id.in_(post_ids)))
        removed = _purge_threads(list(db.session.scalars(threads_stmt).all()))
        flash(
            f"Posts deleted successfully! {len(post_ids)} post(s) and {removed} thread(s) deleted."
            " It is recommended that you update counters now.",
            "success",
        )
        return redirect(url_for("admin.threads_prune"))

    if step == "user_select":
        user_obj = db.session.get(User, request.form.get("userid", type=int))
        if user_obj is None:
            flash("No such user found.", "error")
            return redirect(url_for("admin.threads_prune"))
        threads_stmt = select(Thread).where(Thread.author_id == user_obj.id)
        posts_stmt = (
            select(Post)
            .join(Thread, Thread.id == Post.thread_id)
            .where(Post.author_id == user_obj.id)
        )
        if forum_id > 0:
            threads_stmt = threads_stmt.where(Thread.forum_id == forum_id)
            posts_stmt = posts_stmt.where(Thread.forum_id == forum_id)
        rows = db.session.execute(threads_stmt.order_by(Thread.last_post_at.desc())).scalars().all()
        posts = db.session.execute(
            posts_stmt.order_by(Post.thread_id.desc(), Post.created_at.desc())
        ).scalars().all()
        return render_template(
            "admin/thread_prune.html",
            mode="select_user",
            forums=forums,
            categories=categories,
            user_obj=user_obj,
            rows=rows,
            posts=posts,
            forum_id=forum_id,
        )

    if step == "user_do":
        user_obj = db.session.get(User, request.form.get("userid", type=int))
        if user_obj is None:
            flash("No such user found.", "error")
            return redirect(url_for("admin.threads_prune"))
        thread_ids = _checked_ids(request.form, "deletethread_")
        post_ids = _checked_ids(request.form, "deletepost_")
        if post_ids:
            db.session.execute(delete(PostReport).where(PostReport.post_id.in_(post_ids)))
            db.session.execute(delete(Post).where(Post.id.in_(post_ids)))
            db.session.commit()
        removed = _purge_threads(thread_ids)
        flash(
            f"Threads and posts deleted successfully! {len(post_ids)} post(s) and {removed} thread(s) deleted."
            " It is recommended that you update counters now.",
            "success",
        )
        return redirect(url_for("admin.threads_prune"))

    return redirect(url_for("admin.threads_prune"))


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
            deleted = _purge_threads(ids)
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
    try:
        limit_bytes = int(get_settings().get("avatarmaxsize") or 20000)
    except ValueError:
        limit_bytes = 20000
    if limit_bytes and size > limit_bytes:
        target.unlink(missing_ok=True)
        flash(f"图片超过 {limit_bytes // 1024 or 1} KB（后台「头像」组 avatarmaxsize）上限，已放弃。", "error")
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
