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


# ------------------------------------------------ 组 12：vB 的 PHP 日期格式
# vB 后台存的是 PHP date() 的格式串（dateformat=m-d-Y、timeformat=h:i A、
# registereddateformat=M Y），这里逐字符翻译成 strftime，供页面使用。
_PHP_DATE_TOKENS = {
    "d": "%d", "j": "%d", "m": "%m", "n": "%m",
    "Y": "%Y", "y": "%y",
    "M": "%b", "F": "%B", "D": "%a", "l": "%A",
    "h": "%I", "H": "%H", "g": "%I", "G": "%H",
    "i": "%M", "s": "%S",
    "A": "%p", "a": "%p",
    "S": "", "U": "",
}


def php_to_strftime(fmt: str) -> str:
    """把 PHP date() 格式串翻成 strftime 格式串（未知字符原样保留）。"""
    out: list[str] = []
    for char in fmt or "":
        if char == "%":
            out.append("%%")
        elif char in _PHP_DATE_TOKENS:
            out.append(_PHP_DATE_TOKENS[char])
        elif char == "\\":
            continue
        else:
            out.append(char)
    return "".join(out)


def _site_fmt(key: str, default: str) -> str:
    from .settings import get_setting

    return php_to_strftime(get_setting(key, default) or default)


def format_date(value: datetime | None) -> str:
    return format_dt(value, _site_fmt("dateformat", "m-d-Y"))


def format_time(value: datetime | None) -> str:
    return format_dt(value, _site_fmt("timeformat", "h:i A"))


def format_datetime(value: datetime | None) -> str:
    return f"{format_date(value)} {format_time(value)}"


def format_joined(value: datetime | None) -> str:
    return format_dt(value, _site_fmt("registereddateformat", "M Y"))


def now_gmt(fmt: str | None = None) -> str:
    """页脚那一行 ``The time now is ...`` 用的当前站点时间。"""
    fmt = fmt or _site_fmt("timeformat", "h:i A")
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
    from .i18n import current_language

    english = current_language() == "en"
    if value is None:
        return "—"
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - value
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return "Just now" if english else "刚刚"
    if seconds < 3600:
        minutes = seconds // 60
        if english:
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        return f"{minutes} 分钟前"
    if seconds < 86400:
        hours = seconds // 3600
        if english:
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        return f"{hours} 小时前"
    if seconds < 86400 * 30:
        days = seconds // 86400
        if english:
            return f"{days} day{'s' if days != 1 else ''} ago"
        return f"{days} 天前"
    return format_dt(value, "%Y-%m-%d")


# ---------------------------------------------------------------- BBCode

_URL_OK = re.compile(r"^(https?://|mailto:)", re.I)
_CODE_BLOCK = re.compile(r"\[code\](.*?)\[/code\]", re.I | re.S)
_PHP_BLOCK = re.compile(r"\[php\](.*?)\[/php\]", re.I | re.S)
# [size=3] [font=arial] [color=red] 的属性值：只允许字母、数字、空格、# 和 _
# 标签参数会落进 <font size="…"> 之类属性，只允许不含引号/尖括号/换行的值
_TAG_VALUE_OK = re.compile(r"^[^<>\"'\r\n]{1,60}$")


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


def censor_text(text: str) -> str:
    """vB 的 censortext()：按后台「敏感词过滤选项」组替换入帖文字。

    规则照原版（admin/functions.php）：
    - 只有 enablecensor=1 且 censorwords 非空才生效
    - censorwords 用空格分隔；写成 {词} 的是「整词」匹配（前后不能是英文字母）
    - 命中部分替换成 censorchar 重复到原词长度（默认 *）
    - 结尾把软连字符与不换行空格换成下划线
    """
    if not text:
        return text

    options = _posting_options()
    if not _flag(options, "enablecensor", "0"):
        return text
    words = (options.get("censorwords") or "").strip()
    if not words:
        return text

    char = (options.get("censorchar") or "*").strip()[:1] or "*"
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

    return text.replace("\u00ad", "_").replace("\u00a0", "_")


def dowordwrap(text: str) -> str:
    """vB admin/functions.php 的 dowordwrap：在 wordwrap 宽度处硬断词。

    原版正则是把连续 N 个「不是空白、标点、HTML 尖括号」的字符后面补一个空格加换行，
    避免超长单词或网址把表格撑破；wordwrap=0 表示不断。
    """
    from .settings import get_setting

    try:
        width = int(get_setting("wordwrap") or 0)
    except (TypeError, ValueError):
        width = 50
    if width <= 0 or not text:
        return text
    pattern = re.compile(r"([^\n\r ?&./<>\"\-]{%d})" % width)
    return pattern.sub(lambda match: " " + match.group(1) + "\n", text)


_BBCODE_RULES: list[tuple[str, int, str]] | None = None

# vBulletin 2.3.11 安装包自带的 9 条 bbcode 定义（bbcodes 表为空时的兜底，
# 也让新建的空库在没有 seed 的情况下仍能渲染基本代码）
DEFAULT_BBCODES: list[tuple[str, int, str]] = [
    ("b", 0, "<b>\\4</b>"),
    ("i", 0, "<i>\\4</i>"),
    ("email", 0, '<a href="mailto:\\4">\\4</a>'),
    ("email", 1, '<a href="mailto:\\5">\\7</a>'),
    ("size", 1, '<font size="\\5">\\7</font>'),
    ("quote", 0, "<blockquote><smallfont>quote:</smallfont><hr>\\4<hr></blockquote>"),
    ("u", 0, "<u>\\4</u>"),
    ("color", 1, '<font color="\\5">\\7</font>'),
    ("font", 1, '<font face="\\5">\\7</font>'),
]


