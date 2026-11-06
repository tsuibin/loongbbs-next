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
    # ---- 个人资料（对应 vB modifyprofile 的「可选信息」与 profile field）----
    homepage = db.Column(db.String(255), nullable=False, default="", server_default="")
    icq = db.Column(db.String(30), nullable=False, default="", server_default="")
    aim = db.Column(db.String(30), nullable=False, default="", server_default="")
    yahoo = db.Column(db.String(30), nullable=False, default="", server_default="")
    location = db.Column(db.String(100), nullable=False, default="", server_default="")
    interests = db.Column(db.String(200), nullable=False, default="", server_default="")
    occupation = db.Column(db.String(100), nullable=False, default="", server_default="")
    birthday = db.Column(db.String(10), nullable=False, default="", server_default="")
    avatar_id = db.Column(db.Integer, nullable=False, default=0, server_default="0")
    custom_avatar = db.Column(db.String(255), nullable=False, default="", server_default="")
    joined_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    last_seen = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    # 上一次访问（vB 的 lastvisit）：用来判断「有没有新帖」，不能和 last_seen（本次在线）混用
    last_visit = db.Column(db.DateTime(timezone=True), nullable=True)

    # ---- 用户选项（对应 vBulletin 2.x user 表的 editoptions 一组字段）----
    invisible = db.Column(db.Boolean, nullable=False, default=False, server_default="0")
    cookieuser = db.Column(db.Boolean, nullable=False, default=True, server_default="1")
    nosessionhash = db.Column(db.Boolean, nullable=False, default=False, server_default="0")
    allowmail = db.Column(db.Boolean, nullable=False, default=True, server_default="1")
    showemail = db.Column(db.Boolean, nullable=False, default=True, server_default="1")
    emailnotification = db.Column(db.Boolean, nullable=False, default=False, server_default="0")
    receivepm = db.Column(db.Boolean, nullable=False, default=True, server_default="1")
    emailonpm = db.Column(db.Boolean, nullable=False, default=True, server_default="1")
    pmpopup = db.Column(db.Boolean, nullable=False, default=True, server_default="1")
    showsignatures = db.Column(db.Boolean, nullable=False, default=True, server_default="1")
    showavatars = db.Column(db.Boolean, nullable=False, default=True, server_default="1")
    showimages = db.Column(db.Boolean, nullable=False, default=True, server_default="1")
    vbcode = db.Column(db.Boolean, nullable=False, default=True, server_default="1")
    prunedays = db.Column(db.Integer, nullable=False, default=-1, server_default="-1")
    umaxposts = db.Column(db.Integer, nullable=False, default=-1, server_default="-1")
    startofweek = db.Column(db.Integer, nullable=False, default=1, server_default="1")
    # vB 的时区偏移带半小时（-3.5 / +5.5），这里存分钟数：480 表示 +8:00
    timezoneoffset = db.Column(db.Integer, nullable=False, default=0, server_default="0")
    # 用户组：vB 用 usergroupid 指向 usergroup 表，usertitle 为空时取组的 usertitle
    referrerid = db.Column(db.Integer, default=0, nullable=False, server_default="0")
    usergroupid = db.Column(db.Integer, nullable=False, default=2, server_default="2")
    usertitle = db.Column(db.String(100), nullable=False, default="", server_default="")
    # vB 的 customtitle：1 表示用户自填头衔（usertitle 即自定义值），0 表示由组头衔/发帖数档位决定
    customtitle = db.Column(db.Integer, nullable=False, default=0, server_default="0")
    newstyleset = db.Column(db.Integer, nullable=False, default=0, server_default="0")
    buddylist = db.Column(db.String(255), nullable=False, default="", server_default="")
    ignorelist = db.Column(db.String(255), nullable=False, default="", server_default="")

    threads = db.relationship("Thread", back_populates="author", lazy="dynamic")
    posts = db.relationship(
        "Post", back_populates="author", lazy="dynamic", foreign_keys="Post.author_id"
    )
    # vB 用 avatar_id=0 表示「没有头像」，所以这里不加外键，改成显式 join
    avatar = db.relationship(
        "Avatar",
        primaryjoin="foreign(User.avatar_id) == Avatar.id",
        viewonly=True,
        lazy="select",
    )
    usergroup = db.relationship(
        "UserGroup",
        primaryjoin="foreign(User.usergroupid) == UserGroup.id",
        viewonly=True,
        lazy="select",
    )

    @property
    def usertitle_text(self) -> str:
        """vB 的 ``$post[usertitle]``：自定义头衔优先，其次用户组头衔，最后按发帖数分档。

        原版在注册 / 发帖 / 编辑资料时把「组头衔为空则按 usertitle 档位」的结果写回
        user.usertitle，并用 customtitle 标记是否用户自填。本地同样物化这个缓存，
        但读取时再兜底实时算一次，保证后台改档位后不会显示旧档。
        """
        if self.customtitle and self.usertitle:
            return self.usertitle
        group = self.usergroup
        if group is not None and group.usertitle:
            return group.usertitle
        return usertitle_for_posts(self.post_count) or self.usertitle

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


