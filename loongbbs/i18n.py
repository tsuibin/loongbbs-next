"""界面语言层（对照参考站 admin/lang.php 的实现）。

参考站的做法：模板里存英文原文，`lang_zh.php` 提供「英文原文 → 中文」的短语表，
渲染时在**模板源码**上做文本节点替换，语言由 `bblanguage` cookie 决定，
`?lang=zh|en` 切一次即写 cookie 并 302 回干净 URL。

本项目模板里存的是中文（界面早已汉化），所以这里的方向相反：短语表是
「中文原文 → 英文」，默认语言 zh 时原样输出、en 时替换成原版英文措辞。
替换同样只发生在模板输出层（文本节点 + 按钮类属性），不会改写用户内容。
"""

from __future__ import annotations

import re
from functools import lru_cache

from flask import request

SUPPORTED_LANGUAGES = ("zh", "en")
COOKIE_NAME = "bblanguage"
COOKIE_MAX_AGE = 31536000  # 原版同样给一年
CJK_RE = re.compile(r"[\u4e00-\u9fff]")
SPACE_RE = re.compile(r"\s+")

TAG_RE = re.compile(r"<[^<>]*>")
PROTECT_RE = re.compile(
    r"<!--.*?-->|<script\b[^>]*>.*?</script>|<style\b[^>]*>.*?</style>|<textarea\b[^>]*>.*?</textarea>",
    re.S,
)
LABEL_ATTR_RE = re.compile(r'\b(value|alt|title|placeholder)(\s*=\s*")([^"]*)(")', re.I)


def norm(text: str) -> str:
    """查表用的归一化：压空白、统一全角标点，避免「，」与「,」这类差异漏配。"""
    text = text.replace("&nbsp;", " ")
    text = SPACE_RE.sub(" ", text).strip()
    for full, half in (
        ("（", "("), ("）", ")"), ("，", ","), ("；", ";"), ("：", ":"),
        ("！", "!"), ("？", "?"), ("「", '"'), ("」", '"'), ("。", "."),
        ("、", ","), ("…", "..."), ("—", "-"), ("－", "-"),
    ):
        text = text.replace(full, half)
    return text


@lru_cache(maxsize=1)
def phrase_map() -> dict[str, str]:
    """中文原文 → 英文。分模块存放，按模块合并；后加载的覆盖先加载的。"""
    from . import (
        i18n_zh_en_admin,
        i18n_zh_en_common,
        i18n_zh_en_ucp,
        i18n_zh_en_ui,
    )

    merged: dict[str, str] = {}
    for module in (i18n_zh_en_common, i18n_zh_en_ucp, i18n_zh_en_admin, i18n_zh_en_ui):
        merged.update(getattr(module, "MAP", {}))
    return merged


@lru_cache(maxsize=1)
def _normalized_map() -> dict[str, str]:
    out: dict[str, str] = {}
    for zh, en in phrase_map().items():
        key = norm(zh)
        if key and key not in out:
            out[key] = en
    return out


@lru_cache(maxsize=1)
def _prefix_candidates() -> tuple[tuple[str, str], ...]:
    """用于「键 + 动态内容」的前缀匹配：只收以冒号或空格结尾的键，避免误伤。"""
    pairs = [
        (zh, en)
        for zh, en in phrase_map().items()
        if zh.endswith((":", "：", " ")) and len(zh.strip()) >= 3
    ]
    pairs.sort(key=lambda item: -len(item[0]))
    return tuple(pairs)


def translate(text: str) -> str:
    """翻一条短语；查不到就原样返回（与原版 missing key 的行为一致）。

    三级匹配：
    1. 整段（模板里的整句、表头、按钮）；
    2. 「站点名 - 页面名」这类拼接标题，只翻尾段（站名是变量，整串键写不出来）；
    3. 面包屑/带前缀的句子（`&gt; 会员列表`、`注册于: Nov 2026`），
       剥掉前导标记或按最长前缀键替换。
    """
    if not CJK_RE.search(text):
        return text
    table = _normalized_map()
    key = norm(text)
    if key in table:
        return table[key]

    for separator in (" - ", " | "):
        if separator in text:
            head, _, tail = text.rpartition(separator)
            tail_key = norm(tail)
            if CJK_RE.search(tail) and tail_key in table:
                return head + separator + table[tail_key]

    last_space = text.rfind(" ")
    if last_space > 0:
        space_tail = text[last_space + 1:]
        tail_key = norm(space_tail)
        if CJK_RE.search(space_tail) and tail_key in table:
            return text[: last_space + 1] + table[tail_key]

    for marker in ("&gt;", "&lt;", "&laquo;", "&raquo;", ">", "<", "»", "«"):
        if text.lstrip().startswith(marker):
            stripped = text.lstrip()[len(marker):].lstrip()
            stripped_key = norm(stripped)
            if stripped_key in table:
                prefix = text[: len(text) - len(text.lstrip())] + marker + " "
                return prefix + table[stripped_key]

    for phrase_key, phrase_value in _prefix_candidates():
        if text.startswith(phrase_key):
            rest = text[len(phrase_key):]
            if not CJK_RE.search(rest):
                return phrase_value + rest

    return _multi_key_replace(text)


