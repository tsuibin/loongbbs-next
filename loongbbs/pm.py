"""Private messaging."""
from __future__ import annotations

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func, or_, select

from .extensions import db
from .models import PrivateMessage, User, utcnow
from .settings import get_setting
from .utils import format_dt, render_body, time_ago

bp = Blueprint("pm", __name__, url_prefix="/pm")


def _pm_int(name: str, default: int) -> int:
    try:
        return int(str(get_setting(name, str(default)) or default).strip())
    except (TypeError, ValueError):
        return default


def _minutes_since(value) -> float:
    if value is None:
        return 1e9
    if value.tzinfo is None:
        from datetime import timezone

        value = value.replace(tzinfo=timezone.utc)
    return (utcnow() - value).total_seconds() / 60


@bp.before_request
@login_required
def _require_pms_enabled():
    """组 19 enablepms：关闭私信后所有 /pm 页面都只显示说明页。"""
    if get_setting("enablepms", "1") != "1":
        return render_template("pm_disabled.html"), 403
    return None


def _inbox_rows(user: User):
    return (
        db.session.execute(
            select(PrivateMessage)
            .where(PrivateMessage.recipient_id == user.id)
            .order_by(PrivateMessage.created_at.desc())
            .limit(50)
        )
        .scalars()
        .all()
    )


def _sent_rows(user: User):
    return (
        db.session.execute(
            select(PrivateMessage)
            .where(PrivateMessage.sender_id == user.id)
            .order_by(PrivateMessage.created_at.desc())
            .limit(50)
        )
        .scalars()
        .all()
    )


@bp.get("/")
@login_required
def inbox():
    rows = _inbox_rows(current_user)
    unread = sum(1 for row in rows if row.read_at is None)
    return render_template(
        "pm/inbox.html", rows=rows, unread=unread, time_ago=time_ago
    )


@bp.get("/sent")
@login_required
def sent():
    return render_template("pm/sent.html", rows=_sent_rows(current_user), time_ago=time_ago)


@bp.get("/new")
@login_required
def compose_form():
    to = (request.args.get("to") or "").strip()
    subject = ""
    body = ""
    reply_id = request.args.get("reply")
    if reply_id:
        original = db.session.get(PrivateMessage, int(reply_id))
        if original and original.recipient_id == current_user.id:
            to = original.sender.username
            subject = original.subject if original.subject.startswith("Re:") else f"Re: {original.subject}"
            body = f"[quote]{original.body}[/quote]\n\n"
    return render_template("pm/compose.html", to=to, subject=subject, body=body)


@bp.post("/new")
@login_required
def compose():
    to_name = (request.form.get("to") or "").strip()
    subject = (request.form.get("subject") or "").strip()
    body = (request.form.get("body") or "").strip()

    recipient = db.session.scalar(select(User).where(User.username == to_name))
    errors = []
    if recipient is None:
        errors.append("收件人不存在。")
    elif recipient.id == current_user.id:
        errors.append("不能给自己发私信。")
    if not subject:
        errors.append("主题不能为空。")
    if not body:
        errors.append("正文不能为空。")

    # 组 19 pmmaxchars：私信正文的最大字符数（原版 private2.php 的 $pmmaxchars）
    max_chars = _pm_int("pmmaxchars", 1000)
    if max_chars > 0 and len(body) > max_chars:
        errors.append(f"悄悄话正文最多 {max_chars} 个字符，请精简后再发。")

    # 组 19 pmfloodtime：两次发信的最小间隔（原版 private2.php:515）
    flood = _pm_int("pmfloodtime", 60)
    if flood > 0:
        last_sent = db.session.scalar(
            select(func.max(PrivateMessage.created_at)).where(
                PrivateMessage.sender_id == current_user.id
            )
        )
        elapsed = _minutes_since(last_sent) * 60
        if last_sent is not None and elapsed < flood:
            errors.append(f"两次发信至少间隔 {flood} 秒，请稍后再试。")

    # 组 19 pmquota：收件人收件箱上限（原版 private.php 的 $pmquota）
    quota = _pm_int("pmquota", 70)
    if recipient is not None and quota > 0:
        in_inbox = db.session.scalar(
            select(func.count())
            .select_from(PrivateMessage)
            .where(PrivateMessage.recipient_id == recipient.id)
        ) or 0
        if in_inbox >= quota:
            errors.append(f"{recipient.username} 的悄悄话收件箱已满（上限 {quota} 条）。")

    if errors:
        for message in errors:
            flash(message, "error")
        return render_template("pm/compose.html", to=to_name, subject=subject, body=body), 400

    message = PrivateMessage(
        sender_id=current_user.id,
        recipient_id=recipient.id,
        subject=subject[:200],
        body=body,
        created_at=utcnow(),
    )
    db.session.add(message)
    db.session.commit()

    flash("私信已发送。", "success")
    return redirect(url_for("pm.sent"))


@bp.get("/<int:message_id>")
@login_required
def read(message_id: int):
    message = db.session.get(PrivateMessage, message_id)
    if message is None:
        abort(404)
    if current_user.id not in (message.sender_id, message.recipient_id):
        abort(403)

    if message.recipient_id == current_user.id and message.read_at is None:
        message.read_at = utcnow()
        db.session.commit()

    return render_template(
        "pm/read.html",
        message=message,
        body=render_body(message.body, prefix="priv"),
        format_dt=format_dt,
    )