class UserTitle(db.Model):
    """User Titles：按发帖数分档的头衔（对应原版 usertitle 表）。"""

    __tablename__ = "usertitles"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False, default="", server_default="")
    minposts = db.Column(db.Integer, nullable=False, default=0, server_default="0")


def usertitle_for_posts(posts: int) -> str:
    """按原版取档口径返回头衔：minposts<=posts 里 minposts 最大的那一档。"""
    row = db.session.execute(
        select(UserTitle).where(UserTitle.minposts <= int(posts or 0))
        .order_by(UserTitle.minposts.desc(), UserTitle.id.desc())
    ).scalars().first()
    return row.title if row is not None else ""


class UserProfileField(db.Model):
    """User Profile Fields：自定义资料字段定义（对应原版 profilefield 表）。"""

    __tablename__ = "userprofilefields"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(60), nullable=False, default="", server_default="")
    description = db.Column(db.String(260), nullable=False, default="", server_default="")
    required = db.Column(db.Boolean, nullable=False, default=False, server_default="0")
    hidden = db.Column(db.Boolean, nullable=False, default=False, server_default="0")
    editable = db.Column(db.Boolean, nullable=False, default=True, server_default="1")
    maxlength = db.Column(db.Integer, nullable=False, default=100, server_default="100")
    size = db.Column(db.Integer, nullable=False, default=25, server_default="25")
    displayorder = db.Column(db.Integer, nullable=False, default=0, server_default="0")


class UserField(db.Model):
    """自定义资料字段的值（对应原版 userfield 表：userid + field1…fieldN）。

    参考站的 userfield 只有 field1…field4（profilefield 表就 4 条）；
    本地预备到 field10，后台新增字段时不必改表结构。
    """

    __tablename__ = "userfield"

    userid = db.Column(db.Integer, primary_key=True)
    field1 = db.Column(db.String(250), nullable=False, default="", server_default="")
    field2 = db.Column(db.String(250), nullable=False, default="", server_default="")
    field3 = db.Column(db.String(250), nullable=False, default="", server_default="")
    field4 = db.Column(db.String(250), nullable=False, default="", server_default="")
    field5 = db.Column(db.String(250), nullable=False, default="", server_default="")
    field6 = db.Column(db.String(250), nullable=False, default="", server_default="")
    field7 = db.Column(db.String(250), nullable=False, default="", server_default="")
    field8 = db.Column(db.String(250), nullable=False, default="", server_default="")
    field9 = db.Column(db.String(250), nullable=False, default="", server_default="")
    field10 = db.Column(db.String(250), nullable=False, default="", server_default="")

    def get_field(self, profilefieldid: int) -> str:
        """按 profilefieldid 取 fieldN；超出 1…10 的字段返回空串。"""
        if not 1 <= int(profilefieldid or 0) <= 10:
            return ""
        return getattr(self, f"field{int(profilefieldid)}", "") or ""

    def set_field(self, profilefieldid: int, value: str) -> None:
        if 1 <= int(profilefieldid or 0) <= 10:
            setattr(self, f"field{int(profilefieldid)}", value or "")


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

    @property
    def rating_stats(self) -> tuple[float, int]:
        """(平均分, 票数)。vB 的 threadrate 聚合；列表页由路由预先填 _rating_cache。"""
        cached = getattr(self, "_rating_cache", None)
        if cached is not None:
            return cached
        avg, count = db.session.execute(
            select(func.avg(ThreadRating.vote), func.count(ThreadRating.id)).where(
                ThreadRating.thread_id == self.id
            )
        ).one()
        return (float(avg or 0), int(count or 0))


