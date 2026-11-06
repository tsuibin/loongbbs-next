"""Private messaging."""
from __future__ import annotations

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_, select

from .extensions import db
from .models import PrivateMessage, User, utcnow
from .utils import format_dt, render_body, time_ago

bp = Blueprint("pm", __name__, url_prefix="/pm")


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
        body=render_body(message.body),
        format_dt=format_dt,
    )