@lru_cache(maxsize=1)
def _long_keys() -> tuple[tuple[str, str], ...]:
    """复刻原版 `strtr` 的「多键替换」：只收长度 >= 3 的原样键，避免单字误伤正文。"""
    pairs = [
        (zh, en)
        for zh, en in phrase_map().items()
        if len(zh.strip()) >= 3 and zh != en
    ]
    pairs.sort(key=lambda item: -len(item[0]))
    return tuple(pairs)


def _multi_key_replace(text: str) -> str:
    out = text
    for zh, en in _long_keys():
        if zh in out:
            out = out.replace(zh, en)
    return out


def default_language() -> str:
    try:
        from .settings import get_setting

        value = (get_setting("defaultlanguage", "zh") or "zh").strip().lower()
    except Exception:
        value = "zh"
    return value if value in SUPPORTED_LANGUAGES else "zh"


def current_language() -> str:
    lang = (request.cookies.get(COOKIE_NAME) or "").strip().lower()
    if lang in SUPPORTED_LANGUAGES:
        return lang
    return default_language()


def language_url(lang: str) -> str:
    """当前页面地址 + lang 参数（原版 vb_lang_url 的等价物）。"""
    from urllib.parse import urlencode

    query = request.args.to_dict(flat=True)
    query["lang"] = lang
    return f"{request.path}?{urlencode(query)}"


def _translate_attr(match: re.Match) -> str:
    attr, prefix, value, quote = match.groups()
    new = translate(value)
    if new == value:
        return match.group(0)
    return f"{attr}{prefix}{new}{quote}"


def translate_html(html: str, translate_attrs: bool = True) -> str:
    """在 HTML 输出上做文本节点 / 按钮属性替换（保护 script、style、textarea、注释）。"""
    if not isinstance(html, str) or "<" not in html:
        return html

    stash: dict[str, str] = {}

    def _stash(match: re.Match) -> str:
        token = f"\x00{len(stash)}\x00"
        stash[token] = match.group(0)
        return token

    protected = PROTECT_RE.sub(_stash, html)
    parts = TAG_RE.split(protected)
    tags = TAG_RE.findall(protected)

    rebuilt: list[str] = []
    for index, chunk in enumerate(parts):
        if CJK_RE.search(chunk):
            stripped = chunk.strip()
            if stripped:
                lead = chunk[: len(chunk) - len(chunk.lstrip())]
                tail = chunk[len(chunk.rstrip()):]
                chunk = lead + translate(stripped) + tail
        rebuilt.append(chunk)
        if index < len(tags):
            tag = tags[index]
            if translate_attrs:
                tag = LABEL_ATTR_RE.sub(_translate_attr, tag)
            rebuilt.append(tag)

    out = "".join(rebuilt)
    for token, original in stash.items():
        out = out.replace(token, original)
    return out


@lru_cache(maxsize=1)
def _admin_reverse_regex() -> re.Pattern:
    """英文骨架的整词匹配正则（长键优先，一次扫描）。"""
    from .i18n_admin_zh_reverse import MAP

    keys = sorted(MAP, key=len, reverse=True)
    return re.compile(r"(?<![\w&])(?:" + "|".join(re.escape(key) for key in keys) + r")(?![\w&])")


def _reverse_attr(match: re.Match) -> str:
    from .i18n_admin_zh_reverse import MAP

    attr, prefix, value, quote = match.groups()
    new = _admin_reverse_regex().sub(lambda m: MAP[m.group(0)], value)
    if new == value:
        return match.group(0)
    return f"{attr}{prefix}{new}{quote}"


def translate_html_reverse(html: str, translate_attrs: bool = True) -> str:
    """后台中文态：把模板里保留的英文骨架（表头/按钮）按参考站语言包换成中文。

    只处理文本节点和按钮类属性，保护 script、style、textarea、注释，
    因此不会碰标签结构、URL、字段名。
    """
    if not isinstance(html, str) or "<" not in html:
        return html

    from .i18n_admin_zh_reverse import MAP

    regex = _admin_reverse_regex()
    stash: dict[str, str] = {}

    def _stash(match: re.Match) -> str:
        token = f"\x00{len(stash)}\x00"
        stash[token] = match.group(0)
        return token

    protected = PROTECT_RE.sub(_stash, html)
    parts = TAG_RE.split(protected)
    tags = TAG_RE.findall(protected)

    rebuilt: list[str] = []
    for index, chunk in enumerate(parts):
        chunk = regex.sub(lambda m: MAP[m.group(0)], chunk)
        rebuilt.append(chunk)
        if index < len(tags):
            tag = tags[index]
            if translate_attrs:
                tag = LABEL_ATTR_RE.sub(_reverse_attr, tag)
            rebuilt.append(tag)

    out = "".join(rebuilt)
    for token, original in stash.items():
        out = out.replace(token, original)
    return out
