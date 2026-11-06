"""Who's Online：vB online.php 的对应页面（后台组 31）。"""
from __future__ import annotations

import secrets
import socket
from datetime import timedelta

from flask import Blueprint, render_template, request, session
from flask_login import current_user
from markupsafe import Markup, escape
from sqlalchemy import select

from .extensions import db
from .models import Forum, OnlineSession, Thread, User, utcnow
from .settings import get_setting

bp = Blueprint("online", __name__)

ONLINE_HASH_KEY = "onlinehash"
SKIP_ENDPOINTS = {"static"}


def _naive(value):
    if value is not None and value.tzinfo is not None:
        return value.replace(tzinfo=None)
    return value


def _cookietimeout() -> int:
    try:
        timeout = int(get_setting("cookietimeout") or 900)
    except (TypeError, ValueError):
        timeout = 900
    return max(60, timeout)


def _current_location() -> str:
    """本次请求在 vB 眼里的位置（session.location 那一列的语义）。"""
    endpoint = request.endpoint or ""
    args = request.view_args or {}
    if endpoint == "forums.index":
        return "index"
    if endpoint == "forums.forum":
        return f"forum:{args.get('forum_id')}"
    if endpoint == "forums.thread":
        return f"thread:{args.get('thread_id')}"
    if endpoint == "online.whos_online":
        return "online"
    if endpoint.startswith("members."):
        return "memberlist"
    if endpoint.startswith("search."):
        return "search"
    if endpoint.startswith("pm."):
        return "pm"
    if endpoint.startswith("admin."):
        return "admin"
    if endpoint.startswith("auth."):
        return "usercp"
    if endpoint.startswith("misc."):
        return "misc"
    return "unknown:" + (request.path or "/")[:200]


def record_activity():
    """把每个请求写进 online_sessions（对应 vB 的 session 表写入）。"""
    if request.endpoint in SKIP_ENDPOINTS:
        return None

    hash_ = session.get(ONLINE_HASH_KEY)
    if not hash_:
        hash_ = secrets.token_hex(16)
        session[ONLINE_HASH_KEY] = hash_

    now = utcnow()
    user_id = current_user.id if current_user.is_authenticated else None
    location = _current_location()
    ip = (request.remote_addr or "")[:45]

    row = db.session.scalar(
        select(OnlineSession).where(OnlineSession.session_hash == hash_)
    )
    if row is None:
        db.session.add(
            OnlineSession(
                session_hash=hash_,
                user_id=user_id,
                ip=ip,
                location=location,
                last_activity=now,
            )
        )
    else:
        row.user_id = user_id
        row.ip = ip
        row.location = location
        row.last_activity = now

    cutoff = now - timedelta(seconds=_cookietimeout())
    stale = db.session.scalars(
        select(OnlineSession).where(OnlineSession.last_activity < cutoff)
    ).all()
    for old in stale:
        db.session.delete(old)

    db.session.commit()
    return None


def _resolve_host(ip: str) -> str:
    if not ip:
        return ""
    try:
        return socket.gethostbyaddr(ip)[0]
    except (OSError, socket.error):
        return ip


def _location_view(location: str) -> tuple[str, str | None]:
    """把 session.location 翻成原版 show() 的「正在浏览」文案与链接。"""
    kind, _, value = (location or "").partition(":")
    if kind == "index":
        return "Index", None
    if kind == "forum":
        forum_obj = db.session.get(Forum, int(value)) if value.isdigit() else None
        if forum_obj is None:
            return "Viewing Forum", None
        return f"Viewing Forum {forum_obj.name}", f"/f/{forum_obj.id}"
    if kind == "thread":
        thread_obj = db.session.get(Thread, int(value)) if value.isdigit() else None
        if thread_obj is None:
            return "Viewing Thread", None
        return f"Viewing Thread {thread_obj.title}", f"/t/{thread_obj.id}"
    if kind == "online":
        return "Who's Online", None
    if kind == "memberlist":
        return "Member List", None
    if kind == "search":
        return "Searching", None
    if kind == "pm":
        return "Private Messaging", None
    if kind == "usercp":
        return "User Control Panel", None
    if kind == "admin":
        return "Admin Control Panel", None
    if kind == "misc":
        return "Miscellaneous", None
    return "Unknown Location", None