class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(db.Integer, db.ForeignKey("threads.id"), nullable=False, index=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    # vB 的 post.title：每条帖子有自己的标题，回复默认是 "Re: 主题标题"
    title = db.Column(db.String(200), nullable=False, default="", server_default="")
    body = db.Column(db.Text, nullable=False, default="")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, index=True)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=True)
    # vB 的 edituserid：组 14 showeditedby 决定是否落这一列，用于「本帖最后由 X 修改」
    edit_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    # vB 的 post.ipaddress：组 15 logip 决定发帖时是否记录
    ipaddress = db.Column(db.String(45), nullable=True)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)
    # vB 的 iconid：发帖时选的帖子图标 1-14，0 = 不使用图标
    iconid = db.Column(db.Integer, nullable=False, default=0, server_default="0")
    # vB 的 post.allowsmilie：1 = 解析表情，0 = 本帖勾了「Disable Smilies」
    allowsmilie = db.Column(db.Integer, nullable=False, default=1, server_default="1")

    thread = db.relationship("Thread", back_populates="posts")
    author = db.relationship("User", back_populates="posts", foreign_keys=[author_id])
    edit_user = db.relationship("User", foreign_keys=[edit_user_id])
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


class Avatar(db.Model):
    """vB 2.3.11 的 ``avatar`` 表：后台可选头像库。"""

    __tablename__ = "avatars"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False, default="")
    minimumposts = db.Column(db.Integer, nullable=False, default=0)
    avatarpath = db.Column(db.String(255), nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Avatar {self.id} {self.title}>"


class Icon(db.Model):
    """vB 2.3.11 的 ``icon`` 表：帖子图标（后台 Post Icons 维护）。"""

    __tablename__ = "icons"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False, default="", server_default="")
    iconpath = db.Column(db.String(255), nullable=False, default="", server_default="")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Icon {self.id} {self.title}>"


class Smilie(db.Model):
    """vB 2.3.11 的 ``smilie`` 表：表情符号（后台 Smilies 维护）。"""

    __tablename__ = "smilies"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False, default="", server_default="")
    smilietext = db.Column(db.String(120), nullable=False, default="", server_default="")
    smiliepath = db.Column(db.String(255), nullable=False, default="", server_default="")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Smilie {self.id} {self.title}>"


class BBCode(db.Model):
    """vB 2.3.11 的 ``bbcode`` 表：自定义 vB Code 定义（后台 Custom vB Codes）。"""

    __tablename__ = "bbcodes"

    id = db.Column(db.Integer, primary_key=True)
    bbcodetag = db.Column(db.String(50), nullable=False, default="", server_default="")
    bbcodereplacement = db.Column(db.Text, nullable=False, default="", server_default="")
    bbcodeexample = db.Column(db.Text, nullable=False, default="", server_default="")
    bbcodeexplanation = db.Column(db.Text, nullable=False, default="", server_default="")
    twoparams = db.Column(db.Integer, nullable=False, default=0, server_default="0")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<BBCode {self.id} {self.bbcodetag}>"


class UserGroup(db.Model):
    """vB 2.3.11 的 ``usergroup`` 表（只保留显示身份要用到的两列）。"""

    __tablename__ = "usergroups"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False, default="")
    usertitle = db.Column(db.String(100), nullable=False, default="")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<UserGroup {self.id} {self.title}>"


