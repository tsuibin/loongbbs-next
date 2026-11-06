"""Database models for LoongBBS Next."""
from __future__ import annotations

from datetime import datetime, timezone

from flask_login import UserMixin
from sqlalchemy import func, select
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db, login_manager


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    is_banned = db.Column(db.Boolean, nullable=False, default=False)
    signature = db.Column(db.Text, nullable=False, default="")
    joined_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    last_seen = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    threads = db.relationship("Thread", back_populates="author", lazy="dynamic")
    posts = db.relationship("Post", back_populates="author", lazy="dynamic")

    def set_password(self, raw: str) -> None:
        self.password_hash = generate_password_hash(raw)

    def verify_password(self, raw: str) -> bool:
        return check_password_hash(self.password_hash, raw)

    @property
    def post_count(self) -> int:
        return db.session.scalar(
            select(func.count(Post.id)).where(Post.author_id == self.id, Post.is_deleted.is_(False))
        ) or 0

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<User {self.username}>"


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    return db.session.get(User, int(user_id))


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    position = db.Column(db.Integer, nullable=False, default=0)

    forums = db.relationship(
        "Forum", back_populates="category", order_by="Forum.position", lazy="selectin"
    )


class Forum(db.Model):
    __tablename__ = "forums"

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    position = db.Column(db.Integer, nullable=False, default=0)
    is_closed = db.Column(db.Boolean, nullable=False, default=False)

    category = db.relationship("Category", back_populates="forums")
    threads = db.relationship("Thread", back_populates="forum", lazy="dynamic")

    @property
    def thread_count(self) -> int:
        return db.session.scalar(
            select(func.count(Thread.id)).where(Thread.forum_id == self.id)
        ) or 0

    @property
    def post_count(self) -> int:
        return db.session.scalar(
            select(func.count(Post.id))
            .join(Thread, Thread.id == Post.thread_id)
            .where(Thread.forum_id == self.id, Post.is_deleted.is_(False))
        ) or 0

    @property
    def last_post(self) -> Post | None:
        return db.session.scalar(
            select(Post)
            .join(Thread, Thread.id == Post.thread_id)
            .where(Thread.forum_id == self.id, Post.is_deleted.is_(False))
            .order_by(Post.created_at.desc())
            .limit(1)
        )


class Thread(db.Model):
    __tablename__ = "threads"

    id = db.Column(db.Integer, primary_key=True)
    forum_id = db.Column(db.Integer, db.ForeignKey("forums.id"), nullable=False, index=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, index=True)
    last_post_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, index=True)
    is_sticky = db.Column(db.Boolean, nullable=False, default=False)
    is_closed = db.Column(db.Boolean, nullable=False, default=False)
    views = db.Column(db.Integer, nullable=False, default=0)

    forum = db.relationship("Forum", back_populates="threads")
    author = db.relationship("User", back_populates="threads")
    posts = db.relationship("Post", back_populates="thread", lazy="dynamic", order_by="Post.created_at")

    @property
    def reply_count(self) -> int:
        return db.session.scalar(
            select(func.count(Post.id)).where(Post.thread_id == self.id, Post.is_deleted.is_(False))
        ) or 0

    @property
    def last_post(self) -> Post | None:
        return db.session.scalar(
            select(Post)
            .where(Post.thread_id == self.id, Post.is_deleted.is_(False))
            .order_by(Post.created_at.desc())
            .limit(1)
        )


class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(db.Integer, db.ForeignKey("threads.id"), nullable=False, index=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    body = db.Column(db.Text, nullable=False, default="")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, index=True)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=True)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)

    thread = db.relationship("Thread", back_populates="posts")
    author = db.relationship("User", back_populates="posts")
    attachments = db.relationship(
        "Attachment", back_populates="post", cascade="all, delete-orphan", lazy="selectin"
    )


class Attachment(db.Model):
    __tablename__ = "attachments"

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False, index=True)
    filename = db.Column(db.String(255), nullable=False)
    stored_name = db.Column(db.String(255), nullable=False)
    content_type = db.Column(db.String(120), nullable=False, default="application/octet-stream")
    size = db.Column(db.Integer, nullable=False, default=0)
    uploaded_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    post = db.relationship("Post", back_populates="attachments")

    @property
    def is_image(self) -> bool:
        return self.content_type.startswith("image/")


class PrivateMessage(db.Model):
    __tablename__ = "private_messages"

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    subject = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False, default="")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, index=True)
    read_at = db.Column(db.DateTime(timezone=True), nullable=True)

    sender = db.relationship("User", foreign_keys=[sender_id])
    recipient = db.relationship("User", foreign_keys=[recipient_id])


class Setting(db.Model):
    __tablename__ = "settings"

    key = db.Column(db.String(64), primary_key=True)
    value = db.Column(db.Text, nullable=False, default="")
