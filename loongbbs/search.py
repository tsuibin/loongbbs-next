"""Keyword search over thread titles and post bodies, with vB-style advanced options."""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

from flask import Blueprint, render_template, request, session
from sqlalchemy import func, or_, select

from .extensions import db
from .i18n import translate
from .models import Category, Forum, Post, Thread, User, utcnow
from .settings import get_setting
from .utils import clamp_page, page_args, render_body

bp = Blueprint("search", __name__)

SORT_FIELDS = ("lastpost", "dateline", "replycount", "views", "title", "poster", "forum")

# 参考站 sortby 的六个值 → 本站内部排序键（另兼容本站旧参数值）
SORT_ALIASES = {
    "title": "title",
    "replies": "replycount",
    "views": "views",
    "lastpost": "lastpost",
    "poster": "poster",
    "forum": "forum",
    "dateline": "dateline",
    "replycount": "replycount",
}

# 与 vB 一致：只在 words 之间用空白，操作符不参与匹配
SEARCH_OPERATORS = {"and", "or", "not"}


def _setting_int(name: str, default: int, low: int = 0, high: int = 200) -> int:
    try:
        value = int(get_setting(name, str(default)) or default)
    except (TypeError, ValueError):
        value = default
    return max(low, min(value, high))


def _error(message: str):
    return render_template("search_error.html", message=message)


def _apply_min_length(query: str, min_len: int) -> tuple[str, str | None]:
    """按原版 search.php 的规则处理最小词长：首个短词跳过，AND 后面的短词报错。"""
    kept: list[str] = []
    for index, word in enumerate(query.split()):
        if word.lower() in SEARCH_OPERATORS:
            kept.append(word)
            continue
        # 原版对含 * 的词按「去掉 * 的长度 + 1」算，中文按字节数
        body = word.replace("*", "")
        length = len(body.encode("utf-8")) + (1 if "*" in word else 0)
        if min_len and length < min_len:
            if index == 0:
                continue
            if kept and kept[-1].lower() == "and":
                return query, (
                    f"你指定的搜索词（{word}）低于最小词长（{min_len}），因此不会被搜到。请把这个词写长一些。"
                )
            continue
        kept.append(word)
    return " ".join(kept), None