# vB 2.3.11 admin/forumpermission.php:makeyesnocode 的 16 个权限字段，
# 顺序照该文件里 makeyesnocode 的调用顺序。
PERMISSION_FIELDS = (
    "canview",
    "cansearch",
    "canemail",
    "canpostnew",
    "canpostpoll",
    "canvote",
    "canpostattachment",
    "cangetattachment",
    "canmove",
    "canopenclose",
    "candeletethread",
    "canreplyown",
    "canreplyothers",
    "canviewothers",
    "caneditpost",
    "candeletepost",
)

# admin/forumpermission.php 里 makeyesnocode 的英文标签，逐条照抄。
PERMISSION_LABELS = {
    "canview": "Can view forum",
    "cansearch": "Can search",
    "canemail": "Can use 'email to friend' feature",
    "canpostnew": "Can post new threads",
    "canpostpoll": "Can post polls",
    "canvote": "Can vote on polls",
    "canpostattachment": "Can post attachments",
    "cangetattachment": "Can download attachments",
    "canmove": "Can move own threads to other forums",
    "canopenclose": "Can open / close own threads",
    "candeletethread": "Can delete own threads",
    "canreplyown": "Can reply to own threads",
    "canreplyothers": "Can reply to other's threads",
    "canviewothers": "Can view others' threads",
    "caneditpost": "Can edit own posts",
    "candeletepost": "Can delete own posts",
}


def _permission_columns() -> dict:
    return {
        field: db.Column(field, db.Boolean, nullable=False, default=True)
        for field in PERMISSION_FIELDS
    }


# admin/usergroup.php 里除 forumpermission 的 16 项之外，用户组级还要用到的权限/数值列。
# 顺序照该文件 add/edit 表单的 makeyesnocode 顺序。
GROUP_EXTRA_FIELDS = (
    "showgroup",
    "canviewmembers",
    "canmodifyprofile",
    "canthreadrate",
    "canusepm",
    "cantrackpm",
    "candenypmreceipts",
    "canpublicevent",
    "canpublicedit",
    "canwhosonline",
    "canwhosonlineip",
    "ismoderator",
    "cancontrolpanel",
)

GROUP_EXTRA_LABELS = {
    "showgroup": "Viewable on Show Groups?",
    "canviewmembers": "Can view members info (including other\'s profiles and members list)",
    "canmodifyprofile": "Can modify profile",
    "canthreadrate": "Can Rate threads if thread rating is enabled in the forum?",
    "canusepm": "Can use Private Messaging",
    "cantrackpm": "Can Use Message Tracking?",
    "candenypmreceipts": "Can Deny Private Message Read Receipt Request?",
    "canpublicevent": "Can post Public events on Calendar",
    "canpublicedit": "Can edit other\'s Public events on Calendar",
    "canwhosonline": "Can View Who\'s Online",
    "canwhosonlineip": "Can View IP Addresses on Who\'s Online",
    "ismoderator": "Is Super Moderator",
    "cancontrolpanel": "Can access control panel",
}