def _location_html(location: str) -> Markup:
    """原版 show() 的 where 列：前半是动作，后半（论坛/主题名）是链接。"""
    text, href = _location_view(location)
    if not href:
        return Markup(escape(text))
    prefix, _, name = text.partition(" ")
    # 「Viewing Forum <链接>」/「Viewing Thread <链接>」：动作词 + 链接
    action, _, rest = text.partition(" ")
    return Markup(
        f"{escape(action)} <a href=\"{escape(href)}\">{escape(rest)}</a>"
    )


@bp.get("/online")
def whos_online():
    if get_setting("WOLenable", "1") == "0":
        return render_template("online_disabled.html"), 200

    timeout = _cookietimeout()
    cutoff = utcnow() - timedelta(seconds=timeout)
    rows = db.session.execute(
        select(OnlineSession).where(OnlineSession.last_activity >= cutoff)
    ).scalars().all()

    # 同一会员可能有多条会话行：原版取 lastactivity 最新的那一条
    members: dict[int, OnlineSession] = {}
    for row in rows:
        if not row.user_id:
            continue
        current_row = members.get(row.user_id)
        if current_row is None or _naive(row.last_activity) > _naive(current_row.last_activity):
            members[row.user_id] = row

    show_guests = get_setting("WOLguests", "1") != "0"
    guests = [row for row in rows if not row.user_id] if show_guests else []

    resolve = get_setting("WOLresolve", "0") == "1"
    show_ip = bool(current_user.is_authenticated and getattr(current_user, "is_admin", False))
    highlight_admin = get_setting("highlightadmin", "1") != "0"
    show_email = get_setting("displayemails", "0") == "1"
    show_pm = get_setting("enablepms", "1") != "0"

    member_rows = []
    for user_id, row in members.items():
        user = db.session.get(User, user_id)
        if user is None or user.invisible:
            continue  # 原版 invisible 的行不进列表，也不计入 Members 数
        where_text, where_href = _location_view(row.location or "")
        member_rows.append(
            {
                "username": user.username,
                "profile_url": f"/u/{user.username}",
                "is_admin": bool(user.is_admin) and highlight_admin,
                "where_html": _location_html(row.location or ""),
                "last_active": row.last_activity,
                "ip": _resolve_host(row.ip) if resolve else (row.ip or ""),
                "pm_url": f"/pm/new?to={user.username}" if show_pm else None,
                "email": user.email if show_email else None,
            }
        )
    member_rows.sort(key=lambda item: item["username"].lower())

    guest_rows = []
    for row in sorted(guests, key=lambda r: _naive(r.last_activity) or utcnow()):
        guest_rows.append(
            {
                "username": "Guest",
                "profile_url": None,
                "is_admin": False,
                "where_html": _location_html(row.location or ""),
                "last_active": row.last_activity,
                "ip": _resolve_host(row.ip) if resolve else (row.ip or ""),
                "pm_url": None,
                "email": None,
            }
        )

    refresh = get_setting("WOLrefresh", "60")
    try:
        refresh_seconds = int(refresh or 0)
    except (TypeError, ValueError):
        refresh_seconds = 0

    return render_template(
        "online.html",
        member_rows=member_rows,
        guest_rows=guest_rows,
        number_members=len(member_rows),
        number_guests=len(guest_rows),
        show_guests=show_guests,
        show_ip=show_ip,
        show_email=show_email,
        show_pm=show_pm,
        show_legend=highlight_admin,
        refresh_seconds=refresh_seconds,
    )
