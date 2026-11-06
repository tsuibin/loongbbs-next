"""Small helpers: template filters, CSRF, BBCode, pagination."""
from __future__ import annotations

import html
import os
import re
import secrets
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from flask import abort, request, session
from flask_login import current_user

# ---------------------------------------------------------------- CSRF


def csrf_token() -> str:
    token = session.get("_csrf")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf"] = token
    return token


def csrf_protect():
    """Reject state-changing requests without a matching session token."""
    if request.method not in ("POST", "PUT", "PATCH", "DELETE"):
        return
    sent = request.form.get("_csrf") or request.headers.get("X-CSRF-Token", "")
    if not sent or not secrets.compare_digest(sent, session.get("_csrf", "")):
        abort(400, "CSRF token 校验失败，请刷新页面后重试。")


def current_user_or_none():
    return current_user if current_user.is_authenticated else None


# ---------------------------------------------------------------- formatting


# vB 2.3.11 的页脚固定写 ``All times are GMT``，访客的时区偏移是 0，
# 所以默认按 UTC 显示（与参考站一致）。需要本地时区时用环境变量覆盖。
try:
    LOCAL_TZ = ZoneInfo(os.environ.get("LOONG_BBS_TIMEZONE", "UTC"))
except Exception:  # 缺少 tz 数据时退回 UTC，不至于渲染报错
    LOCAL_TZ = timezone.utc


def format_dt(value: datetime | None, fmt: str = "%Y-%m-%d %H:%M") -> str:
    """数据库里存 UTC，展示时按站点时区（默认 GMT）渲染。"""
    if value is None:
        return "—"
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(LOCAL_TZ).strftime(fmt)


def now_gmt(fmt: str = "%I:%M %p") -> str:
    """页脚那一行 ``The time now is ...`` 用的当前站点时间。"""
    return datetime.now(timezone.utc).astimezone(LOCAL_TZ).strftime(fmt)


def avatar_src(user) -> str:
    """Return the image URL for a user's avatar, or "" when they have none.

    ``small_avatar`` 对应 vB 的 ``avatarpath``（相对 static 的路径或外链）。
    """
    from flask import url_for

    if user is None:
        return ""
    custom = getattr(user, "custom_avatar", "") or ""
    if custom:
        if custom.startswith(("http://", "https://")):
            return custom
        return url_for("static", filename=custom.lstrip("/"))
    avatar = getattr(user, "avatar", None)
    if avatar is not None and avatar.avatarpath:
        path = avatar.avatarpath
        if path.startswith(("http://", "https://")):
            return path
        return url_for("static", filename=path.lstrip("/"))
    return ""


def human_size(num: int) -> str:
    step = 1024.0
    for unit in ("B", "KB", "MB", "GB"):
        if num < step or unit == "GB":
            return f"{num:.0f} B" if unit == "B" else f"{num:.1f} {unit}"
        num /= step
    return f"{num:.1f} GB"


def time_ago(value: datetime | None) -> str:
    if value is None:
        return "—"
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - value
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return "刚刚"
    if seconds < 3600:
        return f"{seconds // 60} 分钟前"
    if seconds < 86400:
        return f"{seconds // 3600} 小时前"
    if seconds < 86400 * 30:
        return f"{seconds // 86400} 天前"
    return format_dt(value, "%Y-%m-%d")


# ---------------------------------------------------------------- BBCode

_URL_OK = re.compile(r"^(https?://|mailto:)", re.I)
_CODE_BLOCK = re.compile(r"\[code\](.*?)\[/code\]", re.I | re.S)


def _url_tagged(match: re.Match) -> str:
    href, label = match.group(1), match.group(2)
    if not _URL_OK.match(href):
        return label
    return (
        f'<a href="{href}" rel="noopener noreferrer nofollow" target="_blank">{label}</a>'
    )


def _url_plain(match: re.Match) -> str:
    url = match.group(1)
    if not _URL_OK.match(url):
        return url
    return (
        f'<a href="{url}" rel="noopener noreferrer nofollow" target="_blank">{url}</a>'
    )


def render_body(text: str) -> str:
    """Escape everything, then re-enable a small BBCode subset.

    Raw HTML is never allowed, so a post can not inject markup; the only tags
    that can appear in the output are the ones built here.
    """
    if not text:
        return ""

    escaped = html.escape(text.replace("\r\n", "\n").replace("\r", "\n"), quote=False)

    # Pull [code] blocks out first: inside them newlines must stay newlines.
    code_blocks: list[str] = []

    def stash(match: re.Match) -> str:
        code_blocks.append(match.group(1))
        return f"\x00code{len(code_blocks) - 1}\x00"

    escaped = _CODE_BLOCK.sub(stash, escaped)

    escaped = re.sub(r"\[url=([^\]\s]+)\](.*?)\[/url\]", _url_tagged, escaped, flags=re.I | re.S)
    escaped = re.sub(r"\[url\](.*?)\[/url\]", _url_plain, escaped, flags=re.I | re.S)
    for tag in ("b", "i", "u", "s"):
        escaped = re.sub(
            rf"\[{tag}\](.*?)\[/{tag}\]", rf"<{tag}>\1</{tag}>", escaped, flags=re.I | re.S
        )
    escaped = re.sub(
        r"\[quote\](.*?)\[/quote\]",
        r"<blockquote class='quote'>\1</blockquote>",
        escaped,
        flags=re.I | re.S,
    )
    escaped = escaped.replace("\n", "<br>")

    for index, body in enumerate(code_blocks):
        escaped = escaped.replace(f"\x00code{index}\x00", f"<pre class='codeblock'>{body}</pre>")
    return escaped


# ---------------------------------------------------------------- pagination


def page_args(page: int) -> dict:
    """Preserve current query args while changing the page number."""
    args = {k: v for k, v in request.args.items() if k != "page"}
    if page > 1:
        args["page"] = page
    return args


def clamp_page(raw: str | None) -> int:
    try:
        page = int(raw or 1)
    except (TypeError, ValueError):
        return 1
    return max(1, min(page, 10_000))
