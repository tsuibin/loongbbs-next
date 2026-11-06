"""misc.php 的对应页：vB 代码帮助与表情列表。"""
from __future__ import annotations

from flask import Blueprint, render_template

from .utils import SMILIES

bp = Blueprint("misc", __name__, url_prefix="/misc")


@bp.get("/bbcode")
def bbcode():
    """对应 vB misc.php?action=bbcode，发帖页「[帮助]」指向这里（#buttons 锚点）。"""
    return render_template("misc/bbcode.html")


@bp.get("/smilies")
def smilies():
    """对应 vB misc.php?action=smilies：可用的表情清单。"""
    return render_template("misc/smilies.html", smilies=SMILIES)