def _parse_date(raw: str | None) -> datetime | None:
    """vB 的日期搜索用 MM-DD-YYYY；这里同时接受 YYYY-MM-DD 与 MM-DD-YYYY。"""
    if not raw:
        return None
    raw = raw.strip()
    for fmt in ("%Y-%m-%d", "%m-%d-%Y"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def _naive(dt):
    if dt is None:
        return None
    return dt.astimezone(timezone.utc).replace(tzinfo=None) if dt.tzinfo else dt


@bp.get("/search")
def search():
    # 组 10 enablesearches：管理员关掉后照原版直接给错误页
    if get_setting("enablesearches") != "1":
        return _error("抱歉！管理员关闭了搜索功能。")

    # usergroup 级的 cansearch（原版 search.php 一开始就查这个）
    from .permissions import can

    if not can("cansearch", None):
        return _error("抱歉！你所在的用户组没有搜索权限。")

    args = request.args
    query = (args.get("query") or args.get("q") or "").strip()
    searchuser = (args.get("searchuser") or args.get("author") or "").strip()
    # 参考站 exactname: yes=精确匹配用户名，no=部分匹配
    exactname = (args.get("exactname") or "yes").lower() != "no"
    titleonly = (args.get("titleonly") or "").lower() == "yes"
    showposts = (args.get("showposts") or "") == "1"
    submitted = any(k in args for k in ("query", "q", "searchuser", "author", "action"))
    page = clamp_page(args.get("page"))
    per_page = _setting_int("searchperpage", 25, low=1)

    # 版块：参考站 forumchoice=-1 是「搜索所有开放版块」
    forum_raw = (args.get("forumchoice") or args.get("forum") or "").strip()
    forum_id = int(forum_raw) if forum_raw.isdigit() and int(forum_raw) > 0 else None
    selected_forum = db.session.get(Forum, forum_id) if forum_id else None

    # 组 10 searchfloodtime：两次搜索之间的最小间隔（按会话记录上次搜索时间）
    flood = _setting_int("searchfloodtime", 0, low=0, high=3600)
    if flood > 0 and (query or searchuser):
        last = session.get("search_last_at")
        try:
            last_value = float(last) if last is not None else None
        except (TypeError, ValueError):
            last_value = None
        if last_value is not None and time.time() - last_value < flood:
            return _error(f"抱歉！管理员规定每 {flood} 秒只能搜索一次。")

    # 组 10 minsearchlength：短词按原版规则过滤/报错
    min_len = _setting_int("minsearchlength", 4, low=0)
    if query and min_len:
        query, problem = _apply_min_length(query, min_len)
        if problem:
            return _error(problem)

    # 日期：参考站 searchdate 是「几天前」的档位（-1 不限），beforeafter 决定边界
    sd_raw = (args.get("startdate") or "").strip()
    ed_raw = (args.get("enddate") or "").strip()
    try:
        searchdate = int(args.get("searchdate") or -1)
    except (TypeError, ValueError):
        searchdate = -1
    if searchdate < 0:
        searchdate = -1
    beforeafter = (args.get("beforeafter") or "after").lower()
    if beforeafter not in {"after", "before"}:
        beforeafter = "after"

    # 排序：参考站 sortby=title/replies/views/lastpost/poster/forum
    sortby = (args.get("sortby") or "lastpost").lower()
    sortby = SORT_ALIASES.get(sortby, "lastpost")
    sortorder_raw = (args.get("sortorder") or "descending").lower()
    sortorder = "asc" if sortorder_raw in {"ascending", "asc"} else "desc"
    searchin = (args.get("searchin") or "both").lower()
    if titleonly:
        searchin = "title"
    if searchin not in {"title", "body", "both"}:
        searchin = "both"

    startdate = _parse_date(sd_raw)
    enddate = _parse_date(ed_raw)
    end_exclusive = enddate + timedelta(days=1) if enddate else None
    if searchdate > 0 and not sd_raw and not ed_raw:
        edge = _naive(utcnow()) - timedelta(days=searchdate)
        if beforeafter == "before":
            end_exclusive = edge
        else:
            startdate = edge

    author_ids: list[int] = []
    author_missing = False
    if searchuser:
        if exactname:
            found = db.session.scalar(select(User).where(func.lower(User.username) == searchuser.lower()))
            if found is None:
                author_missing = True
            else:
                author_ids = [found.id]
        else:
            matches = db.session.execute(
                select(User).where(User.username.ilike(f"%{searchuser}%"))
            ).scalars().all()
            author_ids = [user.id for user in matches]
            if not author_ids:
                author_missing = True

    results: list[dict] = []
    total = 0
    if searchuser and author_missing:
        return _error(f"没有找到会员「{searchuser}」。")
    if not query and not author_ids:
        if submitted:
            return _error("请给出要搜索的词，或一个有效的用户名。")
    if (query or author_ids) and not author_missing:
        # 组 10 allowwildcards：打开时 * 当通配符，关闭时按普通字符处理
        allow_wild = get_setting("allowwildcards") == "1"
        term = query.replace("*", "%") if allow_wild else query
        pattern = f"%{term}%"

        title_query = select(Thread)
        post_query = select(Post).join(Thread, Post.thread_id == Thread.id).where(
            Post.is_deleted.is_(False)
        )
        if query:
            title_query = title_query.where(Thread.title.ilike(pattern))
            post_query = post_query.where(Post.body.ilike(pattern))
        if selected_forum is not None:
            title_query = title_query.where(Thread.forum_id == selected_forum.id)
            post_query = post_query.where(Thread.forum_id == selected_forum.id)
        if author_ids:
            title_query = title_query.where(Thread.author_id.in_(author_ids))
            post_query = post_query.where(Post.author_id.in_(author_ids))
        if startdate is not None:
            title_query = title_query.where(Thread.last_post_at >= startdate)
            post_query = post_query.where(Post.created_at >= startdate)
        if end_exclusive is not None:
            title_query = title_query.where(Thread.last_post_at < end_exclusive)
            post_query = post_query.where(Post.created_at < end_exclusive)

        seen_threads: set[int] = set()
        if searchin in {"title", "both"}:
            title_matches = db.session.execute(
                title_query.order_by(Thread.last_post_at.desc()).limit(50)
            ).scalars().all()
            for thread_obj in title_matches:
                if thread_obj.id in seen_threads:
                    continue
                seen_threads.add(thread_obj.id)
                results.append(
                    {
                        "thread": thread_obj,
                        "post": None,
                        "snippet": render_body(thread_obj.title),
                        "matched_in": translate("标题"),
                    }
                )

        if searchin in {"body", "both"}:
            post_matches = db.session.execute(
                post_query.order_by(Post.created_at.desc()).limit(80)
            ).scalars().all()
            for post in post_matches:
                if post.thread_id in seen_threads:
                    continue
                seen_threads.add(post.thread_id)
                body = post.body or ""
                position = body.lower().find(query.lower())
                snippet = (
                    body[max(0, position - 40) : position + 120] if position >= 0 else body[:160]
                )
                results.append(
                    {
                        "thread": post.thread,
                        "post": post,
                        "snippet": render_body(snippet),
                        "matched_in": translate("正文"),
                    }
                )

        # 排序：vB 的 sortby 选项，默认按最后发表
        def sort_key(item: dict):
            thread_obj = item["thread"]
            if sortby == "replycount":
                return thread_obj.reply_count
            if sortby == "views":
                return thread_obj.views
            if sortby == "title":
                return (thread_obj.title or "").lower()
            if sortby == "poster":
                return (thread_obj.author.username if thread_obj.author else "").lower()
            if sortby == "forum":
                return (thread_obj.forum.name if thread_obj.forum else "").lower()
            if sortby == "dateline":
                return _naive(thread_obj.created_at) or datetime.min
            return _naive(thread_obj.last_post_at) or datetime.min

        if sortby in {"title", "poster", "forum"}:
            results.sort(key=sort_key, reverse=(sortorder == "desc"))
        else:
            results.sort(key=lambda item: sort_key(item) or datetime.min, reverse=(sortorder == "desc"))
        total = len(results)
        first = (page - 1) * per_page
        results = results[first : first + per_page]
        session["search_last_at"] = time.time()
        limitlower = first + 1 if total else 0
        limitupper = first + len(results)
    else:
        limitlower = limitupper = 0

    if query or author_ids:
        categories = (
            db.session.execute(select(Category).order_by(Category.position)).scalars().all()
        )
        return render_template(
            "search_results.html",
            query=query,
            results=results,
            total=total,
            page=page,
            pages=max(1, (total + per_page - 1) // per_page),
            page_args=page_args,
            selected_forum=selected_forum,
            author=searchuser,
            sortby=sortby,
            sortorder=sortorder,
            searchin=searchin,
            showposts=showposts,
            limitlower=limitlower,
            limitupper=limitupper,
            categories=categories,
            forumchoice=forum_id,
            searchdate=searchdate,
            beforeafter=beforeafter,
            exactname=exactname,
            titleonly=titleonly,
        )

    categories = db.session.execute(select(Category).order_by(Category.position)).scalars().all()
    return render_template(
        "search.html",
        query=query,
        searchuser=searchuser,
        select_forum=selected_forum,
        exactname=exactname,
        categories=categories,
        forumchoice=forum_id,
        searchdate=searchdate,
        beforeafter=beforeafter,
        sortby=sortby,
        sortorder=sortorder,
        titleonly=titleonly,
    )
