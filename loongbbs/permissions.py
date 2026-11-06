"""版块权限：vB 2.3.11 的 getpermissions() + admin/forumpermission.php 的落库语义。

参考站取值链（includes/functions.php:getpermissions）：
1. ``forumpermission`` 表里该 (forumid, usergroupid) 的记录 → 自定义权限；
2. 没有则看父版块链上有没有自定义记录（``getforumlist`` 递归）→ 继承；
3. 都没有 → 该用户组在 ``usergroup`` 表里的 16 个 ``can*`` 默认列。

本站版块只有「分类 → 版块」两层、没有子版块，所以第 2 步的继承链最多只到 0 层，
与参考站只有分类和版块时的表现一致（列表页不会出现「蓝色」继承行）。
"""

from __future__ import annotations

from sqlalchemy import select

from .extensions import db
from .models import PERMISSION_FIELDS, ForumPermission, UserGroupPermission

# vB 的 1 号用户组就是「未登录」；本地 usergroups 表第 1 行同样是
# Unregistered / Not Logged In。
GUEST_USERGROUP_ID = 1
# 注册用户组（本地 users.loongfan 用的是 2）
REGISTERED_USERGROUP_ID = 2

# 参考站 MariaDB ``vbulletin.usergroup`` 表 16 个 can* 列的原值（7 个用户组）。
# 顺序同 models.PERMISSION_FIELDS：canview, cansearch, canemail, canpostnew,
# canpostpoll, canvote, canpostattachment, cangetattachment, canmove,
# canopenclose, candeletethread, canreplyown, canreplyothers, canviewothers,
# caneditpost, candeletepost
_SEED: dict[int, tuple[int, ...]] = {
    1: (1, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0),  # Unregistered
    2: (1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1),  # Registered
    3: (1, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0),  # Awaiting Email
    4: (1, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0),  # COPPA Awaiting
    5: (1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1),  # Super Moderators
    6: (1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1),  # Administrators
    7: (1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 1),  # Moderators
}


def ensure_seed() -> None:
    """首次运行时把 usergroup 的默认权限写成参考站原值（幂等）。"""
    if db.session.scalar(select(UserGroupPermission.usergroup_id).limit(1)) is not None:
        return
    for usergroup_id, values in _SEED.items():
        row = UserGroupPermission(usergroup_id=usergroup_id)
        for field, value in zip(PERMISSION_FIELDS, values):
            setattr(row, field, bool(value))
        db.session.add(row)
    db.session.commit()


def group_defaults(usergroup_id: int) -> dict[str, bool]:
    row = db.session.get(UserGroupPermission, usergroup_id)
    if row is None:
        return {field: True for field in PERMISSION_FIELDS}
    return {field: bool(getattr(row, field)) for field in PERMISSION_FIELDS}


def forum_override(forum_id: int, usergroup_id: int) -> ForumPermission | None:
    """该版块对该用户组的自定义权限记录（没有就是 None）。"""
    return db.session.scalar(
        select(ForumPermission).where(
            ForumPermission.forum_id == forum_id,
            ForumPermission.usergroup_id == usergroup_id,
        )
    )


def permissions_for_group(forum_id: int, usergroup_id: int) -> dict[str, bool]:
    override = forum_override(forum_id, usergroup_id)
    if override is not None:
        return {field: bool(getattr(override, field)) for field in PERMISSION_FIELDS}
    return group_defaults(usergroup_id)


def current_usergroup_id(user) -> int:
    if getattr(user, "is_authenticated", False):
        return int(getattr(user, "usergroupid", 0) or REGISTERED_USERGROUP_ID)
    return GUEST_USERGROUP_ID


def current_permissions(forum_id: int | None) -> dict[str, bool]:
    """当前登录用户（或游客）在某个版块上的权限。forum_id=None 用游客默认。"""
    from flask_login import current_user

    usergroup_id = current_usergroup_id(current_user)
    if forum_id is None:
        return group_defaults(usergroup_id)
    return permissions_for_group(forum_id, usergroup_id)


def can(permission: str, forum_id: int | None) -> bool:
    return current_permissions(forum_id).get(permission, True)
