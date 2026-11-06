"""misc.php 的对应页：vB 代码帮助、表情列表与常见问题（FAQ）。"""
from __future__ import annotations

from flask import Blueprint, render_template, request

from .faq_zh import translate_faq_html
from .i18n import current_language
from .settings import get_setting
from .utils import SMILIES

bp = Blueprint("misc", __name__, url_prefix="/misc")

# vB misc.php 的 faq 分支：page 为空渲染 faq.html（三节目录），1/2/3 渲染 faq1/2/3.html
FAQ_PAGES = {
    1: "misc/faq1.html",
    2: "misc/faq2.html",
    3: "misc/faq3.html",
}


@bp.get("/bbcode")
def bbcode():
    """对应 vB misc.php?action=bbcode，发帖页「[帮助]」指向这里（#buttons 锚点）。"""
    return render_template("misc/bbcode.html")


@bp.get("/smilies")
def smilies():
    """对应 vB misc.php?action=smilies：可用的表情清单。"""
    return render_template("misc/smilies.html", smilies=SMILIES)


@bp.get("/faq")
def faq():
    """对应 vB misc.php?action=faq[&page=N]。

    与参考站一致：不带 page 时是 FAQ 目录页（三节 + 27 条锚点链接），
    page=1/2/3 分别是「用户自助 / 版面使用 / 阅读与发帖」分节页。
    FAQ 正文沿用参考站模板里的英文原文（原版在中文语言包下同样是英文）。
    """
    page = request.args.get("page", type=int) or 0
    template = FAQ_PAGES.get(page, "misc/faq.html")
    html_text = render_template(
        template,
        inbox_name=get_setting("inboxname") or "Inbox",
        sentitems_name=get_setting("sentitemsname") or "Sent Items",
        attachextensions=(get_setting("attachextensions") or "").replace(",", ", "),
        censor_char=((get_setting("censorchar") or "*").strip()[:1] or "*"),
    )
    if current_language() == "zh":
        # 参考站在中文语言下会把这些 phrase 替换进 FAQ 模板，结果是中英混排
        html_text = translate_faq_html(html_text)
    return html_text
