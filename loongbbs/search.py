"""Keyword search over thread titles and post bodies, with vB-style advanced options."""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

from flask import Blueprint, render_template, request, session
from sqlalchemy import or_, select

from .extensions import db
from .i18n import translate
from .models import Forum, Post, Thread, User
from .settings import get_setting
from .utils import clamp_page, page_args, render_body

bp = Blueprint("search", __name__)

SORT_FIELDS = ("lastpost", "dateline", "replycount", "views")

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

    query = (request.args.get("q") or "").strip()
    submitted = "q" in request.args
    page = clamp_page(request.args.get("page"))
    forum_id = request.args.get("forum", type=int)
    selected_forum = db.session.get(Forum, forum_id) if forum_id else None
    per_page = _setting_int("searchperpage", 25, low=1)

    # 组 10 searchfloodtime：两次搜索之间的最小间隔（按会话记录上次搜索时间）
    flood = _setting_int("searchfloodtime", 0, low=0, high=3600)
    if flood > 0 and (query or (request.args.get("author") or "").strip()):
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

    # 高级选项：对应 vB search.php 的 searchuser / startdate / enddate / sortby / sortorder / searchposts
    author = (request.args.get("author") or "").strip()
    startdate_raw = (request.args.get("startdate") or "").strip()
    enddate_raw = (request.args.get("enddate") or "").strip()
    sortby = (request.args.get("sortby") or "lastpost").lower()
    if sortby not in SORT_FIELDS:
        sortby = "lastpost"
    sortorder = (request.args.get("sortorder") or "desc").lower()
    if sortorder not in {"asc", "desc"}:
        sortorder = "desc"
    searchin = (request.args.get("searchin") or "both").lower()
    if searchin not in {"title", "body", "both"}:
        searchin = "both"

    startdate = _parse_date(startdate_raw)
    enddate = _parse_date(enddate_raw)
    end_exclusive = enddate + timedelta(days=1) if enddate else None

    author_user = None
    author_missing = False
    if author:
        author_user = db.session.scalar(select(User).where(User.username == author))
        if author_user is None:
            author_missing = True

    results: list[dict] = []
    total = 0
    if submitted and not query and not author and not author_missing:
        return _error("请给出要搜索的词，或一个有效的用户名。")
    # 原版 search.php：没有关键词但给了有效用户名时，也按用户搜
    if (query or author_user is not None) and not author_missing:
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
        if author_user is not None:
            title_query = title_query.where(Thread.author_id == author_user.id)
            post_query = post_query.where(Post.author_id == author_user.id)
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
            if sortby == "dateline":
                return _naive(thread_obj.created_at) or datetime.min
            return _naive(thread_obj.last_post_at) or datetime.min

        results.sort(key=sort_key, reverse=(sortorder == "desc"))

        total = len(results)
        results = results[(page - 1) * per_page : page * per_page]
        session["search_last_at"] = time.time()

    return render_template(
        "search.html",
        query=query,
        results=results,
        total=total,
        page=page,
        pages=max(1, (total + per_page - 1) // per_page),
        page_args=page_args,
        selected_forum=selected_forum,
        author=author,
        author_missing=author_missing,
        startdate=startdate_raw,
        enddate=enddate_raw,
        sortby=sortby,
        sortorder=sortorder,
        searchin=searchin,
    )