class UserGroupPermission(db.Model):
    """``usergroup`` 表里那 16 个 ``can*`` 默认权限列（本站在这里单独存）。

    对应参考站 admin/forumpermission.php 的「Use usergroup default」分支：
    某个版块没有 ``forumpermissions`` 记录时，就用这张表里该用户组的默认值。
    """

    __tablename__ = "usergroup_permissions"

    usergroup_id = db.Column(
        db.Integer, db.ForeignKey("usergroups.id"), primary_key=True
    )
    canview = db.Column(db.Boolean, nullable=False, default=True)
    cansearch = db.Column(db.Boolean, nullable=False, default=True)
    canemail = db.Column(db.Boolean, nullable=False, default=True)
    canpostnew = db.Column(db.Boolean, nullable=False, default=True)
    canpostpoll = db.Column(db.Boolean, nullable=False, default=True)
    canvote = db.Column(db.Boolean, nullable=False, default=True)
    canpostattachment = db.Column(db.Boolean, nullable=False, default=True)
    cangetattachment = db.Column(db.Boolean, nullable=False, default=True)
    canmove = db.Column(db.Boolean, nullable=False, default=False)
    canopenclose = db.Column(db.Boolean, nullable=False, default=False)
    candeletethread = db.Column(db.Boolean, nullable=False, default=False)
    canreplyown = db.Column(db.Boolean, nullable=False, default=True)
    canreplyothers = db.Column(db.Boolean, nullable=False, default=True)
    canviewothers = db.Column(db.Boolean, nullable=False, default=True)
    caneditpost = db.Column(db.Boolean, nullable=False, default=True)
    candeletepost = db.Column(db.Boolean, nullable=False, default=True)

    showgroup = db.Column(db.Boolean, nullable=False, default=False)
    canviewmembers = db.Column(db.Boolean, nullable=False, default=True)
    canmodifyprofile = db.Column(db.Boolean, nullable=False, default=True)
    canthreadrate = db.Column(db.Boolean, nullable=False, default=True)
    canusepm = db.Column(db.Boolean, nullable=False, default=True)
    cantrackpm = db.Column(db.Boolean, nullable=False, default=False)
    candenypmreceipts = db.Column(db.Boolean, nullable=False, default=False)
    canpublicevent = db.Column(db.Boolean, nullable=False, default=False)
    canpublicedit = db.Column(db.Boolean, nullable=False, default=False)
    canwhosonline = db.Column(db.Boolean, nullable=False, default=True)
    canwhosonlineip = db.Column(db.Boolean, nullable=False, default=False)
    ismoderator = db.Column(db.Boolean, nullable=False, default=False)
    cancontrolpanel = db.Column(db.Boolean, nullable=False, default=False)
    maxbuddypm = db.Column(db.Integer, nullable=False, default=0)
    maxforwardpm = db.Column(db.Integer, nullable=False, default=0)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<UserGroupPermission {self.usergroup_id}>"


