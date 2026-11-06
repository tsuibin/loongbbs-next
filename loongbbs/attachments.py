"""Attachment upload, inline display and download."""
from __future__ import annotations

import mimetypes
import re
import secrets
from pathlib import Path

from flask import Blueprint, abort, current_app, redirect, render_template, request, send_file, url_for
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from .extensions import db
from .models import Attachment, Post, utcnow
from .settings import get_setting

bp = Blueprint("attachments", __name__)

MAX_PER_POST = 5
BLOCKED_EXT = {
    "php", "php3", "php4", "php5", "phtml", "phar", "cgi", "pl", "py", "sh", "exe",
    "bat", "cmd", "com", "js", "jsp", "asp", "aspx", "htaccess",
}
IMAGE_TYPES = {
    "image/jpeg", "image/png", "image/gif", "image/webp", "image/bmp", "image/svg+xml",
}


def _detect_type(path: Path, filename: str) -> str:
    guessed, _ = mimetypes.guess_type(filename)
    with path.open("rb") as handle:
        head = handle.read(16)
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if head.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if head.startswith(b"GIF8"):
        return "image/gif"
    if head.startswith(b"RIFF") and head[8:12] == b"WEBP":
        return "image/webp"
    if head.startswith(b"BM"):
        return "image/bmp"
    return guessed or "application/octet-stream"


def save_uploads(post: Post, files) -> list[Attachment]:
    """Persist uploaded files for a post. Returns the attachments created."""
    if not files:
        return []

    created: list[Attachment] = []
    upload_dir = Path(current_app.config["UPLOAD_DIR"])
    upload_dir.mkdir(parents=True, exist_ok=True)

    existing = len(post.attachments or [])

    for storage in files:
        if not storage or not storage.filename:
            continue
        if existing + len(created) >= MAX_PER_POST:
            break

        display_name = secure_filename(storage.filename) or "attachment"
        ext = display_name.rsplit(".", 1)[-1].lower() if "." in display_name else ""
        if ext in BLOCKED_EXT:
            continue

        stored_name = f"{secrets.token_hex(16)}.bin"
        target = upload_dir / stored_name
        storage.save(target)
        size = target.stat().st_size
        if size == 0:
            target.unlink(missing_ok=True)
            continue

        content_type = _detect_type(target, display_name)
        if content_type not in IMAGE_TYPES and content_type.startswith("image/"):
            content_type = "application/octet-stream"

        attachment = Attachment(
            post_id=post.id,
            filename=display_name[:255],
            stored_name=stored_name,
            content_type=content_type,
            size=size,
            uploaded_at=utcnow(),
        )
        db.session.add(attachment)
        created.append(attachment)

    return created


def _path_for(attachment: Attachment) -> Path:
    return Path(current_app.config["UPLOAD_DIR"]) / attachment.stored_name


@bp.get("/attachment/<int:attachment_id>")
def download(attachment_id: int):
    attachment = db.session.get(Attachment, attachment_id)
    if attachment is None:
        abort(404)

    path = _path_for(attachment)
    if not path.exists():
        abort(404)

    inline = request.args.get("inline") == "1" and attachment.is_image
    response = send_file(
        path,
        mimetype=attachment.content_type,
        as_attachment=not inline,
        download_name=attachment.filename,
        max_age=3600,
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    if not inline:
        response.headers["Content-Disposition"] = (
            f"attachment; filename*=UTF-8''{_rfc5987(attachment.filename)}"
        )
    return response


def _rfc5987(name: str) -> str:
    from urllib.parse import quote

    return quote(name, safe="")


@bp.post("/attachment/<int:attachment_id>/delete")
@login_required
def delete(attachment_id: int):
    attachment = db.session.get(Attachment, attachment_id)
    if attachment is None:
        abort(404)
    if attachment.post.author_id != current_user.id and not current_user.is_admin:
        abort(403)

    path = _path_for(attachment)
    db.session.delete(attachment)
    db.session.commit()
    path.unlink(missing_ok=True)

    return redirect(request.referrer or url_for("forums.index"))


def thumb_limits() -> tuple[int, int] | None:
    """Return (width, height) when thumbnail mode is on, else None."""
    if get_setting("thumb_mode") != "1":
        return None
    try:
        width = int(get_setting("thumb_width") or 480)
        height = int(get_setting("thumb_height") or 360)
    except ValueError:
        width, height = 480, 360
    if width <= 0 or height <= 0:
        return None
    return width, height


def attachment_css() -> str:
    """Inline stylesheet for attachment images (thin frame + thumbnail limits)."""
    limits = thumb_limits()
    extra = ""
    if limits:
        extra = (
            "\n.attachment-thumb img { max-width: %dpx; max-height: %dpx; width: auto; height: auto; cursor: zoom-in; }"
            % limits
        )
    return (
        "img.attachment-image { border: 1px solid #C6C6D0; padding: 5px; background: #fff;"
        " border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,.12); box-sizing: border-box;"
        " max-width: 100%; height: auto; vertical-align: middle; }" + extra
    )
