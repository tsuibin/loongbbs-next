"""Keyword search over thread titles and post bodies."""
from __future__ import annotations

from flask import Blueprint, render_template, request
from sqlalchemy import or_, select

from .extensions import db
from .models import Forum, Post, Thread
from .utils import clamp_page, page_args, render_body

bp = Blueprint("search", __name__)


@bp.get("/search")
def search():
    query = (request.args.get("q") or "").strip()
    page = clamp_page(request.args.get("page"))
    forum_id = request.args.get("forum", type=int)
    selected_forum = db.session.get(Forum, forum_id) if forum_id else None
    per_page = 20

    results: list[dict] = []
    total = 0
    if query:
        pattern = f"%{query}%"

        title_query = select(Thread).where(Thread.title.ilike(pattern))
        post_query = select(Post).join(Thread, Post.thread_id == Thread.id).where(
            Post.body.ilike(pattern), Post.is_deleted.is_(False)
        )
        if selected_forum is not None:
            title_query = title_query.where(Thread.forum_id == selected_forum.id)
            post_query = post_query.where(Thread.forum_id == selected_forum.id)

        title_matches = db.session.execute(
            title_query.order_by(Thread.last_post_at.desc()).limit(50)
        ).scalars().all()

        post_matches = db.session.execute(
            post_query.order_by(Post.created_at.desc()).limit(80)
        ).scalars().all()

        seen_threads: set[int] = set()
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
        for post in post_matches:
            if post.thread_id in seen_threads:
                continue
            seen_threads.add(post.thread_id)
            body = post.body or ""
            position = body.lower().find(query.lower())
            snippet = body[max(0, position - 40) : position + 120] if position >= 0 else body[:160]
            results.append(
                {
                    "thread": post.thread,
                    "post": post,
                    "snippet": render_body(snippet),
                    "matched_in": "正文",
                }
            )

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
    )
