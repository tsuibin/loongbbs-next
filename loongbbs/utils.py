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
_PHP_BLOCK = re.compile(r"\[php\](.*?)\[/php\]", re.I | re.S)
# [size=3] [font=arial] [color=red] 的属性值：只允许字母、数字、空格、# 和 _
_TAG_VALUE_OK = re.compile(r"^[A-Za-z0-9#_\s\-]{1,40}$")


def _attr_value(raw: str, default: str) -> str:
    """属性值白名单校验，非法值直接回落，避免把用户文本塞进标签属性。"""
    value = (raw or "").strip()
    return value if _TAG_VALUE_OK.match(value) else default


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


def _img_tag(match: re.Match) -> str:
    url = match.group(1).strip()
    if not _URL_OK.match(url):
        return url
    return f'<img src="{url}" border="0" alt="">'


def _size_tag(match: re.Match) -> str:
    size = (match.group(1) or "").strip()
    if not size.isdigit() or not 1 <= int(size) <= 7:
        return match.group(2)
    return f'<font size="{int(size)}">{match.group(2)}</font>'


def _font_tag(match: re.Match) -> str:
    face = _attr_value(match.group(1), "arial")
    return f'<font face="{face}">{match.group(2)}</font>'


def _color_tag(match: re.Match) -> str:
    color = _attr_value(match.group(1), "black")
    return f'<font color="{color}">{match.group(2)}</font>'


def _list_tag(match: re.Match) -> str:
    inner = match.group(1)
    items = [item.strip() for item in inner.split("[*]")]
    items = [item for item in items if item]
    return "<ul>" + "".join(f"<li>{item}</li>" for item in items) + "</ul>"


# vB 2.3.11 安装时自带的 11 个表情：代码、含义、images/smilies 下的文件名
SMILIES = (
    (":)", "微笑", "smile.gif"),
    (":D", "大笑", "biggrin.gif"),
    (":(", "皱眉", "frown.gif"),
    (":o", "尴尬", "redface.gif"),
    (":p", "吐舌", "tongue.gif"),
    (";)", "眨眼", "wink.gif"),
    (":cool:", "酷", "cool.gif"),
    (":rolleyes:", "翻白眼", "rolleyes.gif"),
    (":mad:", "生气", "mad.gif"),
    (":confused:", "困惑", "confused.gif"),
    (":eek:", "惊讶", "eek.gif"),
)


def smilie_img(filename: str, title: str) -> str:
    return (
        f'<img src="/static/images/smilies/{filename}" border="0" alt="{title}" title="{title}">'
    )


def _posting_options() -> dict[str, str]:
    """发帖代码权限：读后台「发帖代码权限」组的设置，拿不到时按原版默认全开。"""
    try:
        from .settings import get_settings

        return get_settings()
    except Exception:  # pragma: no cover - 没有 app context 时（脚本、测试）
        return {}


def _flag(options: dict[str, str], key: str, default: str = "1") -> bool:
    return str(options.get(key, default) or default).strip().lower() not in ("0", "", "no", "off")


def render_body(text: str) -> str:
    """Escape everything, then re-enable a small BBCode subset.

    Raw HTML is never allowed, so a post can not inject markup; the only tags
    that can appear in the output are the ones built here.

    解析范围受后台「发帖代码权限」组控制（vB 的 allowbbcode / allowhtml /
    allowbbimagecode / allowsmilies / allowdynimg / maximages）。
    """
    if not text:
        return ""

    options = _posting_options()
    allow_bbcode = _flag(options, "allowbbcode")
    allow_img = _flag(options, "allowbbimagecode", "0")
    allow_smilies = _flag(options, "allowsmilies")
    allow_dynimg = _flag(options, "allowdynimg", "0")
    try:
        max_images = int(str(options.get("maximages", "10") or "10").strip())
    except ValueError:
        max_images = 10

    escaped = html.escape(text.replace("\r\n", "\n").replace("\r", "\n"), quote=False)

    if not allow_bbcode:
        # 关掉 vB 代码后只剩换行与表情（表情是独立开关）
        escaped = escaped.replace("\n", "<br>")
        if allow_smilies:
            for code, title, filename in SMILIES:
                escaped = escaped.replace(code, smilie_img(filename, title))
        return escaped

    # Pull [code] blocks out first: inside them newlines must stay newlines.
    code_blocks: list[str] = []

    def stash(match: re.Match) -> str:
        code_blocks.append(match.group(1))
        return f"\x00code{len(code_blocks) - 1}\x00"

    escaped = _CODE_BLOCK.sub(stash, escaped)
    escaped = _PHP_BLOCK.sub(stash, escaped)

    escaped = re.sub(r"\[url=([^\]\s]+)\](.*?)\[/url\]", _url_tagged, escaped, flags=re.I | re.S)
    escaped = re.sub(r"\[url\](.*?)\[/url\]", _url_plain, escaped, flags=re.I | re.S)
    escaped = re.sub(
        r"\[email\](.*?)\[/email\]",
        r"<a href='mailto:\1'>\1</a>",
        escaped,
        flags=re.I | re.S,
    )

    drawn_images = 0

    def img_replace(match: re.Match) -> str:
        nonlocal drawn_images
        url = match.group(1).strip()
        if not allow_img or not _URL_OK.match(url):
            return url
        if not allow_dynimg and ("?" in url or "&" in url):
            return url
        if drawn_images >= max_images:
            return url
        drawn_images += 1
        return f'<img src="{url}" border="0" alt="">'

    escaped = re.sub(r"\[img\](.*?)\[/img\]", img_replace, escaped, flags=re.I | re.S)
    for tag in ("b", "i", "u", "s"):
        escaped = re.sub(
            rf"\[{tag}\](.*?)\[/{tag}\]", rf"<{tag}>\1</{tag}>", escaped, flags=re.I | re.S
        )
    # [size=3] / [font=arial] / [color=red] 与 vB 一样落到 <font> 上
    escaped = re.sub(
        r"\[size=(.+?)\](.*?)\[/size\]", _size_tag, escaped, flags=re.I | re.S
    )
    escaped = re.sub(
        r"\[font=(.+?)\](.*?)\[/font\]", _font_tag, escaped, flags=re.I | re.S
    )
    escaped = re.sub(
        r"\[color=(.+?)\](.*?)\[/color\]", _color_tag, escaped, flags=re.I | re.S
    )
    # [list][*]项目[/list]：vB 的有序/无序列表
    escaped = re.sub(r"\[list\](.*?)\[/list\]", _list_tag, escaped, flags=re.I | re.S)
    escaped = re.sub(
        r"\[quote\](.*?)\[/quote\]",
        r"<blockquote class='quote'>\1</blockquote>",
        escaped,
        flags=re.I | re.S,
    )
    escaped = escaped.replace("\n", "<br>")

    # 表情：和 vB 一样在解析完 BBCode 后按代码替换（[code] 块已被暂存，不会被替换）
    if allow_smilies:
        for code, title, filename in SMILIES:
            escaped = escaped.replace(code, smilie_img(filename, title))

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