class ForumPermission(db.Model):
    """vB 2.3.11 的 ``forumpermission`` 表：某版块对某用户组的自定义权限。"""

    __tablename__ = "forumpermissions"

    id = db.Column(db.Integer, primary_key=True)
    usergroup_id = db.Column(
        db.Integer, db.ForeignKey("usergroups.id"), nullable=False, index=True
    )
    forum_id = db.Column(
        db.Integer, db.ForeignKey("forums.id"), nullable=False, index=True
    )
    canview = db.Column(db.Boolean, nullable=False, default=True)
    cansearch = db.Column(db.Boolean, nullable=False, default=True)
    canemail = db.Column(db.Boolean, nullable=False, default=True)
    canpostnew = db.Column(db.Boolean, nullable=False, default=True)
    canpostpoll = db.Column(db.Boolean, nullable=False, default=True)
    canvote = db.Column(db.Boolean, nullable=False, default=True)
    canpostattachment = db.Column(db.Boolean, nullable=False, default=True)
    cangetattachment = db.Column(db.Boolean, nullable=False, default=True)
    canmove = db.Column(db.Boolean, nullable=False, default=False)
    canopenclose = db.Column(db.Boolean, nullable=False, default=False)
    candeletethread = db.Column(db.Boolean, nullable=False, default=False)
    canreplyown = db.Column(db.Boolean, nullable=False, default=True)
    canreplyothers = db.Column(db.Boolean, nullable=False, default=True)
    canviewothers = db.Column(db.Boolean, nullable=False, default=True)
    caneditpost = db.Column(db.Boolean, nullable=False, default=True)
    candeletepost = db.Column(db.Boolean, nullable=False, default=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ForumPermission {self.id} forum={self.forum_id} group={self.usergroup_id}>"



class ForumRead(db.Model):
    """vB 2.3.11 的 ``forumread`` 表：记录每个用户在每个版块「已读到此」的时间。

    ``forum_id = -1`` 表示「全部版块标记为已读」。
    """

    __tablename__ = "forum_reads"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    forum_id = db.Column(db.Integer, nullable=False, default=-1, index=True)
    marked_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ForumRead user={self.user_id} forum={self.forum_id}>"


class ThreadSubscription(db.Model):
    """vB 的 ``subscribethread`` 表：用户订阅某个主题，UCP 中可列出来。"""

    __tablename__ = "thread_subscriptions"
    __table_args__ = (db.UniqueConstraint("thread_id", "user_id", name="uq_thread_subscription"),)

    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(db.Integer, db.ForeignKey("threads.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    thread = db.relationship("Thread")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ThreadSubscription thread={self.thread_id} user={self.user_id}>"


class ThreadRating(db.Model):
    """vB 的 ``threadrate`` 表：一个用户对一个主题只能有一票，再投即改票。"""

    __tablename__ = "thread_ratings"
    __table_args__ = (db.UniqueConstraint("thread_id", "user_id", name="uq_thread_rating"),)

    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(db.Integer, db.ForeignKey("threads.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    vote = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ThreadRating thread={self.thread_id} user={self.user_id} vote={self.vote}>"


class PostReport(db.Model):
    """vB 的 reported post：会员举报某条帖子，后台 Moderation 组里处理。"""

    __tablename__ = "post_reports"

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False, index=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    reason = db.Column(db.String(50), nullable=False, default="", server_default="")
    note = db.Column(db.Text, nullable=False, default="")
    resolved = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    post = db.relationship("Post")
    reporter = db.relationship("User")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<PostReport post={self.post_id} by={self.reporter_id} resolved={self.resolved}>"


class EmailLog(db.Model):
    """待发邮件记录：本地演示环境没有 SMTP，sendtofriend 只把内容落库并展示。"""
    __tablename__ = "email_log"

    id = db.Column(db.Integer, primary_key=True)
    to_email = db.Column(db.String(150), nullable=False)
    from_name = db.Column(db.String(100), nullable=False, default="", server_default="")
    subject = db.Column(db.String(200), nullable=False, default="", server_default="")
    body = db.Column(db.Text, nullable=False, default="")
    thread_id = db.Column(db.Integer, db.ForeignKey("threads.id"), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<EmailLog to={self.to_email} subject={self.subject}>"


class Poll(db.Model):
    """vB 的 poll 表：发新主题时可附一个投票。"""

    __tablename__ = "polls"

    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(db.Integer, db.ForeignKey("threads.id"), nullable=False, index=True)
    question = db.Column(db.String(200), nullable=False)
    is_closed = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    thread = db.relationship("Thread")
    options = db.relationship(
        "PollOption", back_populates="poll", cascade="all, delete-orphan", order_by="PollOption.position"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Poll {self.question}>"


class PollOption(db.Model):
    __tablename__ = "poll_options"

    id = db.Column(db.Integer, primary_key=True)
    poll_id = db.Column(db.Integer, db.ForeignKey("polls.id"), nullable=False, index=True)
    position = db.Column(db.Integer, nullable=False, default=0)
    text = db.Column(db.String(200), nullable=False)

    poll = db.relationship("Poll", back_populates="options")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<PollOption {self.text}>"


class PollVote(db.Model):
    """一个用户对一个投票只能投一票（vB 的 voterlist 语义）。"""

    __tablename__ = "poll_votes"
    __table_args__ = (db.UniqueConstraint("poll_id", "user_id", name="uq_poll_vote"),)

    id = db.Column(db.Integer, primary_key=True)
    poll_id = db.Column(db.Integer, db.ForeignKey("polls.id"), nullable=False, index=True)
    option_id = db.Column(db.Integer, db.ForeignKey("poll_options.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    poll = db.relationship("Poll")
    option = db.relationship("PollOption")
    user = db.relationship("User")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<PollVote poll={self.poll_id} user={self.user_id} option={self.option_id}>"


class OnlineSession(db.Model):
    """vB session 表的对应物：在线用户页（online.php）的 lastactivity / location / host。

    vB 的 session 行同时承载会员与游客；本站用同一张表区分：user_id 为空即为游客。
    """

    __tablename__ = "online_sessions"

    id = db.Column(db.Integer, primary_key=True)
    session_hash = db.Column(db.String(40), nullable=False, unique=True, index=True)
    user_id = db.Column(db.Integer, nullable=True, index=True)
    ip = db.Column(db.String(45), nullable=False, default="", server_default="")
    location = db.Column(db.String(255), nullable=False, default="", server_default="")
    last_activity = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<OnlineSession {self.session_hash[:8]} user={self.user_id}>"


class Announcement(db.Model):
    """vB 的 announcement 表（后台 Announcements → Add / Modify）。

    参考站表结构：announcementid, title, userid, startdate, enddate, pagetext, forumid，
    其中 forumid=-1 表示「全站公告」，否则只在那个版块显示。
    原版把 allowhtml / allowvbcode / allowsmilies 只在提交时用于解析正文，不落库，
    所以这里同样不存那三个开关。
    """

    __tablename__ = "announcements"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, default="")
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    # -1 表示全站公告；其它值等于版块 id
    forum_id = db.Column(db.Integer, nullable=False, default=-1, server_default="-1", index=True)
    start_date = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    end_date = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    pagetext = db.Column(db.Text, nullable=False, default="")

    author = db.relationship("User")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Announcement {self.id} forum={self.forum_id} {self.title}>"

class AdminLog(db.Model):
    """vB 2.3.11 的 ``adminlog`` 表：后台操作日志（后台 Statistics & Logs → Admin Log）。"""

    __tablename__ = "admin_log"

    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    dateline = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    script = db.Column(db.String(120), nullable=False, default="", server_default="")
    action = db.Column(db.String(120), nullable=False, default="", server_default="")
    extrainfo = db.Column(db.String(255), nullable=False, default="", server_default="")
    ipaddress = db.Column(db.String(45), nullable=False, default="", server_default="")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AdminLog {self.id} {self.script} {self.action}>"


class Replacement(db.Model):
    """vB 2.3.11 的 ``replacement`` 表：替换集里的一条 findword → replaceword。"""

    __tablename__ = "replacements"

    id = db.Column(db.Integer, primary_key=True)
    replacementsetid = db.Column(db.Integer, nullable=False, default=-1, server_default="-1", index=True)
    findword = db.Column(db.String(255), nullable=False, default="", server_default="")
    replaceword = db.Column(db.Text, nullable=False, default="", server_default="")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Replacement {self.id} {self.findword}>"


class Template(db.Model):
    """vB 2.3.11 的 ``template`` 表：模板集里的一条 title → template。"""

    __tablename__ = "templates"

    id = db.Column(db.Integer, primary_key=True)
    templatesetid = db.Column(db.Integer, nullable=False, default=-1, server_default="-1", index=True)
    title = db.Column(db.String(120), nullable=False, default="", server_default="")
    template = db.Column(db.Text, nullable=False, default="", server_default="")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Template {self.id} {self.title}>"


class ReplacementSet(db.Model):
    """vB 2.3.11 的 ``replacementset`` 表：文字替换集（命名容器）。"""

    __tablename__ = "replacement_sets"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False, default="", server_default="")


class TemplateSet(db.Model):
    """vB 2.3.11 的 ``templateset`` 表：模板集（命名容器）。"""

    __tablename__ = "template_sets"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False, default="", server_default="")


class StyleSet(db.Model):
    """vB 2.3.11 的 ``style`` 表：风格集。"""

    __tablename__ = "style_sets"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False, default="", server_default="")
    replacementsetid = db.Column(db.Integer, nullable=False, default=-1, server_default="-1")
    templatesetid = db.Column(db.Integer, nullable=False, default=-1, server_default="-1")
    userselect = db.Column(db.Integer, nullable=False, default=1, server_default="1")

