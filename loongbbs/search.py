"""Keyword search over thread titles and post bodies, with vB-style advanced options."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from flask import Blueprint, render_template, request
from sqlalchemy import or_, select

from .extensions import db
from .models import Forum, Post, Thread, User
from .utils import clamp_page, page_args, render_body

bp = Blueprint("search", __name__)

SORT_FIELDS = ("lastpost", "dateline", "replycount", "views")


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
    query = (request.args.get("q") or "").strip()
    page = clamp_page(request.args.get("page"))
    forum_id = request.args.get("forum", type=int)
    selected_forum = db.session.get(Forum, forum_id) if forum_id else None
    per_page = 20

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
    if query and not author_missing:
        pattern = f"%{query}%"

        title_query = select(Thread).where(Thread.title.ilike(pattern))
        post_query = select(Post).join(Thread, Post.thread_id == Thread.id).where(
            Post.body.ilike(pattern), Post.is_deleted.is_(False)
        )
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
                        "matched_in": "标题",
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
                        "matched_in": "正文",
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
