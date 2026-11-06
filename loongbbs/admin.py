"""Admin control panel: settings, forums, users, avatars, threads, stats."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import re
from html import escape as _html_escape
import socket

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    Response,
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
    BBCode,
    Attachment,
    Avatar,
    Category,
    Forum,
    ForumPermission,
    Icon,
    Smilie,
    PERMISSION_FIELDS,
    generate_password_hash,
    PERMISSION_LABELS,
    Poll,
    PollOption,
    PollVote,
    Post,
    OnlineSession,
    PostReport,
    PrivateMessage,
    Thread,
    ThreadRating,
    ThreadSubscription,
    User,
    UserGroup,
    UserGroupPermission,
    UserProfileField,
    UserTitle,
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
        {"label": "Add", "endpoint": "admin.forum_add"},
        {"label": "Modify", "endpoint": "admin.forums_page"},
        {"label": "Permissions", "endpoint": "admin.permissions_page"},
    ]},
    {"title": "Threads & Posts", "links": [
        {"label": "Mass Prune", "endpoint": "admin.threads_prune"},
        {"label": "Mass Move", "endpoint": "admin.threads_move"},
        {"label": "Unsubscribe Thread", "endpoint": "admin.threads_unsubscribe"},
        {"label": "Strip Poll", "endpoint": "admin.threads_strip_poll"},
        {"label": "Who Voted?", "endpoint": "admin.threads_votes"},
    ]},
    {"title": "Moderation", "links": [
        {"label": "Reported Posts", "endpoint": "admin.reports_page"},
        {"label": "New Posts", "endpoint": "admin.moderate_posts"},
        {"label": "New Attachments", "endpoint": "admin.moderate_attachments"},
    ]},
    {"title": "Users", "links": [
        {"label": "Add", "endpoint": "admin.user_add"},
        {"label": "Find", "endpoint": "admin.users_page"},
        {"label": "Move/Prune", "module": "Move/Prune Users"},
        {"label": "PM Statistics", "endpoint": "admin.users_pmstats"},
        {"label": "IP Addresses", "endpoint": "admin.users_ips"},
        {"label": "Referrals", "endpoint": "admin.users_referrals"},
        {"label": "Email Users", "endpoint": "admin.users_email"},
        {"label": "Build Mailing List", "endpoint": "admin.users_email_genlist"},
    ]},
    {"title": "User Titles", "links": [
        {"label": "Add", "endpoint": "admin.usertitles_add"},
        {"label": "Modify", "endpoint": "admin.usertitles"},
    ]},
    {"title": "User Profile Fields", "links": [
        {"label": "Add", "endpoint": "admin.profilefields_add"},
        {"label": "Modify", "endpoint": "admin.profilefields"},
    ]},
    {"title": "User Groups", "links": [
        {"label": "Add", "endpoint": "admin.usergroups_add"},
        {"label": "Modify", "endpoint": "admin.usergroups"},
        {"label": "Forum Permissions", "endpoint": "admin.permissions_page"},
    ]},
    {"title": "Avatars", "links": [
        {"label": "Add", "endpoint": "admin.avatars_add"},
        {"label": "Modify", "endpoint": "admin.avatars_page"},
        {"label": "Upload", "endpoint": "admin.avatars_upload"},
    ]},
    {"title": "Post Icons", "links": [
        {"label": "Add", "endpoint": "admin.icons_add"},
        {"label": "Modify", "endpoint": "admin.icons"},
        {"label": "Upload", "endpoint": "admin.icons_upload"},
    ]},
    {"title": "Smilies", "links": [
        {"label": "Add", "endpoint": "admin.smilies_add"},
        {"label": "Modify", "endpoint": "admin.smilies"},
        {"label": "Upload", "module": "Upload Smilies"},
    ]},
    {"title": "Custom vB Codes", "links": [
        {"label": "Add", "endpoint": "admin.bbcodes_add"},
        {"label": "Modify", "endpoint": "admin.bbcodes"},
    ]},
    {"title": "Import & Maintenance", "links": [
        {"label": "Back-up Database", "endpoint": "admin.backup_choose"},
        {"label": "Database Settings", "endpoint": "admin.dbsettings"},
        {"label": "BB Import Systems", "endpoint": "admin.bbimport"},
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


@bp.route("/threads/unsubscribe", methods=["GET", "POST"])
def threads_unsubscribe():
    """Threads & Posts → Unsubscribe Thread（原版 thread.php 的 unsubscribe 系列）。"""
    forums = db.session.execute(
        select(Forum).order_by(Forum.position, Forum.id)
    ).scalars().all()
    categories = (
        db.session.execute(select(Category).order_by(Category.position, Category.id))
        .scalars()
        .all()
    )
    step = (request.form.get("step") or "").strip()

    def _page():
        return render_template(
            "admin/thread_unsubscribe.html", mode="form", forums=forums, categories=categories
        )

    if request.method == "GET" or not step:
        return _page()

    if step == "specific":
        ids_text = (request.form.get("ids") or "").strip()
        if not ids_text:
            flash("No threads specified!", "error")
            return _page()
        thread_ids = [int(x) for x in re.split(r"\s+", ids_text) if x.isdigit()]
        if not thread_ids:
            flash("No threads specified!", "error")
            return _page()
        return _confirm_page(thread_ids)

    if step == "mass":
        days = request.form.get("daysprune", type=int) or 0
        forum_id = request.form.get("forumid", type=int) or -1
        stmt = select(Thread.id)
        if forum_id > 0:
            stmt = stmt.where(Thread.forum_id == forum_id)
        if days > 0:
            stmt = stmt.where(
                Thread.last_post_at <= datetime.now(timezone.utc) - timedelta(days=days)
            )
        thread_ids = list(db.session.scalars(stmt).all())
        if not thread_ids:
            flash("No threads matched your query!", "error")
            return _page()
        return _confirm_page(thread_ids)

    if step == "do":
        ids = [int(x) for x in re.split(r"[,\s]+", request.form.get("threadids") or "") if x.isdigit()]
        if not ids:
            flash("No threads specified!", "error")
            return _page()
        removed = db.session.execute(
            delete(ThreadSubscription).where(ThreadSubscription.thread_id.in_(ids))
        ).rowcount
        db.session.commit()
        flash(f"Threads unsubscribed ({removed} subscription record(s) deleted)", "success")
        return redirect(url_for("admin.threads_unsubscribe"))

    return _page()


def _confirm_page(thread_ids):
    """confirmunsubscribe：先数一下这些主题里到底有多少条订阅，再让人确认。"""
    total = db.session.scalar(
        select(func.count(ThreadSubscription.id)).where(
            ThreadSubscription.thread_id.in_(thread_ids)
        )
    ) or 0
    if total <= 0:
        flash("No thread subscriptions matched your conditions", "error")
        return redirect(url_for("admin.threads_unsubscribe"))
    return render_template(
        "admin/thread_unsubscribe.html",
        mode="confirm",
        ids_text=",".join(str(i) for i in thread_ids),
        total=total,
    )


def _pm_counts():
    """每个用户"存了多少条悄悄话"：本地一条 PM 一行，收件方与发件方各计一条。"""
    counts: dict[int, int] = {}
    for col in (PrivateMessage.recipient_id, PrivateMessage.sender_id):
        for uid, n in db.session.execute(
                select(col, func.count(PrivateMessage.id)).group_by(col)).all():
            counts[uid] = counts.get(uid, 0) + n
    return counts


def _yn(form, name: str, default: bool = False) -> bool:
    raw = form.get(name)
    if raw is None:
        return default
    return raw == "1"


def _ip_users(prefix: str, prev_uid: int, depth: int) -> list[dict]:
    """原版 doipaddress：按 IP 前缀找发过帖的用户，depth>0 时递归展开这些用户的其它 IP。"""
    nodes: list[dict] = []
    rows = db.session.execute(
        select(User.id, User.username)
        .join(Post, Post.author_id == User.id)
        .where(Post.ipaddress.like(f"{prefix}%"), User.id != prev_uid)
        .distinct().order_by(User.username)
    ).all()
    for uid, username in rows:
        node = {"kind": "user", "id": uid, "username": username, "children": []}
        if depth > 0:
            node["children"] = _ip_list(uid, prefix, depth - 1)
        nodes.append(node)
    return nodes


def _ip_list(uid: int, prev_ip: str, depth: int) -> list[dict]:
    """原版 douserid：列出该用户发帖用过的 IP，depth>0 时递归展开同 IP 的其它用户。"""
    nodes: list[dict] = []
    rows = db.session.execute(
        select(Post.ipaddress).where(Post.author_id == uid, Post.ipaddress != "",
                                     Post.ipaddress != prev_ip)
        .distinct().order_by(Post.ipaddress)
    ).all()
    for (ip,) in rows:
        try:
            host = socket.gethostbyaddr(ip)[0]
        except Exception:
            host = ip
        node = {"kind": "ip", "ip": ip, "host": host, "children": []}
        if depth > 0:
            node["children"] = _ip_users(ip, uid, depth - 1)
        nodes.append(node)
    return nodes


@bp.route("/users/ips", methods=["GET", "POST"])
def users_ips():
    """Users → IP Addresses：照原版 user.php 的 doipaddress / douserid / doips。"""
    ipaddress = (request.values.get("ipaddress") or "").strip()
    username = (request.values.get("username") or "").strip()
    uid = request.values.get("userid", type=int) or 0
    depth = request.values.get("depth", type=int) or 1
    # 原版：没带 depth 参数且 depth>2 时回落 1
    if depth > 2 and "depth" not in request.values:
        depth = 1
    depth = max(1, min(depth, 3))

    tree: list[dict] = []
    if username and not uid:
        found = db.session.scalar(select(User.id).where(User.username == username))
        uid = found or 0
    if ipaddress:
        tree += _ip_users(ipaddress, 0, depth - 1)
    if uid:
        tree += _ip_list(uid, "", depth - 1)

    return render_template("admin/users_ips.html", tree=tree, ipaddress=ipaddress,
                           username=username, depth=depth, uid=uid)


REF_DATE_FMT = "%m-%d-%Y %I:%M %p"


def _ref_parse_date(raw: str):
    """把 yyyy-mm-dd[ hh:mm:ss] 转成 datetime；空或非法返回 None。"""
    raw = (raw or "").strip()
    if not raw:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _ref_counts(startdate, enddate, referrerid=None):
    """按 user.referrerid 统计被推荐人数（原版 referrers / showreferrers 的那条 GROUP BY）。"""
    stmt = (select(User.referrerid, func.count(User.id))
            .where(User.referrerid != 0))
    if startdate is not None:
        stmt = stmt.where(User.joined_at >= startdate)
    if enddate is not None:
        stmt = stmt.where(User.joined_at <= enddate)
    if referrerid is not None:
        stmt = stmt.where(User.referrerid == referrerid)
    return db.session.execute(stmt.group_by(User.referrerid)).all()


_MAIL_LOG = Path(__file__).resolve().parent.parent / "logs" / "admin-email.log"


def _groups():
    return db.session.execute(select(UserGroup).order_by(UserGroup.title)).scalars().all()


def _mail_conditions(form, *, genlist: bool) -> list:
    """把原版 email.php 的 WHERE 串翻译成条件列表（本地缺列的项不参与）。"""
    conds = []
    pairs = [("ausername", User.username)]
    pairs.append(("email" if genlist else "aemail", User.email))
    pairs += [
        ("homepage", User.homepage),
        ("icq", User.icq),
        ("aim", User.aim),
        ("yahoo", User.yahoo),
        ("signature", User.signature),
        ("usertitle", User.usertitle),
    ]
    for name, column in pairs:
        raw = (form.get(name) or "").strip()
        if raw:
            conds.append(func.lower(column).like(f"%{raw.lower()}%"))

    group_raw = (form.get("usergroupid") or "").strip()
    if group_raw not in ("", "-1"):
        try:
            conds.append(User.usergroupid == int(group_raw))
        except ValueError:
            pass

    for name, column, op in (("joindateafter", User.joined_at, ">"),
                             ("joindatebefore", User.joined_at, "<"),
                             ("lastvisitafter", User.last_visit, ">"),
                             ("lastvisitbefore", User.last_visit, "<")):
        dt = _ref_parse_date(form.get(name) or "")
        if dt is not None:
            conds.append(column > dt if op == ">" else column < dt)

    # 原版用 user.posts 字段；本地没有该列，按 posts 表实时计数比较
    posts_count = (select(func.count(Post.id)).where(Post.author_id == User.id)
                   .correlate(User).scalar_subquery())
    lower = (form.get("postslower") or "").strip()
    upper = (form.get("postsupper") or "").strip()
    if lower.isdigit():
        conds.append(posts_count > int(lower))
    if upper.isdigit():
        conds.append(posts_count < int(upper))
    return conds


def _mail_targets(form, *, genlist: bool):
    # 原版所有查询都追加 adminemail=1（用户同意接收管理员邮件），本地对应 allowmail
    conds = _mail_conditions(form, genlist=genlist)
    stmt = select(User).where(*conds, User.allowmail.is_(True))
    return db.session.execute(stmt.order_by(User.id.desc())).scalars().all()


@bp.route("/email", methods=["GET", "POST"])
def users_email():
    """Users → Email Users：照原版 email.php 的 start / dosendmail / donext。"""
    if request.method == "GET":
        return render_template("admin/email.html", mode="start",
                               from_addr=get_settings().get("webmasteremail", ""),
                               groups=_groups())

    form = request.form
    perpage = request.form.get("perpage", type=int) or 500
    startat = request.form.get("startat", type=int) or 0
    test = (form.get("test") or "") == "1"
    subject = form.get("subject") or ""
    message = form.get("message") or ""
    sender = form.get("from") or get_settings().get("webmasteremail", "")

    targets = _mail_targets(form, genlist=False)
    if not targets:
        return render_template("admin/email.html", mode="result", no_match=True)

    chunk = targets[startat:startat + perpage]
    page = startat // perpage + 1
    totalpages = max(1, -(-len(targets) // perpage))
    log: list[str] = []
    log.append(f"Emailing users. Page {page}/{totalpages} ({len(targets)} users total).")
    for u in chunk:
        body = (message.replace("$email", u.email)
                       .replace("$username", u.username)
                       .replace("$userid", str(u.id)))
        log.append(f"{u.id} - {u.username} .... ")
        if test:
            log.append("testing ... ")
        else:
            _MAIL_LOG.parent.mkdir(parents=True, exist_ok=True)
            with _MAIL_LOG.open("a", encoding="utf-8") as fh:
                fh.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] to={u.email} from={sender} "
                         f"subject={subject}\n{body}\n---\n")
            log.append("sending ... ")
        log.append("ok")

    hidden = {k: v for k, v in form.items() if k not in ("_csrf", "action")}
    next_page = page + 1 if page < totalpages else None
    return render_template("admin/email.html", mode="result", log=log,
                           next_page=next_page, hidden=hidden,
                           startat=startat + perpage, perpage=perpage)


@bp.route("/email/genlist", methods=["GET", "POST"])
def users_email_genlist():
    """Users → Build Mailing List：照原版 email.php 的 genlist / makelist。"""
    if request.method == "GET":
        return render_template("admin/email.html", mode="genlist", groups=_groups())

    septext = request.form.get("septext")
    if septext is None:
        septext = " "
    targets = _mail_targets(request.form, genlist=True)
    text = "".join(u.email + septext for u in targets)
    return Response(text, mimetype="text/plain; charset=utf-8")


@bp.route("/users/referrals", methods=["GET", "POST"])
def users_referrals():
    """Users → Referrals：照原版 user.php 的 referrers / showreferrers。"""
    if request.method == "GET":
        today = datetime.now()
        start_default = (today - timedelta(days=31)).strftime("%Y-%m-%d")
        end_default = today.strftime("%Y-%m-%d")
        return render_template("admin/referrals.html",
                               startdate=request.args.get("startdate", start_default),
                               enddate=request.args.get("enddate", end_default))

    start_raw = request.form.get("startdate") or ""
    end_raw = request.form.get("enddate") or ""
    startdate = _ref_parse_date(start_raw)
    enddate = _ref_parse_date(end_raw)
    # 原版只在两个日期都填了才加时间条件
    if not (startdate and enddate):
        startdate = enddate = None

    rows = []
    for referrerid, cnt in sorted(_ref_counts(startdate, enddate),
                                  key=lambda kv: (-kv[1], kv[0])):
        name = db.session.scalar(select(User.username).where(User.id == referrerid))
        rows.append({"id": referrerid, "username": name or f"(id {referrerid})", "count": cnt})

    return render_template("admin/referrals.html", mode="result", rows=rows,
                           startdate=start_raw, enddate=end_raw,
                           startdate_norm=start_raw, enddate_norm=end_raw)


@bp.route("/users/referrals/detail")
def users_referrals_detail():
    """Users → Referrals → 某个推荐人推荐了谁（原版 showreferrals）。"""
    referrerid = request.args.get("referrerid", type=int) or 0
    start_raw = request.args.get("startdate") or ""
    end_raw = request.args.get("enddate") or ""
    startdate = _ref_parse_date(start_raw)
    enddate = _ref_parse_date(end_raw)
    if not (startdate and enddate):
        startdate = enddate = None

    referrer = db.session.get(User, referrerid) if referrerid else None
    stmt = select(User).where(User.referrerid == referrerid) if referrerid else select(User).where(User.id == 0)
    if startdate is not None:
        stmt = stmt.where(User.joined_at >= startdate)
    if enddate is not None:
        stmt = stmt.where(User.joined_at <= enddate)
    members = db.session.execute(stmt.order_by(User.joined_at)).scalars().all()

    counts = dict(db.session.execute(
        select(Post.author_id, func.count(Post.id)).group_by(Post.author_id)).all())
    rows = [{
        "id": u.id,
        "username": u.username,
        "posts": counts.get(u.id, 0),
        "email": u.email,
        "joined": u.joined_at.strftime(REF_DATE_FMT) if u.joined_at else "",
        "last_visit": u.last_visit.strftime(REF_DATE_FMT) if u.last_visit else "",
    } for u in members]

    return render_template("admin/referrals.html", mode="detail", rows=rows,
                           referrer=referrer, referrerid=referrerid,
                           startdate=start_raw, enddate=end_raw)


GROUP_FORM_GROUPS = (
    ("", ("showgroup",)),
    ("Viewing Permissions", ("canview", "canviewmembers", "canviewothers", "cangetattachment")),
    ("Miscellaneous Permissions", ("cansearch", "canemail", "canmodifyprofile")),
    ("Posting Permissions", ("canpostnew", "canreplyown", "canreplyothers",
                             "canthreadrate", "canpostattachment")),
    ("Post/Thread Editing Permissions", ("caneditpost", "candeletepost", "canmove",
                                         "canopenclose", "candeletethread")),
    ("Poll Permissions", ("canpostpoll", "canvote")),
    ("Private Messaging Permissions", ("canusepm", "cantrackpm", "candenypmreceipts")),
    ("Calendar Permissions", ("canpublicevent", "canpublicedit")),
    ("Who's Online Permissions", ("canwhosonline", "canwhosonlineip")),
    ("Adminstrative Permissions", ("ismoderator", "cancontrolpanel")),
)

GROUP_FORM_LABELS = {
    "showgroup": "Viewable on Show Groups?",
    "canview": "Can view board",
    "canviewmembers": "Can view members info (including other&#39;s profiles and members list)",
    "canviewothers": "Can view others&#39; threads",
    "cangetattachment": "Can download attachments",
    "cansearch": "Can search",
    "canemail": "Can use &#39;email to friend&#39; feature",
    "canmodifyprofile": "Can modify profile",
    "canpostnew": "Can post new threads",
    "canreplyown": "Can reply to own threads",
    "canreplyothers": "Can reply to other&#39;s threads",
    "canthreadrate": "Can Rate threads if thread rating is enabled in the forum?",
    "canpostattachment": "Can post attachments",
    "caneditpost": "Can edit own posts",
    "candeletepost": "Can delete own posts",
    "canmove": "Can move own threads to other forums",
    "canopenclose": "Can open / close own threads",
    "candeletethread": "Can delete own threads by deleting the first post",
    "canpostpoll": "Can post polls",
    "canvote": "Can vote on polls",
    "canusepm": "Can use Private Messaging",
    "cantrackpm": "Can Use Message Tracking?",
    "candenypmreceipts": "Can Deny Private Message Read Receipt Request?",
    "canpublicevent": "Can post Public events on Calendar",
    "canpublicedit": "Can edit other&#39;s Public events on Calendar",
    "canwhosonline": "Can View Who&#39;s Online",
    "canwhosonlineip": "Can View IP Addresses on Who&#39;s Online",
    "ismoderator": "Is Super Moderator",
    "cancontrolpanel": "Can access control panel",
}

# 原版 usergroup.php add 表单里 makeyesnocode 的默认值
GROUP_FORM_DEFAULTS = {
    "showgroup": True, "canview": True, "canviewmembers": True, "canviewothers": True,
    "cangetattachment": True, "cansearch": True, "canemail": False, "canmodifyprofile": True,
    "canpostnew": False, "canreplyown": False, "canreplyothers": False, "canthreadrate": True,
    "canpostattachment": True, "caneditpost": False, "candeletepost": False, "canmove": False,
    "canopenclose": False, "candeletethread": False, "canpostpoll": True, "canvote": True,
    "canusepm": True, "cantrackpm": False, "candenypmreceipts": False, "canpublicevent": False,
    "canpublicedit": False, "canwhosonline": True, "canwhosonlineip": False,
    "ismoderator": False, "cancontrolpanel": False,
}


def _group_perms(group_id: int) -> dict:
    row = db.session.get(UserGroupPermission, group_id)
    if row is None:
        return dict(GROUP_FORM_DEFAULTS)
    return {name: bool(getattr(row, name)) for name in GROUP_FORM_DEFAULTS}


def _group_form_groups() -> list:
    return [(title, [(name, GROUP_FORM_LABELS[name]) for name in names])
            for title, names in GROUP_FORM_GROUPS]


ICONS_STATIC = None


def _icons_dir() -> Path:
    return Path(current_app.static_folder) / "images" / "icons"


def _icon_src(iconpath: str) -> str:
    """原版是 ../{iconpath}（相对后台目录）；本地静态目录对应 /static/{iconpath}。"""
    p = iconpath.replace("{imagesfolder}", "images")
    if p.startswith("http://") or p.startswith("/"):
        return p
    return "/static/" + p.lstrip("./")


def _icons_page(startpage: int, perpage: int):
    total = db.session.scalar(select(func.count(Icon.id))) or 0
    if startpage < 1:
        startpage = 1
    if perpage < 1:
        perpage = 20
    numpages = max(1, (total + perpage - 1) // perpage)
    if startpage > numpages:
        startpage = numpages
    rows = db.session.execute(
        select(Icon).order_by(Icon.title).offset((startpage - 1) * perpage).limit(perpage)
    ).scalars().all()
    sicon = (startpage - 1) * perpage + 1
    eicon = min(total, startpage * perpage)
    return rows, total, startpage, perpage, numpages, sicon, eicon


@bp.route("/icons")
def icons():
    """Post Icons → Modify：照原版 icon.php 的 modify。"""
    startpage = request.args.get("startpage", type=int) or 1
    perpage = request.args.get("perpage", type=int) or 20
    rows, total, startpage, perpage, numpages, sicon, eicon = _icons_page(startpage, perpage)
    return render_template("admin/icons.html", mode="list", rows=rows, total=total,
                           startpage=startpage, perpage=perpage, numpages=numpages,
                           sicon=sicon, eicon=eicon, icon_src=_icon_src)


@bp.route("/icons/add", methods=["GET", "POST"])
def icons_add():
    """Post Icons → Add：原版 add（单条）/ insert（保存单条）。"""
    if request.method == "GET":
        return render_template("admin/icons.html", mode="add")
    form = request.form
    db.session.add(Icon(title=(form.get("title") or "").strip(),
                        iconpath=(form.get("iconpath") or "").strip()))
    db.session.commit()
    flash("Record added", "success")
    return redirect(url_for("admin.icons"))


@bp.route("/icons/multiple", methods=["GET", "POST"])
def icons_multiple():
    """Add multiple icons：原版 insertmultiple（扫目录挑图）/ domultiple（批量入库）。"""
    if request.method == "POST":
        iconpath = (request.form.get("iconpath") or "images/icons").strip().rstrip("/")
        uses = request.form.getlist("iconuse")
        titles = request.form
        count = 0
        for name in uses:
            db.session.add(Icon(title=(titles.get("icontitle[%s]" % name) or "").strip(),
                                iconpath=f"{iconpath}/{name}"))
            count += 1
        db.session.commit()
        if count == 0:
            return render_template("admin/icons.html", mode="multiple_empty")
        flash(f"Record added", "success")
        return redirect(url_for("admin.icons"))

    iconpath = (request.args.get("iconpath") or "images/icons").strip().rstrip("/")
    startpage = request.args.get("startpage", type=int) or 1
    iconsperpage = request.args.get("iconsperpage", type=int) or 10
    if startpage < 1:
        startpage = 1
    if iconsperpage < 1:
        iconsperpage = 10
    folder = _icons_dir()
    existing = {r.iconpath for r in db.session.execute(select(Icon)).scalars().all()}
    names = []
    if folder.is_dir():
        for f in sorted(folder.iterdir()):
            if not f.is_file():
                continue
            if f.suffix.lower() not in (".gif", ".bmp", ".jpg", ".jpeg", ".png"):
                continue
            rel = f"{iconpath}/{f.name}"
            if rel in existing:
                continue
            names.append(f.name)
    numpages = max(1, (len(names) + iconsperpage - 1) // iconsperpage)
    if startpage > numpages:
        startpage = numpages
    chunk = names[(startpage - 1) * iconsperpage:startpage * iconsperpage]
    return render_template("admin/icons.html", mode="multiple", names=chunk, iconpath=iconpath,
                           startpage=startpage, iconsperpage=iconsperpage, numpages=numpages,
                           total=len(names), folder_missing=not folder.is_dir(),
                           icon_src=_icon_src)


@bp.route("/icons/edit", methods=["GET", "POST"])
def icons_edit():
    """Post Icons 编辑：原版 edit / doupdate。"""
    iid = request.values.get("iconid", type=int) or 0
    row = db.session.get(Icon, iid) if iid else None
    if row is None:
        flash("Record not found", "error")
        return redirect(url_for("admin.icons"))
    if request.method == "GET":
        return render_template("admin/icons.html", mode="edit", row=row,
                               perpage=request.args.get("perpage", type=int) or 20,
                               startpage=request.args.get("startpage", type=int) or 1)
    row.title = (request.form.get("title") or "").strip()
    row.iconpath = (request.form.get("iconpath") or "").strip()
    db.session.commit()
    flash("Record updated!", "success")
    return redirect(url_for("admin.icons", startpage=request.form.get("startpage", type=int) or 1,
                            perpage=request.form.get("perpage", type=int) or 20))


@bp.route("/icons/remove", methods=["GET", "POST"])
def icons_remove():
    """Post Icons 删除：原版 remove / kill。"""
    iid = request.values.get("iconid", type=int) or 0
    row = db.session.get(Icon, iid) if iid else None
    if row is None:
        flash("Record not found", "error")
        return redirect(url_for("admin.icons"))
    if request.method == "GET":
        return render_template("admin/icons.html", mode="remove", row=row,
                               perpage=request.args.get("perpage", type=int) or 20,
                               startpage=request.args.get("startpage", type=int) or 1)
    db.session.execute(delete(Icon).where(Icon.id == row.id))
    db.session.commit()
    flash("Deleted! & thread/posts with that icon have been updated.", "success")
    return redirect(url_for("admin.icons", startpage=request.form.get("startpage", type=int) or 1,
                            perpage=request.form.get("perpage", type=int) or 20))


@bp.route("/icons/upload", methods=["GET", "POST"])
def icons_upload():
    """Post Icons → Upload：原版 upload / doupload（存盘后按单条插入）。"""
    if request.method == "GET":
        return render_template("admin/icons.html", mode="upload")
    iconfile = request.files.get("iconfile")
    title = (request.form.get("title") or "").strip()
    iconpath = (request.form.get("iconpath") or "images/icons").strip().rstrip("/")
    if not iconfile or not iconfile.filename:
        flash("No file uploaded", "error")
        return redirect(url_for("admin.icons_upload"))
    dest_dir = _icons_dir()
    dest_dir.mkdir(parents=True, exist_ok=True)
    name = Path(iconfile.filename).name
    iconfile.save(dest_dir / name)
    db.session.add(Icon(title=title, iconpath=f"{iconpath}/{name}"))
    db.session.commit()
    flash("Icon successfuly uploaded", "success")
    return redirect(url_for("admin.icons"))


def _smilies_dir() -> Path:
    return Path(current_app.static_folder) / "images" / "smilies"


def _smilies_page(startpage: int, perpage: int):
    total = db.session.scalar(select(func.count(Smilie.id))) or 0
    if startpage < 1:
        startpage = 1
    if perpage < 1:
        perpage = 15
    numpages = max(1, (total + perpage - 1) // perpage)
    if startpage > numpages:
        startpage = numpages
    rows = db.session.execute(
        select(Smilie).order_by(Smilie.title).offset((startpage - 1) * perpage).limit(perpage)
    ).scalars().all()
    sicon = (startpage - 1) * perpage + 1
    eicon = min(total, startpage * perpage)
    return rows, total, startpage, perpage, numpages, sicon, eicon


@bp.route("/smilies")
def smilies():
    """Smilies → Modify：照原版 smilie.php 的 modify。"""
    startpage = request.args.get("startpage", type=int) or 1
    perpage = request.values.get("perpage", type=int) or 15
    rows, total, startpage, perpage, numpages, sicon, eicon = _smilies_page(startpage, perpage)
    return render_template("admin/smilies.html", mode="list", rows=rows, total=total,
                           startpage=startpage, perpage=perpage, numpages=numpages,
                           sicon=sicon, eicon=eicon, icon_src=_icon_src)


@bp.route("/smilies/add", methods=["GET", "POST"])
def smilies_add():
    """Smilies → Add：原版 add（单条）/ insert（保存单条）。"""
    if request.method == "GET":
        return render_template("admin/smilies.html", mode="add")
    form = request.form
    db.session.add(Smilie(title=(form.get("title") or "").strip(),
                          smilietext=(form.get("smilietext") or ""),
                          smiliepath=(form.get("smiliepath") or "").strip()))
    db.session.commit()
    flash("Record added", "success")
    return redirect(url_for("admin.smilies"))


@bp.route("/smilies/multiple", methods=["GET", "POST"])
def smilies_multiple():
    """Add multiple smilies：原版 insertmultiple（扫目录）/ domultiple（批量入库）。"""
    if request.method == "POST":
        smiliepath = (request.form.get("smiliepath") or "images/smilies").strip().rstrip("/")
        used = request.form.getlist("smilieuse")
        count = 0
        for name in used:
            db.session.add(Smilie(
                title=(request.form.get("smilietitle[%s]" % name) or "").strip(),
                smilietext=(request.form.get("smilietext[%s]" % name) or ""),
                smiliepath=f"{smiliepath}/{name}"))
            count += 1
        db.session.commit()
        if count == 0:
            return render_template("admin/smilies.html", mode="multiple_empty")
        flash("Record added", "success")
        return redirect(url_for("admin.smilies"))

    smiliepath = (request.args.get("smiliepath") or "images/smilies").strip().rstrip("/")
    startpage = request.args.get("startpage", type=int) or 1
    iconsperpage = request.args.get("iconsperpage", type=int) or 10
    if startpage < 1:
        startpage = 1
    if iconsperpage < 1:
        iconsperpage = 10
    folder = _smilies_dir()
    existing = {r.smiliepath for r in db.session.execute(select(Smilie)).scalars().all()}
    names = []
    if folder.is_dir():
        for f in sorted(folder.iterdir()):
            if not f.is_file():
                continue
            if f.suffix.lower() not in (".gif", ".bmp", ".jpg", ".jpeg", ".png"):
                continue
            if f"{smiliepath}/{f.name}" in existing:
                continue
            names.append(f.name)
    numpages = max(1, (len(names) + iconsperpage - 1) // iconsperpage)
    if startpage > numpages:
        startpage = numpages
    chunk = names[(startpage - 1) * iconsperpage:startpage * iconsperpage]
    return render_template("admin/smilies.html", mode="multiple", names=chunk,
                           smiliepath=smiliepath, startpage=startpage,
                           iconsperpage=iconsperpage, numpages=numpages,
                           total=len(names), folder_missing=not folder.is_dir(),
                           icon_src=_icon_src)


@bp.route("/smilies/edit", methods=["GET", "POST"])
def smilies_edit():
    """Smilies 编辑：原版 edit / doupdate。"""
    sid = request.values.get("smilieid", type=int) or 0
    row = db.session.get(Smilie, sid) if sid else None
    if row is None:
        flash("Record not found", "error")
        return redirect(url_for("admin.smilies"))
    if request.method == "GET":
        return render_template("admin/smilies.html", mode="edit", row=row,
                               perpage=request.args.get("perpage", type=int) or 15,
                               startpage=request.args.get("startpage", type=int) or 1)
    row.title = (request.form.get("title") or "").strip()
    row.smilietext = request.form.get("smilietext") or ""
    row.smiliepath = (request.form.get("smiliepath") or "").strip()
    db.session.commit()
    flash("Record updated!", "success")
    return redirect(url_for("admin.smilies", startpage=request.form.get("startpage", type=int) or 1,
                            perpage=request.form.get("perpage", type=int) or 15))


@bp.route("/smilies/remove", methods=["GET", "POST"])
def smilies_remove():
    """Smilies 删除：原版 remove / kill。"""
    sid = request.values.get("smilieid", type=int) or 0
    row = db.session.get(Smilie, sid) if sid else None
    if row is None:
        flash("Record not found", "error")
        return redirect(url_for("admin.smilies"))
    if request.method == "GET":
        return render_template("admin/smilies.html", mode="remove", row=row,
                               perpage=request.args.get("perpage", type=int) or 15,
                               startpage=request.args.get("startpage", type=int) or 1)
    db.session.execute(delete(Smilie).where(Smilie.id == row.id))
    db.session.commit()
    flash("Deleted!", "success")
    return redirect(url_for("admin.smilies", startpage=request.form.get("startpage", type=int) or 1,
                            perpage=request.form.get("perpage", type=int) or 15))


@bp.route("/smilies/upload", methods=["GET", "POST"])
def smilies_upload():
    """Smilies → Upload：原版 upload / doupload（存盘后按单条插入）。"""
    if request.method == "GET":
        return render_template("admin/smilies.html", mode="upload")
    iconfile = request.files.get("smiliefile")
    title = (request.form.get("title") or "").strip()
    smilietext = request.form.get("smilietext") or ""
    smiliepath = (request.form.get("smiliepath") or "images/smilies").strip().rstrip("/")
    if not iconfile or not iconfile.filename:
        flash("No file uploaded", "error")
        return redirect(url_for("admin.smilies_upload"))
    dest_dir = _smilies_dir()
    dest_dir.mkdir(parents=True, exist_ok=True)
    name = Path(iconfile.filename).name
    iconfile.save(dest_dir / name)
    db.session.add(Smilie(title=title, smilietext=smilietext, smiliepath=f"{smiliepath}/{name}"))
    db.session.commit()
    flash("Smilie successfuly uploaded", "success")
    return redirect(url_for("admin.smilies"))


_BB_SINGLE = r"\[(%s)\](.*?)\[/(%s)\]"
_BB_DOUBLE = r"\[(%s)=(['\"]?)([^\"']*)\2\](.*?)\[/(%s)\]"


def _bbcode_pattern(tag: str, twoparams: int):
    """照原版 bbcode.php 的 $singleRegex / $doubleRegex 构造（/siU = 忽略大小写 + 非贪婪）。"""
    if twoparams:
        return re.compile(_BB_DOUBLE % (tag, tag), re.IGNORECASE | re.DOTALL)
    return re.compile(_BB_SINGLE % (tag, tag), re.IGNORECASE | re.DOTALL)


def _bbcode_html(tag: str, replacement: str, twoparams: int, text: str) -> str:
    """把 replacement 里的 \\N 反引用换成实际捕获组（\4/\7 = 正文，\5 = 选项）。"""
    html = replacement
    repl = (lambda m: html.replace("\\7", m.group(4)).replace("\\5", m.group(3))
            .replace("\\4", m.group(4))) if twoparams else (lambda m: html.replace("\\4", m.group(2)))
    return _bbcode_pattern(tag, twoparams).sub(repl, text) if text else text


def _apply_bbcodes(text: str) -> str:
    rows = db.session.execute(select(BBCode)).scalars().all()
    out = text
    for row in rows:
        out = _bbcode_html(row.bbcodetag, row.bbcodereplacement, row.twoparams, out)
    return out


def _sqlite_tables() -> list:
    """等价原版 SHOW tables：列出本地 sqlite 库里的用户表。"""
    rows = db.session.execute(
        db.text("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
    ).all()
    return [r[0] for r in rows]


def _sqlite_dump(tables: list) -> str:
    """生成 sqlite 的 SQL dump（表结构 + INSERT），等价原版 sqldumptable/dump_header。"""
    import sqlite3

    uri = current_app.config["SQLALCHEMY_DATABASE_URI"].replace("sqlite:///", "", 1)
    path = Path(uri) if Path(uri).is_absolute() else Path(current_app.root_path).parent / uri
    conn = sqlite3.connect(str(path))
    out = ["-- vBulletin Next database dump", "-- SQLite format", ""]
    for name in tables:
        row = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone()
        if not row:
            continue
        out.append(f"DROP TABLE IF EXISTS {name};")
        out.append(f"{row[0]};")
        cols = [c[1] for c in conn.execute(f"PRAGMA table_info({name})").fetchall()]
        for rec in conn.execute(f"SELECT * FROM {name}").fetchall():
            values = []
            for v in rec:
                if v is None:
                    values.append("NULL")
                elif isinstance(v, (int, float)):
                    values.append(str(v))
                else:
                    values.append("'" + str(v).replace("'", "''") + "'")
            out.append(f"INSERT INTO {name} ({', '.join(cols)}) VALUES ({', '.join(values)});")
        out.append("")
    conn.close()
    return "\n".join(out)


def _search_backup_path(raw: str):
    """只允许写到应用根目录内的相对路径（原版允许任意路径；这里做安全收敛）。"""
    base = Path(current_app.root_path).parent
    raw = (raw or "").strip().lstrip("./")
    if not raw:
        return None
    candidate = (base / raw).resolve()
    if base.resolve() not in candidate.parents:
        return None
    return candidate


def _db_migrate(source_uri: str, target_uri: str, recreate: bool) -> list:
    """把当前库的表结构与数据整体复制到目标库，等价原版 "Copy data to this database and switch"。"""
    from sqlalchemy import create_engine, MetaData

    details = []
    src = create_engine(source_uri)
    dst = create_engine(target_uri)
    with src.connect() as sconn, dst.begin() as dconn:
        names = [r[0] for r in sconn.execute(db.text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )).all()] if source_uri.startswith("sqlite") else None
        if names is None:
            meta = MetaData()
            meta.reflect(bind=src)
            names = list(meta.tables.keys())
        meta = MetaData()
        meta.reflect(bind=src, only=names)
        if recreate:
            meta.drop_all(bind=dst, checkfirst=True)
            details.append("目标库里同名的表已删除后重建。")
        meta.create_all(bind=dst, checkfirst=True)
        total = 0
        for name in names:
            table = meta.tables[name]
            rows = sconn.execute(table.select()).mappings().all()
            if rows:
                dconn.execute(table.insert(), [dict(r) for r in rows])
                total += len(rows)
        dconn.commit()
    src.dispose()
    dst.dispose()
    details.append(f"已复制 {len(names)} 张表、{total} 行数据到目标库。")
    return details


DB_SETTING_KEYS = ("dbservertype", "servername", "dbport", "dbschema", "dbusername",
                   "dbpassword", "dbname", "usepconnect")


def _env_local_path() -> Path:
    return Path(current_app.root_path).parent / ".env.local"


def _db_uri_parts(uri: str) -> dict:
    """把 SQLALCHEMY_DATABASE_URI 拆成原版表单那几个字段。"""
    parts = dict.fromkeys(DB_SETTING_KEYS, "")
    if uri.startswith("sqlite"):
        parts["dbservertype"] = "sqlite"
        parts["dbname"] = uri.split("///", 1)[-1] if "///" in uri else uri
        parts["usepconnect"] = "0"
        return parts
    import urllib.parse as up

    parsed = up.urlparse(uri)
    scheme = (parsed.scheme or "").split("+")[0]
    parts["dbservertype"] = "pgsql" if scheme in ("postgresql", "postgres") else (scheme or "mysql")
    parts["servername"] = parsed.hostname or ""
    parts["dbport"] = str(parsed.port or "")
    parts["dbusername"] = up.unquote(parsed.username or "")
    parts["dbpassword"] = up.unquote(parsed.password or "")
    parts["dbname"] = (parsed.path or "").lstrip("/")
    schema = up.parse_qs(parsed.query).get("options", [""])[0]
    parts["dbschema"] = schema.split("-c")[-1].strip() if schema else ""
    parts["usepconnect"] = "1" if "pool_pre_ping" in uri else "0"
    return parts


def _db_uri_build(v: dict) -> str:
    import urllib.parse as up

    if v["dbservertype"] == "sqlite":
        # SQLite 相对路径会被 SQLAlchemy 按 instance 目录解析，这里统一成绝对路径
        raw = v["dbname"] or ""
        target = Path(raw) if Path(raw).is_absolute() else Path(current_app.root_path).parent / raw
        return "sqlite:///" + str(target).replace("\\", "/")
    user = up.quote(v["dbusername"] or "", safe="")
    pwd = up.quote(v["dbpassword"] or "", safe="")
    auth = f"{user}:{pwd}@" if (user or pwd) else ""
    host = v["servername"] or "127.0.0.1"
    port = f":{v['dbport']}" if v["dbport"] else ""
    base = "postgresql" if v["dbservertype"] == "pgsql" else "mysql+pymysql"
    uri = f"{base}://{auth}{host}{port}/{v['dbname'] or ''}"
    if v["dbservertype"] == "pgsql" and v["dbschema"]:
        uri += f"?options=-csearch_path%3D{v['dbschema']}"
    return uri


def _db_test(uri: str):
    """返回 (ok, details list)，等价原版 dbsettings_test_connection。"""
    import importlib.util as ilu

    details = []
    if uri.startswith("sqlite"):
        path = Path(uri.split("///", 1)[-1])
        if not path.is_absolute():
            path = Path(current_app.root_path).parent / path
        if not path.parent.exists():
            details.append(f"SQLite 目录不存在：{path.parent}")
            return False, details
        try:
            import sqlite3
            conn = sqlite3.connect(str(path))
            n = conn.execute("SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
            conn.close()
        except Exception as exc:  # pragma: no cover - 连接异常信息给管理员看
            details.append(f"SQLite 连接失败：{exc}")
            return False, details
        details.append(f"已连接 SQLite 文件 {path}。")
        details.append(f"该库下现有 {n} 张表。")
        return True, details
    if uri.startswith("postgresql"):
        if not ilu.find_spec("psycopg2"):
            details.append("Python 未安装 psycopg2 驱动，无法连接 PostgreSQL。")
            return False, details
    else:
        if not (ilu.find_spec("pymysql") or ilu.find_spec("MySQLdb")):
            details.append("Python 未安装 MySQL 驱动（pymysql / MySQLdb），无法连接 MySQL/MariaDB。")
            return False, details
    try:
        from sqlalchemy import create_engine, text

        engine = create_engine(uri, pool_pre_ping=True)
        with engine.connect() as conn:
            version = conn.execute(text("SELECT version()")).scalar()
            tables = conn.execute(text("SELECT count(*) FROM information_schema.tables "
                                       "WHERE table_schema NOT IN ('pg_catalog','information_schema')")).scalar()
        details.append(f"已连接：{version}")
        details.append(f"该库下现有 {tables} 张表。")
        return True, details
    except Exception as exc:
        details.append(f"连接失败：{exc}")
        return False, details


@bp.route("/bbimport", methods=["GET", "POST"])
def bbimport():
    """Import & Maintenance → BB Import Systems：照原版 bbimport.php 的导入系统选择页。

    原版从 ../importers/ 目录里扫 bbimport_*.php 导入脚本，把脚本第二行的系统名列进下拉框；
    参考站没有 importers 目录，因此原版页面本身就是"没有可用导入脚本"的三个兜底选项。
    本项目同样不内建任何外部论坛导入器，页面按同一状态输出。
    """
    started = None
    if request.method == "POST" and request.form.get("action") == "choosebb":
        started = request.form.get("importbb") or "membersarea"
    return render_template("admin/bbimport.html", started=started)


@bp.route("/dbsettings", methods=["GET", "POST"])
def dbsettings():
    """Import & Maintenance → Database Settings：照原版 dbsettings.php 的连接设置表单。"""
    current_uri = current_app.config["SQLALCHEMY_DATABASE_URI"]
    values = _db_uri_parts(current_uri)
    messages, errors = [], []
    raw_action = (request.form.get("action") or request.args.get("action") or "modify")
    action = {"Test Connection": "test", "Save Settings": "save",
              "Load Saved Settings": "load",
              "Copy data to this database and switch": "migrate"}.get(raw_action, raw_action)

    if request.method == "POST":
        values = {k: (request.form.get("db[%s]" % k) or "").strip() for k in DB_SETTING_KEYS}
        values["dbservertype"] = values["dbservertype"] if values["dbservertype"] in (
            "mysql", "pgsql", "sqlite") else "mysql"
        values["usepconnect"] = "1" if values["usepconnect"] == "1" else "0"
        uri = _db_uri_build(values)
        if action in ("test", "save", "migrate"):
            ok, details = _db_test(uri)
            (messages if ok else errors).extend(details)
            if ok and action == "migrate":
                recreate = request.form.get("recreate") == "1"
                try:
                    details2 = _db_migrate(current_uri, uri, recreate)
                    messages.extend(details2)
                    ok = True
                except Exception as exc:
                    errors.append(f"复制数据失败：{exc}")
                    ok = False
                if ok:
                    action = "save"
            if ok and action == "save":
                env = _env_local_path()
                stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                if env.exists():
                    (env.parent / f"{env.name}.bak.{stamp}").write_text(
                        env.read_text(encoding="utf-8"), encoding="utf-8")
                lines = [ln for ln in (env.read_text(encoding="utf-8").splitlines()
                                       if env.exists() else [])
                         if not ln.startswith("LOONG_BBS_DATABASE_URL=")]
                lines.append(f"LOONG_BBS_DATABASE_URL={uri}")
                env.write_text("\n".join(lines) + "\n", encoding="utf-8")
                messages.append("已写入 .env.local（旧文件备份为 .env.local.bak." + stamp + "）。")
                messages.append("新的连接设置在下次启动服务时生效：请重启 start-server.ps1。")
        elif action == "load":
            messages.append("本地只有当前这一套连接设置，表单已回填当前值。")

    return render_template("admin/dbsettings.html", values=values, messages=messages,
                           errors=errors, current_uri=current_uri)


@bp.route("/backup")
def backup_choose():
    """Import & Maintenance → Back-up Database：照原版 backup.php?action=choose 的三块表单。"""
    tables = _sqlite_tables()
    default_name = "./forumbackup-" + datetime.now().strftime("%m-%d-%Y") + ".sql"
    return render_template("admin/backup.html", tables=tables, default_name=default_name)


@bp.route("/backup/sql", methods=["POST"])
def backup_sql():
    """原版 action=sqltable：把所有勾选的表 dump 成一个 vbulletin.sql 下载。"""
    chosen = [t for t in _sqlite_tables() if request.form.get(f"table[{t}]") in ("1", "on")]
    body = _sqlite_dump(chosen)
    return Response(body, mimetype="application/octet-stream",
                    headers={"Content-disposition": "filename=vbulletin.sql"})


@bp.route("/backup/file", methods=["POST"])
def backup_file():
    """原版 action=sqlfile：把 dump 写到服务器上指定路径的 .sql 文件。"""
    filename = request.form.get("filename") or ""
    target = _search_backup_path(filename)
    if target is None:
        flash("Invalid path - backup must be written inside the board directory", "error")
        return redirect(url_for("admin.backup_choose"))
    body = _sqlite_dump(_sqlite_tables())
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body, encoding="utf-8")
    lines = "".join(f"<p>Dumping {t}</p>" for t in _sqlite_tables())
    return render_template("admin/backup.html", mode="done", tables=_sqlite_tables(),
                           dumped=lines, target=filename)


@bp.route("/backup/csv", methods=["POST"])
def backup_csv():
    """原版 action=csvtable：把单表 dump 成 CSV 下载。"""
    import sqlite3

    table = request.form.get("table") or ""
    if table not in _sqlite_tables():
        flash("Table not found", "error")
        return redirect(url_for("admin.backup_choose"))
    separator = request.form.get("separator") or ","
    quotes = request.form.get("quotes") or "'"
    showhead = _yn(request.form, "showhead", 1)
    uri = current_app.config["SQLALCHEMY_DATABASE_URI"].replace("sqlite:///", "", 1)
    path = Path(uri) if Path(uri).is_absolute() else Path(current_app.root_path).parent / uri
    conn = sqlite3.connect(str(path))
    out = []
    if showhead:
        cols = [c[1] for c in conn.execute(f"PRAGMA table_info({table})").fetchall()]
        out.append(separator.join(quotes + c + quotes for c in cols))
    for rec in conn.execute(f"SELECT * FROM {table}").fetchall():
        out.append(separator.join(
            "NULL" if v is None else (quotes + str(v).replace(quotes, quotes + quotes) + quotes)
            for v in rec))
    conn.close()
    body = "\n".join(out) + "\n"
    return Response(body, mimetype="text/csv",
                    headers={"Content-disposition": f"filename={table}.csv"})


@bp.route("/bbcodes", methods=["GET", "POST"])
def bbcodes():
    """Custom vB Codes → Modify：照原版 bbcode.php 的 modify，附带 Test your vB Codes 表单。"""
    if request.method == "POST" and request.form.get("action") == "test":
        text = request.form.get("text") or ""
        parsed = _apply_bbcodes(text)
        # 原版是 nl2br(preg_replace(...)) 后直接输出，不做转义
        parsed = re.sub(r"\r\n|\n", "<br />\n", parsed)
        return render_template("admin/bbcodes.html", mode="test", text=text, parsed=parsed)
    rows = db.session.execute(select(BBCode)).scalars().all()
    items = []
    for row in rows:
        parsed = _bbcode_html(row.bbcodetag, row.bbcodereplacement, row.twoparams, row.bbcodeexample)
        items.append({"row": row, "example": row.bbcodeexample, "parsed": parsed})
    return render_template("admin/bbcodes.html", mode="list", items=items)


@bp.route("/bbcodes/add", methods=["GET", "POST"])
def bbcodes_add():
    """Custom vB Codes → Add：原版 add / insert。"""
    if request.method == "GET":
        return render_template("admin/bbcodes.html", mode="add")
    form = request.form
    twoparams = 1 if _yn(form, "twoparams", 1) else 0
    repl = (form.get("bbcodereplacement") or "").strip()
    if twoparams:
        repl = repl.replace("{param}", "\\7").replace("{option}", "\\5")
    else:
        repl = repl.replace("{param}", "\\4")
    db.session.add(BBCode(bbcodetag=re.escape((form.get("bbcodetag") or "").strip()),
                          bbcodereplacement=repl,
                          bbcodeexample=(form.get("bbcodeexample") or "").strip(),
                          bbcodeexplanation=(form.get("bbcodeexplanation") or "").strip(),
                          twoparams=twoparams))
    db.session.commit()
    flash("Record added", "success")
    return redirect(url_for("admin.bbcodes"))


@bp.route("/bbcodes/edit", methods=["GET", "POST"])
def bbcodes_edit():
    """Custom vB Codes 编辑：原版 edit / doupdate（显示时把反引用还原成 {param}/{option}）。"""
    bid = request.values.get("bbcodeid", type=int) or 0
    row = db.session.get(BBCode, bid) if bid else None
    if row is None:
        flash("Record not found", "error")
        return redirect(url_for("admin.bbcodes"))
    if request.method == "GET":
        shown = row.bbcodereplacement
        if row.twoparams:
            shown = shown.replace("\\7", "{param}").replace("\\5", "{option}")
        else:
            shown = shown.replace("\\4", "{param}")
        return render_template("admin/bbcodes.html", mode="edit", row=row,
                               tag=row.bbcodetag.replace("\\\\", "\\"), shown=shown)
    form = request.form
    twoparams = 1 if _yn(form, "twoparams", 1) else 0
    repl = (form.get("bbcodereplacement") or "").strip()
    if twoparams:
        repl = repl.replace("{param}", "\\7").replace("{option}", "\\5")
    else:
        repl = repl.replace("{param}", "\\4")
    row.bbcodetag = re.escape((form.get("bbcodetag") or "").strip())
    row.bbcodereplacement = repl
    row.bbcodeexample = (form.get("bbcodeexample") or "").strip()
    row.bbcodeexplanation = (form.get("bbcodeexplanation") or "").strip()
    row.twoparams = twoparams
    db.session.commit()
    flash("Record updated!", "success")
    return redirect(url_for("admin.bbcodes"))


@bp.route("/bbcodes/remove", methods=["GET", "POST"])
def bbcodes_remove():
    """Custom vB Codes 删除：原版 remove / kill（原版删除后无任何提示语）。"""
    bid = request.values.get("bbcodeid", type=int) or 0
    row = db.session.get(BBCode, bid) if bid else None
    if row is None:
        flash("Record not found", "error")
        return redirect(url_for("admin.bbcodes"))
    if request.method == "GET":
        return render_template("admin/bbcodes.html", mode="remove", row=row)
    db.session.execute(delete(BBCode).where(BBCode.id == row.id))
    db.session.commit()
    return redirect(url_for("admin.bbcodes"))


@bp.route("/usergroups")
def usergroups():
    """User Groups → Modify：照原版 usergroup.php 的 modify。"""
    rows = db.session.execute(
        select(UserGroup).order_by(UserGroup.title)).scalars().all()
    counts = dict(db.session.execute(
        select(User.usergroupid, func.count(User.id)).group_by(User.usergroupid)).all())
    group_rows = [{"id": g.id, "title": g.title, "count": counts.get(g.id, 0)} for g in rows]
    return render_template("admin/usergroups.html", mode="list", rows=group_rows)


@bp.route("/usergroups/add", methods=["GET", "POST"])
def usergroups_add():
    """User Groups → Add：原版 add / insert。"""
    if request.method == "GET":
        return render_template("admin/usergroups.html", mode="add",
                               form_groups=_group_form_groups(),
                               perms=dict(GROUP_FORM_DEFAULTS))
    form = request.form
    group = UserGroup(title=(form.get("title") or "").strip(),
                      usertitle=(form.get("usertitle") or "").strip())
    db.session.add(group)
    db.session.flush()
    values = {name: _yn(form, name, GROUP_FORM_DEFAULTS[name]) for name in GROUP_FORM_DEFAULTS}
    db.session.add(UserGroupPermission(
        usergroup_id=group.id, **values,
        maxbuddypm=form.get("maxbuddypm", type=int) or 0,
        maxforwardpm=form.get("maxforwardpm", type=int) or 0,
    ))
    db.session.commit()
    flash("Record added", "success")
    return redirect(url_for("admin.usergroups"))


@bp.route("/usergroups/edit", methods=["GET", "POST"])
def usergroups_edit():
    """User Groups 编辑：原版 edit / doupdate。"""
    gid = request.values.get("usergroupid", type=int) or 0
    group = db.session.get(UserGroup, gid) if gid else None
    if group is None:
        flash("Record not found", "error")
        return redirect(url_for("admin.usergroups"))
    if request.method == "GET":
        perms = _group_perms(group.id)
        # 原版：1/2/3/4/7 组且 showgroup 不为 1 时，这一项改成 hidden（不允许改）
        hide_showgroup = group.id in (1, 2, 3, 4, 7) and not perms["showgroup"]
        row = db.session.get(UserGroupPermission, group.id)
        return render_template("admin/usergroups.html", mode="edit", row=group,
                               form_groups=_group_form_groups(), perms=perms,
                               hide_showgroup=hide_showgroup,
                               maxbuddypm=row.maxbuddypm if row else 0,
                               maxforwardpm=row.maxforwardpm if row else 0)

    form = request.form
    if not _yn(form, "cancontrolpanel") and group.id != 0:
        others = db.session.scalar(select(func.count(UserGroupPermission.usergroup_id)).where(
            UserGroupPermission.cancontrolpanel.is_(True),
            UserGroupPermission.usergroup_id != group.id)) or 0
        if others == 0:
            return ("<p>You are about to remove the last group with control panel access. "
                    "This would lock you out of the control panel - you cannot proceed."
                    "</body></html>", 200, {"Content-Type": "text/html; charset=utf-8"})

    group.title = (form.get("title") or "").strip()
    group.usertitle = (form.get("usertitle") or "").strip()
    row = db.session.get(UserGroupPermission, group.id)
    if row is None:
        row = UserGroupPermission(usergroup_id=group.id)
        db.session.add(row)
    for name in GROUP_FORM_DEFAULTS:
        if name == "showgroup" and group.id in (1, 2, 3, 4, 7) and "showgroup" not in form:
            continue
        setattr(row, name, _yn(form, name, GROUP_FORM_DEFAULTS[name]))
    row.maxbuddypm = form.get("maxbuddypm", type=int) or 0
    row.maxforwardpm = form.get("maxforwardpm", type=int) or 0
    # 原版：填了 User Status 就把该组里没自定义头衔的用户统一改掉
    if group.usertitle:
        db.session.execute(db.update(User).where(
            User.usergroupid == group.id, User.usertitle == "").values(usertitle=group.usertitle))
    db.session.commit()
    flash("Record updated!", "success")
    return redirect(url_for("admin.usergroups"))


@bp.route("/usergroups/remove", methods=["GET", "POST"])
def usergroups_remove():
    """User Groups 删除：原版 remove / kill。"""
    gid = request.values.get("usergroupid", type=int) or 0
    group = db.session.get(UserGroup, gid) if gid else None
    if group is None:
        flash("Record not found", "error")
        return redirect(url_for("admin.usergroups"))
    if request.method == "GET":
        return render_template("admin/usergroups.html", mode="remove", row=group)
    db.session.execute(db.update(User).where(User.usergroupid == group.id).values(usergroupid=2))
    db.session.execute(delete(ForumPermission).where(ForumPermission.usergroup_id == group.id))
    db.session.execute(delete(UserGroupPermission).where(
        UserGroupPermission.usergroup_id == group.id))
    db.session.execute(delete(UserGroup).where(UserGroup.id == group.id))
    db.session.commit()
    flash("Record deleted sucessfully - all existing members of this group have been "
          "returned to the 'registered' group", "success")
    return redirect(url_for("admin.usergroups"))


@bp.route("/profilefields")
def profilefields():
    """User Profile Fields → Modify：照原版 profilefield.php 的 modify。"""
    rows = db.session.execute(
        select(UserProfileField).order_by(UserProfileField.displayorder)).scalars().all()
    return render_template("admin/profile_fields.html", mode="list", rows=rows)


@bp.route("/profilefields/add", methods=["GET", "POST"])
def profilefields_add():
    """User Profile Fields → Add：原版 add / insert。"""
    if request.method == "GET":
        return render_template("admin/profile_fields.html", mode="add")
    form = request.form
    db.session.add(UserProfileField(
        title=(form.get("title") or "").strip(),
        description=(form.get("description") or "").strip(),
        required=(form.get("required") or "") == "1",
        hidden=(form.get("hidden") or "") == "1",
        editable=(form.get("editable") or "") == "1",
        maxlength=form.get("maxlength", type=int) or 0,
        size=form.get("size", type=int) or 0,
        displayorder=form.get("displayorder", type=int) or 0,
    ))
    db.session.commit()
    flash("Record added", "success")
    return redirect(url_for("admin.profilefields"))


@bp.route("/profilefields/edit", methods=["GET", "POST"])
def profilefields_edit():
    """User Profile Fields 编辑：原版 edit / doupdate。"""
    fid = request.values.get("profilefieldid", type=int) or 0
    row = db.session.get(UserProfileField, fid) if fid else None
    if row is None:
        flash("Record not found", "error")
        return redirect(url_for("admin.profilefields"))
    if request.method == "GET":
        return render_template("admin/profile_fields.html", mode="edit", row=row)
    form = request.form
    row.title = (form.get("title") or "").strip()
    row.description = (form.get("description") or "").strip()
    row.required = (form.get("required") or "") == "1"
    row.hidden = (form.get("hidden") or "") == "1"
    row.editable = (form.get("editable") or "") == "1"
    row.maxlength = form.get("maxlength", type=int) or 0
    row.size = form.get("size", type=int) or 0
    row.displayorder = form.get("displayorder", type=int) or 0
    db.session.commit()
    flash("Record updated!", "success")
    return redirect(url_for("admin.profilefields"))


@bp.route("/profilefields/remove", methods=["GET", "POST"])
def profilefields_remove():
    """User Profile Fields 删除：原版 remove / kill。"""
    fid = request.values.get("profilefieldid", type=int) or 0
    row = db.session.get(UserProfileField, fid) if fid else None
    if row is None:
        flash("Record not found", "error")
        return redirect(url_for("admin.profilefields"))
    if request.method == "GET":
        return render_template("admin/profile_fields.html", mode="remove", row=row)
    db.session.execute(delete(UserProfileField).where(UserProfileField.id == row.id))
    db.session.commit()
    flash("Profile field removed", "success")
    return redirect(url_for("admin.profilefields"))


@bp.route("/usertitles")
def usertitles():
    """User Titles → Modify：照原版 usertitle.php 的 modify。"""
    rows = db.session.execute(select(UserTitle).order_by(UserTitle.minposts)).scalars().all()
    return render_template("admin/usertitles.html", mode="list", rows=rows)


@bp.route("/usertitles/add", methods=["GET", "POST"])
def usertitles_add():
    """User Titles → Add：原版 add / insert。"""
    if request.method == "GET":
        return render_template("admin/usertitles.html", mode="add")
    title = (request.form.get("title") or "").strip()
    minposts = request.form.get("minposts", type=int) or 0
    db.session.add(UserTitle(title=title, minposts=minposts))
    db.session.commit()
    flash("Record added", "success")
    return redirect(url_for("admin.usertitles"))


@bp.route("/usertitles/edit", methods=["GET", "POST"])
def usertitles_edit():
    """User Titles → Modify 的编辑分支：原版 edit / doupdate。"""
    uid = request.values.get("usertitleid", type=int) or 0
    row = db.session.get(UserTitle, uid) if uid else None
    if row is None:
        flash("Record not found", "error")
        return redirect(url_for("admin.usertitles"))
    if request.method == "GET":
        return render_template("admin/usertitles.html", mode="edit", row=row)
    row.title = (request.form.get("title") or "").strip()
    row.minposts = request.form.get("minposts", type=int) or 0
    db.session.commit()
    flash("Record updated!", "success")
    return redirect(url_for("admin.usertitles"))


@bp.route("/usertitles/remove", methods=["GET", "POST"])
def usertitles_remove():
    """User Titles → Modify 的删除分支：原版 remove / kill。"""
    uid = request.values.get("usertitleid", type=int) or 0
    row = db.session.get(UserTitle, uid) if uid else None
    if row is None:
        flash("Record not found", "error")
        return redirect(url_for("admin.usertitles"))
    if request.method == "GET":
        return render_template("admin/usertitles.html", mode="remove", row=row)
    db.session.execute(delete(UserTitle).where(UserTitle.id == row.id))
    db.session.commit()
    flash("User title removed", "success")
    return redirect(url_for("admin.usertitles"))


@bp.route("/users/pmstats")
def users_pmstats():
    """Users → PM Statistics：照原版 user.php 的 pmstats。"""
    counts = _pm_counts()
    groups: dict[int, list[int]] = {}
    for uid, n in counts.items():
        groups.setdefault(n, []).append(uid)
    rows = [{"n": n, "users": len(ids), "ids": ",".join(str(i) for i in sorted(ids))}
            for n, ids in sorted(groups.items(), key=lambda kv: (-kv[0], kv[1]))]
    return render_template("admin/pm_stats.html", rows=rows,
                           pmquota=get_settings().get("pmquota", 70))


@bp.route("/users/pmuserstats")
def users_pmuserstats():
    """Users → PM Statistics → 某条数档位的用户列表（原版 pmuserstats）。"""
    pms = request.args.get("pms", type=int) or 0
    counts = _pm_counts()
    ids = [uid for uid, n in counts.items() if n == pms]
    rows = []
    for u in db.session.execute(select(User).where(User.id.in_(ids))).scalars().all():
        rows.append({
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "last_visit": u.last_visit.strftime("%H:%M %d-%b-%Y") if u.last_visit else "never",
        })
    rows.sort(key=lambda r: (r["username"] or "").lower())
    return render_template("admin/pm_stats.html", mode="users", rows=rows, pms=pms,
                           total=len(rows), ids=",".join(str(i) for i in ids))


@bp.route("/users/killpms", methods=["GET", "POST"])
def users_killpms():
    """删除某用户全部悄悄话（原版 killpms / dokillpms）。"""
    uid = request.values.get("userid", type=int) or 0
    user = db.session.get(User, uid) if uid else None
    username = request.values.get("username") or (user.username if user else "")
    if request.method == "POST":
        if user is None:
            flash("Invalid user id specified", "error")
            return redirect(url_for("admin.users_pmstats"))
        db.session.execute(delete(PrivateMessage).where(
            (PrivateMessage.sender_id == user.id) | (PrivateMessage.recipient_id == user.id)))
        db.session.commit()
        flash(f"Private messages belonging to {username} deleted", "success")
        return redirect(url_for("admin.users_pmstats"))
    return render_template("admin/pm_stats.html", mode="kill", user=user,
                           username=username, uid=uid)


@bp.route("/users/prune", methods=["GET", "POST"])
def users_prune():
    """Users → Move/Prune：照原版 user.php 的 prune / pruneusers / dopruneusers。"""
    groups_all = db.session.execute(select(UserGroup).order_by(UserGroup.title)).scalars().all()
    # 原版只允许把用户移到这些组：NOT IN(1,3,4,5,6)
    move_groups = [g for g in groups_all if g.id not in (1, 3, 4, 5, 6)]

    def _post_counts(ids):
        rows = db.session.execute(
            select(Post.author_id, func.count(Post.id)).where(Post.author_id.in_(ids))
        ).all()
        return {uid: n for uid, n in rows}

    def _render_form():
        return render_template("admin/users_prune.html", mode="form", groups=groups_all,
                               move_groups=move_groups)

    if request.method == "GET":
        return _render_form()

    step = request.values.get("step", "find")

    if step == "do":
        # 原版 checkbox 名是 userid[id]，值 1
        ids = [int(k[7:-1]) for k, v in request.form.items()
               if k.startswith("userid[") and k.endswith("]") and v == "1" and k[7:-1].isdigit()]
        me = getattr(current_user, "id", None)
        ids = [i for i in ids if i != me]
        if not ids:
            flash("Error: You did not select any users to prune/move!", "error")
            return redirect(url_for("admin.users_prune"))
        dowhat = request.form.get("dowhat", "")
        if dowhat == "delete":
            targets = db.session.execute(select(User).where(User.id.in_(ids))).scalars().all()
            names = [u.username for u in targets]
            # 原版会把这批人的帖子/主题转到访客名下；本地先做，避免删用户时留下孤儿作者
            db.session.execute(db.update(Post).where(Post.author_id.in_(ids)).values(author_id=1))
            db.session.execute(db.update(Thread).where(Thread.author_id.in_(ids)).values(author_id=1))
            for u in targets:
                db.session.execute(delete(ThreadSubscription).where(ThreadSubscription.user_id == u.id))
                db.session.execute(delete(ThreadRating).where(ThreadRating.user_id == u.id))
                db.session.execute(delete(PollVote).where(PollVote.user_id == u.id))
                db.session.execute(delete(PrivateMessage).where(
                    (PrivateMessage.sender_id == u.id) | (PrivateMessage.recipient_id == u.id)))
                db.session.execute(delete(PostReport).where(PostReport.reporter_id == u.id))
                db.session.execute(delete(OnlineSession).where(OnlineSession.user_id == u.id))
            # 用 Core delete 删行，避开 ORM 关系把外键置空的 flush 顺序问题
            db.session.execute(delete(User).where(User.id.in_(ids)))
            db.session.commit()
            flash(f"Deleting user account(s) .... okay. Deleted {len(names)} user(s): "
                  f"{', '.join(names)}. Their posts and threads were moved to the guest account.", "success")
            return redirect(url_for("admin.users_prune"))
        if dowhat == "move":
            gid = request.form.get("movegroup", type=int)
            group = db.session.get(UserGroup, gid) if gid else None
            if group is None:
                flash("Error: no action specified! Please choose delete or move", "error")
                return redirect(url_for("admin.users_prune"))
            db.session.execute(db.update(User).where(User.id.in_(ids)).values(usergroupid=group.id))
            db.session.commit()
            flash(f"Users moved to <i>{group.title}</i> usergroup.", "success")
            return redirect(url_for("admin.users_prune"))
        flash("Error: no action specified! Please choose delete or move", "error")
        return redirect(url_for("admin.users_prune"))

    # step == "find"：照 pruneusers 的条件组合
    gid = request.form.get("usergroupid", type=int) or -1
    days = request.form.get("daysprune", type=int) or 0
    joindate = (request.form.get("joindate") or "").strip()
    minposts = request.form.get("minposts", type=int) or 0
    order = request.form.get("order") or "username ASC"

    conds = []
    if gid != -1:
        conds.append(User.usergroupid == gid)
    if days:
        cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
        conds.append(User.last_visit < cutoff)
    if joindate:
        try:
            conds.append(User.joined_at < datetime.strptime(joindate, "%Y-%m-%d"))
        except ValueError:
            conds.append(User.joined_at < datetime.now(timezone.utc).replace(tzinfo=None))

    if not conds and not minposts:
        flash("Error: Please enter some search conditions.", "error")
        return redirect(url_for("admin.users_prune"))

    q = select(User)
    if conds:
        q = q.where(*conds)
    users = db.session.execute(q).scalars().all()
    counts = _post_counts([u.id for u in users]) if users else {}
    if minposts:
        users = [u for u in users if counts.get(u.id, 0) < minposts]
    if not users:
        flash("Error: No users matched your search conditions.", "error")
        return redirect(url_for("admin.users_prune"))

    keymap = {
        "username ASC": lambda u: (u.username or "").lower(),
        "email ASC": lambda u: (u.email or "").lower(),
        "usergroup.title ASC": lambda u: u.usergroupid,
        "posts DESC": lambda u: -counts.get(u.id, 0),
        "lastvisit ASC": lambda u: u.last_visit or datetime(1970, 1, 1),
        "joindate DESC": lambda u: -(u.joined_at or datetime(1970, 1, 1)).timestamp(),
    }
    users.sort(key=keymap.get(order, keymap["username ASC"]))
    rows = [{
        "id": u.id,
        "username": u.username,
        "email": u.email,
        "posts": counts.get(u.id, 0),
        "last_visit": (u.last_visit.strftime("%m/%d/%y") if u.last_visit else "never"),
        "joined": u.joined_at.strftime("%m/%d/%y") if u.joined_at else "",
        "group_title": next((g.title for g in groups_all if g.id == u.usergroupid), ""),
        "locked": (u.id == getattr(current_user, "id", None) or u.usergroupid in (5, 6)),
    } for u in users]
    return render_template("admin/users_prune.html", mode="results", rows=rows,
                           move_groups=move_groups, total=len(rows), order=order,
                           usergroupid=gid, daysprune=days, joindate=joindate, minposts=minposts)


@bp.route("/users/add", methods=["GET", "POST"])
def user_add():
    """Users → Add：照原版 user.php 的 add / insert 新建用户。"""
    groups = db.session.execute(select(UserGroup).order_by(UserGroup.id)).scalars().all()

    def _page():
        return render_template("admin/user_add.html", groups=groups)

    if request.method == "GET":
        return _page()

    username = (request.form.get("ausername") or "").strip()
    password = (request.form.get("apassword") or "").strip()
    if not username:
        flash("You did not give this user an username", "error")
        return _page()
    existing = db.session.scalar(select(User).where(func.lower(User.username) == username.lower()))
    if existing is not None:
        flash(f"There is already a user named {username}", "error")
        return _page()
    if not password:
        flash("You did not give this user a password", "error")
        return _page()

    def _yes(name, default):
        return (request.form.get(name) if request.form.get(name) is not None else str(default)) == "1"

    def _dt(field):
        raw = (request.form.get(field) or "").strip()
        if not raw:
            return datetime.now(timezone.utc).replace(tzinfo=None)
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(raw, fmt)
            except ValueError:
                continue
        return datetime.now(timezone.utc).replace(tzinfo=None)

    group_id = request.form.get("usergroupid", type=int) or 2
    custom_title = _yes("customtitle", 0)
    usertitle = (request.form.get("usertitle") or "").strip()
    if not custom_title:
        group_obj = db.session.get(UserGroup, group_id)
        usertitle = (group_obj.usertitle or "") if group_obj else ""

    user = User(
        username=username,
        email=(request.form.get("email") or "").strip(),
        password_hash=generate_password_hash(password),
        usergroupid=group_id,
        usertitle=usertitle,
        homepage=(request.form.get("homepage") or "").strip(),
        birthday=(request.form.get("birthday") or "").strip(),
        signature=request.form.get("signature") or "",
        icq=(request.form.get("icq") or "").strip(),
        aim=(request.form.get("aim") or "").strip(),
        yahoo=(request.form.get("yahoo") or "").strip(),
        allowmail=_yes("adminemail", 1),
        showemail=_yes("showemail", 1),
        invisible=_yes("invisible", 0),
        receivepm=_yes("receivepm", 1),
        emailonpm=_yes("emailonpm", 0),
        pmpopup=_yes("pmpopup", 0),
        showsignatures=_yes("showsignatures", 1),
        showavatars=_yes("showavatars", 1),
        showimages=_yes("showimages", 1),
        vbcode=_yes("showvbcode", 1),
        emailnotification=_yes("emailnotification", 1),
        cookieuser=_yes("cookieuser", 1),
        nosessionhash=_yes("nosessionhash", 1),
        prunedays=request.form.get("daysprune", type=int) if request.form.get("daysprune") else -1,
        timezoneoffset=request.form.get("timezoneoffset", type=int) or 0,
        newstyleset=request.form.get("userstyleid", type=int) or 0,
        joined_at=_dt("joindate"),
        last_visit=_dt("lastvisit"),
        last_seen=_dt("lastactivity"),
    )
    db.session.add(user)
    db.session.commit()
    flash("Record added", "success")
    return redirect(url_for("admin.users_page"))


@bp.route("/mod/moderate/posts", methods=["GET", "POST"])
def moderate_posts():
    """Moderation → New Posts（原版前台 mod/moderate.php?action=posts）。"""
    if request.method == "POST":
        flash("Threads and posts moderated sucessfully.", "success")
        return redirect(url_for("admin.moderate_posts"))
    return render_template("admin/moderate_queue.html", mode="posts")


@bp.route("/mod/moderate/attachments", methods=["GET", "POST"])
def moderate_attachments():
    """Moderation → New Attachments（原版前台 mod/moderate.php?action=attachments）。"""
    if request.method == "POST":
        flash("Attachments moderated sucessfully.", "success")
        return redirect(url_for("admin.moderate_attachments"))
    return render_template("admin/moderate_queue.html", mode="attachments")


@bp.route("/forums/add", methods=["GET", "POST"])
def forum_add():
    """Forums & Moderators → Add：照原版 forum.php 的 add / insert 新建版块。"""
    categories = (
        db.session.execute(select(Category).order_by(Category.position, Category.id))
        .scalars()
        .all()
    )
    if request.method == "GET":
        return render_template("admin/forum_add.html", categories=categories)

    title = (request.form.get("title") or "").strip()
    description = (request.form.get("description") or "").strip()
    category_id = request.form.get("parentid", type=int) or 0
    position = request.form.get("displayorder", type=int) or 0
    private = (request.form.get("private") or "0") == "1"
    allow_posting = (request.form.get("allowposting") or "1") == "1"

    if not title:
        flash("Please enter a title for this forum.", "error")
        return render_template("admin/forum_add.html", categories=categories)
    category_obj = db.session.get(Category, category_id)
    if category_obj is None:
        flash("Please choose a parent forum.", "error")
        return render_template("admin/forum_add.html", categories=categories)

    forum_obj = Forum(
        category_id=category_obj.id,
        name=title,
        description=description,
        position=position,
        is_closed=not allow_posting,
    )
    db.session.add(forum_obj)
    db.session.flush()

    if private:
        # 原版 private=1 时把 usergroupid<5 或 >6 的组全部写成 deny，只有 admin / super mod 能看
        groups = db.session.execute(
            select(UserGroup.id).where((UserGroup.id < 5) | (UserGroup.id > 6))
        ).scalars().all()
        for gid in groups:
            perm = ForumPermission(usergroup_id=gid, forum_id=forum_obj.id)
            for field in PERMISSION_FIELDS:
                setattr(perm, field, False)
            db.session.add(perm)

    db.session.commit()
    flash("Record added", "success")
    return redirect(url_for("admin.forums_page"))


@bp.route("/threads/poll", methods=["GET", "POST"])
def threads_strip_poll():
    """Threads & Posts → Strip Poll（原版 thread.php 的 killpoll / removepoll / doremovepoll）。"""
    step = (request.form.get("step") or "").strip()

    def _entry():
        return render_template("admin/thread_strip_poll.html", mode="form")

    if request.method == "GET" or not step:
        return _entry()

    if step == "lookup":
        raw = (request.form.get("threadid") or "").strip()
        if not raw.isdigit():
            flash("No thread id specified!", "error")
            return _entry()
        thread_obj = db.session.get(Thread, int(raw))
        if thread_obj is None:
            flash("Invalid thread id specified", "error")
            return _entry()
        poll_obj = db.session.scalar(select(Poll).where(Poll.thread_id == thread_obj.id))
        if poll_obj is None:
            flash("No poll found in this thread!", "error")
            return _entry()
        return render_template(
            "admin/thread_strip_poll.html",
            mode="confirm",
            thread_obj=thread_obj,
            poll_obj=poll_obj,
        )

    if step == "kill":
        thread_id = request.form.get("threadid", type=int)
        do_delete = (request.form.get("dodelete") or "0") == "1"
        thread_obj = db.session.get(Thread, thread_id) if thread_id else None
        poll_obj = (
            db.session.scalar(select(Poll).where(Poll.thread_id == thread_id))
            if thread_obj is not None
            else None
        )
        if thread_obj is None or poll_obj is None or not do_delete:
            flash("Poll NOT deleted.", "error")
            return _entry()
        db.session.execute(delete(PollVote).where(PollVote.poll_id == poll_obj.id))
        db.session.delete(poll_obj)
        db.session.commit()
        return render_template(
            "admin/thread_strip_poll.html",
            mode="done",
            thread_obj=thread_obj,
        )

    return _entry()


@bp.route("/threads/votes", methods=["GET", "POST"])
def threads_votes():
    """Threads & Posts → Who Voted?（原版 thread.php 的 votes / dovotes）。"""
    polls = db.session.execute(
        select(Poll).order_by(Poll.id.desc())
    ).scalars().all()
    titles = {}
    for poll_obj in polls:
        thread_obj = db.session.get(Thread, poll_obj.thread_id) if poll_obj.thread_id else None
        titles[poll_obj.id] = thread_obj.title if thread_obj else ""

    def _page():
        return render_template(
            "admin/thread_votes.html", mode="form", polls=polls, titles=titles
        )

    if request.method == "GET" or not (request.form.get("step") or "").strip():
        return _page()

    if request.form.get("step") == "votes":
        poll_id = request.form.get("pollid", type=int)
        poll_obj = db.session.get(Poll, poll_id) if poll_id else None
        if poll_obj is None:
            flash("Invalid poll id specified", "error")
            return _page()
        thread_obj = db.session.get(Thread, poll_obj.thread_id) if poll_obj.thread_id else None
        options = db.session.execute(
            select(PollOption).where(PollOption.poll_id == poll_obj.id).order_by(PollOption.position)
        ).scalars().all()
        votes = db.session.execute(
            select(PollVote, User)
            .join(User, User.id == PollVote.user_id, isouter=True)
            .where(PollVote.poll_id == poll_obj.id)
            .order_by(PollVote.option_id, User.username)
        ).all()
        groups = []
        last_option_id = None
        for vote, user_obj in votes:
            if vote.option_id != last_option_id:
                opt = next((o for o in options if o.id == vote.option_id), None)
                groups.append({"option": opt.text if opt else "", "users": []})
                last_option_id = vote.option_id
            groups[-1]["users"].append(user_obj.username if user_obj else "")
        return render_template(
            "admin/thread_votes.html",
            mode="result",
            polls=polls,
            titles=titles,
            poll_obj=poll_obj,
            thread_obj=thread_obj,
            groups=groups,
        )

    return _page()


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
    gid = request.args.get("usergroupid", type=int) or 0
    per_page = 20
    stmt = select(User).order_by(User.id)
    count_stmt = select(func.count(User.id))
    if q:
        stmt = stmt.where(User.username.ilike(f"%{q}%"))
        count_stmt = count_stmt.where(User.username.ilike(f"%{q}%"))
    if gid:
        stmt = stmt.where(User.usergroupid == gid)
        count_stmt = count_stmt.where(User.usergroupid == gid)
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