def _load_bbcode_rules() -> list[tuple[str, int, str]]:
    rows = []
    try:
        from sqlalchemy import select

        from .extensions import db
        from .models import BBCode

        rows = db.session.execute(select(BBCode).order_by(BBCode.id)).scalars().all()
    except Exception:  # pragma: no cover - 没有 app context / 表还没建
        return []
    return [
        ((row.bbcodetag or "").strip(), int(row.twoparams or 0), row.bbcodereplacement or "")
        for row in rows
        if (row.bbcodetag or "").strip()
    ]


def _bbcode_rules() -> list[tuple[str, int, str]]:
    """读 bbcodes 表得到 (tag, twoparams, replacement)，对应原版的 $bbcodecache。

    有 app context 时按请求缓存（后台改一条 Custom vB Code 后立即影响下一次渲染），
    脚本 / 无请求的场景退回进程级缓存。表里缺的 tag 用 DEFAULT_BBCODES 兜底，
    同 (tag, twoparams) 以表里的为准。
    """
    global _BBCODE_RULES
    try:
        from flask import g, has_app_context

        if has_app_context():
            cached = g.get("_bbcode_rules")
            if cached is not None:
                return cached
            rules = _merge_bbcode_rules(_load_bbcode_rules())
            g._bbcode_rules = rules
            return rules
    except Exception:  # pragma: no cover
        pass
    if _BBCODE_RULES is None:
        _BBCODE_RULES = _merge_bbcode_rules(_load_bbcode_rules())
    return _BBCODE_RULES


def _merge_bbcode_rules(
    rows: list[tuple[str, int, str]],
) -> list[tuple[str, int, str]]:
    """表里有数据就完全以表为准（原版 bbcodecache 就是这么用的）；
    表为空（新库还没 seed、或测试库）才退回安装包自带的 9 条默认定义。"""
    if rows:
        return rows
    return list(DEFAULT_BBCODES)


def _bbcode_fill(replacement: str, content: str, param: str | None) -> str:
    """把原版 replacement 里的 \\4（内容）/\\5（参数）/\\7（双参数的内容）填上。

    \\5 会落进 ``<font size="…">`` 这类 HTML 属性里，所以先过白名单，
    非法（含引号、尖括号等）一律丢弃，防止用户借标签参数注入标记。
    """
    out = replacement.replace("\\4", content).replace("\\7", content)
    if param is not None:
        value = (param or "").strip()
        out = out.replace("\\5", value if _TAG_VALUE_OK.match(value) else "")
    return out


def _apply_bbcode_table(text: str) -> str:
    """按 bbcodes 表逐条替换：先双参数 [tag=param]…[/tag]，再单参数 [tag]…[/tag]。"""
    for tag, twoparams, replacement in _bbcode_rules():
        escaped_tag = re.escape(tag)
        if twoparams:
            def two(match: re.Match, replacement: str = replacement) -> str:
                return _bbcode_fill(replacement, match.group(2), match.group(1))

            text = re.sub(
                rf"\[{escaped_tag}=(.+?)\](.*?)\[/{escaped_tag}\]",
                two,
                text,
                flags=re.I | re.S,
            )
        else:
            def one(match: re.Match, replacement: str = replacement) -> str:
                return _bbcode_fill(replacement, match.group(1), None)

            text = re.sub(
                rf"\[{escaped_tag}\](.*?)\[/{escaped_tag}\]",
                one,
                text,
                flags=re.I | re.S,
            )
    return text


def render_body(text: str, prefix: str = "") -> str:
    """Escape everything, then re-enable a small BBCode subset.

    Raw HTML is never allowed, so a post can not inject markup; the only tags
    that can appear in the output are the ones built here.

    解析范围受后台「发帖代码权限」组控制（vB 的 allowbbcode / allowhtml /
    allowbbimagecode / allowsmilies / allowdynimg / maximages）；传 prefix="priv"
    时改读「私信选项」组的 privallowbbcode / privallowbbimagecode / privallowsmilies。
    """
    if not text:
        return ""

    options = _posting_options()
    allow_bbcode = _flag(options, f"{prefix}allowbbcode")
    allow_img = _flag(options, f"{prefix}allowbbimagecode", "0")
    allow_smilies = _flag(options, f"{prefix}allowsmilies")
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
    # b / i / u / email / size / color / font / quote 一律由后台 bbcodes 表驱动
    # （原版就是读 bbcodecache，所以后台 Custom vB Codes 改一条就立即影响前台渲染）
    escaped = _apply_bbcode_table(escaped)
    # [s] 原版 2.3.11 的 bbcode 表里没有，属于本板补齐的删除线写法
    escaped = re.sub(r"\[s\](.*?)\[/s\]", r"<s>\1</s>", escaped, flags=re.I | re.S)
    # [list][*]项目[/list]：vB 的有序/无序列表（表里没有，仍由这里处理）
    escaped = re.sub(r"\[list\](.*?)\[/list\]", _list_tag, escaped, flags=re.I | re.S)
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
